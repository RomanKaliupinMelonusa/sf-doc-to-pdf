#!/usr/bin/env python3
"""
Deterministic Salesforce Developer Docs exporter — v2 (browser-driven).

Why v2: /docs/get_document/* returns 403 to plain HTTP clients (Akamai bot
protection). So all requests now go through a real Chromium session:

  1. Open the docs site once (Akamai cookies get set).
  2. Fetch the TOC JSON *from inside the page* via fetch() -> deterministic tree.
     Fallback: scrape the fully-expanded sidebar nav (same tree, from the DOM).
  3. For each page in the subtree: page.goto(url) -> hide site chrome -> page.pdf().
  4. Mirror the TOC hierarchy as folders, write manifest.json, zip it all.
     Optional: merge into one combined.pdf.

Usage:
  pip install playwright pypdf
  playwright install chromium

  python sfdocs_export.py --doc commerce.pwa-kit-managed-runtime --inspect
  python sfdocs_export.py --doc commerce.pwa-kit-managed-runtime \
      --root "Storefront Next" --out ./sfnext-docs --merge

  # If you hit bot-detection issues, run headed once:
  python sfdocs_export.py ... --headed
"""

import argparse
import json
import re
import shutil
import sys
import time
from pathlib import Path

BASE = "https://developer.salesforce.com"
PAGE_DELAY = 0.5          # polite delay between page loads (seconds)
NAV_TIMEOUT_MS = 45_000

HIDE_CHROME_CSS = """
header, footer, nav, aside,
[class*="header"], [class*="Header"],
[class*="sidebar"], [class*="Sidebar"],
[class*="leftNav"], [class*="left-nav"],
[class*="breadcrumb"], [class*="Breadcrumb"],
[class*="feedback"], [class*="Feedback"],
[class*="toc-right"], [id*="onetrust"], [class*="cookie"] {
  display: none !important;
}
main, [role="main"], [class*="content"] {
  margin: 0 !important; padding: 12px !important; max-width: 100% !important;
}
body { overflow: visible !important; }
"""

# ---------------------------------------------------------------------------
# TOC: in-browser JSON fetch (primary) + sidebar DOM scrape (fallback)
# ---------------------------------------------------------------------------

FETCH_TOC_JS = """
async (docId) => {
  const r = await fetch(`/docs/get_document/${docId}`, {
    headers: { accept: 'application/json' },
    credentials: 'include',
  });
  if (!r.ok) return { __error: r.status };
  return await r.json();
}
"""

# Expand every collapsible item in the left nav, then serialize the UL/LI tree.
SCRAPE_SIDEBAR_JS = """
async () => {
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));
  // Find the nav containing doc links
  const navs = [...document.querySelectorAll('nav, aside, [class*="sidebar"], [class*="Sidebar"]')];
  const nav = navs.find(n => n.querySelectorAll('a[href*="/docs/"]').length > 3);
  if (!nav) return { __error: 'sidebar nav not found' };

  // Keep clicking unexpanded toggles until none remain (lazy-rendered trees)
  for (let pass = 0; pass < 30; pass++) {
    const toggles = [...nav.querySelectorAll(
      '[aria-expanded="false"], button[class*="expand"], button[class*="toggle"], [class*="chevron"]'
    )].filter(el => el.offsetParent !== null);
    if (!toggles.length) break;
    toggles.forEach(t => t.click());
    await sleep(250);
  }

  const serialize = (ul) => [...ul.children]
    .filter(li => li.tagName === 'LI')
    .map(li => {
      const a = li.querySelector(':scope a[href], :scope > * a[href]');
      const childUl = li.querySelector(':scope ul, :scope > * ul');
      return {
        text: (a ? a.textContent : li.textContent || '').trim().split('\\n')[0],
        href: a ? a.getAttribute('href') : null,
        children: childUl ? serialize(childUl) : [],
      };
    });

  const topUl = nav.querySelector('ul');
  if (!topUl) return { __error: 'no list inside nav' };
  return { toc: serialize(topUl) };
}
"""


def node_title(node):
    for key in ("text", "title", "label", "name"):
        v = node.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return node.get("id", "untitled")


def node_href(node):
    a_attr = node.get("a_attr") or {}
    for c in (a_attr.get("href"), node.get("href"), node.get("link"), node.get("url")):
        if isinstance(c, str) and c.strip():
            return c.strip()
    return None


def node_children(node):
    ch = node.get("children")
    return ch if isinstance(ch, list) else []


def toc_roots(toc_json):
    for key in ("toc", "tocItems", "items", "children"):
        v = toc_json.get(key)
        if isinstance(v, list):
            return v
    for v in toc_json.values():
        if isinstance(v, dict):
            inner = toc_roots(v)
            if inner:
                return inner
    return []


def print_tree(nodes, depth=0):
    for n in nodes:
        print(f"{'  ' * depth}- {node_title(n)}   {node_href(n) or ''}")
        print_tree(node_children(n), depth + 1)


def find_subtree(nodes, needle):
    needle_l = needle.lower()
    for n in nodes:
        if needle_l in node_title(n).lower() or needle_l in (node_href(n) or "").lower():
            return n
        hit = find_subtree(node_children(n), needle)
        if hit:
            return hit
    return None


