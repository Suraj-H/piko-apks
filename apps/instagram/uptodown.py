from apps.common.uptodown import UptodownError, download_uptodown_bundle

INSTAGRAM_UPTODOWN_URL = "https://instagram.en.uptodown.com/android"

__all__ = ["UptodownError", "download_instagram_apkm"]


def download_instagram_apkm(version: str, dest: str) -> None:
    download_uptodown_bundle(INSTAGRAM_UPTODOWN_URL, "Instagram", version, dest)
