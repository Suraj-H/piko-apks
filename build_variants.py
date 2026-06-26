from apkmirror import Version
from utils import patch_apk

MORPHE_CLI = "bins/morphe-cli.jar"

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


def build_apks(latest_version: Version, patch_files: list[str], apkm: str):
    common_excludes: list[str] = []

    patch_apk(
        MORPHE_CLI,
        patch_files,
        apkm,
        includes=["Dynamic color", *COMMON_INCLUDES],
        excludes=common_excludes,
        out=f"x-piko-material-you-v{latest_version.version}.apk",
    )

    patch_apk(
        MORPHE_CLI,
        patch_files,
        apkm,
        includes=COMMON_INCLUDES,
        excludes=["Dynamic color", *common_excludes],
        out=f"x-piko-v{latest_version.version}.apk",
    )

    patch_apk(
        MORPHE_CLI,
        patch_files,
        apkm,
        includes=["Bring back twitter", "Dynamic color", *COMMON_INCLUDES],
        excludes=common_excludes,
        out=f"twitter-piko-material-you-v{latest_version.version}.apk",
    )

    patch_apk(
        MORPHE_CLI,
        patch_files,
        apkm,
        includes=["Bring back twitter", *COMMON_INCLUDES],
        excludes=["Dynamic color", *common_excludes],
        out=f"twitter-piko-v{latest_version.version}.apk",
    )
