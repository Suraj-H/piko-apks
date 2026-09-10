import re
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from http_client import get_http_client

from apps.mindicator.bundle import bundle_has_arm64

APKPURE_SLUG = "m-indicator-mumbai-local"
PACKAGE_NAME = "com.mobond.mindicator"
APKPURE_BASE_URL = f"https://apkpure.com/{APKPURE_SLUG}/{PACKAGE_NAME}"


class ApkPureError(Exception):
    pass


def _page_has_arm64_variant(html: str, version: str) -> bool:
    lowered = html.lower()
    if version not in html:
        return False
    version_index = lowered.find(version.lower())
    if version_index < 0:
        return False
    window = lowered[max(0, version_index - 200) : version_index + 400]
    return "arm64" in window


def _extract_download_url(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "")
        if not href:
            continue
        if "d.apkpure.com" in href and (".xapk" in href.lower() or "/b/xapk/" in href.lower()):
            return href
        if "/b/XAPK/" in href or "/b/APK/" in href:
            return urljoin(APKPURE_BASE_URL, href)

    match = re.search(r"https://d\.apkpure\.com/[^\"'\s>]+", html)
    if match:
        return match.group(0)

    return None


def download_mindicator_bundle(version: str, dest: str) -> None:
    client = get_http_client()
    page_url = f"{APKPURE_BASE_URL}/download/{version}"
    print(f"Trying APKPure fallback for m-Indicator {version}: {page_url}")

    response = client.get(page_url, timeout=30)
    if not response.ok:
        raise ApkPureError(f"APKPure page returned HTTP {response.status_code}")

    if not _page_has_arm64_variant(response.text, version):
        raise ApkPureError(
            f"APKPure listing for m-Indicator {version} does not advertise arm64"
        )

    download_url = _extract_download_url(response.text)
    if download_url is None:
        raise ApkPureError(f"Could not find APKPure download link for {version}")

    print(f"Downloading m-Indicator {version} from APKPure")
    download_response = client.get(
        download_url,
        timeout=(30, 600),
        stream=True,
        allow_redirects=True,
    )
    try:
        download_response.raise_for_status()
        with open(dest, "wb") as handle:
            for chunk in download_response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    finally:
        download_response.close()

    if not bundle_has_arm64(dest):
        raise ApkPureError(
            f"APKPure artifact for m-Indicator {version} is not arm64-capable"
        )

    time.sleep(0.5)
