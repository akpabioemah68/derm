import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Target website
url = "https://www.creativeeducationfoundation.org/"

# Headers to mimic a real browser
headers = {
    "User-Agent": "Mozilla/5.0"
}

# Get HTML content
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

# Create a folder to save assets
os.makedirs("assets/css", exist_ok=True)
os.makedirs("assets/js", exist_ok=True)

# Function to download and save files
def download_file(file_url, folder):
    local_filename = os.path.basename(urlparse(file_url).path)
    full_url = urljoin(url, file_url)
    try:
        r = requests.get(full_url, headers=headers)
        if r.status_code == 200:
            with open(os.path.join(folder, local_filename), 'wb') as f:
                f.write(r.content)
            print(f"Downloaded: {full_url}")
            return os.path.join(folder, local_filename)
    except Exception as e:
        print(f"Failed to download {full_url}: {e}")
    return None

# Process CSS files
for link in soup.find_all("link", rel="stylesheet"):
    href = link.get("href")
    if href:
        downloaded = download_file(href, "assets/css")
        if downloaded:
            link["href"] = downloaded

# Process JS files
for script in soup.find_all("script", src=True):
    src = script.get("src")
    if src:
        downloaded = download_file(src, "assets/js")
        if downloaded:
            script["src"] = downloaded

# Replace all href attributes with "#"
for tag in soup.find_all(href=True):
    tag["href"] = "#"

# Save modified HTML
with open("cloned_page.html", "w", encoding="utf-8") as f:
    f.write(str(soup.prettify()))

print("Website cloned and saved as cloned_page.html")
