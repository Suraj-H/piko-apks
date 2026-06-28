from apkmirror import Version
from apps.shared import MORPHE_CLI
from utils import patch_apk

COMMON_INCLUDES = [
    "Disable ads",
    "Download media",
    "Add settings",
    "Disable analytics",
    "Disable video autoplay",
    "Hide suggested content",
    "Improve image viewing",
    "Open links externally",
    "Remove screenshot popup",
    "Unlock developer options",
]


def build_apks(latest_version: Version, patch_files: list[str], apkm: str) -> list[str]:
    version = latest_version.version
    arch = "arm64-v8a"
    outputs = [
        f"instagram-piko-v{version}-{arch}.apk",
        f"instagram-piko-amoled-v{version}-{arch}.apk",
    ]

    patch_apk(
        MORPHE_CLI,
        patch_files,
        apkm,
        includes=COMMON_INCLUDES,
        excludes=["Amoled theme"],
        out=outputs[0],
    )

    patch_apk(
        MORPHE_CLI,
        patch_files,
        apkm,
        includes=["Amoled theme", *COMMON_INCLUDES],
        excludes=[],
        out=outputs[1],
    )

    return outputs
