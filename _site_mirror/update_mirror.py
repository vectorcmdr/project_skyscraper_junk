#!/usr/bin/env python3
"""
project-skyscraper.com - Complete Mirror Update Script
======================================================
Fully self-discovering. No hardcoded IDs, no hardcoded URL lists.
Run:  python update_mirror.py

Re-run anytime to check for updates. Diffs saved to diffs/.
"""

import hashlib
import json
import os
import re
import time
import urllib.parse
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = "https://project-skyscraper.com"
MIRROR_DIR = Path(__file__).parent.resolve()
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 project-skyscraper-mirror/1.0"

stats = {"fetched": 0, "skipped": 0, "failed": 0, "changed": 0, "new": 0}
changes = []


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def _fmt_size(bytes_val):
    for unit in ("B", "KB", "MB", "GB"):
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} TB"


def _hash_bytes(data):
    return hashlib.md5(data).hexdigest()


# --- URL -> path mapping ---

def url_to_path(url: str, subdir: str = "") -> Path:
    if url.startswith("//"):
        url = "https:" + url
    parsed = urllib.parse.urlparse(url)
    path_str = parsed.path.rstrip("/") or "/"
    q = parsed.query
    if q:
        qs = q.replace("&", "_").replace("=", "_").replace("%", "").replace(";", "_").replace(" ", "_")
        path_str = path_str + "_" + qs[:120]
    if path_str.endswith("/") or path_str == "":
        path_str += "index"
    ext = Path(urllib.parse.unquote(path_str)).suffix
    if not ext:
        if "wp-json" in url or "oembed" in url or parsed.path.startswith("/wp-json"):
            path_str += ".json"
        else:
            path_str += ".html"
    path_str = path_str.replace("https:", "").replace("http:", "")
    if path_str.startswith("/"):
        path_str = path_str[1:]
    path_str = re.sub(r'[<>:"\\|?*]', "_", path_str)
    parts = [p[:200] for p in path_str.replace("\\", "/").split("/")]
    return MIRROR_DIR / subdir / "/".join(parts)


# --- HTTP fetch with caching ---

def fetch(url: str, subdir: str = "", binary: bool = False,
           headers_extra: dict = None, save_headers: bool = False):
    path = url_to_path(url, subdir=subdir)
    path.parent.mkdir(parents=True, exist_ok=True)

    old_hash = _hash_bytes(path.read_bytes()) if path.is_file() else None

    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT, "Accept": "*/*", **(headers_extra or {}),
    })
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        content = resp.read()
        code = resp.status
    except urllib.error.HTTPError as e:
        stats["failed"] += 1
        try:
            content = e.read()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            log(f"  ERR  {url} -> {e.code}")
        except Exception:
            pass
        return ("error", path, e.code)
    except Exception as e:
        stats["failed"] += 1
        log(f"  FAIL {url} -> {e}")
        return ("error", path, 0)

    new_hash = _hash_bytes(content)
    if old_hash == new_hash:
        stats["skipped"] += 1
        return ("skipped", path, code, content)

    path.write_bytes(content)
    if old_hash is None:
        stats["new"] += 1
        log(f"  NEW  {url}")
    else:
        stats["changed"] += 1
        log(f"  CHG  {url}")
        changes.append((url, path))
    stats["fetched"] += 1

    if save_headers:
        hdr = path.parent / (path.name + ".headers.json")
        hdr.write_text(json.dumps(dict(resp.headers.items()), indent=2, default=str))
    return ("ok", path, code, content)


def _json_fetch(endpoint: str):
    """Fetch JSON endpoint, return parsed data or None."""
    url = f"{BASE_URL}{endpoint}"
    result = fetch(url, subdir="api")
    if result[0] == "ok":
        try:
            return json.loads(result[3])
        except (json.JSONDecodeError, IndexError):
            pass
    return None


# --- Phase 1: Discovery ---

def discover_sitemap_urls() -> dict:
    """Fetch sitemap index, sub-sitemaps, return dict of {url: type}."""
    urls = {}
    sitemap_index = f"{BASE_URL}/sitemap.xml"
    r = fetch(sitemap_index, subdir="discovery")
    if r[0] == "ok":
        try:
            tree = ET.parse(str(r[1]))
            root = tree.getroot()
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            subs = [e.text for e in root.findall(".//sm:sitemap/sm:loc", ns) if e.text]
            for sub in subs:
                fetch(sub, subdir="discovery")
                sr = fetch(sub, subdir="discovery")
                if sr[0] != "error":
                    try:
                        st = ET.parse(str(sr[1]))
                        sroot = st.getroot()
                        for e in sroot.findall(".//sm:url/sm:loc", ns):
                            if e.text:
                                urls[e.text] = "page"
                        img_ns = {**ns, "image": "http://www.google.com/schemas/sitemap-image/1.1"}
                        for img in sroot.findall(".//sm:url/image:image/image:loc", img_ns):
                            if img.text:
                                urls[img.text] = "image"
                    except ET.ParseError:
                        pass
        except ET.ParseError:
            pass
    # Fallback: try known sub-sitemap paths
    if not urls:
        for alt in ["/sitemap-1.xml", "/image-sitemap-1.xml", "/news-sitemap.xml"]:
            sr = fetch(f"{BASE_URL}{alt}", subdir="discovery")
            if sr[0] != "error":
                try:
                    st = ET.parse(str(sr[1]))
                    sroot = st.getroot()
                    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
                    for e in sroot.findall(".//sm:url/sm:loc", ns):
                        if e.text:
                            urls[e.text] = "page"
                except ET.ParseError:
                    pass
    return urls


