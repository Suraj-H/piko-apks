#!/usr/bin/env bash
set -euo pipefail

KEYSTORE_PATH="${KEYSTORE_PATH:-signing/release.keystore}"
KEY_ALIAS="${KEY_ALIAS:-twitter-piko}"
STORE_PASSWORD="${STORE_PASSWORD:?Set STORE_PASSWORD before running this script}"
KEY_PASSWORD="$STORE_PASSWORD"

mkdir -p "$(dirname "$KEYSTORE_PATH")"

keytool -genkeypair \
  -v \
  -keystore "$KEYSTORE_PATH" \
  -storetype PKCS12 \
  -storepass "$STORE_PASSWORD" \
  -alias "$KEY_ALIAS" \
  -keypass "$KEY_PASSWORD" \
  -keyalg RSA \
  -keysize 4096 \
  -validity 10000 \
  -dname "CN=Twitter Piko Custom Builder, OU=Personal, O=Personal, L=Local, ST=Local, C=US"

base64 -i "$KEYSTORE_PATH" > "$KEYSTORE_PATH.b64"

cat <<EOF
Created:
  $KEYSTORE_PATH
  $KEYSTORE_PATH.b64

Add these GitHub repository secrets:
  APK_KEYSTORE_BASE64 = contents of $KEYSTORE_PATH.b64
  APK_KEYSTORE_PASSWORD = STORE_PASSWORD
  APK_KEY_ALIAS = $KEY_ALIAS
  APK_KEY_PASSWORD = STORE_PASSWORD
EOF
