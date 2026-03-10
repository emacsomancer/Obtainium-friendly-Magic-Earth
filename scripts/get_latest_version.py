#!/usr/bin/env python3
import os
import sys
import requests
import re

# URL of the Magic Earth download page (or repository XML)
DOWNLOAD_PAGE = "https://www.magicearth.com/download/"

try:
    response = requests.get(DOWNLOAD_PAGE, timeout=15)
    response.raise_for_status()
    page_text = response.text
except requests.RequestException as e:
    print("Failed to fetch download page:", e)
    sys.exit(1)

# Find APK filenames like: magicearth-7.1.26.8.0D340BB6.5A28C3D6-arm64-v8a-release.apk
apk_files = re.findall(r"magicearth-[\d\.A-Z]+-[\w-]+-release\.apk", page_text)

if not apk_files:
    print("No APKs found on page")
    sys.exit(1)

# Sort and take the latest APK filename
apk_files.sort()
latest_apk = apk_files[-1]

# Extract version from filename
parts = latest_apk.split("-")
if len(parts) < 4:
    print("Unexpected APK filename format:", latest_apk)
    sys.exit(1)

version = parts[1]

# 1. Output to GitHub Actions (if running in a workflow)
if "GITHUB_OUTPUT" in os.environ:
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        f.write(f"version={version}\n")

# 2. Print to logs ONLY (stderr doesn't get captured by RAW_VER=$(...))
sys.stderr.write(f"Latest version found: {version}\n")

# 3. The ONLY thing printed to stdout (this is what RAW_VER captures)
print(version.strip())
