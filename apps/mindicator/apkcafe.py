import base64
import re
import time
import urllib.parse

from bs4 import BeautifulSoup
from http_client import get_http_client

APKCAFE_APP_SLUG = "m-indicator-indian-rail-msrtc"
SEED_DOWNLOAD_PAGE = (
    "https://apk.cafe/download?split=563770/3508444/m-indicator-indian-rail-msrtc"
)


class ApkCafeError(Exception):
    pass


def _get_with_retry(client, url: str, *, retries: int = 3, **kwargs) -> object:
    response = None
    last_error = "unknown error"
    for attempt in range(retries):
        try:
            response = client.get(url, **kwargs)
            if response.ok:
                return response
            last_error = f"HTTP {response.status_code}"
        except Exception as error:  # noqa: BLE001
            response = None
            last_error = str(error)
        if attempt < retries - 1:
            print(f"apk.cafe request to {url} failed ({last_error}), retrying...")
            time.sleep(2 * (attempt + 1))
    if response is not None:
        return response
    raise ApkCafeError(f"apk.cafe request to {url} failed: {last_error}")


def _normalize_href(href: str) -> str:
    if href.startswith("http"):
        return href
    return f"https://apk.cafe{href}"


def _parse_version_entries(html: str, version: str) -> list[tuple[str, float]]:
    soup = BeautifulSoup(html, "html.parser")
    entries: list[tuple[str, float]] = []

    for link in soup.select("a[href]"):
        href = link.get("href", "")
        text = link.get_text(" ", strip=True)
        if version not in text:
            continue
        if "APKS" not in text.upper():
            continue
        if "split=" not in href:
            continue

        size_match = re.search(r"size:\s*([\d.]+)\s*M", text, re.IGNORECASE)
        size_mb = float(size_match.group(1)) if size_match else 0.0
        entries.append((_normalize_href(href), size_mb))

    return entries


def find_split_download_page(version: str) -> str:
    client = get_http_client()
    response = _get_with_retry(client, SEED_DOWNLOAD_PAGE, timeout=30)
    response.raise_for_status()

    entries = _parse_version_entries(response.text, version)
    if not entries:
        raise ApkCafeError(f"m-Indicator {version} not found on apk.cafe")

    entries.sort(key=lambda entry: entry[1], reverse=True)
    return entries[0][0]


def resolve_cdn_url(download_page_url: str) -> str:
    client = get_http_client()
    response = _get_with_retry(client, download_page_url, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    button = soup.select_one("a.dwn1, a[class*=dwn]")
    if button is None or not button.get("href"):
        raise ApkCafeError("apk.cafe download button not found")

    go_url = _normalize_href(str(button["href"]))
    params = urllib.parse.parse_qs(urllib.parse.urlparse(go_url).query)
    encoded = params.get("b", [None])[0]
    if not encoded:
        raise ApkCafeError("apk.cafe download link missing CDN payload")

    return base64.b64decode(encoded).decode()


def download_mindicator_apkm(version: str, dest: str) -> None:
    download_page = find_split_download_page(version)
    print(f"Downloading m-Indicator {version} from apk.cafe ({download_page})")

    cdn_url = resolve_cdn_url(download_page)
    client = get_http_client()
    response = client.get(cdn_url, timeout=(30, 600), stream=True, allow_redirects=True)
    try:
        response.raise_for_status()
        with open(dest, "wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    finally:
        response.close()

    time.sleep(0.5)
