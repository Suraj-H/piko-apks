from apkmirror import Version, Variant
from build_variants import build_apks
from download_bins import download_binaries
import github
from utils import panic, merge_apk, publish_release, report_to_telegram
import apkmirror
import os
import argparse
import tomllib


def get_latest_release(versions: list[Version]) -> Version | None:
    for i in versions:
        if i.version.find("release") >= 0:
            return i


def process(latest_version: Version, config: dict):
    binaries_info = download_binaries(config)

    # get bundle and universal variant
    variants: list[Variant] = apkmirror.get_variants(latest_version)

    download_link: Variant | None = None
    for variant in variants:
        if variant.is_bundle and variant.arcithecture == "universal":
            download_link = variant
            break

    if download_link is None:
        raise Exception("Bundle not Found")

    apkmirror.download_apk(download_link)
    if not os.path.exists("big_file.apkm"):
        panic("Failed to download apk")

    if not os.path.exists("big_file_merged.apk"):
        merge_apk("big_file.apkm")
    else:
        print("apkm is already merged")

    message = "Changelogs:\n"
    for name, info in binaries_info.items():
        message += f"[{name}-{info['tag_name']}]({info['html_url']})\n"

    generated_apks = build_apks(latest_version, config)

    if config["project"].get("publish", False):
        print("Publishing release...")
        publish_release(
            latest_version.version, generated_apks, message, latest_version.version
        )
    else:
        print("Skipping publish (disabled in config)")

    if config["project"].get("telegram_report", False):
        print("Reporting to telegram...")
        report_to_telegram(config["project"]["repo"])
    else:
        print("Skipping telegram report (disabled in config)")


def main():
    with open("config.toml", "rb") as f:
        config = tomllib.load(f)

    # get latest version
    url: str = config["project"]["apkmirror_url"]
    repo_url: str = config["project"]["repo"]

    versions = apkmirror.get_versions(url)

    latest_version = get_latest_release(versions)
    if latest_version is None:
        raise Exception("Could not find the latest version")

    # only continue if it's a release
    if latest_version.version.find("release") < 0:
        panic("Latest version is not a release version")

    last_build_version: github.GithubRelease | None = github.get_last_build_version(
        repo_url
    )

    if last_build_version is None:
        # If no release exists yet, we should probably still continue
        print("No previous release found, proceeding with first build")
    elif last_build_version.tag_name == latest_version.version:
        print("No new version found")
        return
    else:
        print(f"New version found: {latest_version.version}")

    process(latest_version, config)


def manual(version: str):
    with open("config.toml", "rb") as f:
        config = tomllib.load(f)

    link = f"https://www.apkmirror.com/apk/x-corp/twitter/x-formerly-twitter-{version.replace('.', '-')}-release"
    latest_version = Version(link=link, version=version)
    process(latest_version, config)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Piko APK")
    # 0 = auto; 1 = manual;
    parser.add_argument("--m", action="store", dest="mode", default=0, type=int)
    parser.add_argument("--v", action="store", dest="version", default="")

    args = parser.parse_args()
    mode = args.mode

    if not mode:  # auto
        main()
    else:  # manual
        version = args.version
        if not version:
            raise Exception("Version is required.")
        manual(version)
