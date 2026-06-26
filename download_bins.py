import os
import re

import requests

from utils import download

X_SHIM_VERSION = os.environ.get("X_SHIM_VERSION")
APKSIG_VERSION = os.environ.get("APKSIG_VERSION", "8.7.3")
X_SHIM_BUNDLE_URL = "https://gitlab.com/inotia00/x-shim/-/raw/main/patches-bundle.json"


def fetch_latest_x_shim_version() -> str:
    if X_SHIM_VERSION:
        return X_SHIM_VERSION

    response = requests.get(X_SHIM_BUNDLE_URL, timeout=30)
    response.raise_for_status()
    version = response.json().get("version")
    if not version:
        raise Exception("x-shim patches-bundle.json did not include a version")
    return str(version)


def get_latest_github_release(
    repo: str,
    include_prereleases: bool = False,
    version: str | None = None,
) -> dict:
    url = f"https://api.github.com/repos/{repo}/releases"
    response = requests.get(url, timeout=30)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch github releases for {repo}")

    releases = [
        release
        for release in response.json()
        if include_prereleases or not release["prerelease"]
    ]
    if not releases:
        raise Exception(f"No releases found for {repo}")

    if version is not None:
        releases = [release for release in releases if release["tag_name"] == version]
        if not releases:
            raise Exception(f"No release found for version {version} in {repo}")

    return releases[0]


def download_release_asset(
    repo: str,
    regex: str,
    out_dir: str,
    filename=None,
    include_prereleases: bool = False,
    version=None,
):
    latest_release = get_latest_github_release(
        repo,
        include_prereleases=include_prereleases,
        version=version,
    )

    link = None
    for asset in latest_release["assets"]:
        name = asset["name"]
        if re.search(regex, name):
            link = asset["browser_download_url"]
            if filename is None:
                filename = name
            break

    if link is None:
        raise Exception(
            f"Failed to find asset matching {regex} "
            f"on release {latest_release['tag_name']}"
        )

    download(link, f"{out_dir.lstrip('/')}/{filename}")
    return latest_release


def get_latest_piko_release(include_prereleases: bool = True) -> dict:
    return get_latest_github_release("crimera/piko", include_prereleases=include_prereleases)


def download_morphe_cli(include_prereleases: bool = False):
    print("Downloading morphe cli")
    download_release_asset(
        "MorpheApp/morphe-cli",
        r"^morphe-cli.*-all\.jar$",
        "bins",
        "morphe-cli.jar",
        include_prereleases=include_prereleases,
    )


def download_piko_patches(
    include_prereleases: bool = True,
    version: str | None = None,
):
    print("Downloading piko patches")
    return download_release_asset(
        "crimera/piko",
        r"^patches.*\.mpp$",
        "bins",
        "patches.mpp",
        include_prereleases=include_prereleases,
        version=version,
    )


def download_x_shim(version: str | None = None):
    resolved_version = version or fetch_latest_x_shim_version()
    print(f"Downloading x-shim v{resolved_version}")
    url = (
        f"https://gitlab.com/inotia00/x-shim/-/releases/v{resolved_version}/downloads/"
        f"patches-{resolved_version}.mpp"
    )
    download(url, "bins/x-shim.mpp")
    return resolved_version


def download_apksig(version: str = APKSIG_VERSION):
    print(f"Downloading apksig v{version}")
    url = (
        f"https://dl.google.com/android/maven2/com/android/tools/build/apksig/"
        f"{version}/apksig-{version}.jar"
    )
    download(url, "bins/apksig.jar")
