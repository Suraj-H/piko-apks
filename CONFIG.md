# Configuration Guide (`config.toml`)

The build system is driven by `config.toml`. This file controls which version of Twitter is downloaded, which patches are applied, and which build variants are generated.

---

## 1. Project Settings (`[project]`)

| Key | Description |
| :--- | :--- |
| `repo` | The GitHub repository where releases will be published (e.g., `crimera/twitter-apk`). |
| `apkmirror_url` | The URL of the Twitter page on APKMirror used to check for new versions. |
| `publish` | (Boolean) If `true`, the script will create a GitHub release with the generated APKs. |
| `telegram_report` | (Boolean) If `true`, the script will send a release notification to Telegram. |

---

## 2. Binary Dependencies (`[binaries]`)

This section defines the tools required for patching. Each entry (e.g., `cli`, `patches`, `apkeditor`) supports the following keys:

| Key | Description |
| :--- | :--- |
| `repo` | GitHub repository to fetch the binary from. |
| `regex` | Regular expression to match the asset name in the GitHub release. |
| `filename` | Local name for the downloaded file in the `bins/` directory. |
| `version` | (Optional) Specific tag name to download (e.g., `v5.0.1`). If omitted, the latest release is used. |
| `include_prerelease` | (Boolean) Whether to consider pre-release versions. |

---

## 3. Patch Configuration (`[patches]`)

Global settings for the patching process.

| Key | Description |
| :--- | :--- |
| `exclusive` | (Boolean) If `true`, only patches explicitly listed in `includes` will be applied. Highly recommended. |
| `extra_args` | (List of Strings) Additional raw flags to pass to the ReVanced CLI (e.g., `["--force"]`). |
| `common_includes` | List of patch names to be included in **all** build variants. |
| `common_excludes` | List of patch names to be excluded from **all** build variants. |

### Example Extra Arguments:

```toml
[patches]
exclusive = true
# Pass any raw ReVanced CLI flags here.
# For flags with values, you can use "key=value" or separate strings.
extra_args = [
    "--force", 
    "--mount", 
    "-i", "<device-serial>"
]
common_includes = [
    "Enable app downgrading",
]
```

---

## 4. Build Variants (`[[variants]]`)

You can define multiple variants by adding multiple `[[variants]]` blocks.

| Key | Description |
| :--- | :--- |
| `name` | The name of the variant. The output file will be named `{name}-v{version}.apk`. |
| `includes` | (Optional) Patch names to add specifically for this variant. |
| `excludes` | (Optional) Patch names to remove specifically for this variant. |
| `extra_args` | (Optional) Additional raw flags to add specifically for this variant. |

### Example Variant Configuration:

```toml
[[variants]]
name = "x-piko-material-you"

[[variants]]
name = "twitter-piko-material-you"
includes = ["Bring back twitter"]

[[variants]]
name = "x-piko"
excludes = ["Dynamic color"]
```

---

## Usage Note
- **ReVanced CLI 5.x**: This configuration is designed for ReVanced CLI 5.0.1 and above.
- **Keystore**: The system expects a `ks.keystore` file in the root directory for signing.
