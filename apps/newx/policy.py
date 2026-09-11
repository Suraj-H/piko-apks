import requests

from download_bins import PIKO_NEWX_REPO, fetch_piko_newx_bundle

PATCHES_SOURCE = PIKO_NEWX_REPO

FALLBACK_PATCHES_VERSION = "3.19.0"
FALLBACK_SUPPORTED_VERSIONS: tuple[str, ...] = ("12.24.0-prod.02",)

DEFAULT_EXCLUDES: tuple[str, ...] = (
    "NewX: Restore Twitter branding",
    "NewX: Browse tweet object",
    "NewX: Server error logging",
)

TWITTER_BRANDING_PATCH = "NewX: Restore Twitter branding"


def parse_version_tuple(version: str) -> tuple[int, ...]:
    base = version.split("-", maxsplit=1)[0]
    return tuple(int(part) for part in base.split("."))


def fetch_bundle_metadata(patches_ref: str) -> dict:
    try:
        return fetch_piko_newx_bundle(patches_ref)
    except (requests.RequestException, ValueError) as error:
        print(f"Failed to fetch piko-newx bundle metadata from {patches_ref}: {error}")
        return {}


def fetch_supported_versions(patches_ref: str) -> tuple[str, ...]:
    metadata = fetch_bundle_metadata(patches_ref)
    app_version = metadata.get("app_version")
    if isinstance(app_version, str) and app_version:
        return (app_version,)

    print("piko-newx patches-bundle.json missing app_version, using fallback versions")
    return FALLBACK_SUPPORTED_VERSIONS


def resolve_pinned_version(
    supported_versions: tuple[str, ...],
    manual_version: str | None = None,
) -> str:
    if manual_version:
        return manual_version

    ordered = sorted(supported_versions, key=parse_version_tuple, reverse=True)
    if not ordered:
        raise ValueError("No supported X versions in piko-newx bundle metadata")
    return ordered[0]


def release_tag(version_name: str) -> str:
    return f"newx-{version_name}"
