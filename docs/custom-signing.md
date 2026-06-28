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

- Patches the original APKMirror **APKM** bundle directly (arm64-v8a)
- No X-Shim required
- Release tag: `ig-{version}` (example: `ig-435.0.0.37.76`)
- Outputs:
  - `instagram-piko-v{version}-arm64-v8a.apk`
  - `instagram-piko-amoled-v{version}-arm64-v8a.apk`

## 4. Automation

The `Release` workflow runs daily at 06:00 UTC with a matrix job for `x` and
`instagram`. Each app rebuilds independently when its own version metadata
changes.

Rebuild triggers per app:

- highest piko-supported app version on APKMirror
- latest piko patch release
- latest x-shim release (X only)

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
