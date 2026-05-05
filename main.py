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
