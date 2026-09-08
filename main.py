import argparse
import contextlib
import os
import sys

from apps.registry import APP_IDS, get_app
from apps.build_policy import evaluate_build, log_decision
from build_planner import create_build_plan
from constants import REPO
import github
from utils import panic


def is_force_build() -> bool:
    return os.environ.get("FORCE_BUILD", "").strip().lower() in ("1", "true", "yes")


def build_app(app_id: str, *, manual_version: str | None = None) -> None:
    app = get_app(app_id)
    patches_release = app.get_patches_release()
    patches_ref = patches_release["tag_name"]
    print(f"[{app_id}] Latest patches release: {patches_ref}")

    supported_versions = app.fetch_supported_versions(patches_ref)
    print(f"[{app_id}] Supported versions: {', '.join(supported_versions)}")

    latest_version = app.resolve_version(supported_versions, manual_version)
    print(f"[{app_id}] Selected version: {latest_version.version}")

    x_shim_version = app.resolve_extra_version(latest_version.version)
    if x_shim_version:
        print(f"[{app_id}] Latest x-shim release: {x_shim_version}")

    patches_version = app.resolve_patches_version(patches_release)
    if patches_version:
        print(f"[{app_id}] Latest morphe-patches release: {patches_version}")

    last_release = github.get_last_release_for_app(REPO, app_id)
    decision = evaluate_build(
        app_id,
        latest_version.version,
        x_shim_version,
        last_release,
        force=is_force_build(),
        patches_version=patches_version,
    )
    if not decision.build:
        log_decision(decision)
        return

    log_decision(decision)
    app.process(latest_version, supported_versions, patches_release)


def run_apps(app_ids: tuple[str, ...], *, manual_version: str | None = None) -> None:
    for app_id in app_ids:
        build_app(app_id, manual_version=manual_version)


def parse_app_ids(raw: str, *, manual: bool, plan: bool) -> tuple[str, ...]:
    if raw == "all":
        if manual:
            panic("Manual builds require a single app. Use --app x, instagram, or mindicator.")
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
        # create_build_plan() logs progress via print() as it resolves each
        # app's version. Route that to stderr so stdout carries only the
        # final JSON — the workflow captures stdout via `$(...)` and feeds
        # it straight to `jq`, which fails to parse if diagnostic lines are
        # mixed in (silently producing empty outputs, not a visible error).
        with contextlib.redirect_stdout(sys.stderr):
            plan = create_build_plan(force=is_force_build())
        print(plan.to_json())
        raise SystemExit(0)

    app_ids = parse_app_ids(args.app, manual=manual, plan=False)

    if manual and not args.version:
        panic("Version is required for manual builds.")

    run_apps(app_ids, manual_version=args.version or None)
