import argparse
import os

from apps.registry import APP_IDS, get_app, should_build
from constants import REPO
from download_bins import get_latest_piko_release
import github
from utils import panic


def is_force_build() -> bool:
    return os.environ.get("FORCE_BUILD", "").strip().lower() in ("1", "true", "yes")


def build_app(app_id: str, *, manual_version: str | None = None) -> None:
    app = get_app(app_id)
    piko_release = get_latest_piko_release(include_prereleases=True)
    piko_ref = piko_release["tag_name"]
    print(f"[{app_id}] Latest piko release: {piko_ref}")

    supported_versions = app.fetch_supported_versions(piko_ref)
    print(f"[{app_id}] Piko-supported versions: {', '.join(supported_versions)}")

    latest_version = app.resolve_version(supported_versions, manual_version)
    print(f"[{app_id}] Selected version: {latest_version.version}")

    x_shim_version = app.resolve_extra_version(latest_version.version)
    if x_shim_version:
        print(f"[{app_id}] Latest x-shim release: {x_shim_version}")

    last_release = github.get_last_release_for_app(REPO, app_id)
    if not should_build(
        app_id,
        latest_version.version,
        piko_ref,
        x_shim_version,
        last_release,
        force=is_force_build(),
    ):
        return

    app.process(latest_version, supported_versions, piko_release)


def run_apps(app_ids: tuple[str, ...], *, manual_version: str | None = None) -> None:
    for app_id in app_ids:
        build_app(app_id, manual_version=manual_version)


def parse_app_ids(raw: str, *, manual: bool) -> tuple[str, ...]:
    if raw == "all":
        if manual:
            panic("Manual builds require a single app. Use --app x or --app instagram.")
        return APP_IDS

    if raw not in APP_IDS:
        panic(f"Unknown app {raw!r}. Expected one of: {', '.join([*APP_IDS, 'all'])}")

    return (raw,)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Piko APK builder")
    parser.add_argument(
        "--app",
        choices=[*APP_IDS, "all"],
        default="all",
        help="App to build (default: all)",
    )
    parser.add_argument("--m", action="store", dest="mode", default=0)
    parser.add_argument("--v", action="store", dest="version", default="")

    args = parser.parse_args()
    manual = bool(args.mode)
    app_ids = parse_app_ids(args.app, manual=manual)

    if manual and not args.version:
        panic("Version is required for manual builds.")

    run_apps(app_ids, manual_version=args.version or None)