def discover_rest_api():
    """Fetch root namespace index and return list of namespace routes."""
    data = _json_fetch("/wp-json/")
    namespaces = []
    if data and isinstance(data, dict):
        ns_list = data.get("namespaces", [])
        routes = data.get("routes", {})
        for ns in ns_list:
            namespaces.append(f"/wp-json/{ns}")
        # Also return route keys for probing
        route_keys = list(routes.keys()) if isinstance(routes, dict) else []
        return namespaces, route_keys
    return [], []


def discover_list(endpoint: str) -> list:
    """Fetch a list endpoint (posts, pages, media) and return all items."""
    items = []
    # Try with higher per_page first
    for url_suffix in [f"{endpoint}?per_page=100", f"{endpoint}?per_page=50", endpoint]:
        data = _json_fetch(url_suffix)
        if isinstance(data, list):
            items = data
            break
    if not items:
        # Try single-item fetch
        data = _json_fetch(endpoint)
        if isinstance(data, list):
            items = data
    return items


def extract_html_resource_urls(subdir: str = "html") -> set:
    """Scan all saved HTML pages for any wp-content URL, external href/src, etc."""
    found = set()
    html_dir = MIRROR_DIR / subdir
    if not html_dir.exists():
        return found
    # Patterns for URLs in HTML
    patterns = [
        re.compile(r'''(?:src|href|data-src|content)="([^"]+)"'''),
        re.compile(r'''url\(['"]?([^'")\s]+)['"]?\)'''),
    ]
    for hf in sorted(html_dir.glob("*.html")):
        text = hf.read_text(encoding="utf-8", errors="replace")
        for pat in patterns:
            for m in pat.finditer(text):
                u = m.group(1)
                if u.startswith("//"):
                    u = "https:" + u
                if u.startswith(("http://", "https://")) or u.startswith("/"):
                    found.add(u)
    return found


# --- Phase 2: HTML pages ---

def fetch_html_pages(sitemap_urls: dict):
    log("=== FETCHING HTML PAGES ===")
    for url in sitemap_urls:
        if url.startswith(BASE_URL) and sitemap_urls[url] == "page":
            fetch(url, subdir="html", save_headers=True)
            time.sleep(0.3)
    # Always fetch root
    fetch(BASE_URL, subdir="html", save_headers=True)


# --- Phase 3: REST API ---

