# Custom signing for your fork

Android only installs an APK as an update when the package name and signing
certificate match the app already installed on the device. Use one private
keystore for every build from your fork.

## 1. Generate your private keystore

Run this locally from the repo root:

```sh
STORE_PASSWORD='replace-with-a-long-password' \
KEY_ALIAS='twitter-piko' \
bash scripts/create-signing-keystore.sh
```

This creates ignored local files under `signing/`:

- `signing/release.keystore`
- `signing/release.keystore.b64`

Keep both private. Do not commit them.

## 2. Add GitHub Secrets

In your fork, open `Settings` -> `Secrets and variables` -> `Actions`, then add:

- `APK_KEYSTORE_BASE64`: the full contents of `signing/release.keystore.b64`
- `APK_KEYSTORE_PASSWORD`: the value used for `STORE_PASSWORD`
- `APK_KEY_ALIAS`: the value used for `KEY_ALIAS`
- `APK_KEY_PASSWORD`: the same value used for `STORE_PASSWORD`

The workflows restore the keystore from those secrets and pass the signing
values to `main.py`.

## 3. Supported apps and versions

The builder resolves supported versions from the latest piko release at build
time, intersects them with APKMirror, and picks the highest buildable release.

### X/Twitter

- Patches the original APKMirror **APKM** bundle directly
- Includes [X-Shim](https://gitlab.com/inotia00/x-shim) when required (11.88+)
- Release tag: `{version}` (example: `12.2.0-release.0`)
- Outputs: `x-piko-*`, `twitter-piko-*` (standard + Material You variants)

### Instagram

- Downloads the original bundle from [Uptodown](https://instagram.en.uptodown.com/android)
  because APKMirror serves Instagram behind Cloudflare blocks in CI
- Patches the bundle directly with Morphe (same as X)
- No X-Shim required
- Release tag: `ig-{version}` (example: `ig-435.0.0.37.76`)
- Outputs:
  - `instagram-piko-v{version}-arm64-v8a.apk`
  - `instagram-piko-amoled-v{version}-arm64-v8a.apk`

## 4. Automation

The `Release` workflow runs weekly on Monday at 06:00 UTC.

1. A lightweight **plan** job resolves the current X/Instagram target versions and
   compares them to each app's last release metadata.
2. Build jobs start **only** for apps that need a new release.

Rebuild triggers per app:

- resolved app version changed (new target on APKMirror/Uptodown or new piko-supported version)
- latest x-shim release changed (X only)

A piko release alone does **not** rebuild an app unless that app's resolved target
version also changed. Release notes still record the piko version used for the build.

Use `workflow_dispatch` with `force: true` to rebuild anyway.

Manual version builds are available in `Release - manual` with `app` and
`version` inputs.

## 5. Telegram notifications (optional)

If you want release announcements in Telegram, add these GitHub Secrets:

- `TG_TOKEN`
- `TG_CHAT_ID`
- `TG_THREAD_ID` (optional for non-topic chats)

If they are missing, the build still completes and only skips the Telegram
notification step.

## 6. Install once from your fork

If your phone currently has an APK from the official `crimera/twitter-apk`
releases, uninstall it once before installing your first fork build. After that,
future APKs from this fork should install as updates as long as these secrets do
not change.

Rename the GitHub repo to `piko-apks` when ready — no code changes required
beyond updating local remotes; `GITHUB_REPOSITORY` is injected automatically in
Actions.
