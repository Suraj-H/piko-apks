import requests

MORPHE_PATCHES_REPO = "rushiranpise/morphe-patches"
MINDICATOR_PACKAGE = "com.mobond.mindicator"
REMOVE_ADS_PATCH = "Remove Ads"


def fetch_patches_list(patches_ref: str) -> dict:
    url = (
        f"https://raw.githubusercontent.com/{MORPHE_PATCHES_REPO}/"
        f"{patches_ref}/patches-list.json"
    )
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("patches-list.json did not contain a JSON object")
    return payload


def fetch_mindicator_versions(patches_ref: str) -> tuple[str, ...]:
    payload = fetch_patches_list(patches_ref)
    versions: list[str] = []

    for patch in payload.get("patches") or []:
        if patch.get("name") != REMOVE_ADS_PATCH:
            continue
        for package in patch.get("compatiblePackages") or []:
            if package.get("packageName") != MINDICATOR_PACKAGE:
                continue
            for target in package.get("targets") or []:
                version = target.get("version")
                if version:
                    versions.append(str(version))

    if not versions:
        return ()

    return tuple(
        sorted(set(versions), key=lambda value: tuple(int(part) for part in value.split(".")))
    )
