from dataclasses import dataclass

from apkmirror import Version
from apps.build_policy import APP_IDS
from download_bins import get_latest_morphe_patches_release, get_latest_piko_release


@dataclass(frozen=True)
class AppSpec:
    app_id: str
    display_name: str
    policy_module: object
    pipeline_module: object
    patches_kind: str

    def fetch_supported_versions(self, patches_ref: str) -> tuple[str, ...]:
        return self.policy_module.fetch_supported_versions(patches_ref)

    def release_tag(self, version_name: str) -> str:
        return self.policy_module.release_tag(version_name)

    def resolve_version(
        self,
        supported_versions: tuple[str, ...],
        manual_version: str | None = None,
    ) -> Version:
        return self.pipeline_module.resolve_version(supported_versions, manual_version)

    def get_patches_release(self) -> dict:
        if self.patches_kind == "morphe-patches":
            return get_latest_morphe_patches_release(include_prereleases=True)
        return get_latest_piko_release(include_prereleases=True)

    def process(self, version: Version, supported: tuple[str, ...], patches_release: dict) -> None:
        if self.app_id == "x":
            from apps.x.pipeline import resolve_x_shim_version

            x_shim_version = resolve_x_shim_version(version.version)
            self.pipeline_module.process(
                version,
                supported,
                patches_release,
                x_shim_version,
            )
            return

        self.pipeline_module.process(version, supported, patches_release)

    def resolve_extra_version(self, version_name: str) -> str | None:
        if self.app_id != "x":
            return None
        from apps.x.pipeline import resolve_x_shim_version

        return resolve_x_shim_version(version_name)

    def resolve_patches_version(self, patches_release: dict) -> str | None:
        if self.patches_kind != "morphe-patches":
            return None
        return patches_release["tag_name"]


def get_app(app_id: str) -> AppSpec:
    if app_id == "x":
        from apps import x

        return AppSpec("x", "X/Twitter", x.policy, x.pipeline, "piko")

    if app_id == "instagram":
        from apps import instagram

        return AppSpec("instagram", "Instagram", instagram.policy, instagram.pipeline, "piko")

    if app_id == "mindicator":
        from apps import mindicator

        return AppSpec(
            "mindicator",
            "m-Indicator",
            mindicator.policy,
            mindicator.pipeline,
            "morphe-patches",
        )

    raise ValueError(f"Unknown app: {app_id}. Expected one of: {', '.join(APP_IDS)}")
