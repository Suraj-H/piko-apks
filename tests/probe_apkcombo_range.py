from constants import HEADERS
from sites.apkcombo import get_download_url, get_versions
import requests

URL = "https://apkcombo.com/twitter/com.twitter.android/"

versions = get_versions(URL)
print("Versions:", [version.version for version in versions[:5]])

for version in versions:
    direct_link = get_download_url(version)
    headers = {
        **HEADERS,
        "Accept": "*/*",
        "Origin": "https://apkcombo.com",
        "Referer": version.link,
        "Range": "bytes=0-0",
    }

    response = requests.get(
        direct_link,
        headers=headers,
        stream=True,
        allow_redirects=True,
        verify=False,
    )

    print("\nVersion:", version.version)
    print("Status:", response.status_code)
    print("Content-Disposition:", response.headers.get("Content-Disposition"))
    print("Content-Range:", response.headers.get("Content-Range"))
    print("Content-Type:", response.headers.get("Content-Type"))

    disposition = response.headers.get("Content-Disposition", "").lower()
    response.close()

    if response.status_code != 206:
        continue

    if "alpha" in disposition or "beta" in disposition:
        continue

    print("Selected stable version:", version.version)
    break
