import zipfile

from utils import panic

ARM64_MARKERS = (
    "arm64_v8a",
    "arm64-v8a",
    "config.arm64",
)


def bundle_has_arm64(path: str) -> bool:
    with zipfile.ZipFile(path, "r") as archive:
        for name in archive.namelist():
            lowered = name.lower()
            if lowered.startswith("lib/arm64-v8a/"):
                return True
            if any(marker in lowered for marker in ARM64_MARKERS):
                return True
    return False


def require_arm64_bundle(path: str) -> None:
    if not bundle_has_arm64(path):
        panic(
            f"Downloaded bundle {path} has no arm64 / config.arm64_v8a split; "
            "refusing to build"
        )
