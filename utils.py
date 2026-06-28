import os
import subprocess
import sys

import requests
from constants import REPO
from github import get_last_build_version, get_release_by_tag

_scraper = None


def _env(name: str, default: str) -> str:
    value = os.environ.get(name)
    return value if value else default


def get_signing_config() -> dict[str, str]:
    return {
        "keystore": _env("APK_KEYSTORE_PATH", "ks.keystore"),
        "keystore_password": _env("APK_KEYSTORE_PASSWORD", "123456789"),
        "key_alias": _env("APK_KEY_ALIAS", "jhc"),
        "key_password": _env("APK_KEY_PASSWORD", _env("APK_KEYSTORE_PASSWORD", "123456789")),
        "signer": _env("APK_SIGNER", _env("APK_KEY_ALIAS", "jhc")),
    }

def get_scraper():
    global _scraper
    if _scraper is None:
        import cloudscraper
        _scraper = cloudscraper.create_scraper()
        _scraper.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        })
    return _scraper


def panic(message: str):
    print(message, file=sys.stderr)
    exit(1)


def send_message(message: str, token: str, chat_id: str, thread_id: str | None = None):
    endpoint = f"https://api.telegram.org/bot{token}/sendMessage"

    data = {
        "parse_mode": "Markdown",
        "disable_web_page_preview": "true",
        "text": message,
        "chat_id": chat_id,
    }
    if thread_id:
        data["message_thread_id"] = thread_id

    response = requests.post(endpoint, data=data)
    response.raise_for_status()


def telegram_is_configured() -> bool:
    return bool(os.environ.get("TG_TOKEN") and os.environ.get("TG_CHAT_ID"))


def report_to_telegram(tag: str | None = None):
    if not telegram_is_configured():
        print("Telegram secrets not configured, skipping notification")
        return

    tg_token = os.environ["TG_TOKEN"]
    tg_chat_id = os.environ["TG_CHAT_ID"]
    tg_thread_id = os.environ.get("TG_THREAD_ID")

    release = get_release_by_tag(REPO, tag) if tag else get_last_build_version(REPO)

    if release is None and tag:
        raise RuntimeError(f"Could not fetch release for tag: {tag}")

    if release is None:
        raise RuntimeError("Could not fetch latest release")

    downloads = [
        f"[{asset.name}]({asset.browser_download_url})" for asset in release.assets
    ]

    message = f"""
[New Update Released !]({release.html_url})

▼ Downloads ▼

{"\n\n".join(downloads)}
"""

    print(message)

    send_message(message, tg_token, tg_chat_id, tg_thread_id)


def download(link, out, headers=None, use_scraper=False):
    dir_name = os.path.dirname(out)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    if os.path.exists(out):
        print(f"{out} already exists skipping download")
        return

    if use_scraper:
        print(f"Downloading with scraper: {link}")

    session = get_scraper() if use_scraper else requests

    # https://www.slingacademy.com/article/python-requests-module-how-to-download-files-from-urls/#Streaming_Large_Files
    with session.get(link, stream=True, headers=headers) as r:
        r.raise_for_status()
        with open(out, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)


def run_command(command: list[str]):
    cmd = subprocess.run(command, capture_output=True, shell=True)

    try:
        cmd.check_returncode()
    except subprocess.CalledProcessError:
        print(cmd.stdout)
        print(cmd.stderr)
        exit(1)


def merge_apk(path: str):
    subprocess.run(
        ["java", "-jar", "./bins/apkeditor.jar", "m", "-extractNativeLibs", "true", "-i", path]
    ).check_returncode()


def ensure_sign_apk() -> None:
    if os.path.exists("scripts/SignApk.class"):
        return
    if not os.path.exists("bins/apksig.jar"):
        raise FileNotFoundError("bins/apksig.jar is missing; run download_apksig() first")
    subprocess.run(
        ["javac", "-cp", "bins/apksig.jar", "scripts/SignApk.java"],
        check=True,
    )


def sign_apk(unsigned_apk: str, signed_apk: str) -> None:
    ensure_sign_apk()
    signing = get_signing_config()
    if os.path.exists(signed_apk):
        os.unlink(signed_apk)
    subprocess.run(
        [
            "java",
            "-cp",
            "bins/apksig.jar:scripts",
            "SignApk",
            unsigned_apk,
            signed_apk,
            signing["keystore"],
            signing["keystore_password"],
            signing["key_alias"],
            signing["key_password"],
        ],
        check=True,
    )


def patch_apk(
    cli: str,
    patch_files: list[str],
    apk: str,
    includes: list[str] | None = None,
    excludes: list[str] | None = None,
    out: str | None = None,
):
    if out is None:
        raise ValueError("patch_apk requires an explicit output path")

    unsigned_apk = out.removesuffix(".apk") + "-unsigned.apk"
    for path in (unsigned_apk, out):
        if os.path.exists(path):
            os.unlink(path)

    command = ["java", "-jar", cli, "patch", "--unsigned", "-o", unsigned_apk]
    for patch_file in patch_files:
        command.extend(["-p", patch_file])

    if includes is not None:
        for include in includes:
            command.extend(["-e", include])

    if excludes is not None:
        for exclude in excludes:
            command.extend(["-d", exclude])

    command.append(apk)
    subprocess.run(command, check=True)
    sign_apk(unsigned_apk, out)
    os.unlink(unsigned_apk)


def publish_release(
    tag: str,
    files: list[str],
    message: str,
    title="",
    *,
    mark_latest: bool = True,
):
    if os.environ.get("GITHUB_TOKEN") is None:
        raise Exception("GITHUB_TOKEN is not set")

    if len(files) == 0:
        raise Exception("Files should have atleast one item")

    env = os.environ.copy()
    existing = get_release_by_tag(REPO, tag)
    latest_args = ["--latest"] if mark_latest else []

    if existing is None:
        command = [
            "gh",
            "release",
            "create",
            *latest_args,
            tag,
            "--notes",
            message,
            "--title",
            title,
            *files,
        ]
        subprocess.run(command, env=env, check=True)
        return

    print(f"Release {tag} already exists, uploading assets")
    subprocess.run(
        ["gh", "release", "upload", tag, *files, "--clobber"],
        env=env,
        check=True,
    )
    edit_command = [
        "gh",
        "release",
        "edit",
        tag,
        *latest_args,
        "--notes",
        message,
        "--title",
        title,
    ]
    subprocess.run(edit_command, env=env, check=True)