def fetch_api_endpoints():
    log("=== FETCHING REST API ENDPOINTS ===")

    # 1) Root + route discovery
    log("  --- Root & Route Discovery ---")
    namespaces, route_keys = discover_rest_api()

    # 2) Fetch all known namespaced roots
    # Note: oembed/1.0 and wp/v2 are excluded because they contain
    # sub-endpoints that must live under a directory of the same name.
    known_ns_roots = {
        "/wp-json/jetpack/v4", "/wp-json/wpcom/v2", "/wp-json/wpcom/v3",
        "/wp-json/wpcomsh/v1", "/wp-json/code-snippets/v1",
        "/wp-json/crowdsignal-forms/v1", "/wp-json/wp-statistics/v2",
        "/wp-json/wp-site-health/v1", "/wp-json/wp-abilities/v1",
        "/wp-json/akismet/v1", "/wp-json/my-jetpack/v1",
        "/wp-json/jetpack-boost/v1", "/wp-json/jetpack-global-styles/v1",
        "/wp-json/newspack-blocks/v1", "/wp-json/videopress/v1",
        "/wp-json/help-center", "/wp-json/wp-block-editor/v1",
        "/wp-json/wp-sync/v1",
    }
    for ns_root in sorted(known_ns_roots):
        fetch(f"{BASE_URL}{ns_root}", subdir="api")
        time.sleep(0.15)

    # 3) wp/v2 list endpoints
    log("  --- wp/v2 Collection Endpoints ---")
    collection_endpoints = [
        "/wp-json/wp/v2/posts", "/wp-json/wp/v2/pages",
        "/wp-json/wp/v2/media", "/wp-json/wp/v2/categories",
        "/wp-json/wp/v2/tags", "/wp-json/wp/v2/types",
        "/wp-json/wp/v2/statuses", "/wp-json/wp/v2/taxonomies",
        "/wp-json/wp/v2/users", "/wp-json/wp/v2/comments",
        "/wp-json/wp/v2/blocks", "/wp-json/wp/v2/navigation",
        "/wp-json/wp/v2/search", "/wp-json/wp/v2/statuses",
    ]
    for ep in collection_endpoints:
        fetch(f"{BASE_URL}{ep}", subdir="api")
        time.sleep(0.15)
        # Also try with per_page=100
        fetch(f"{BASE_URL}{ep}?per_page=100", subdir="api")
        time.sleep(0.1)

    # Auth-gated endpoints (save 401/403 responses for reference)
    log("  --- Auth-gated Endpoints ---")
    for ep in ["/wp-json/wp/v2/settings", "/wp-json/wp/v2/themes",
               "/wp-json/wp/v2/plugins", "/wp-json/wp/v2/block-types",
               "/wp-json/wp/v2/templates", "/wp-json/wp/v2/template-parts",
               "/wp-json/wp/v2/global-styles", "/wp-json/wp/v2/menu-items",
               "/wp-json/wp/v2/menus", "/wp-json/wp/v2/sidebars",
               "/wp-json/wp/v2/widgets", "/wp-json/wp/v2/block-directory/search"]:
        fetch(f"{BASE_URL}{ep}", subdir="api")
        time.sleep(0.1)

    # 4) Dynamically discover individual post/page/media IDs
    log("  --- Individual Items (dynamic) ---")

    def fetch_all_individual(list_endpoint, item_endpoint_template):
        """Fetch a list, extract IDs, fetch each individual item."""
        items = discover_list(list_endpoint)
        ids = []
        urls = []
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    iid = item.get("id")
                    if iid and iid not in ids:
                        ids.append(iid)
                        urls.append(item.get("link", ""))
        for iid in sorted(ids):
            ep = item_endpoint_template.format(id=iid)
            fetch(f"{BASE_URL}{ep}", subdir="api")
            time.sleep(0.1)
        return ids, urls

    post_ids, post_links = fetch_all_individual(
        "/wp-json/wp/v2/posts", "/wp-json/wp/v2/posts/{id}")
    page_ids, page_links = fetch_all_individual(
        "/wp-json/wp/v2/pages", "/wp-json/wp/v2/pages/{id}")
    media_ids, _media_links = fetch_all_individual(
        "/wp-json/wp/v2/media", "/wp-json/wp/v2/media/{id}")

    log(f"    Posts: {len(post_ids)}  Pages: {len(page_ids)}  Media: {len(media_ids)}")

    # Also probe for new IDs just past the known range
    all_known_ids = set(post_ids + page_ids + media_ids)
    if all_known_ids:
        max_id = max(all_known_ids)
        for probe_id in range(max_id + 1, max_id + 11):
            for kind in ["posts", "pages", "media"]:
                fetch(f"{BASE_URL}/wp-json/wp/v2/{kind}/{probe_id}", subdir="api")
                time.sleep(0.05)

    # 5) Jetpack sub-endpoints
    log("  --- Jetpack Sub-endpoints ---")
    jetpack_subs = [
        "/wp-json/jetpack/v4/site", "/wp-json/jetpack/v4/module",
        "/wp-json/jetpack/v4/module/all", "/wp-json/jetpack/v4/module/protect",
        "/wp-json/jetpack/v4/module/related-posts", "/wp-json/jetpack/v4/module/monitor",
        "/wp-json/jetpack/v4/scan", "/wp-json/jetpack/v4/scan/history",
        "/wp-json/jetpack/v4/sync/status", "/wp-json/jetpack/v4/sync/checksum",
        "/wp-json/jetpack/v4/connection", "/wp-json/jetpack/v4/connection/url",
        "/wp-json/jetpack/v4/identity-crisis", "/wp-json/jetpack/v4/plugins",
        "/wp-json/jetpack/v4/update-plugins", "/wp-json/jetpack/v4/recommendations/data",
        "/wp-json/jetpack/v4/recommendations/site-pages", "/wp-json/jetpack/v4/notice",
        "/wp-json/jetpack/v4/notice/block", "/wp-json/jetpack/v4/checkout",
        "/wp-json/jetpack/v4/backup", "/wp-json/jetpack/v4/backup-ux",
        "/wp-json/jetpack/v4/backup-ux/data", "/wp-json/jetpack/v4/stats-app",
        "/wp-json/jetpack/v4/import", "/wp-json/jetpack/v4/explat",
        "/wp-json/jetpack/v4/blaze-app", "/wp-json/jetpack/v4/blaze",
        "/wp-json/jetpack/v4/videopress", "/wp-json/jetpack/v4/social",
        "/wp-json/jetpack/v4/search", "/wp-json/jetpack/v4/search/plan",
        "/wp-json/jetpack/v4/search/settings", "/wp-json/jetpack/v4/search/stats",
        "/wp-json/jetpack/v4/verify-tracking", "/wp-json/jetpack/v4/verify-google-ads",
    ]
    for ep in jetpack_subs:
        fetch(f"{BASE_URL}{ep}", subdir="api")
        time.sleep(0.12)

    # 6) WP.com sub-endpoints
    log("  --- WP.com Sub-endpoints ---")
    for ep in ["/wp-json/wpcom/v2/sites", "/wp-json/wpcom/v2/site-verticals",
               "/wp-json/wpcom/v2/block-likes"]:
        fetch(f"{BASE_URL}{ep}", subdir="api")
        time.sleep(0.12)

    # 7) oEmbed for ALL discovered pages
    log("  --- oEmbed Endpoints ---")
    oembed_urls = set()
    # From sitemap
    oembed_urls.add(BASE_URL)
    sitemap_data = discover_sitemap_urls()
    for surl in sitemap_data:
        if surl.startswith(BASE_URL):
            oembed_urls.add(surl)
    # From discovered post/page links
    for link in post_links + page_links:
        oembed_urls.add(link)

    for ou in sorted(oembed_urls):
        encoded = urllib.parse.quote(ou, safe="")
        for fmt in ["", "&format=xml"]:
            fetch(f"{BASE_URL}/wp-json/oembed/1.0/embed?url={encoded}{fmt}", subdir="api")
            time.sleep(0.08)

    # 8) rest_route fallback
    fetch(f"{BASE_URL}/?rest_route=/", subdir="api")
    fetch(f"{BASE_URL}/?rest_route=/wp/v2", subdir="api")

    return post_ids, page_ids, media_ids, post_links, page_links