def sanitize(name, maxlen=80):
    name = re.sub(r"[^\w\s\-.]", "", name).strip()
    name = re.sub(r"\s+", "_", name)
    return name[:maxlen] or "untitled"


def collect_pages(node, dir_parts, counter, out):
    counter[0] += 1
    idx = counter[0]
    title, href, children = node_title(node), node_href(node), node_children(node)
    if href:
        out.append({"index": idx, "title": title, "href": href,
                    "dir_parts": list(dir_parts)})
    if children:
        child_dir = dir_parts + [f"{idx:03d}_{sanitize(title)}"]
        for c in children:
            collect_pages(c, child_dir, counter, out)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", required=True,
                    help="Doc id, e.g. commerce.pwa-kit-managed-runtime")
    ap.add_argument("--start-url", default=None,
                    help="Any page of that doc (used to bootstrap cookies). "
                         "Defaults to /docs/{category}/{deliverable}")
    ap.add_argument("--root", default=None,
                    help="Menu item (title or href substring) to export; "
                         "omit for the whole document")
    ap.add_argument("--out", default="./export")
    ap.add_argument("--inspect", action="store_true")
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--headed", action="store_true",
                    help="Run a visible browser (helps against bot detection)")
    args = ap.parse_args()

    category, _, deliverable = args.doc.partition(".")
    start_url = args.start_url or f"{BASE}/docs/{category}/{deliverable}"

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        ctx = browser.new_context(
            user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/125.0.0.0 Safari/537.36"),
            viewport={"width": 1400, "height": 1000},
        )
        page = ctx.new_page()
        page.set_default_timeout(NAV_TIMEOUT_MS)

        print(f"Bootstrapping session at {start_url} ...")
        page.goto(start_url, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)  # let Akamai + SPA settle

        print("Fetching TOC via in-page API call ...")
        toc_json = page.evaluate(FETCH_TOC_JS, args.doc)
        if isinstance(toc_json, dict) and "__error" in toc_json:
            print(f"  get_document returned {toc_json['__error']}; "
                  f"falling back to sidebar scrape ...")
            toc_json = page.evaluate(SCRAPE_SIDEBAR_JS)
            if isinstance(toc_json, dict) and "__error" in toc_json:
                print(f"  Sidebar fallback failed: {toc_json['__error']}")
                browser.close()
                sys.exit(1)

        roots = toc_roots(toc_json)
        if not roots:
            Path("toc_dump.json").write_text(json.dumps(toc_json, indent=2))
            print("Could not find TOC list; raw response saved to toc_dump.json")
            browser.close()
            sys.exit(1)

        if args.inspect:
            print_tree(roots)
            browser.close()
            return

        if args.root:
            subtree = find_subtree(roots, args.root)
            if not subtree:
                print(f"No menu item matching {args.root!r}. "
                      f"Run with --inspect to list titles.")
                browser.close()
                sys.exit(1)
            nodes = [subtree]
            print(f"Exporting subtree: {node_title(subtree)}")
        else:
            nodes = roots
            print("Exporting entire document.")

        pages, counter = [], [0]
        for n in nodes:
            collect_pages(n, [], counter, pages)
        print(f"{len(pages)} pages to export.")

        out_root = Path(args.out)
        if out_root.exists():
            shutil.rmtree(out_root)
        out_root.mkdir(parents=True)

        manifest, failures = [], []
        for item in pages:
            url = item["href"] if item["href"].startswith("http") \
                else BASE + item["href"]
            rel_dir = Path(*item["dir_parts"]) if item["dir_parts"] else Path(".")
            (out_root / rel_dir).mkdir(parents=True, exist_ok=True)
            fname = f"{item['index']:03d}_{sanitize(item['title'])}.pdf"
            pdf_path = out_root / rel_dir / fname
            try:
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_selector("main, [role='main'], article, h1",
                                       timeout=NAV_TIMEOUT_MS)
                page.wait_for_timeout(800)  # late-rendered code blocks/images
                page.add_style_tag(content=HIDE_CHROME_CSS)
                page.emulate_media(media="print")
                page.pdf(path=str(pdf_path), format="A4",
                         margin={"top": "16mm", "bottom": "16mm",
                                 "left": "12mm", "right": "12mm"},
                         print_background=True)
                manifest.append({**item, "url": url, "pdf": str(rel_dir / fname)})
                print(f"  ok   {rel_dir / fname}")
            except Exception as e:  # noqa: BLE001
                failures.append({**item, "url": url, "error": str(e)})
                print(f"  FAIL {url}: {e}")
            time.sleep(PAGE_DELAY)

        browser.close()

    (out_root / "manifest.json").write_text(
        json.dumps({"doc": args.doc, "pages": manifest,
                    "failures": failures}, indent=2))

    if args.merge and manifest:
        from pypdf import PdfWriter
        writer = PdfWriter()
        for m in manifest:
            writer.append(str(out_root / m["pdf"]))
        with open(out_root / "combined.pdf", "wb") as f:
            writer.write(f)
        print("Merged PDF written to combined.pdf")

    archive = shutil.make_archive(str(out_root), "zip", root_dir=out_root)
    print(f"\nDone. {len(manifest)} exported, {len(failures)} failed.")
    print(f"Archive: {archive}")


if __name__ == "__main__":
    main()
