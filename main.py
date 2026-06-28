import argparse
import os

from apps.registry import APP_IDS, get_app
from apps.build_policy import evaluate_build, log_decision
from build_planner import create_build_plan
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
    decision = evaluate_build(
        app_id,
        latest_version.version,
        x_shim_version,
        last_release,
        force=is_force_build(),
    )
    if not decision.build:
        log_decision(decision)
        return

    log_decision(decision)
    app.process(latest_version, supported_versions, piko_release)


def run_apps(app_ids: tuple[str, ...], *, manual_version: str | None = None) -> None:
    for app_id in app_ids:
        build_app(app_id, manual_version=manual_version)


def parse_app_ids(raw: str, *, manual: bool, plan: bool) -> tuple[str, ...]:
    if raw == "all":
        if manual:
            panic("Manual builds require a single app. Use --app x or --app instagram.")
        if plan:
            return APP_IDS
        return APP_IDS

    if raw not in APP_IDS:
        panic(f"Unknown app {raw!r}. Expected one of: {', '.join([*APP_IDS, 'all'])}")

    if plan and raw != "all":
        return (raw,)

    return (raw,)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Piko APK builder")
    parser.add_argument(
        "--app",
        choices=[*APP_IDS, "all"],
        default="all",
        help="App to build (default: all)",
    )
    parser.add_argument(
        "--plan",
        action="store_true",
        help="Print build plan JSON and exit without building",
    )
    parser.add_argument("--m", action="store", dest="mode", default=0)
    parser.add_argument("--v", action="store", dest="version", default="")

    args = parser.parse_args()
    manual = bool(args.mode)

    if args.plan:
        if manual:
            panic("--plan cannot be combined with manual builds.")
        plan = create_build_plan(force=is_force_build())
        print(plan.to_json())
        raise SystemExit(0)

    app_ids = parse_app_ids(args.app, manual=manual, plan=False)

    if manual and not args.version:
        panic("Version is required for manual builds.")

    run_apps(app_ids, manual_version=args.version or None)
