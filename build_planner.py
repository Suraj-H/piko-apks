import json
from dataclasses import dataclass

from apps.build_policy import APP_IDS, BuildDecision, evaluate_build, log_decision
from apps.registry import get_app
from constants import REPO
from download_bins import get_latest_piko_release
import github


@dataclass(frozen=True)
class BuildPlan:
    apps: dict[str, BuildDecision]

    @property
    def any_build(self) -> bool:
        return any(decision.build for decision in self.apps.values())

    def to_json(self) -> str:
        payload = {
            "any_build": self.any_build,
            "apps": {
                app_id: {
                    "build": decision.build,
                    "app_version": decision.app_version,
                    "reasons": list(decision.reasons),
                }
                for app_id, decision in self.apps.items()
            },
        }
        return json.dumps(payload, indent=2)


def create_build_plan(*, force: bool = False) -> BuildPlan:
    piko_release = get_latest_piko_release(include_prereleases=True)
    piko_ref = piko_release["tag_name"]
    print(f"Latest piko release: {piko_ref}")

    decisions: dict[str, BuildDecision] = {}
    for app_id in APP_IDS:
        app = get_app(app_id)
        supported_versions = app.fetch_supported_versions(piko_ref)
        print(f"[{app_id}] Piko-supported versions: {', '.join(supported_versions)}")

        latest_version = app.resolve_version(supported_versions)
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
            force=force,
        )
        log_decision(decision)
        decisions[app_id] = decision

    return BuildPlan(apps=decisions)
