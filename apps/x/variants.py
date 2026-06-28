from apkmirror import Version
from apps.shared import MORPHE_CLI
from utils import patch_apk

COMMON_INCLUDES = [
    "Enable app downgrading",
    "Hide FAB",
    "Disable chirp font",
    "Add ability to copy media link",
    "Hide Banner",
    "Hide promote button",
    "Hide Community Notes",
    "Delete from database",
    "Customize Navigation Bar items",
    "Remove premium upsell",
    "Control video auto scroll",
    "Force enable translate",
]


def build_apks(latest_version: Version, patch_files: list[str], apkm: str) -> list[str]:
    version = latest_version.version
    outputs = [
        f"x-piko-material-you-v{version}.apk",
        f"x-piko-v{version}.apk",
        f"twitter-piko-material-you-v{version}.apk",
        f"twitter-piko-v{version}.apk",
    ]

    patch_apk(
        MORPHE_CLI,
        patch_files,
        apkm,
        includes=["Dynamic color", *COMMON_INCLUDES],
        excludes=[],
        out=outputs[0],
    )

    patch_apk(
        MORPHE_CLI,
        patch_files,
        apkm,
        includes=COMMON_INCLUDES,
        excludes=["Dynamic color"],
        out=outputs[1],
    )

    patch_apk(
        MORPHE_CLI,
        patch_files,
        apkm,
        includes=["Bring back twitter", "Dynamic color", *COMMON_INCLUDES],
        excludes=[],
        out=outputs[2],
    )

    patch_apk(
        MORPHE_CLI,
        patch_files,
        apkm,
        includes=["Bring back twitter", *COMMON_INCLUDES],
        excludes=["Dynamic color"],
        out=outputs[3],
    )

    return outputs
