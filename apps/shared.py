import os

from apkmirror import Variant, Version

APKM_INPUT_DIR = "build-cache"
PIKO_PATCHES = "bins/patches.mpp"
X_SHIM_PATCHES = "bins/x-shim.mpp"
MORPHE_CLI = "bins/morphe-cli.jar"


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


def version_from_manual(app_id: str, version: str) -> Version:
    if app_id == "x":
        link = (
            f"https://www.apkmirror.com/apk/x-corp/twitter/"
            f"x-{version.replace('.', '-')}-release"
        )
        return Version(link=link, version=version)

    link = (
        f"https://www.apkmirror.com/apk/instagram/instagram-instagram/"
        f"instagram-{version.replace('.', '-')}-release"
    )
    return Version(link=link, version=version)
