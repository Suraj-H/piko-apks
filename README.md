# Piko APK builds

Automated builds of [Piko](https://github.com/crimera/piko) patched APKs for **X/Twitter** and **Instagram**.

Planned repo rename: `piko-apks` (currently may still be named `twitter-apk` on GitHub).

## Releases

| App | Tag format | Example assets |
|-----|------------|----------------|
| X/Twitter | `{version}` | `x-piko-v12.2.0-release.0.apk`, `twitter-piko-*.apk` |
| Instagram | `ig-{version}` | `instagram-piko-v435.0.0.37.76-arm64-v8a.apk`, `instagram-piko-amoled-*.apk` |

Each app publishes to its own release tag with independent rebuild logic.

## Local usage

```sh
uv sync
uv run main.py --plan              # JSON build plan, no APK build
uv run main.py --app all           # build only apps that need releases
uv run main.py --app x            # X only
uv run main.py --app instagram    # Instagram only
SKIP_PUBLISH=1 uv run main.py --app instagram
uv run main.py --app x --m 1 --v 12.2.0-release.0
uv run main.py --app instagram --m 1 --v 435.0.0.37.76
```

See [docs/custom-signing.md](docs/custom-signing.md) for keystore and GitHub Secrets setup.

## Credits

- [morphe](https://github.com/MorpheApp) — patcher
- [crimera/piko](https://github.com/crimera/piko) — patches
- [inotia00/x-shim](https://gitlab.com/inotia00/x-shim) — X compatibility shim
- [j-hc](https://github.com/j-hc) — builder template inspiration
