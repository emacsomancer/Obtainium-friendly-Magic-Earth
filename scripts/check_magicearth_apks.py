import requests
from bs4 import BeautifulSoup
import os
import sys
import re
from urllib.parse import urljoin

# --- CONFIGURATION ---
BASE_URL = "https://www.magicearth.com"
DOWNLOAD_PAGE = f"{BASE_URL}/download"
DEST_DIR = "apks"
# Set via environment variable in GitHub Action
REPO_API_URL = os.environ.get("REPO_API_URL")

os.makedirs(DEST_DIR, exist_ok=True)

def set_github_output(name, value):
    """Sets an output variable for use in subsequent GitHub Action steps."""
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"{name}={value}\n")

# 1. Scrape Magic Earth Website
print("Checking Magic Earth website...")
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}
resp = requests.get(DOWNLOAD_PAGE, headers=headers)
resp.raise_for_status()
soup = BeautifulSoup(resp.text, "html.parser")

# Find all APK links
links = [urljoin(BASE_URL, a["href"]) for a in soup.find_all("a", href=True) if a["href"].endswith(".apk")]

if not links:
    print("Error: No APK links found on the website.")
    sys.exit(1)

# Extract version from first APK (e.g., magicearth-7.1.26.8.0D340BB6.5A28C3D6-arm64-v8a-release.apk)
sample_name = os.path.basename(links[0])
match = re.search(r"magicearth-(.*?)-(?:armeabi|arm64|x86)", sample_name)
if not match:
    print(f"Error: Could not parse version from {sample_name}")
    sys.exit(1)

web_version = match.group(1)
print(f"Web Version: {web_version}")

# 2. Check GitHub Repo's Latest Release
print(f"Comparing with: {REPO_API_URL}")
try:
    gh_resp = requests.get(REPO_API_URL, timeout=10)
    if gh_resp.status_code == 200:
        current_tag = gh_resp.json().get("tag_name")
        print(f"GitHub Version: {current_tag}")
        
        if current_tag == web_version:
            print("Versions match. No update needed.")
            set_github_output("new_version_found", "false")
            sys.exit(0)
    else:
        print(f"No existing release found (Status {gh_resp.status_code}).")
except Exception as e:
    print(f"Warning: GitHub check failed ({e}), proceeding with download.")

# 3. New Version Detected
set_github_output("new_version_found", "true")
set_github_output("version", web_version)

print(f"New version {web_version} detected. Downloading variants...")
for link in links:
    name = os.path.basename(link)
    print(f"Downloading {name}...")
    with requests.get(link, stream=True, headers=headers) as r:
        r.raise_for_status()
        with open(os.path.join(DEST_DIR, name), "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

print("All APKs downloaded successfully.")
