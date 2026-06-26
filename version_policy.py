from dataclasses import dataclass

from apkmirror import Version

# Highest-first. Must match piko v3.7.0-dev.7 Constants.kt (APKMirror-sourced builds).
SUPPORTED_APKMIRROR_VERSIONS: tuple[str, ...] = (
    "12.2.0-release.0",
    "12.0.0-release.0",
    "11.81.0-release.0",
)

# PairIP-ripped builds are supported by piko but not published on APKMirror.
RIPPED_VERSIONS: tuple[str, ...] = (
    "11.99.0-release-ripped.1",
)

APKM_INPUT_DIR = "build-cache"
PIKO_PATCHES = "bins/patches.mpp"
X_SHIM_PATCHES = "bins/x-shim.mpp"


def apkm_input_for(version_name: str) -> str:
    safe_name = version_name.replace(".", "-")
    return f"{APKM_INPUT_DIR}/{safe_name}.apkm"


@dataclass(frozen=True)
class BuildTarget:
    version: Version
    patch_files: tuple[str, ...]
    uses_x_shim: bool


def parse_version_tuple(version: str) -> tuple[int, int, int]:
    base = version.split("-", maxsplit=1)[0]
    parts = base.split(".")
    return (int(parts[0]), int(parts[1]), int(parts[2]))


def needs_x_shim(version_name: str) -> bool:
    if version_name in RIPPED_VERSIONS:
        return False
    if version_name == "11.81.0-release.0":
        return False
    return parse_version_tuple(version_name) >= (11, 88, 0)


def is_supported_version(version_name: str) -> bool:
    return version_name in SUPPORTED_APKMIRROR_VERSIONS or version_name in RIPPED_VERSIONS


def get_patch_files(version_name: str) -> tuple[str, ...]:
    files = [PIKO_PATCHES]
    if needs_x_shim(version_name):
        files.append(X_SHIM_PATCHES)
    return tuple(files)


def get_best_buildable_version(versions: list[Version]) -> Version | None:
    by_name = {version.version: version for version in versions if "release" in version.version}
    for version_name in SUPPORTED_APKMIRROR_VERSIONS:
        if version_name in by_name:
            return by_name[version_name]
    return None


def build_target(version: Version) -> BuildTarget:
    if not is_supported_version(version.version):
        supported = ", ".join([*SUPPORTED_APKMIRROR_VERSIONS, *RIPPED_VERSIONS])
        raise ValueError(
            f"Unsupported version {version.version}. Supported builds: {supported}"
        )
    uses_x_shim = needs_x_shim(version.version)
    return BuildTarget(
        version=version,
        patch_files=get_patch_files(version.version),
        uses_x_shim=uses_x_shim,
    )
