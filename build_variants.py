from apkmirror import Version
from utils import patch_apk
import os


def build_apks(latest_version: Version, config: dict) -> list[str]:
    # patch
    apk = "bins/big_file_merged.apk"
    patches_filename = config["binaries"]["patches"].get("filename", "patches.rvp")
    cli_filename = config["binaries"]["cli"].get("filename", "cli.jar")
    patches = f"bins/{patches_filename}"
    cli = f"bins/{cli_filename}"

    common_includes = config["patches"].get("common_includes", [])
    common_excludes = config["patches"].get("common_excludes", [])
    exclusive = config["patches"].get("exclusive", False)
    extra_args = config["patches"].get("extra_args", [])

    # Ensure result directory exists
    os.makedirs("bins/result", exist_ok=True)

    generated_files = []

    for variant in config["variants"]:
        name = variant["name"]
        includes = common_includes + variant.get("includes", [])
        excludes = common_excludes + variant.get("excludes", [])
        variant_extra_args = extra_args + variant.get("extra_args", [])
        out_filename = f"bins/result/{name}-v{latest_version.version}.apk"

        print(f"Building {name}...")
        patch_apk(
            cli,
            patches,
            apk,
            includes=includes,
            excludes=excludes,
            out=out_filename,
            exclusive=exclusive,
            extra_args=variant_extra_args,
        )
        generated_files.append(out_filename)

    return generated_files