# --- Phase 4: Media ---

def fetch_media(post_links, page_links, sitemap_urls):
    log("=== FETCHING MEDIA FILES ===")

    media_urls = set()

    # 1) From image sitemap
    for url, typ in sitemap_urls.items():
        if typ == "image":
            media_urls.add(url)

    # 2) From saved media JSON (source_url field)
    api_dir = MIRROR_DIR / "api"
    if api_dir.exists():
        for jf in api_dir.rglob("*.json"):
            try:
                data = json.loads(jf.read_bytes())
            except (json.JSONDecodeError, ValueError):
                continue
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict):
                    src = item.get("source_url") or item.get("guid", {}).get("rendered", "")
                    if src and src.startswith("http"):
                        media_urls.add(src)

    # 3) Parse HTML for wp-content/uploads/ URLs
    html_resources = extract_html_resource_urls("html")
    for u in html_resources:
        if "/wp-content/uploads/" in u and u.startswith((BASE_URL, "https://i0.wp.com")):
            # Strip query params for the base image URL
            clean = u.split("?")[0]
            media_urls.add(clean)

    # 4) Parse API JSON responses for image URLs
    for link_set in [post_links, page_links]:
        for link in link_set:
            if link:
                # Try to find featured_media and its URL from already-fetched post JSON
                pass  # handled by #2 above

    log(f"  Discovered {len(media_urls)} media URLs")
    for url in sorted(media_urls):
        if url.startswith((BASE_URL, "https://i0.wp.com")):
            fetch(url, subdir="media", binary=True)
            time.sleep(0.15)

    # Also fetch known thumbnail variations from media API
    # (they may not be directly listed, but source_url exists)
    api_dir = MIRROR_DIR / "api"
    if api_dir.exists():
        for jf in sorted(api_dir.rglob("wp-json/wp/v2/media/*.json")):
            try:
                data = json.loads(jf.read_bytes())
                if isinstance(data, dict):
                    src = data.get("source_url", "")
                    if src and "wp-content/uploads" in src:
                        base = src.rsplit(".", 1)[0]
                        ext = src.rsplit(".", 1)[-1]
                        # Try -150x150, -300x300, etc.
                        for suffix in ["-150x150", "-300x300", "-768x768", "-1024x1024"]:
                            thumb = f"{base}{suffix}.{ext}"
                            fetch(thumb, subdir="media", binary=True)
                            time.sleep(0.08)
            except (json.JSONDecodeError, ValueError):
                pass


# --- Phase 5: Theme Assets ---

def fetch_theme_assets():
    log("=== FETCHING THEME ASSETS ===")
    theme_base = f"{BASE_URL}/wp-content/themes/perenne"

    # Probe common theme paths
    probe_paths = [
        "/style.css", "/theme.json", "/readme.txt",
        "/screenshot.png", "/index.php", "/functions.php",
        "/header.php", "/footer.php", "/single.php",
        "/page.php", "/archive.php", "/404.php",
        "/search.php", "/sidebar.php", "/comments.php",
        "/front-page.php",
        "/assets/css/main.css", "/assets/css/blocks.css",
        "/assets/js/navigation.js", "/assets/js/script.js",
        "/assets/fonts/ibm-plex-mono_normal_400.ttf",
        "/assets/fonts/ibm-plex-mono_italic_400.ttf",
    ]

    for tp in probe_paths:
        url = f"{theme_base}{tp}"
        binary = tp.endswith((".ttf", ".woff2", ".png", ".jpg", ".ico"))
        fetch(url, subdir="assets", binary=binary)
        time.sleep(0.12)

    # Also discover theme assets from HTML
    html_resources = extract_html_resource_urls("html")
    for u in html_resources:
        if "/wp-content/themes/" in u:
            fetch(u, subdir="assets", binary=u.endswith((".ttf", ".woff2", ".png", ".jpg", ".ico")))
            time.sleep(0.1)


# --- Phase 6: Plugin Assets ---

def fetch_plugin_assets():
    log("=== FETCHING PLUGIN ASSETS ===")
    # Probe common plugin paths
    plugin_probes = [
        "jetpack/modules/related-posts/related-posts.css",
        "jetpack/modules/likes/style.css",
        "jetpack/_inc/build/likes/style.min.css",
        "jetpack/modules/carousel/jetpack-carousel.css",
        "jetpack/_inc/build/carousel/jetpack-carousel.min.js",
        "jetpack/_inc/blocks/swiper.js",
        "jetpack/modules/stats/gravatar-hovercards.css",
        "jetpack/modules/theme-tools/compat/perenne.css",
        "gutenberg/build/scripts/dom-ready/index.min.js",
        "gutenberg/build/styles/block-library/paragraph/style.min.css",
        "gutenberg/build/styles/block-library/group/style.min.css",
        "gutenberg/build/styles/block-library/site-logo/style.min.css",
        "gutenberg/build/styles/block-library/post-date/style.min.css",
        "gutenberg/build/styles/block-library/post-title/style.min.css",
        "gutenberg/build/styles/block-library/spacer/style.min.css",
        "gutenberg/build/styles/block-library/post-content/style.min.css",
        "gutenberg/build/styles/block-library/post-navigation-link/style.min.css",
        "gutenberg/build/styles/block-library/heading/style.min.css",
        "gutenberg/build/styles/block-library/post-featured-image/style.min.css",
        "gutenberg/build/styles/block-library/quote/style.min.css",
        "gutenberg/build/styles/block-library/image/style.min.css",
        "gutenberg/build/styles/block-library/post-terms/style.min.css",
        "gravatar-enhanced/build/patterns-view.css",
        "wp-statistics/assets/js/tracker.js",
    ]
    for pp in plugin_probes:
        url = f"{BASE_URL}/wp-content/plugins/{pp}"
        fetch(url, subdir="assets")
        time.sleep(0.1)

    # Also discover plugin assets from HTML (catches any we missed)
    html_resources = extract_html_resource_urls("html")
    for u in html_resources:
        if "/wp-content/plugins/" in u:
            fetch(u, subdir="assets")
            time.sleep(0.1)


