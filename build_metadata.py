import re
from typing import TypedDict


class BuildMetadata(TypedDict):
    app: str
    app_version: str
    piko_version: str
    x_shim_version: str


class MorpheBuildMetadata(TypedDict):
    app: str
    app_version: str
    patches_source: str
    patches_version: str


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


def format_morphe_build_metadata(
    app: str,
    app_version: str,
    patches_source: str,
    patches_version: str,
) -> str:
    return (
        "Build metadata:\n"
        f"- app: {app}\n"
        f"- app_version: {app_version}\n"
        f"- patches_source: {patches_source}\n"
        f"- patches_version: {patches_version}"
    )


def parse_build_metadata(body: str) -> BuildMetadata | MorpheBuildMetadata | None:
    if "Build metadata:" not in body:
        return None

    values: dict[str, str] = {}
    for match in _METADATA_LINE.finditer(body):
        values[match.group(1)] = match.group(2).strip()

    if "app_version" not in values and "x_version" in values:
        values["app"] = "x"
        values["app_version"] = values["x_version"]

    if "patches_source" in values:
        required = ("app", "app_version", "patches_source", "patches_version")
        if not all(key in values for key in required):
            return None
        return MorpheBuildMetadata(
            app=values["app"],
            app_version=values["app_version"],
            patches_source=values["patches_source"],
            patches_version=values["patches_version"],
        )

    required = ("app", "app_version", "piko_version", "x_shim_version")
    if not all(key in values for key in required):
        return None

    return BuildMetadata(
        app=values["app"],
        app_version=values["app_version"],
        piko_version=values["piko_version"],
        x_shim_version=values["x_shim_version"],
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


def format_morphe_release_notes(
    app: str,
    patches_source: str,
    patches_tag: str,
    patches_url: str,
    app_version: str,
) -> str:
    metadata = format_morphe_build_metadata(
        app,
        app_version,
        patches_source,
        patches_tag,
    )
    return f"""Changelogs:
[{patches_source} {patches_tag}]({patches_url})

m-Indicator {app_version}

{metadata}
"""
