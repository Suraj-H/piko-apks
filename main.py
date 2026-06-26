from apkmirror import Version, Variant
from build_variants import build_apks
from download_bins import (
    download_apksig,
    download_morphe_cli,
    download_piko_patches,
    download_x_shim,
)
import github
from utils import panic, publish_release, report_to_telegram
from constants import REPO
from version_policy import (
    apkm_input_for,
    build_target,
    get_best_buildable_version,
)
import apkmirror
import os
import argparse


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


def process(latest_version: Version):
    target = build_target(latest_version)
    apkm_input = apkm_input_for(latest_version.version)
    os.makedirs("build-cache", exist_ok=True)

    if target.uses_x_shim:
        print(f"Using X-Shim for {latest_version.version}")

    variants = apkmirror.get_variants(latest_version)
    download_link = select_bundle_variant(variants)

    apkmirror.download_apk(download_link, apkm_input)
    if not os.path.exists(apkm_input):
        panic(f"Failed to download apk bundle: {apkm_input}")

    download_morphe_cli(include_prereleases=True)
    download_apksig()
    piko_release = download_piko_patches(include_prereleases=True)

    if target.uses_x_shim:
        download_x_shim()

    message = f"""
Changelogs:
[piko-{piko_release["tag_name"]}]({piko_release["html_url"]})
"""

    build_apks(latest_version, list(target.patch_files), apkm_input)

    if os.environ.get("SKIP_PUBLISH") == "1":
        print("SKIP_PUBLISH=1, skipping GitHub release and Telegram notification")
        return

    publish_release(
        latest_version.version,
        [
            f"x-piko-v{latest_version.version}.apk",
            f"x-piko-material-you-v{latest_version.version}.apk",
            f"twitter-piko-v{latest_version.version}.apk",
            f"twitter-piko-material-you-v{latest_version.version}.apk",
        ],
        message,
        latest_version.version,
    )

    report_to_telegram(tag=latest_version.version)


def main():
    url = "https://www.apkmirror.com/apk/x-corp/twitter/"
    repo_url = REPO

    versions = apkmirror.get_versions(url)
    latest_version = get_best_buildable_version(versions)
    if latest_version is None:
        panic("Could not find a supported release version on APKMirror")

    if latest_version.version.find("release") < 0:
        panic("Latest supported version is not a release version")

    last_build_version = github.get_last_build_version(repo_url)
    if last_build_version is None:
        panic("Failed to fetch the latest build version")
        return

    if last_build_version.tag_name != latest_version.version:
        print(f"New supported version found: {latest_version.version}")
    else:
        print("No new supported version found")
        return

    process(latest_version)


def manual(version: str):
    link = f"https://www.apkmirror.com/apk/x-corp/twitter/x-{version.replace('.', '-')}-release"
    latest_version = Version(link=link, version=version)
    process(latest_version)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Piko APK")
    parser.add_argument("--m", action="store", dest="mode", default=0)
    parser.add_argument("--v", action="store", dest="version", default=0)

    args = parser.parse_args()
    mode = args.mode

    if not mode:
        main()
    else:
        version = args.version
        if not version:
            raise Exception("Version is required.")
        manual(version)
