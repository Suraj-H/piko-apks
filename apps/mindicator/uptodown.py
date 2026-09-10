from apps.common.uptodown import UptodownError, download_uptodown_bundle

MINDICATOR_UPTODOWN_URL = "https://m-indicator.en.uptodown.com/android"


def download_mindicator_bundle(version: str, dest: str) -> None:
    download_uptodown_bundle(
        MINDICATOR_UPTODOWN_URL,
        "m-Indicator",
        version,
        dest,
    )
