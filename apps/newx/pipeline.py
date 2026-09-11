import os

from apkmirror import Version, version_page_exists
from apps.mindicator.bundle import require_arm64_bundle
from apps.newx import policy, variants
from apps.shared import (
    NEWX_PATCHES,
    apkm_input_for,
    ensure_build_cache,
    select_arm64_bundle_variant,
    x_version_page,
)
from build_metadata import format_newx_release_notes
from download_bins import download_apksig, download_morphe_cli, download_piko_newx_patches
from utils import panic, publish_release, report_to_telegram

import apkmirror

APP_ID = "newx"
APKMIRROR_URL = "https://www.apkmirror.com/apk/x-corp/twitter/"


def resolve_version(
    supported_versions: tuple[str, ...],
    manual_version: str | None = None,
) -> Version:
    if manual_version:
        from apps.shared import version_from_manual

        return version_from_manual(APP_ID, manual_version)

    version_name = policy.resolve_pinned_version(supported_versions)
    link = x_version_page(version_name)
    if version_page_exists(link):
        return Version(version=version_name, link=link)

    versions = apkmirror.get_versions(APKMIRROR_URL)
    by_name = {version.version: version for version in versions}
    if version_name in by_name:
        return by_name[version_name]

    panic(
        f"Could not find X {version_name} on APKMirror "
        f"(checked {link} and recent listing)"
    )


def process(
    latest_version: Version,
    supported_versions: tuple[str, ...],
    patches_release: dict,
    *,
    manual_version: str | None = None,
) -> None:
    if manual_version is None and latest_version.version not in supported_versions:
        allowed = ", ".join(supported_versions)
        panic(
            f"Unsupported X version {latest_version.version} for piko-newx. "
            f"Supported builds: {allowed}"
        )

    bundle_input = apkm_input_for(APP_ID, latest_version.version)
    ensure_build_cache()

    variants_list = apkmirror.get_variants(latest_version)
    download_link = select_arm64_bundle_variant(variants_list)
    apkmirror.download_apk(download_link, bundle_input)
    if not os.path.exists(bundle_input):
        panic(f"Failed to download X apk bundle: {bundle_input}")

    require_arm64_bundle(bundle_input)

    download_morphe_cli(include_prereleases=True)
    download_apksig()
    download_piko_newx_patches(version=patches_release["tag_name"])

    message = format_newx_release_notes(
        app_version=latest_version.version,
        patches_tag=patches_release["tag_name"],
        patches_url=patches_release["html_url"],
        patches_source=policy.PATCHES_SOURCE,
    )

    output_files = variants.build_apks(
        latest_version,
        [NEWX_PATCHES],
        bundle_input,
    )

    if os.environ.get("SKIP_PUBLISH") == "1":
        print("SKIP_PUBLISH=1, skipping GitHub release and Telegram notification")
        return

    tag = policy.release_tag(latest_version.version)
    publish_release(
        tag,
        output_files,
        message,
        f"NewX {latest_version.version}",
        mark_latest=False,
    )
    report_to_telegram(tag=tag)
