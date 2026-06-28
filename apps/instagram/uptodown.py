import json
import time

from bs4 import BeautifulSoup
from http_client import get_http_client

INSTAGRAM_UPTODOWN_URL = "https://instagram.en.uptodown.com/android"


class UptodownError(Exception):
    pass


def _find_version_entry(data_code: str, version: str) -> dict:
    client = get_http_client()
    xapk_entry: dict | None = None

    for page in range(1, 21):
        response = client.get(
            f"{INSTAGRAM_UPTODOWN_URL}/apps/{data_code}/versions/{page}",
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        entries = payload.get("data") or []
        if not entries:
            break

        for entry in entries:
            if entry.get("version") != version:
                continue
            if entry.get("kindFile") == "xapk":
                return entry
            if xapk_entry is None:
                xapk_entry = entry

    if xapk_entry is not None:
        return xapk_entry

    raise UptodownError(f"Instagram {version} not found on Uptodown")


def download_instagram_apkm(version: str, dest: str) -> None:
    client = get_http_client()
    versions_page = client.get(f"{INSTAGRAM_UPTODOWN_URL}/versions", timeout=30)
    versions_page.raise_for_status()

    soup = BeautifulSoup(versions_page.text, "html.parser")
    app_node = soup.select_one("#detail-app-name")
    if app_node is None or not app_node.get("data-code"):
        raise UptodownError("Could not resolve Uptodown app id for Instagram")

    data_code = str(app_node["data-code"])
    entry = _find_version_entry(data_code, version)
    version_id = entry["versionURL"]["versionID"]
    print(f"Downloading Instagram {version} from Uptodown (kind={entry.get('kindFile')})")

    download_page = client.get(
        f"{INSTAGRAM_UPTODOWN_URL}/download/{version_id}",
        timeout=30,
    )
    download_page.raise_for_status()
    soup = BeautifulSoup(download_page.text, "html.parser")
    button = soup.select_one("#detail-download-button")
    if button is None or not button.get("data-url"):
        raise UptodownError("Uptodown download button not found")

    download_url = f"https://dw.uptodown.com/dwn/{button['data-url']}"
    response = client.get(download_url, timeout=(30, 600), stream=True, allow_redirects=True)
    try:
        response.raise_for_status()
        with open(dest, "wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    finally:
        response.close()

    time.sleep(0.5)
