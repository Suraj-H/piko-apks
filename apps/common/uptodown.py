import time

from bs4 import BeautifulSoup
from http_client import get_http_client


class UptodownError(Exception):
    pass


def _raise_for_status(response, url: str) -> None:
    try:
        response.raise_for_status()
    except Exception as error:  # noqa: BLE001
        raise UptodownError(f"Uptodown request to {url} failed: {error}") from error


def _get_with_retry(client, url: str, *, retries: int = 3, **kwargs) -> object:
    """GET with retries.

    Uptodown occasionally returns transient errors (observed: a bare 410)
    to the scraper client that clear up on a plain retry seconds later, so
    treat any non-2xx/exception as retryable rather than failing outright.
    """
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
            print(f"Uptodown request to {url} failed ({last_error}), retrying...")
            time.sleep(2 * (attempt + 1))
    raise UptodownError(f"Uptodown request to {url} failed: {last_error}")


def _find_version_entry(base_url: str, data_code: str, version: str) -> dict:
    client = get_http_client()
    xapk_entry: dict | None = None

    for page in range(1, 21):
        versions_url = f"{base_url}/apps/{data_code}/versions/{page}"
        response = _get_with_retry(client, versions_url, timeout=30)
        _raise_for_status(response, versions_url)
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

    raise UptodownError(f"Version {version} not found on Uptodown")


def download_uptodown_bundle(
    base_url: str,
    app_label: str,
    version: str,
    dest: str,
) -> None:
    client = get_http_client()
    versions_url = f"{base_url}/versions"
    versions_page = _get_with_retry(client, versions_url, timeout=30)
    _raise_for_status(versions_page, versions_url)

    soup = BeautifulSoup(versions_page.text, "html.parser")
    app_node = soup.select_one("#detail-app-name")
    if app_node is None or not app_node.get("data-code"):
        raise UptodownError(f"Could not resolve Uptodown app id for {app_label}")

    data_code = str(app_node["data-code"])
    entry = _find_version_entry(base_url, data_code, version)
    version_id = entry["versionURL"]["versionID"]
    print(
        f"Downloading {app_label} {version} from Uptodown "
        f"(kind={entry.get('kindFile')})"
    )

    download_url_page = f"{base_url}/download/{version_id}"
    download_page = _get_with_retry(client, download_url_page, timeout=30)
    _raise_for_status(download_page, download_url_page)
    soup = BeautifulSoup(download_page.text, "html.parser")
    button = soup.select_one("#detail-download-button")
    if button is None or not button.get("data-url"):
        raise UptodownError("Uptodown download button not found")

    download_url = f"https://dw.uptodown.com/dwn/{button['data-url']}"
    response = client.get(download_url, timeout=(30, 600), stream=True, allow_redirects=True)
    try:
        _raise_for_status(response, download_url)
        with open(dest, "wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    finally:
        response.close()

    time.sleep(0.5)
