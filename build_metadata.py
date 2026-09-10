import re
from dataclasses import dataclass
from typing import TypedDict


class PikoBuildMetadata(TypedDict):
    app: str
    app_version: str
    piko_version: str
    x_shim_version: str


class MorpheBuildMetadata(TypedDict):
    app: str
    app_version: str
    patches_source: str
    patches_version: str


BuildMetadata = PikoBuildMetadata | MorpheBuildMetadata


@dataclass(frozen=True)
class ParsedBuildMetadata:
    app: str
    app_version: str
    piko_version: str | None = None
    x_shim_version: str | None = None
    patches_source: str | None = None
    patches_version: str | None = None


_METADATA_LINE = re.compile(
    r"^- (app|app_version|piko_version|x_shim_version|x_version|patches_source|patches_version): (.+)$",
    re.MULTILINE,
)


def format_build_metadata(
    app: str,
    app_version: str,
    piko_version: str,
    x_shim_version: str | None,
) -> str:
    shim = x_shim_version or "none"
    return (
        "Build metadata:\n"
        f"- app: {app}\n"
        f"- app_version: {app_version}\n"
        f"- piko_version: {piko_version}\n"
        f"- x_shim_version: {shim}"
    )


def format_mindicator_metadata(
    app_version: str,
    patches_source: str,
    patches_version: str,
) -> str:
    return (
        "Build metadata:\n"
        "- app: mindicator\n"
        f"- app_version: {app_version}\n"
        f"- patches_source: {patches_source}\n"
        f"- patches_version: {patches_version}"
    )


def parse_build_metadata(body: str) -> ParsedBuildMetadata | None:
    if "Build metadata:" not in body:
        return None

    values: dict[str, str] = {}
    for match in _METADATA_LINE.finditer(body):
        values[match.group(1)] = match.group(2).strip()

    if "app_version" not in values and "x_version" in values:
        values["app"] = "x"
        values["app_version"] = values["x_version"]

    app = values.get("app")
    app_version = values.get("app_version")
    if app is None or app_version is None:
        return None

    if app == "mindicator":
        patches_source = values.get("patches_source")
        patches_version = values.get("patches_version")
        if patches_source is None or patches_version is None:
            return None
        return ParsedBuildMetadata(
            app=app,
            app_version=app_version,
            patches_source=patches_source,
            patches_version=patches_version,
        )

    piko_version = values.get("piko_version")
    x_shim_version = values.get("x_shim_version")
    if piko_version is None or x_shim_version is None:
        return None

    return ParsedBuildMetadata(
        app=app,
        app_version=app_version,
        piko_version=piko_version,
        x_shim_version=x_shim_version,
    )


def format_release_notes(
    app: str,
    piko_tag: str,
    piko_url: str,
    app_version: str,
    x_shim_version: str | None,
) -> str:
    metadata = format_build_metadata(app, app_version, piko_tag, x_shim_version)
    app_label = "X/Twitter" if app == "x" else "Instagram"
    return f"""Changelogs:
[piko-{piko_tag}]({piko_url})

{app_label} {app_version}

{metadata}
"""


def format_mindicator_release_notes(
    app_version: str,
    patches_tag: str,
    patches_url: str,
    patches_source: str,
) -> str:
    patches_version = patches_tag.removeprefix("v")
    metadata = format_mindicator_metadata(app_version, patches_source, patches_version)
    return f"""Changelogs:
[morphe-patches-{patches_tag}]({patches_url})

m-Indicator {app_version}

{metadata}
"""
