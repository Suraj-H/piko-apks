import requests

from download_bins import MORPHE_PATCHES_REPO

PACKAGE_NAME = "com.mobond.mindicator"
PATCH_NAME = "Remove Ads"
PATCHES_SOURCE = MORPHE_PATCHES_REPO

FALLBACK_PATCHES_VERSION = "1.21.5"
FALLBACK_SUPPORTED_VERSIONS: tuple[str, ...] = ("18.0.364",)


def parse_version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def _patches_list_url(ref: str) -> str:
    return f"https://raw.githubusercontent.com/{MORPHE_PATCHES_REPO}/{ref}/patches-list.json"


def fetch_patches_list(ref: str) -> dict | None:
    url = _patches_list_url(ref)
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as error:
        print(f"Failed to fetch morphe patches list from {ref}: {error}")
        return None


def extract_supported_versions(patches_list: dict) -> tuple[str, ...]:
    for patch in patches_list.get("patches", []):
        if patch.get("name") != PATCH_NAME:
            continue
        for package in patch.get("compatiblePackages", []):
            if package.get("packageName") != PACKAGE_NAME:
                continue
            versions = tuple(
                target["version"]
                for target in package.get("targets", [])
                if target.get("version")
            )
            if versions:
                return versions
    return ()


def fetch_supported_versions(patches_version: str | None = None) -> tuple[str, ...]:
    ref = f"v{patches_version}" if patches_version else "main"
    patches_list = fetch_patches_list(ref)
    if patches_list is None and patches_version is not None:
        patches_list = fetch_patches_list("main")

    if patches_list is None:
        print("Using fallback m-Indicator supported versions")
        return FALLBACK_SUPPORTED_VERSIONS

    versions = extract_supported_versions(patches_list)
    if not versions:
        print("Remove Ads patch has no m-Indicator targets, using fallback versions")
        return FALLBACK_SUPPORTED_VERSIONS

    return versions


def resolve_pinned_version(
    supported_versions: tuple[str, ...],
    manual_version: str | None = None,
) -> str:
    if manual_version:
        return manual_version

    ordered = sorted(supported_versions, key=parse_version_tuple, reverse=True)
    if not ordered:
        raise ValueError("No supported m-Indicator versions in morphe patches metadata")
    return ordered[0]


def release_tag(version_name: str) -> str:
    return f"mi-{version_name}"
