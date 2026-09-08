import os

from apkmirror import Version
from apps.mindicator import policy, variants
from apps.mindicator.apkcafe import download_mindicator_apkm
from apps.mindicator.patches_list import MORPHE_PATCHES_REPO
from apps.shared import MORPHE_PATCHES, apkm_input_for, ensure_build_cache
from build_metadata import format_morphe_release_notes
from download_bins import download_apksig, download_morphe_cli, download_morphe_patches
from utils import panic, publish_release, report_to_telegram

APP_ID = "mindicator"


def resolve_version(
    supported_versions: tuple[str, ...],
    manual_version: str | None = None,
) -> Version:
    if manual_version:
        from apps.shared import version_from_manual

        return version_from_manual(APP_ID, manual_version)

    ordered = sorted(supported_versions, key=policy.parse_version_tuple, reverse=True)
    if not ordered:
        panic("No morphe-patches-supported m-Indicator versions")

    version_name = ordered[0]
    return Version(version=version_name, link="")


def process(
    latest_version: Version,
    supported_versions: tuple[str, ...],
    patches_release: dict,
) -> None:
    if latest_version.version not in supported_versions:
        allowed = ", ".join(supported_versions)
        panic(
            f"Unsupported m-Indicator version {latest_version.version}. "
            f"Supported builds: {allowed}"
        )

    apkm_input = apkm_input_for(APP_ID, latest_version.version)
    ensure_build_cache()

    download_mindicator_apkm(latest_version.version, apkm_input)
    if not os.path.exists(apkm_input):
        panic(f"Failed to download m-Indicator apk bundle: {apkm_input}")

    download_morphe_cli(include_prereleases=True)
    download_apksig()
    download_morphe_patches(
        include_prereleases=True,
        version=patches_release["tag_name"],
    )

    message = format_morphe_release_notes(
        app=APP_ID,
        patches_source=MORPHE_PATCHES_REPO,
        patches_tag=patches_release["tag_name"],
        patches_url=patches_release["html_url"],
        app_version=latest_version.version,
    )

    output_files = variants.build_apks(
        latest_version,
        [MORPHE_PATCHES],
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
        f"m-Indicator {latest_version.version}",
        mark_latest=False,
    )
    report_to_telegram(tag=tag)
