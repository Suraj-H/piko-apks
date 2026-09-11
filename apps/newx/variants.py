from apkmirror import Version
from apps.newx.policy import DEFAULT_EXCLUDES, TWITTER_BRANDING_PATCH
from apps.shared import MORPHE_CLI
from utils import patch_apk


def build_apks(latest_version: Version, patch_files: list[str], bundle_path: str) -> list[str]:
    version = latest_version.version
    outputs = [
        f"x-newx-v{version}.apk",
        f"twitter-newx-v{version}.apk",
    ]

    patch_apk(
        MORPHE_CLI,
        patch_files,
        bundle_path,
        includes=None,
        excludes=list(DEFAULT_EXCLUDES),
        out=outputs[0],
    )

    patch_apk(
        MORPHE_CLI,
        patch_files,
        bundle_path,
        includes=None,
        excludes=[
            patch
            for patch in DEFAULT_EXCLUDES
            if patch != TWITTER_BRANDING_PATCH
        ],
        out=outputs[1],
    )

    return outputs
