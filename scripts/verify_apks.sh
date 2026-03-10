#!/bin/bash
set -e

# 1. Clean the expected SHA
EXPECTED=$(echo "$1" | sed 's/[:[:space:]]//g' | tr '[:lower:]' '[:upper:]')
SEARCH_DIR=${2:-"apks/"}

# 2. Find apksigner in the SYSTEM Android SDK
# If ANDROID_HOME is empty, we check the common GitHub runner path
SDK_PATH="${ANDROID_HOME:-/usr/local/lib/android/sdk}"
APKSIGNER=$(find "$SDK_PATH/build-tools" -name apksigner | sort -V | tail -1)

if [ -z "$APKSIGNER" ]; then
    echo "ERROR: apksigner not found in $SDK_PATH/build-tools"
    # List directory contents to help debug if it fails again
    ls -R "$SDK_PATH/build-tools" | head -n 20
    exit 1
fi

echo "Using apksigner at: $APKSIGNER"

# 3. Verify every APK in the search directory
find "$SEARCH_DIR" -name "*.apk" -print0 | while IFS= read -r -d '' apk; do
    echo "--- Verifying: $apk ---"
    
    # 4. Extract first SHA-256
    FOUND=$("$APKSIGNER" verify --print-certs "$apk" | \
        grep "SHA-256 digest" | head -n 1 | awk '{print $NF}' | sed 's/[:[:space:]]//g' | tr '[:lower:]' '[:upper:]')
    
    echo "Expected: $EXPECTED"
    echo "Found:    $FOUND"

    if [ "$FOUND" != "$EXPECTED" ]; then
        echo "FINGERPRINT MISMATCH for $apk!"
        exit 1
    fi
    echo "Verified: $apk"
done
