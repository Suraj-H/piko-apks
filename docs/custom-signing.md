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

The builder patches the original APKMirror **APKM** bundle directly and includes
[X-Shim](https://gitlab.com/inotia00/x-shim) for newer releases.

Highest APKMirror build today:

- `12.2.0-release.0`

Older fallback:

- `12.0.0-release.0`
- `11.81.0-release.0`

`12.2.1` and other unreleased-by-piko versions are skipped automatically.

Manual build example:

```sh
GITHUB_REPOSITORY=your-user/twitter-apk uv run main.py --m 1 --v 12.2.0-release.0
```

## 4. Install once from your fork

If your phone currently has an APK from the official `crimera/twitter-apk`
releases, uninstall it once before installing your first fork build. After that,
future APKs from this fork should install as updates as long as these secrets do
not change.