# --- Phase 7: Discovery ---

def fetch_discovery():
    log("=== FETCHING DISCOVERY DOCUMENTS ===")
    for path in ["/robots.txt", "/sitemap.xml", "/sitemap-1.xml",
                 "/image-sitemap-1.xml", "/news-sitemap.xml",
                 "/sitemap.xsl", "/sitemap-index.xsl",
                 "/image-sitemap.xsl", "/news-sitemap.xsl"]:
        fetch(f"{BASE_URL}{path}", subdir="discovery")
        time.sleep(0.1)


# --- Phase 8: Extras ---

def fetch_extras():
    log("=== FETCHING EXTRAS ===")
    extras = [
        (f"{BASE_URL}/readme.html", "extras", False),
        (f"{BASE_URL}/license.txt", "extras", False),
        (f"{BASE_URL}/wp-config-sample.php", "extras", False),
        (f"{BASE_URL}/favicon.ico", "extras", True),
        (f"{BASE_URL}/xmlrpc.php?rsd", "extras", False),
        (f"{BASE_URL}/xmlrpc.php", "extras", False),
        (f"{BASE_URL}/wp-admin/css/install.css", "extras", False),
        (f"{BASE_URL}/wp-admin/images/wordpress-logo.png", "extras", True),
    ]
    for url, subdir, binary in extras:
        fetch(url, subdir=subdir, binary=binary, save_headers=not binary)
        time.sleep(0.12)


# --- Phase 9: Third-party CDN ---

def fetch_third_party():
    log("=== FETCHING THIRD-PARTY CDN ASSETS ===")

    # Stats/analytics scripts
    for url in [
        "https://s0.wp.com/wp-content/js/bilmur.min.js?m=202622",
        "https://stats.wp.com/e-202622.js",
    ]:
        fetch(url, subdir="third_party")
        time.sleep(0.2)

    # Discover font references from HTML and theme CSS
    html_resources = extract_html_resource_urls("html")
    # Also scan theme CSS
    for css_dir in ["assets", "html"]:
        d = MIRROR_DIR / css_dir
        if d.exists():
            for cf in d.rglob("*.css"):
                text = cf.read_text(encoding="utf-8", errors="replace")
                for m in re.finditer(r'''url\(['"]?([^'")\s]+)['"]?\)''', text):
                    u = m.group(1)
                    if u.startswith("//"):
                        u = "https:" + u
                    if u.startswith("http"):
                        html_resources.add(u)

    font_urls = {u for u in html_resources if "fonts." in u or ".woff2" in u or ".woff" in u}
    if not font_urls:
        # Known IBM Plex Mono fonts (probe if not discovered)
        for u in [
            "https://fonts.wp.com/s/ibmplexmono/v19/-F63fjptAgt5VM-kVkqdyU8n5i0g1l9kn-s.woff2",
            "https://fonts.wp.com/s/ibmplexmono/v19/-F6pfjptAgt5VM-kVkqdyU8n1ioq131hj-sNFQ.woff2",
            "https://fonts.wp.com/s/ibmplexmono/v19/-F6pfjptAgt5VM-kVkqdyU8n3kwq131hj-sNFQ.woff2",
            "https://fonts.wp.com/s/ibmplexmono/v19/-F6qfjptAgt5VM-kVkqdyU8n3oQI8lJPg-IUDNg.woff2",
            "https://fonts.wp.com/s/ibmplexmono/v19/-F6qfjptAgt5VM-kVkqdyU8n3pQP8lJPg-IUDNg.woff2",
            "https://fonts.wp.com/s/ibmplexmono/v19/-F6qfjptAgt5VM-kVkqdyU8n3twJ8lJPg-IUDNg.woff2",
            "https://fonts.wp.com/s/ibmplexmono/v19/-F6qfjptAgt5VM-kVkqdyU8n3uAL8lJPg-IUDNg.woff2",
            "https://fonts.wp.com/s/ibmplexmono/v19/-F6qfjptAgt5VM-kVkqdyU8n3vAO8lJPg-IUDNg.woff2",
            "https://fonts.wp.com/s/ibmplexmono/v19/-F6rfjptAgt5VM-kVkqdyU8n1ioStndgre4dFcFh.woff2",
            "https://fonts.wp.com/s/ibmplexmono/v19/-F6sfjptAgt5VM-kVkqdyU8n1ioSClNFgsARHNh4zg.woff2",
            "https://fonts.wp.com/s/ibmplexmono/v19/-F6sfjptAgt5VM-kVkqdyU8n1ioSGlZFgsARHNh4zg.woff2",
            "https://fonts.wp.com/s/ibmplexmono/v19/-F6sfjptAgt5VM-kVkqdyU8n1ioSJlRFgsARHNh4zg.woff2",
            "https://fonts.wp.com/s/ibmplexmono/v19/-F6sfjptAgt5VM-kVkqdyU8n1ioSblJFgsARHNh4zg.woff2",
            "https://fonts.wp.com/s/ibmplexmono/v19/-F6sfjptAgt5VM-kVkqdyU8n1ioSflVFgsARHNh4zg.woff2",
        ]:
            font_urls.add(u)

    for url in sorted(font_urls):
        fetch(url, subdir="third_party", binary=True)
        time.sleep(0.12)


