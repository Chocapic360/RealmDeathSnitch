# pip install playwright
# python -m playwright install chromium

from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
import base64, os, re

PAGE_URL = "https://www.realmeye.com"   # <-- put your page here
OUTDIR   = "images"
TARGET_KEY = "sheets"     # only save if filename/URL/headers mention this; set to "" to save all images

FNAME_RE = re.compile(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', re.I)

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

def pick_ext_from_ct(ct: str) -> str:
    ct = (ct or "").lower()
    if "png" in ct: return ".png"
    if "jpeg" in ct or "jpg" in ct: return ".jpg"
    if "webp" in ct: return ".webp"
    if "gif" in ct: return ".gif"
    return ".bin"

def extract_name(url: str, headers: dict, ct: str) -> str:
    # Try Content-Disposition
    cd = ""
    for k, v in headers.items():
        if k.lower() == "content-disposition":
            cd = v
            break
    if cd:
        m = FNAME_RE.search(cd)
        if m:
            return m.group(1).strip().strip('"')
    # Fallback to URL path
    base = os.path.basename(urlparse(url).path)
    if base:
        return base
    # Fallback to content-type guess
    return "image" + pick_ext_from_ct(ct)

def ensure_unique(path: str) -> str:
    if not os.path.exists(path):
        return path
    root, ext = os.path.splitext(path)
    i = 2
    while True:
        cand = f"{root}-{i}{ext}"
        if not os.path.exists(cand):
            return cand
        i += 1

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Create a CDP session and disable cache
    client = context.new_cdp_session(page)
    client.send("Network.enable", {})
    client.send("Network.setCacheDisabled", {"cacheDisabled": True})

    ensure_dir(OUTDIR)

    # Track image-like requests we want to fetch bodies for
    want = {}  # requestId -> (url, headers, contentType)

    def on_response_received(params):
        resp = params.get("response", {})
        url = resp.get("url", "")
        headers = resp.get("headers", {}) or {}
        ctype = headers.get("content-type") or headers.get("Content-Type") or ""
        # Only consider images (or anything that might be the target)
        looks_image = "image" in ctype.lower()
        mentions_target = (TARGET_KEY.lower() in url.lower()) or \
                          (TARGET_KEY and any(TARGET_KEY.lower() in str(v).lower() for v in headers.values()))
        if looks_image or mentions_target:
            want[params["requestId"]] = (url, headers, ctype)

    def on_loading_finished(params):
        req_id = params["requestId"]
        if req_id not in want:
            return
        url, headers, ctype = want.pop(req_id)
        try:
            body = client.send("Network.getResponseBody", {"requestId": req_id})
            data = base64.b64decode(body["body"]) if body.get("base64Encoded") else body["body"].encode()

            # If you only want sheets.png, enforce it here:
            name = extract_name(url, headers, ctype)
            if TARGET_KEY and TARGET_KEY.lower() not in name.lower() \
               and TARGET_KEY.lower() not in url.lower():
                return

            out = ensure_unique(os.path.join(OUTDIR, name))
            with open(out, "wb") as f:
                f.write(data)
            print(f"Saved: {out}  <-  {url}")
        except Exception as e:
            print("Skip (no body):", e)

    client.on("Network.responseReceived", on_response_received)
    client.on("Network.loadingFinished", on_loading_finished)

    page.goto(PAGE_URL, wait_until="networkidle")
    page.wait_for_timeout(2000)  # allow lazy assets to finish
    browser.close()
