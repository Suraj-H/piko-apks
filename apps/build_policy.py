from dataclasses import dataclass

from build_metadata import parse_build_metadata
from github import GithubRelease

APP_IDS = ("x", "instagram", "mindicator")


@dataclass(frozen=True)
class BuildDecision:
    app_id: str
    build: bool
    app_version: str
    reasons: tuple[str, ...]


def normalize_shim_version(x_shim_version: str | None) -> str:
    return x_shim_version or "none"


def evaluate_build(
    app_id: str,
    app_version: str,
    x_shim_version: str | None,
    last_release: GithubRelease | None,
    *,
    force: bool = False,
    patches_version: str | None = None,
) -> BuildDecision:
    if force:
        return BuildDecision(app_id, True, app_version, ("force",))

    if last_release is None:
        return BuildDecision(
            app_id,
            True,
            app_version,
            ("no previous release",),
        )

    metadata = parse_build_metadata(last_release.body)
    if metadata is None or metadata["app"] != app_id:
        return BuildDecision(
            app_id,
            True,
            app_version,
            ("release metadata missing",),
        )

    reasons: list[str] = []
    if metadata["app_version"] != app_version:
        reasons.append(f"app {metadata['app_version']} -> {app_version}")

    if app_id == "x":
        if "piko_version" not in metadata:
            return BuildDecision(app_id, True, app_version, ("release metadata missing",))
        shim = normalize_shim_version(x_shim_version)
        if metadata["x_shim_version"] != shim:
            reasons.append(f"x-shim {metadata['x_shim_version']} -> {shim}")

    if app_id == "mindicator":
        if "patches_version" not in metadata:
            return BuildDecision(app_id, True, app_version, ("release metadata missing",))
        if patches_version and metadata["patches_version"] != patches_version:
            reasons.append(
                f"patches {metadata['patches_version']} -> {patches_version}"
            )

    return BuildDecision(app_id, bool(reasons), app_version, tuple(reasons))


def log_decision(decision: BuildDecision) -> None:
    if decision.build:
        print(f"{decision.app_id} build required:", ", ".join(decision.reasons))
        return
    print(f"No changes for {decision.app_id}, skipping build")