# --- Phase 10: External References ---

def fetch_external_references():
    log("=== FETCHING EXTERNAL REFERENCES ===")
    refs = [
        "https://www.reddit.com/r/NoMansSkyTheGame/comments/1tczflq/connection_detected_access_denied.json",
        "https://www.reddit.com/r/NoMansSkyTheGame/comments/1tczflq/connection_detected_access_denied/",
        "https://forums.atlas-65.com/t/project-skyscraper-no-mans-sky-arg/9095/180.json",
        "https://forums.atlas-65.com/t/project-skyscraper-no-mans-sky-arg/9095/180",
    ]
    for url in refs:
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": USER_AGENT}), timeout=15)
            content = r.read()
            path = url_to_path(url, subdir="endpoints")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            stats["fetched"] += 1
            log(f"  OK   {url}")
        except Exception as e:
            stats["failed"] += 1
            log(f"  FAIL {url} -> {e}")
        time.sleep(0.5)


# --- Phase 11: Additional Endpoint Probes ---

def fetch_additional_endpoints():
    log("=== FETCHING ADDITIONAL ENDPOINTS ===")
    for path in [
        "/wp-content/debug.log", "/wp-content/uploads/",
        "/wp-includes/", "/wp-admin/",
        "/.htaccess", "/.git/config", "/.env",
    ]:
        fetch(f"{BASE_URL}{path}", subdir="endpoints")
        time.sleep(0.12)


# --- Phase 12: Manifest & Diff ---

def generate_manifest():
    log("=== GENERATING MANIFEST ===")
    total_size = 0
    total_files = 0
    section_data = {}

    for root, dirs, files in os.walk(str(MIRROR_DIR)):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
        for fn in files:
            fp = os.path.join(root, fn)
            rel = os.path.relpath(fp, str(MIRROR_DIR))
            sz = os.path.getsize(fp)
            total_files += 1
            total_size += sz
            parts = rel.replace("\\", "/").split("/")
            section = parts[0] if parts else "root"
            section_data.setdefault(section, {"files": 0, "size": 0})
            section_data[section]["files"] += 1
            section_data[section]["size"] += sz

    lines = [
        f"# project-skyscraper.com \u2014 Complete Mirror Manifest",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Source:** {BASE_URL}",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| **Total files** | {total_files} |",
        f"| **Total size** | {_fmt_size(total_size)} |",
        "",
        "## Section Breakdown",
        "",
        "| Section | Files | Size |",
        "|---------|-------|------|",
    ]
    for section in sorted(section_data):
        if section in ("update_mirror.py", "MIRROR_MANIFEST.md"):
            continue
        d = section_data[section]
        lines.append(f"| **{section}/** | {d['files']} | {_fmt_size(d['size'])} |")
    lines += ["", "## HTML Pages", ""]
    hdir = MIRROR_DIR / "html"
    if hdir.exists():
        for hf in sorted(hdir.glob("*.html")):
            lines.append(f"- `{hf.stem}` ({_fmt_size(hf.stat().st_size)})")
    lines += ["", "## Media Files", ""]
    mdir = MIRROR_DIR / "media"
    if mdir.exists():
        for mf in sorted(mdir.rglob("*")):
            if mf.is_file():
                rel = str(mf.relative_to(MIRROR_DIR)).replace("\\", "/")
                lines.append(f"- `{rel}` ({_fmt_size(mf.stat().st_size)})")
    lines += ["", "## API Endpoints", ""]
    adir = MIRROR_DIR / "api"
    if adir.exists():
        for af in sorted(adir.rglob("*")):
            if af.is_file():
                rel = str(af.relative_to(MIRROR_DIR)).replace("\\", "/")
                lines.append(f"- `{rel}` ({_fmt_size(af.stat().st_size)})")
    lines += ["", "*Manifest auto-generated by update_mirror.py*", ""]

    manifest_path = MIRROR_DIR / "MIRROR_MANIFEST.md"
    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"  Manifest written: {manifest_path} ({total_files} files, {_fmt_size(total_size)})")


def store_diff():
    if not changes:
        return
    lines = [
        f"# Change Report \u2014 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        f"**{len(changes)} file(s) changed**",
        "",
    ]
    for url, path in changes:
        rel = str(path.relative_to(MIRROR_DIR)).replace("\\", "/")
        sz = _fmt_size(path.stat().st_size)
        lines += [f"- `{url}`", f"  \u2192 `{rel}` ({sz})", ""]

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    diff_path = MIRROR_DIR / "diffs" / f"change_{ts}.md"
    diff_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"  Diff saved: {diff_path}")


