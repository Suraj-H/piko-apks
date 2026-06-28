import os

import apkmirror
from apkmirror import Version
from apps.shared import (
    apkm_input_for,
    ensure_build_cache,
    select_bundle_variant,
)
from apps.x import policy, variants
from build_metadata import format_release_notes
from download_bins import (
    download_apksig,
    download_morphe_cli,
    download_piko_patches,
    download_x_shim,
    fetch_latest_x_shim_version,
)
from utils import panic, publish_release, report_to_telegram

APP_ID = "x"
APKMIRROR_URL = "https://www.apkmirror.com/apk/x-corp/twitter/"


def resolve_version(
    supported_versions: tuple[str, ...],
    manual_version: str | None = None,
) -> Version:
    if manual_version:
        from apps.shared import version_from_manual

        return version_from_manual(APP_ID, manual_version)

    versions = apkmirror.get_versions(APKMIRROR_URL)
    latest_version = policy.get_best_buildable_version(versions, supported_versions)
    if latest_version is None:
        panic("Could not find a supported X release version on APKMirror")

    if latest_version.version.find("release") < 0:
        panic("Latest supported X version is not a release version")

    return latest_version


def process(
    latest_version: Version,
    supported_versions: tuple[str, ...],
    piko_release: dict,
    x_shim_version: str | None,
) -> None:
    target = policy.build_target(latest_version, supported_versions)
    apkm_input = apkm_input_for(APP_ID, latest_version.version)
    ensure_build_cache()

    if target.uses_x_shim:
        print(f"Using X-Shim {x_shim_version} for {latest_version.version}")

    variants_list = apkmirror.get_variants(latest_version)
    download_link = select_bundle_variant(variants_list)

    apkmirror.download_apk(download_link, apkm_input)
    if not os.path.exists(apkm_input):
        panic(f"Failed to download X apk bundle: {apkm_input}")

    download_morphe_cli(include_prereleases=True)
    download_apksig()
    download_piko_patches(
        include_prereleases=True,
        version=piko_release["tag_name"],
    )

    if target.uses_x_shim:
        if x_shim_version is None:
            x_shim_version = download_x_shim()
        else:
            download_x_shim(x_shim_version)

    message = format_release_notes(
        app=APP_ID,
        piko_tag=piko_release["tag_name"],
        piko_url=piko_release["html_url"],
        app_version=latest_version.version,
        x_shim_version=x_shim_version,
    )

    output_files = variants.build_apks(
        latest_version,
        list(target.patch_files),
        apkm_input,
    )

    if os.environ.get("SKIP_PUBLISH") == "1":
        print("SKIP_PUBLISH=1, skipping GitHub release and Telegram notification")
        return

    tag = policy.release_tag(latest_version.version)
    publish_release(
        tag,
        output_files,
        message,
        latest_version.version,
        mark_latest=True,
    )
    report_to_telegram(tag=tag)


def resolve_x_shim_version(version_name: str) -> str | None:
    if not policy.needs_x_shim(version_name):
        return None
    return fetch_latest_x_shim_version()
