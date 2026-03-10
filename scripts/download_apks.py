import requests
from bs4 import BeautifulSoup
import os, sys, re
from urllib.parse import urljoin

BASE_URL = "https://www.magicearth.com"
DOWNLOAD_PAGE = f"{BASE_URL}/download"
DEST_DIR = "apks"
REPO_API_URL = "https://api.github.com"

os.makedirs(DEST_DIR, exist_ok=True)

# 1. Get APK links from the website
print("Fetching Magic Earth download page...")
resp = requests.get(DOWNLOAD_PAGE)
resp.raise_for_status()
soup = BeautifulSoup(resp.text, "html.parser")

links = [urljoin(BASE_URL, a["href"]) for a in soup.find_all("a", href=True) if a["href"].endswith(".apk")]

if not links:
    print("No APKs found on the website.")
    sys.exit(1)

# Extract version string from the first APK found
sample_name = os.path.basename(links[0])
match = re.search(r"magicearth-(.*?)-(?:armeabi|arm64|x86)", sample_name)
if not match:
    print(f"Could not parse version from {sample_name}")
    sys.exit(1)

new_version = match.group(1)
print(f"Web Version Found: {new_version}")

# 2. Check against GitHub Latest Release to avoid redownloads
print(f"Checking against GitHub: {REPO_API_URL}")
try:
    gh_resp = requests.get(REPO_API_URL, timeout=10)
    if gh_resp.status_code == 200:
        current_tag = gh_resp.json().get("tag_name")
        if current_tag == new_version:
            print(f"Version {new_version} already exists. Stopping.")
            if "GITHUB_OUTPUT" in os.environ:
                with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                    f.write("new_version_found=false\n")
            sys.exit(0)
    else:
        print(f"No existing release (Status {gh_resp.status_code}). Downloading new version.")
except Exception as e:
    print(f"GitHub API check failed ({e}), proceeding with download.")

# 3. New version detected! Inform GitHub and download
if "GITHUB_OUTPUT" in os.environ:
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        f.write("new_version_found=true\n")
        f.write(f"version={new_version}\n")

print(f"Downloading version {new_version}...")
for link in links:
    name = os.path.basename(link)
    print(f"Downloading {name}...")
    with requests.get(link, stream=True) as r:
        r.raise_for_status()
        with open(os.path.join(DEST_DIR, name), "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

print("All APKs downloaded successfully.")
