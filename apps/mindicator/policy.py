import requests

from apps.mindicator.patches_list import fetch_mindicator_versions

FALLBACK_SUPPORTED_VERSIONS: tuple[str, ...] = ("18.0.364",)


def parse_version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def fetch_supported_versions(patches_ref: str) -> tuple[str, ...]:
    try:
        versions = fetch_mindicator_versions(patches_ref)
    except (requests.RequestException, ValueError) as error:
        print(
            f"Failed to fetch morphe-patches supported versions from {patches_ref}: {error}"
        )
        return FALLBACK_SUPPORTED_VERSIONS

    if not versions:
        print(
            "Failed to parse morphe-patches Remove Ads targets for m-Indicator, "
            "using fallback versions"
        )
        return FALLBACK_SUPPORTED_VERSIONS

    return versions


def release_tag(version_name: str) -> str:
    return f"mi-{version_name}"