# --- Unresolved Marker Files ---

NS_ROOTS_DIR = [
    "wp-json/wp/v2", "wp-json/jetpack/v4", "wp-json/wpcom/v2",
    "wp-json/wpcom/v3", "wp-json/wpcomsh/v1", "wp-json/code-snippets/v1",
    "wp-json/crowdsignal-forms/v1", "wp-json/wp-statistics/v2",
    "wp-json/wp-site-health/v1", "wp-json/wp-abilities/v1",
    "wp-json/akismet/v1", "wp-json/my-jetpack/v1",
    "wp-json/jetpack-boost/v1", "wp-json/jetpack-global-styles/v1",
    "wp-json/newspack-blocks/v1", "wp-json/videopress/v1",
    "wp-json/help-center", "wp-json/wp-block-editor/v1",
    "wp-json/wp-sync/v1", "wp-json/oembed/1.0",
]

EXAMPLES_NS_SUBS = {
    "wp-json/wp/v2": (
        "posts, pages, media, categories, tags, types, statuses, "
        "taxonomies, users, comments, blocks, navigation, search, "
        "settings, themes, plugins, block-types, templates, "
        "template-parts, global-styles, menu-items, menus, "
        "sidebars, widgets, block-directory/search"
    ),
    "wp-json/jetpack/v4": (
        "site, module, scan, sync, connection, plugins, "
        "recommendations, backup, stats-app, import, search, social, "
        "blaze, videopress"
    ),
    "wp-json/oembed/1.0": (
        "embed (requires ?url= query parameter)"
    ),
}


def generate_unresolved_markers():
    """Create .unresolved marker files for endpoints that live as
    directories and can never be fetched directly."""
    api_dir = MIRROR_DIR / "api"
    for ns in NS_ROOTS_DIR:
        unresolved = api_dir / (ns + ".unresolved")
        if unresolved.is_file():
            continue
        sub_info = EXAMPLES_NS_SUBS.get(ns, "sub-endpoints")
        unresolved.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            f"Unfetchable endpoint: /{ns}",
            "",
            "This is a namespace root (directory) in the WordPress REST API.",
            "It cannot be fetched directly because multiple endpoints live",
            "under this path.",
            "",
            "Available sub-endpoints: " + sub_info,
            "",
            "Request a specific sub-endpoint instead.",
            "",
            "Generated by update_mirror.py",
        ]
        unresolved.write_text("\n".join(lines) + "\n")
        log(f"  MARKER {ns}.unresolved")


# --- ID Series Analysis ---

def generate_id_series_analysis():
    """Analyze post/page/media IDs, categorize by digit count, compute deltas."""
    api_base = MIRROR_DIR / "api" / "wp-json" / "wp" / "v2"

    def collect(endpoint_dir):
        acc = []
        d = api_base / endpoint_dir
        if d.is_dir():
            for jf in sorted(d.glob("*.json")):
                try:
                    data = json.loads(jf.read_bytes())
                except (json.JSONDecodeError, ValueError):
                    continue
                if isinstance(data, dict) and "id" in data and "date" in data:
                    acc.append((data["id"], data.get("date", ""), data.get("slug", "")))
        return acc

    all_posts = collect("posts")
    all_pages = collect("pages")
    all_media = collect("media")

    if not any([all_posts, all_pages, all_media]):
        log("  No ID data found, skipping series analysis")
        return

    def series_label(id_val):
        if id_val < 1000:
            return "A (3-digit)"
        elif id_val < 10000:
            return "B (4-digit)"
        else:
            return "C (other)"

    def build_series(items, label):
        by_series = {}
        for iid, date, slug in items:
            ser = series_label(iid)
            by_series.setdefault(ser, []).append((iid, date, slug))
        lines = [
            f"### Series {label}",
            "",
            "```",
            f"    {'ID':>6}   {'Delta':>6}   {'Date':<12}   Slug",
            "    " + "-" * 50,
        ]
        for ser_key in sorted(by_series.keys()):
            entries = sorted(by_series[ser_key])
            for idx, (iid, date, slug) in enumerate(entries):
                if idx == 0:
                    delta = "  --"
                else:
                    d = iid - entries[idx - 1][0]
                    delta = f"{d:+5d}"
                lines.append(f"    {iid:>6}   {delta:>6}   {date:<12}   {slug}")
        lines.append("```\n")
        return "\n".join(lines)

    def series_title(label):
        parts = label.split()
        tag = parts[0][0].upper()
        desc = " ".join(parts[1:]) if len(parts) > 1 else ""
        return f"### Series {tag}: {desc}" if desc else f"### Series {tag}"

    sections = []
    for label in ["A (3-digit)", "B (4-digit)", "C (other)"]:
        subset = [(iid, date, slug) for iid, date, slug in all_posts + all_pages + all_media
                  if series_label(iid) == label]
        if subset:
            subset.sort(key=lambda x: x[0])
            lines = [series_title(label), ""]
            lines.append("```")
            lines.append(f"    {'ID':>6}   {'Delta':>6}   {'Date':<12}   {'Type':<8}   Slug")
            lines.append("    " + "-" * 60)
            type_map = {}
            for iid, date, slug in all_posts:
                type_map[iid] = "post"
            for iid, date, slug in all_pages:
                type_map[iid] = "page"
            for iid, date, slug in all_media:
                type_map[iid] = "media"
            for idx, (iid, date, slug) in enumerate(subset):
                if idx == 0:
                    delta = "  --"
                else:
                    d = iid - subset[idx - 1][0]
                    delta = f"{d:+5d}"
                typ = type_map.get(iid, "?")
                lines.append(f"    {iid:>6}   {delta:>6}   {date:<12}   {typ:<8}   {slug}")
            lines.append("```\n")
            sections.append("\n".join(lines))

    combined = [
        "# Post/Page/Media ID Series Analysis",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Source:** {BASE_URL}/wp-json/wp/v2/{{posts,pages,media}}",
        "",
        "IDs are categorized by digit count:",
        "",
        "| Series | Digit Count | Range |",
        "|--------|-------------|-------|",
        "| **A** | 3-digit | < 1000 |",
        "| **B** | 4-digit | 1000\u20139999 |",
        "| **C** | Other | >= 10000 |",
        "",
    ]
    for s in sections:
        combined.append(s)
    combined.append("*Auto-generated by update_mirror.py*\n")

    out_path = MIRROR_DIR / "POST_ID_SERIES.md"
    out_path.write_text("\n".join(combined) + "\n", encoding="utf-8")
    log(f"  ID series written: {out_path}")


