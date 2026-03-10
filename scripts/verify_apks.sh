#!/bin/bash
set -e

# 1. Clean the expected SHA (remove colons and spaces)
EXPECTED=$(echo "$1" | sed 's/[:[:space:]]//g' | tr '[:lower:]' '[:upper:]')
SEARCH_DIR=${2:-"apks/"}

# 2. Find apksigner in the SYSTEM Android SDK
# GitHub-hosted runners provide the SDK at /usr/local/lib/android/sdk
SDK_PATH="/usr/local/lib/android/sdk"
APKSIGNER=$(find "$SDK_PATH/build-tools" -name apksigner | sort -V | tail -1)

if [ -z "$APKSIGNER" ]; then
    echo "Error: apksigner not found in $SDK_PATH/build-tools"
    exit 1
fi

echo "Using apksigner at: $APKSIGNER"

# 3. Verify every APK found in the search directory
# This handles all 3 Magic Earth architectures downloaded by the python script
find "$SEARCH_DIR" -name "*.apk" -print0 | while IFS= read -r -d '' apk; do
    echo "Checking: $apk"
    
    # 4. Extract only the FIRST SHA-256 fingerprint (handles V3 signature lineage)
    FOUND=$("$APKSIGNER" verify --print-certs "$apk" | \
        grep "SHA-256 digest" | head -n 1 | awk '{print $NF}' | sed 's/[:[:space:]]//g' | tr '[:lower:]' '[:upper:]')
    
    if [ -z "$FOUND" ]; then
        echo "Error: Could not extract fingerprint from $apk"
        exit 1
    fi

    # 5. Final Comparison
    if [ "$FOUND" != "$EXPECTED" ]; then
        echo "FINGERPRINT MISMATCH for $apk!"
        echo "Expected: $EXPECTED"
        echo "Found:    $FOUND"
        exit 1
    fi

    echo "Verified: $apk"
done

echo "All APK signatures verified successfully."
