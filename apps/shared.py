import os
import re

from apkmirror import Variant, Version

APKM_INPUT_DIR = "build-cache"
PIKO_PATCHES = "bins/patches.mpp"
NEWX_PATCHES = "bins/newx-patches.mpp"
MORPHE_PATCHES = "bins/morphe-patches.mpp"
X_SHIM_PATCHES = "bins/x-shim.mpp"
MORPHE_CLI = "bins/morphe-cli.jar"


def extract_piko_target_versions(source: str, start_marker: str) -> tuple[str, ...]:
    """Extract AppTarget version strings from a piko Constants.kt Compatibility(...) block.

    Finds start_marker's Compatibility(...) call and matches balanced
    parentheses to locate its end, rather than relying on a hardcoded
    trailing marker (e.g. the next declaration's name) that upstream piko
    is free to rename, reorder, or remove.
    """
    start = source.find(start_marker)
    if start < 0:
        return ()

    open_paren = source.find("(", start)
    if open_paren < 0:
        return ()

    depth = 0
    end = -1
    for i in range(open_paren, len(source)):
        char = source[i]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    if end < 0:
        return ()

    block = source[start:end]
    return tuple(re.findall(r'version\s*=\s*"([^"]+)"', block))


def apkm_input_for(app_id: str, version_name: str) -> str:
    safe_name = version_name.replace(".", "-")
    return f"{APKM_INPUT_DIR}/{app_id}-{safe_name}.apkm"


def select_bundle_variant(variants: list[Variant]) -> Variant:
    for variant in variants:
        if variant.is_bundle and variant.architecture == "universal":
            return variant

    bundle_variants = [variant for variant in variants if variant.is_bundle]
    if not bundle_variants:
        raise Exception("Bundle not Found")

    fallback = next(
        (variant for variant in bundle_variants if variant.architecture == "arm64-v8a"),
        None,
    )
    download_link = fallback or bundle_variants[0]
    print(f"Universal bundle not found, falling back to {download_link.architecture}")
    return download_link


def select_arm64_bundle_variant(variants: list[Variant]) -> Variant:
    bundle_variants = [variant for variant in variants if variant.is_bundle]
    if not bundle_variants:
        raise Exception("Bundle not Found")

    arm64 = next(
        (variant for variant in bundle_variants if variant.architecture == "arm64-v8a"),
        None,
    )
    if arm64 is not None:
        return arm64

    universal = next(
        (variant for variant in bundle_variants if variant.architecture == "universal"),
        None,
    )
    selected = universal or bundle_variants[0]
    print(f"arm64-v8a bundle not found, falling back to {selected.architecture}")
    return selected


def ensure_build_cache() -> None:
    os.makedirs(APKM_INPUT_DIR, exist_ok=True)


def instagram_version_page(version: str) -> str:
    slug = version.replace(".", "-")
    return (
        "https://www.apkmirror.com/apk/instagram/instagram-instagram/"
        f"instagram-{slug}-release/"
    )


def x_version_page(version: str) -> str:
    slug = version.replace(".", "-")
    return f"https://www.apkmirror.com/apk/x-corp/twitter/x-{slug}-release"


def version_from_manual(app_id: str, version: str) -> Version:
    if app_id in ("x", "newx"):
        return Version(link=x_version_page(version), version=version)

    if app_id == "mindicator":
        return Version(version=version, link="")

    link = instagram_version_page(version)
    return Version(link=link, version=version)
