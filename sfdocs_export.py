#!/usr/bin/env python3
"""
Deterministic Salesforce Developer Docs exporter — v2 (browser-driven).

Why v2: /docs/get_document/* returns 403 to plain HTTP clients (Akamai bot
protection). So all requests now go through a real Chromium session:

  1. Open the docs site once (Akamai cookies get set).
  2. Read the TOC from the `sidebar-content` JSON attribute on
     `doc-content-layout` (contains the full hierarchical tree).
     Fallback: traverse DX-TREE-ITEM shadow DOM components.
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
# TOC extraction strategies
# ---------------------------------------------------------------------------

# Primary: read the sidebar-content JSON attribute from doc-content-layout.
# This contains the full hierarchical tree with all children pre-loaded.
FETCH_SIDEBAR_ATTR_JS = """
() => {
  const el = document.querySelector('doc-content-layout');
  if (!el) return { __error: 'doc-content-layout element not found' };
  const raw = el.getAttribute('sidebar-content');
  if (!raw) return { __error: 'no sidebar-content attribute' };
  try {
    return { toc: JSON.parse(raw) };
  } catch (e) {
    return { __error: 'invalid sidebar-content JSON: ' + e.message };
  }
}
"""

# Fallback: traverse DX-TREE-ITEM shadow DOM components (only shows
# expanded items, so the tree may be incomplete).
SCRAPE_SHADOW_TREE_JS = """
async () => {
  function extractTree(root, depth) {
    if (depth > 15) return [];
    const items = [];
    const allEls = root.querySelectorAll ? [...root.querySelectorAll('*')] : [];
    for (const el of allEls) {
      if (el.tagName === 'DX-TREE-ITEM' && el.shadowRoot) {
        const sr = el.shadowRoot;
        let text = '', href = '';
        const link = sr.querySelector('a[href]');
        if (link) {
          href = link.getAttribute('href');
          const tile = sr.querySelector('dx-tree-tile');
          if (tile && tile.shadowRoot) {
            text = tile.shadowRoot.textContent.trim();
          }
          if (!text) text = link.textContent.trim();
        }
        const children = extractTree(sr, depth + 1);
        if (text || href || children.length > 0) {
          items.push({text: text.split('\\n')[0].trim(), href, children});
        }
      }
    }
    return items;
  }
  function findTreeRoot(root, depth) {
    if (depth > 10) return null;
    const allEls = root.querySelectorAll ? [...root.querySelectorAll('*')] : [];
    for (const el of allEls) {
      if (el.shadowRoot) {
        const treeItems = el.shadowRoot.querySelectorAll('dx-tree-item');
        if (treeItems.length > 3) return el.shadowRoot;
        const found = findTreeRoot(el.shadowRoot, depth + 1);
        if (found) return found;
      }
    }
    return null;
  }
  const treeRoot = findTreeRoot(document, 0);
  if (!treeRoot) return { __error: 'sidebar nav not found (no DX-TREE-ITEM tree)' };
  return { toc: extractTree(treeRoot, 0) };
}
"""


def node_title(node):
    for key in ("text", "title", "label"):
        v = node.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return node.get("id", "untitled")


def node_href(node):
    a_attr = node.get("a_attr") or {}
    link = node.get("link") or {}
    for c in (a_attr.get("href"), node.get("href"),
              link.get("href") if isinstance(link, dict) else link,
              node.get("name"), node.get("url")):
        if isinstance(c, str) and c.strip():
            return c.strip()
    return None


def node_children(node):
    ch = node.get("children")
    return ch if isinstance(ch, list) else []


def toc_roots(toc_json):
    if isinstance(toc_json, list):
        return toc_json
    if isinstance(toc_json, dict):
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
                    help="Any guide page of that doc (must render the sidebar). "
                         "Defaults to /docs/{cat}/{deliverable}/guide/getting-started.html")
    ap.add_argument("--root", default=None,
                    help="Menu item (title or href substring) to export; "
                         "omit for the whole document")
    ap.add_argument("--tab", default=None,
                    help="Alias for --root (e.g. 'Storefront Next')")
    ap.add_argument("--out", default="./export")
    ap.add_argument("--inspect", action="store_true")
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--headed", action="store_true",
                    help="Run a visible browser (helps against bot detection)")
    args = ap.parse_args()

    # --tab is an alias for --root
    if args.tab and not args.root:
        args.root = args.tab

    category, _, deliverable = args.doc.partition(".")
    start_url = (args.start_url
                 or f"{BASE}/docs/{category}/{deliverable}/guide/getting-started.html")

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        ctx = browser.new_context(
            user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/125.0.0.0 Safari/537.36"),
            viewport={"width": 3456, "height": 2234},
            device_scale_factor=2,
        )
        page = ctx.new_page()
        page.set_default_timeout(NAV_TIMEOUT_MS)

        print(f"Bootstrapping session at {start_url} ...")
        page.goto(start_url, wait_until="networkidle")
        page.wait_for_timeout(5000)  # let SPA fully render

        # --- Extract TOC ---
        print("Extracting TOC from sidebar-content attribute ...")
        toc_json = page.evaluate(FETCH_SIDEBAR_ATTR_JS)
        if isinstance(toc_json, dict) and "__error" in toc_json:
            print(f"  sidebar-content: {toc_json['__error']}; "
                  f"falling back to shadow DOM scrape ...")
            toc_json = page.evaluate(SCRAPE_SHADOW_TREE_JS)
            if isinstance(toc_json, dict) and "__error" in toc_json:
                print(f"  Shadow DOM fallback failed: {toc_json['__error']}")
                browser.close()
                sys.exit(1)

        roots = toc_roots(toc_json)
        if not roots:
            Path("toc_dump.json").write_text(json.dumps(toc_json, indent=2))
            print("Could not find TOC list; raw response saved to toc_dump.json")
            browser.close()
            sys.exit(1)

        if args.root:
            subtree = find_subtree(roots, args.root)
            if not subtree:
                print(f"No menu item matching {args.root!r}. "
                      f"Run with --inspect to list titles.")
                browser.close()
                sys.exit(1)
            nodes = [subtree]
            print(f"Selected subtree: {node_title(subtree)}")
        else:
            nodes = roots

        if args.inspect:
            print_tree(nodes)
            browser.close()
            return

        print(f"Exporting {'subtree' if args.root else 'entire document'}.")

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
                page.pdf(path=str(pdf_path),
                         width="16in", height="10in",
                         margin={"top": "12mm", "bottom": "12mm",
                                 "left": "10mm", "right": "10mm"},
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
