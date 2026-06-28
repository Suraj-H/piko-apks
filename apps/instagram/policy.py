import re

import requests

from apkmirror import Version
from apps.shared import PIKO_PATCHES

PIKO_CONSTANTS_PATH = (
    "patches/src/main/kotlin/app/crimera/patches/instagram/utils/Constants.kt"
)

FALLBACK_SUPPORTED_VERSIONS: tuple[str, ...] = ("435.0.0.37.76",)

_COMPATIBILITY_IG_START = "val COMPATIBILITY_INSTAGRAM ="
_COMPATIBILITY_IG_END = "// Instagram classes."


def parse_version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def fetch_supported_versions(piko_ref: str) -> tuple[str, ...]:
    url = (
        f"https://raw.githubusercontent.com/crimera/piko/{piko_ref}/"
        f"{PIKO_CONSTANTS_PATH}"
    )
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as error:
        print(
            f"Failed to fetch piko Instagram supported versions from {piko_ref}: {error}"
        )
        return FALLBACK_SUPPORTED_VERSIONS

    source = response.text
    start = source.find(_COMPATIBILITY_IG_START)
    end = source.find(_COMPATIBILITY_IG_END)
    if start < 0 or end < 0 or end <= start:
        print(
            "Failed to parse piko COMPATIBILITY_INSTAGRAM block, using fallback versions"
        )
        return FALLBACK_SUPPORTED_VERSIONS

    block = source[start:end]
    versions = re.findall(r'version\s*=\s*"([^"]+)"', block)
    if not versions:
        print("No piko Instagram target versions found, using fallback versions")
        return FALLBACK_SUPPORTED_VERSIONS

    return tuple(versions)


def get_best_buildable_version(
    versions: list[Version],
    supported: tuple[str, ...],
) -> Version | None:
    by_name = {version.version: version for version in versions}
    ordered = sorted(supported, key=parse_version_tuple, reverse=True)
    for version_name in ordered:
        if version_name in by_name:
            return by_name[version_name]
    return None


def release_tag(version_name: str) -> str:
    return f"ig-{version_name}"
