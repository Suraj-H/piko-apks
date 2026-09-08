from apkmirror import Version
from apps.shared import MORPHE_CLI
from utils import patch_apk

PATCH_INCLUDES = ["Remove Ads"]


def build_apks(latest_version: Version, patch_files: list[str], apkm: str) -> list[str]:
    version = latest_version.version
    output = f"mindicator-v{version}-arm64-v8a.apk"

    patch_apk(
        MORPHE_CLI,
        patch_files,
        apkm,
        includes=PATCH_INCLUDES,
        excludes=[],
        out=output,
    )

    return [output]
