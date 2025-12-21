import requests
import re
import os
from utils import download


def download_release_asset(
    repo: str,
    regex: str,
    out_dir: str,
    filename=None,
    include_prereleases: bool = False,
    version=None,
):
    url = f"https://api.github.com/repos/{repo}/releases"

    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Failed to fetch github")

    releases = [
        r for r in response.json() if include_prereleases or not r["prerelease"]
    ]

    if not releases:
        raise Exception(f"No releases found for {repo}")

    if version is not None:
        releases = [r for r in releases if r["tag_name"] == version]

    if len(releases) == 0:
        raise Exception(f"No release found for version {version}")

    latest_release = releases[0]

    assets = latest_release["assets"]

    link = None
    for i in assets:
        if re.search(regex, i["name"]):
            link = i["browser_download_url"]
            if filename is None:
                filename = i["name"]
            break

    if link is None:
        raise Exception(f"No asset found for {repo} matching {regex}")

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    download(link, f"{out_dir.lstrip('/')}/{filename}")

    return latest_release


def download_binaries(config: dict) -> dict[str, dict]:
    binaries_info = {}
    for name, bin_config in config["binaries"].items():
        print(f"Downloading {name}")
        release_info = download_release_asset(
            repo=bin_config["repo"],
            regex=bin_config["regex"],
            out_dir="bins",
            filename=bin_config.get("filename"),
            include_prereleases=bin_config.get("include_prerelease", False),
            version=bin_config.get("version"),
        )
        binaries_info[name] = release_info
    return binaries_info