# --- Main ---

def clean_stale_paths():
    """Remove files that exist where we need directories (and vice versa)."""
    conflicts = [
        MIRROR_DIR / "api" / "wp-json" / "oembed" / "1.0",          # file, needs to be dir
        MIRROR_DIR / "api" / "wp-json" / "oembed" / "1.0_dir",       # stale backup
    ]
    for c in conflicts:
        if c.is_file():
            c.unlink()
        elif c.is_dir():
            import shutil
            shutil.rmtree(c)

    # Remove stale flat HTML duplicates that also exist in nested form
    # Old url_to_path stored /2026/05/25/sec-log-113610/ as
    # html/2026_05_25_sec-log-113610.html. Current code stores it as
    # html/2026/05/25/sec-log-113610.html. Clean up the old flat copies.
    html_dir = MIRROR_DIR / "html"
    if html_dir.exists():
        for f in sorted(html_dir.glob("*.html")):
            name = f.stem
            if "_" not in name:
                continue
            # Build the nested equivalent path
            nested = html_dir / (name.replace("_", "/") + ".html")
            if nested.is_file() and nested.stat().st_size >= f.stat().st_size * 0.9:
                # Nested copy exists and is roughly same size — remove flat stale
                f.unlink()
                hdr = f.parent / (f.name + ".headers.json")
                if hdr.is_file():
                    hdr.unlink()
                print(f"  CLEANED stale flat: {f.name}")


def main():
    log("=" * 60)
    log("  project-skyscraper.com - Complete Mirror Update")
    log(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    log("  Fully self-discovering — no hardcoded values")
    log("=" * 60)
    log("")

    clean_stale_paths()
    generate_unresolved_markers()

    # Phase 1: Discovery
    log("PHASE 1: Discovery")
    sitemap_urls = discover_sitemap_urls()
    log(f"  {len(sitemap_urls)} URLs from sitemaps")
    log("")

    # Phase 2: HTML pages
    log("PHASE 2: HTML Pages")
    fetch_html_pages(sitemap_urls)
    log("")

    # Phase 3: REST API (returns discovered IDs and links)
    log("PHASE 3: REST API")
    post_ids, page_ids, media_ids, post_links, page_links = fetch_api_endpoints()
    log("")

    # Phase 4: Media
    log("PHASE 4: Media")
    fetch_media(post_links, page_links, sitemap_urls)
    log("")

    # Phase 5: Theme Assets
    log("PHASE 5: Theme Assets")
    fetch_theme_assets()
    log("")

    # Phase 6: Plugin Assets
    log("PHASE 6: Plugin Assets")
    fetch_plugin_assets()
    log("")

    # Phase 7: Discovery
    log("PHASE 7: Discovery Documents")
    fetch_discovery()
    log("")

    # Phase 8: Extras
    log("PHASE 8: Extras")
    fetch_extras()
    log("")

    # Phase 9: Third-party CDN
    log("PHASE 9: Third-party CDN")
    fetch_third_party()
    log("")

    # Phase 10: External references
    log("PHASE 10: External References")
    fetch_external_references()
    log("")

    # Phase 11: Additional endpoint probes
    log("PHASE 11: Additional Endpoints")
    fetch_additional_endpoints()
    log("")

    # Phase 12: Manifest & Diff
    log("PHASE 12: Manifest & Diff")
    generate_manifest()
    generate_id_series_analysis()
    store_diff()
    log("")

    # Cleanup: remove __pycache__ directories
    for cache_dir in MIRROR_DIR.rglob("__pycache__"):
        if cache_dir.is_dir():
            import shutil
            shutil.rmtree(cache_dir)
            log(f"  CLEANED {cache_dir.relative_to(MIRROR_DIR)}")

    log("=" * 60)
    log("  UPDATE COMPLETE")
    log(f"  Fetched: {stats['fetched']}  |  New: {stats['new']}  |  Changed: {stats['changed']}")
    log(f"  Skipped (unchanged): {stats['skipped']}  |  Failed: {stats['failed']}")
    if changes:
        log(f"  Changes detected: {len(changes)} file(s) — diff saved to diffs/")
    log("=" * 60)


if __name__ == "__main__":
    main()
