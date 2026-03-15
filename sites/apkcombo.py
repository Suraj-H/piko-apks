from typing import cast
from bs4 import BeautifulSoup, Tag
from sites.apkmirror import FailedToFetch, FailedToFindElement, Version
import requests
from constants import HEADERS
import utils

HOST = "apkcombo.com"
CHECKIN_URL = "https://apkcombo.com/checkin"
LANG = "en"


def _create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    session.verify = False
    return session


def _get_package_name(version: Version) -> str:
    parts = version.link.rstrip("/").split("/")
    if len(parts) < 5:
        raise FailedToFindElement("Package name")

    return parts[4]


def _select_variant_link(page: BeautifulSoup) -> str:
    variants = page.find_all("a", attrs={"class": "variant"})
    if len(variants) == 0:
        raise FailedToFindElement("Download link")

    for variant in variants:
        variant = cast(Tag, variant)
        name = variant.find("span", attrs={"class": "vername"})
        if name is None:
            continue

        variant_name = name.text.lower()
        if "alpha" in variant_name or "beta" in variant_name:
            continue

        link = variant.get("href")
        if link is not None:
            return cast(str, link)

    link = cast(Tag, variants[0]).get("href")
    if link is None:
        raise FailedToFindElement("Download link")

    return cast(str, link)


def get_download_url(version: Version) -> str:
    session = _create_session()

    response = session.get(version.link)
    if response.status_code != 200:
        raise FailedToFetch(f"{version.link}: {response.status_code}")

    page = BeautifulSoup(response.text, "html.parser")
    link = _select_variant_link(page)

    checkin_response = session.post(CHECKIN_URL)
    if checkin_response.status_code != 200:
        raise FailedToFetch(f"{CHECKIN_URL}: {checkin_response.status_code}")

    package_name = _get_package_name(version)

    return (
        f"https://{HOST}{link}"
        f"&{checkin_response.text}"
        f"&package_name={package_name}"
        f"&lang={LANG}"
    )


def download_apk(version: Version):
    """
    Download apk given a version
    """

    direct_link = get_download_url(version)
    utils.download(direct_link, "big_file.apkm", headers=HEADERS, verify=False)


def get_versions(url: str) -> list[Version]:
    """
    Get the versions of the app from the given apkcombo url
    """

    response = requests.get(url, headers=HEADERS, verify=False)
    if response.status_code != 200:
        raise FailedToFetch(f"{url}: {response.status_code}")

    page = BeautifulSoup(response.text, "html.parser")
    versions = page.find("ul", attrs={"class": "list-versions content"})

    out: list[Version] = []
    if versions is None:
        return out

    versions = cast(Tag, versions)
    for version in versions.findChildren("a", recursive=True):
        name = version.findChild("span", attrs={"class": "vername"}, recursive=True)
        if name is None:
            continue

        href = version.get("href")
        if href is None:
            continue

        value = name.text.split(" ")[-1]
        out.append(Version(value, f"https://{HOST}{href}"))

    return out
