# Piko APK builds

Automated builds of patched APKs for **X/Twitter**, **Instagram** (via [Piko](https://github.com/crimera/piko)), **NewX** (via [piko-newx](https://github.com/crimera/piko-newx)), and **m-Indicator** (via [morphe-patches](https://github.com/rushiranpise/morphe-patches)).

Planned repo rename: `piko-apks` (currently may still be named `twitter-apk` on GitHub).

## Releases

| App | Tag format | Example assets |
|-----|------------|----------------|
| X/Twitter | `{version}` | `x-piko-v12.2.0-release.0.apk`, `twitter-piko-*.apk` |
| Instagram | `ig-{version}` | `instagram-piko-v435.0.0.37.76-arm64-v8a.apk`, `instagram-piko-amoled-*.apk` |
| m-Indicator | `mi-{version}` | `mindicator-no-ads-v18.0.364-arm64-v8a.apk` |
| NewX | `newx-{version}` | `x-newx-v12.24.0-prod.02.apk`, `twitter-newx-*.apk` |

Each app publishes to its own release tag with independent rebuild logic. m-Indicator and NewX builds are dispatched manually via their own workflows (not the Monday scheduled release).

## Local usage

```sh
uv sync
uv run main.py --plan              # JSON build plan, no APK build
uv run main.py --app all           # build only apps that need releases
uv run main.py --app x            # X only
uv run main.py --app instagram    # Instagram only
uv run main.py --app mindicator   # m-Indicator (strict morphe patches pin)
uv run main.py --app newx         # NewX (strict piko-newx bundle pin)
SKIP_PUBLISH=1 uv run main.py --app instagram
uv run main.py --app x --m 1 --v 12.2.0-release.0
uv run main.py --app instagram --m 1 --v 435.0.0.37.76
uv run main.py --app mindicator --m 1 --v 18.0.364
uv run main.py --app newx --m 1 --v 12.24.0-prod.02
```

Dispatch **Release - m-Indicator** or **Release - NewX** in GitHub Actions for CI builds (optional `version_input` override, `force` to rebuild unchanged pins).

See [docs/custom-signing.md](docs/custom-signing.md) for keystore and GitHub Secrets setup.

## Credits

- [morphe](https://github.com/MorpheApp) — patcher
- [crimera/piko](https://github.com/crimera/piko) — patches
- [inotia00/x-shim](https://gitlab.com/inotia00/x-shim) — X compatibility shim
- [j-hc](https://github.com/j-hc) — builder template inspiration
