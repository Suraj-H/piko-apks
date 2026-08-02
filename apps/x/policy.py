from dataclasses import dataclass

import requests

from apkmirror import Version, version_page_exists
from apps.shared import (
    PIKO_PATCHES,
    X_SHIM_PATCHES,
    extract_piko_target_versions,
    x_version_page,
)

PIKO_CONSTANTS_PATH = (
    "patches/src/main/kotlin/app/crimera/patches/twitter/utils/Constants.kt"
)

FALLBACK_SUPPORTED_VERSIONS: tuple[str, ...] = (
    "12.2.0-release.0",
    "12.0.0-release.0",
    "11.81.0-release.0",
)

RIPPED_VERSIONS: tuple[str, ...] = ("11.99.0-release-ripped.1",)

_COMPATIBILITY_X_START = "val COMPATIBILITY_X ="


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


def is_supported_version(version_name: str, supported: tuple[str, ...]) -> bool:
    return version_name in supported or version_name in RIPPED_VERSIONS


def fetch_supported_versions(piko_ref: str) -> tuple[str, ...]:
    url = (
        f"https://raw.githubusercontent.com/crimera/piko/{piko_ref}/"
        f"{PIKO_CONSTANTS_PATH}"
    )
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as error:
        print(f"Failed to fetch piko X supported versions from {piko_ref}: {error}")
        return FALLBACK_SUPPORTED_VERSIONS

    versions = extract_piko_target_versions(response.text, _COMPATIBILITY_X_START)
    if not versions:
        print("Failed to parse piko COMPATIBILITY_X block, using fallback versions")
        return FALLBACK_SUPPORTED_VERSIONS

    return versions


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


def resolve_supported_version_directly(
    supported: tuple[str, ...],
) -> Version | None:
    """Look up piko-supported versions directly on APKMirror by URL.

    get_best_buildable_version only matches versions still on APKMirror's
    front listing page. Piko often targets a single X version that lags
    behind X's release cadence, so by the time we check it has usually
    scrolled past that page even though its APKMirror page still exists.
    This probes the exact page for each candidate instead of requiring it
    to be in the recent-listing scrape.
    """
    ordered = sorted(supported, key=parse_version_tuple, reverse=True)
    for version_name in ordered:
        if version_name in RIPPED_VERSIONS:
            continue
        url = x_version_page(version_name)
        if version_page_exists(url):
            return Version(link=url, version=version_name)
    return None


def build_target(version: Version, supported: tuple[str, ...]) -> BuildTarget:
    if not is_supported_version(version.version, supported):
        allowed = ", ".join([*supported, *RIPPED_VERSIONS])
        raise ValueError(
            f"Unsupported X version {version.version}. Supported builds: {allowed}"
        )
    return BuildTarget(
        version=version,
        patch_files=get_patch_files(version.version),
        uses_x_shim=needs_x_shim(version.version),
    )


def release_tag(version_name: str) -> str:
    return version_name
