import os

from apkmirror import Version
from apps.instagram import policy, variants
from apps.instagram.uptodown import download_instagram_apkm
from apps.shared import (
    PIKO_PATCHES,
    apkm_input_for,
    ensure_build_cache,
    instagram_version_page,
)
from build_metadata import format_release_notes
from download_bins import (
    download_apksig,
    download_morphe_cli,
    download_piko_patches,
)
from utils import panic, publish_release, report_to_telegram

APP_ID = "instagram"


def resolve_version(
    supported_versions: tuple[str, ...],
    manual_version: str | None = None,
) -> Version:
    if manual_version:
        from apps.shared import version_from_manual

        return version_from_manual(APP_ID, manual_version)

    ordered = sorted(supported_versions, key=policy.parse_version_tuple, reverse=True)
    if not ordered:
        panic("No piko-supported Instagram versions")

    version_name = ordered[0]
    return Version(version=version_name, link=instagram_version_page(version_name))


def process(
    latest_version: Version,
    supported_versions: tuple[str, ...],
    piko_release: dict,
) -> None:
    if latest_version.version not in supported_versions:
        allowed = ", ".join(supported_versions)
        panic(
            f"Unsupported Instagram version {latest_version.version}. "
            f"Supported builds: {allowed}"
        )

    apkm_input = apkm_input_for(APP_ID, latest_version.version)
    ensure_build_cache()

    download_instagram_apkm(latest_version.version, apkm_input)
    if not os.path.exists(apkm_input):
        panic(f"Failed to download Instagram apk bundle: {apkm_input}")

    download_morphe_cli(include_prereleases=True)
    download_apksig()
    download_piko_patches(
        include_prereleases=True,
        version=piko_release["tag_name"],
    )

    message = format_release_notes(
        app=APP_ID,
        piko_tag=piko_release["tag_name"],
        piko_url=piko_release["html_url"],
        app_version=latest_version.version,
        x_shim_version=None,
    )

    output_files = variants.build_apks(
        latest_version,
        [PIKO_PATCHES],
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
        f"Instagram {latest_version.version}",
        mark_latest=False,
    )
    report_to_telegram(tag=tag)
