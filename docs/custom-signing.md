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

## 3. Supported X versions

The builder resolves supported X versions from the latest piko release at build
time, intersects them with APKMirror, and picks the highest buildable release.
For newer X versions it patches the original APKMirror **APKM** bundle directly
and includes [X-Shim](https://gitlab.com/inotia00/x-shim) when required.

## 4. Automation

The `Release` workflow runs daily at 06:00 UTC and also supports manual runs.

It rebuilds and publishes when any of these change:

- highest piko-supported X version on APKMirror
- latest piko patch release
- latest x-shim release

Use `workflow_dispatch` with `force: true` to rebuild anyway.

Manual version builds remain available in `Release - manual`.

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
