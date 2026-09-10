import time

from http_client import get_http_client

from apps.mindicator.bundle import bundle_has_arm64

PACKAGE_NAME = "com.mobond.mindicator"
APKPURE_CDN_BASE = "https://d.apkpure.net/b/XAPK"


class ApkPureError(Exception):
    pass


def version_name_to_version_code(version: str) -> int:
    """m-Indicator versionCode matches the last dotted segment (e.g. 18.0.364 -> 364)."""
    segment = version.rsplit(".", 1)[-1]
    if not segment.isdigit():
        raise ApkPureError(f"Cannot derive APKPure versionCode from {version}")
    return int(segment)


def _cdn_download_url(version_code: int) -> str:
    return f"{APKPURE_CDN_BASE}/{PACKAGE_NAME}?versionCode={version_code}"


def download_mindicator_bundle(version: str, dest: str) -> None:
    version_code = version_name_to_version_code(version)
    download_url = _cdn_download_url(version_code)
    print(
        f"Downloading m-Indicator {version} from APKPure CDN "
        f"(versionCode={version_code}): {download_url}"
    )

    client = get_http_client()
    response = client.get(
        download_url,
        timeout=(30, 600),
        stream=True,
        allow_redirects=True,
    )
    try:
        if not response.ok:
            raise ApkPureError(
                f"APKPure CDN returned HTTP {response.status_code} "
                f"for versionCode {version_code}"
            )
        with open(dest, "wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    finally:
        response.close()

    if not bundle_has_arm64(dest):
        raise ApkPureError(
            f"APKPure artifact for m-Indicator {version} is not arm64-capable"
        )

    time.sleep(0.5)
