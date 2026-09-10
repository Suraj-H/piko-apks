import os

from apps.mindicator.apkpure import ApkPureError, download_mindicator_bundle as download_apkpure
from apps.mindicator.bundle import require_arm64_bundle
from apps.mindicator.uptodown import UptodownError, download_mindicator_bundle as download_uptodown
from utils import panic


def download_source_bundle(version: str, dest: str) -> None:
    if os.path.exists(dest):
        os.unlink(dest)

    uptodown_error: Exception | None = None
    try:
        download_uptodown(version, dest)
        require_arm64_bundle(dest)
        return
    except UptodownError as error:
        uptodown_error = error
        print(f"Uptodown download failed: {error}")

    if os.path.exists(dest):
        os.unlink(dest)

    try:
        download_apkpure(version, dest)
        require_arm64_bundle(dest)
        return
    except ApkPureError as error:
        if uptodown_error is not None:
            panic(
                f"Failed to download m-Indicator {version} from Uptodown "
                f"({uptodown_error}) and APKPure ({error})"
            )
        panic(f"Failed to download m-Indicator {version} from APKPure: {error}")
