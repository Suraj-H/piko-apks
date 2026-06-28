from dataclasses import dataclass

from apkmirror import Version
from apps.build_policy import APP_IDS


@dataclass(frozen=True)
class AppSpec:
    app_id: str
    display_name: str
    policy_module: object
    pipeline_module: object

    def fetch_supported_versions(self, piko_ref: str) -> tuple[str, ...]:
        return self.policy_module.fetch_supported_versions(piko_ref)

    def release_tag(self, version_name: str) -> str:
        return self.policy_module.release_tag(version_name)

    def resolve_version(
        self,
        supported_versions: tuple[str, ...],
        manual_version: str | None = None,
    ) -> Version:
        return self.pipeline_module.resolve_version(supported_versions, manual_version)

    def process(self, version: Version, supported: tuple[str, ...], piko_release: dict) -> None:
        if self.app_id == "x":
            from apps.x.pipeline import resolve_x_shim_version

            x_shim_version = resolve_x_shim_version(version.version)
            self.pipeline_module.process(
                version,
                supported,
                piko_release,
                x_shim_version,
            )
            return

        self.pipeline_module.process(version, supported, piko_release)

    def resolve_extra_version(self, version_name: str) -> str | None:
        if self.app_id != "x":
            return None
        from apps.x.pipeline import resolve_x_shim_version

        return resolve_x_shim_version(version_name)


def get_app(app_id: str) -> AppSpec:
    if app_id == "x":
        from apps import x

        return AppSpec("x", "X/Twitter", x.policy, x.pipeline)

    if app_id == "instagram":
        from apps import instagram

        return AppSpec("instagram", "Instagram", instagram.policy, instagram.pipeline)

    raise ValueError(f"Unknown app: {app_id}. Expected one of: {', '.join(APP_IDS)}")
