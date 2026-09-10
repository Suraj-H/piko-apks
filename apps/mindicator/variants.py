from apkmirror import Version
from apps.mindicator.policy import PATCH_NAME
from apps.shared import MORPHE_CLI
from utils import patch_apk


def build_apks(latest_version: Version, patch_files: list[str], bundle_path: str) -> list[str]:
    version = latest_version.version
    arch = "arm64-v8a"
    output = f"mindicator-no-ads-v{version}-{arch}.apk"

    patch_apk(
        MORPHE_CLI,
        patch_files,
        bundle_path,
        includes=[PATCH_NAME],
        excludes=[],
        out=output,
    )

    return [output]
