import re
from typing import TypedDict


class BuildMetadata(TypedDict):
    x_version: str
    piko_version: str
    x_shim_version: str


_METADATA_LINE = re.compile(
    r"^- (x_version|piko_version|x_shim_version): (.+)$",
    re.MULTILINE,
)


def format_build_metadata(
    x_version: str,
    piko_version: str,
    x_shim_version: str | None,
) -> str:
    shim = x_shim_version or "none"
    return (
        "Build metadata:\n"
        f"- x_version: {x_version}\n"
        f"- piko_version: {piko_version}\n"
        f"- x_shim_version: {shim}"
    )


def parse_build_metadata(body: str) -> BuildMetadata | None:
    if "Build metadata:" not in body:
        return None

    values: dict[str, str] = {}
    for match in _METADATA_LINE.finditer(body):
        values[match.group(1)] = match.group(2).strip()

    required = ("x_version", "piko_version", "x_shim_version")
    if not all(key in values for key in required):
        return None

    return BuildMetadata(
        x_version=values["x_version"],
        piko_version=values["piko_version"],
        x_shim_version=values["x_shim_version"],
    )


def format_release_notes(
    piko_tag: str,
    piko_url: str,
    x_version: str,
    x_shim_version: str | None,
) -> str:
    metadata = format_build_metadata(x_version, piko_tag, x_shim_version)
    return f"""Changelogs:
[piko-{piko_tag}]({piko_url})

{metadata}
"""
