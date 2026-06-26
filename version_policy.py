import re
from dataclasses import dataclass

import requests

from apkmirror import Version
from build_metadata import BuildMetadata, parse_build_metadata
from github import GithubRelease

PIKO_CONSTANTS_PATH = (
    "patches/src/main/kotlin/app/crimera/patches/twitter/utils/Constants.kt"
)

# Used only when piko Constants.kt cannot be fetched.
FALLBACK_SUPPORTED_VERSIONS: tuple[str, ...] = (
    "12.2.0-release.0",
    "12.0.0-release.0",
    "11.81.0-release.0",
)

RIPPED_VERSIONS: tuple[str, ...] = (
    "11.99.0-release-ripped.1",
)

APKM_INPUT_DIR = "build-cache"
PIKO_PATCHES = "bins/patches.mpp"
X_SHIM_PATCHES = "bins/x-shim.mpp"

_COMPATIBILITY_X_START = "val COMPATIBILITY_X ="
_COMPATIBILITY_X_END = "val COMPATIBILITY_X_11_69"


@dataclass(frozen=True)
class BuildTarget:
    version: Version
    patch_files: tuple[str, ...]
    uses_x_shim: bool


def apkm_input_for(version_name: str) -> str:
    safe_name = version_name.replace(".", "-")
    return f"{APKM_INPUT_DIR}/{safe_name}.apkm"


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


def is_supported_version(version_name: str, supported: tuple[str, ...]) -> bool:
    return version_name in supported or version_name in RIPPED_VERSIONS


def fetch_piko_supported_versions(piko_ref: str) -> tuple[str, ...]:
    url = (
        f"https://raw.githubusercontent.com/crimera/piko/{piko_ref}/"
        f"{PIKO_CONSTANTS_PATH}"
    )
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as error:
        print(f"Failed to fetch piko supported versions from {piko_ref}: {error}")
        return FALLBACK_SUPPORTED_VERSIONS

    source = response.text
    start = source.find(_COMPATIBILITY_X_START)
    end = source.find(_COMPATIBILITY_X_END)
    if start < 0 or end < 0 or end <= start:
        print("Failed to parse piko COMPATIBILITY_X block, using fallback versions")
        return FALLBACK_SUPPORTED_VERSIONS

    block = source[start:end]
    versions = re.findall(r'version\s*=\s*"([^"]+)"', block)
    if not versions:
        print("No piko target versions found, using fallback versions")
        return FALLBACK_SUPPORTED_VERSIONS

    return tuple(versions)


def get_patch_files(version_name: str) -> tuple[str, ...]:
    files = [PIKO_PATCHES]
    if needs_x_shim(version_name):
        files.append(X_SHIM_PATCHES)
    return tuple(files)


def get_best_buildable_version(
    versions: list[Version],
    supported: tuple[str, ...],
) -> Version | None:
    by_name = {
        version.version: version
        for version in versions
        if "release" in version.version
    }
    ordered = sorted(supported, key=parse_version_tuple, reverse=True)
    for version_name in ordered:
        if version_name in RIPPED_VERSIONS:
            continue
        if version_name in by_name:
            return by_name[version_name]
    return None


def build_target(version: Version, supported: tuple[str, ...]) -> BuildTarget:
    if not is_supported_version(version.version, supported):
        allowed = ", ".join([*supported, *RIPPED_VERSIONS])
        raise ValueError(
            f"Unsupported version {version.version}. Supported builds: {allowed}"
        )
    uses_x_shim = needs_x_shim(version.version)
    return BuildTarget(
        version=version,
        patch_files=get_patch_files(version.version),
        uses_x_shim=uses_x_shim,
    )


def normalize_shim_version(x_shim_version: str | None) -> str:
    return x_shim_version or "none"


def should_build(
    x_version: str,
    piko_version: str,
    x_shim_version: str | None,
    last_release: GithubRelease | None,
    *,
    force: bool = False,
) -> bool:
    if force:
        print("FORCE_BUILD enabled")
        return True

    if last_release is None:
        print("No previous release found, build required")
        return True

    metadata: BuildMetadata | None = parse_build_metadata(last_release.body)
    if metadata is None:
        print("Release metadata missing, build required")
        return True

    shim = normalize_shim_version(x_shim_version)
    reasons: list[str] = []
    if metadata["x_version"] != x_version:
        reasons.append(f"x {metadata['x_version']} -> {x_version}")
    if metadata["piko_version"] != piko_version:
        reasons.append(f"piko {metadata['piko_version']} -> {piko_version}")
    if metadata["x_shim_version"] != shim:
        reasons.append(f"x-shim {metadata['x_shim_version']} -> {shim}")

    if reasons:
        print("Build required:", ", ".join(reasons))
        return True

    print("No changes in x, piko, or x-shim versions, skipping build")
    return False
