# Downloads all images from a page, including those loaded via JS (lazy-loaded, srcset, backgrounds).
# Requirements:
#   pip install playwright requests
#   python -m playwright install
#
# Usage:
#   python download_images.py "https://example.com" out_dir

import os
import re
import sys
import base64
import mimetypes
from urllib.parse import urljoin, urlparse, unquote
import requests
from playwright.sync_api import sync_playwright

JS_COLLECT_IMAGES = """
() => {
  const urls = new Set();

  const add = (u) => { if (u && typeof u === 'string') urls.add(u.trim()); };

  const attrs = ['src','srcset','data-src','data-original','data-lazy','data-lazy-src','data-hi-res-src','data-srcset','data-zoom-image'];

  // <img> and <source> candidates
  document.querySelectorAll('img, source[type^="image/"]').forEach(el => {
    for (const a of attrs) {
      const v = el.getAttribute(a);
      if (!v) continue;
      if (a.endsWith('srcset')) {
        v.split(',').forEach(item => {
          const u = item.trim().split(/\\s+/)[0];
          add(u);
        });
      } else {
        add(v);
      }
    }
  });

  // CSS background-image urls
  document.querySelectorAll('*').forEach(el => {
    const bg = getComputedStyle(el).backgroundImage;
    if (bg && bg !== 'none') {
      const matches = Array.from(bg.matchAll(/url\\(["']?(.*?)["']?\\)/g));
      matches.forEach(m => add(m[1]));
    }
  });

  return Array.from(urls);
}
"""

def scroll_to_load(page, max_steps=40, pause_ms=600):
    prev_total = -1
    for _ in range(max_steps):
        page.evaluate("window.scrollBy(0, Math.max(800, window.innerHeight));")
        page.wait_for_timeout(pause_ms)
        # Try to trigger network idle after loading new content
        try:
            page.wait_for_load_state("networkidle", timeout=2000)
        except:
            pass
        total = page.evaluate("document.documentElement.scrollHeight")
        y = page.evaluate("window.scrollY + window.innerHeight")
        if total == prev_total and y + 10 >= total:
            break
        prev_total = total

def safe_filename(name):
    name = unquote(name).split('?')[0].split('#')[0]
    name = os.path.basename(name) or "image"
    name = re.sub(r'[^a-zA-Z0-9._-]+', '_', name)
    return name[:150] or "image"

def ext_from_content_type(ct, fallback=".jpg"):
    if not ct:
        return fallback
    ext = mimetypes.guess_extension(ct.split(";")[0].strip())
    if not ext:
        return fallback
    # Normalize jpeg extension
    if ext == ".jpe":
        ext = ".jpg"
    return ext

def save_data_uri(data_uri, out_dir, idx):
    try:
        header, data = data_uri.split(",", 1)
    except ValueError:
        return None
    mime = None
    is_base64 = False
    if header.startswith("data:"):
        parts = header[5:].split(";")
        if parts:
            mime = parts[0] or None
        if "base64" in parts:
            is_base64 = True
    try:
        content = base64.b64decode(data) if is_base64 else unquote(data).encode("utf-8", "ignore")
    except Exception:
        return None
    ext = ext_from_content_type(mime, ".bin")
    path = os.path.join(out_dir, f"data_{idx:04d}{ext}")
    with open(path, "wb") as f:
        f.write(content)
    return path

def download_http(url, out_dir, idx, session):
    try:
        r = session.get(url, stream=True, timeout=30)
        r.raise_for_status()
        # Try use URL filename; fallback to Content-Type
        filename = safe_filename(urlparse(url).path)
        base, ext = os.path.splitext(filename)
        if not ext or len(ext) > 5:
            ext = ext_from_content_type(r.headers.get("Content-Type"), ".jpg")
        filename = (base or f"img_{idx:04d}") + ext
        path = os.path.join(out_dir, filename)

        # Avoid overwriting: append index if exists
        if os.path.exists(path):
            path = os.path.join(out_dir, f"img_{idx:04d}{ext}")

        with open(path, "wb") as f:
            for chunk in r.iter_content(8192):
                if chunk:
                    f.write(chunk)
        return path
        except Exception:
        return None
def main():
    if len(sys.argv) < 2:
        print("Usage: python download_images.py <url> [out_dir]")
        sys.exit(1)
    url = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "images"
    os.makedirs(out_dir, exist_ok=True)

    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121 Safari/537.36"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent=ua, viewport={"width": 1400, "height": 900})
        page = ctx.new_page()
        page.set_default_timeout(60000)

        page.goto(url, wait_until="networkidle")
        scroll_to_load(page)

        # Give lazy images a last chance to load
        try:
            page.wait_for_load_state("networkidle", timeout=3000)
        except:
            pass

        raw_urls = page.evaluate(JS_COLLECT_IMAGES)

        # Resolve and clean URLs
        resolved = []
        for u in raw_urls:
            if not u:
                continue
            if u.startswith("data:image"):
                resolved.append(u)
                continue
            # Skip non-http(s) schemes (e.g., blob:)
            if u.startswith("blob:"):
                continue
            # Handle relative and protocol-relative URLs
            absu = urljoin(page.url, u)
            resolved.append(absu)

        # Deduplicate while preserving order
        seen = set()
        urls = []
        for u in resolved:
            if u not in seen:
                seen.add(u)
                urls.append(u)

        session = requests.Session()
        session.headers.update({"User-Agent": ua, "Accept": "*/*"})

        saved = 0
        for idx, u in enumerate(urls, 1):
            if u.startswith("data:image"):
                path = save_data_uri(u, out_dir, idx)
            else:
                path = download_http(u, out_dir, idx, session)
            if path:
                saved += 1
                print(f"[{saved:03d}] saved: {path}")
            else:
                print(f"[---] failed: {u}")

        browser.close()
        print(f"Done. Saved {saved} images to {out_dir}")

if __name__ == "__main__":
    main()
