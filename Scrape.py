import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Target URL and local save path
URL = "https://www.creativeeducationfoundation.org/"
DEST_DIR = "/var/www/ipsite/assets"

# Create destination folder if it doesn't exist
os.makedirs(DEST_DIR, exist_ok=True)

def download_slider_images():
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(URL, headers=headers)
    
    if response.status_code != 200:
        print("Failed to fetch site.")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    image_tags = soup.find_all('img')

    slider_imgs = []
    for img in image_tags:
        src = img.get('src')
        if src and ('slider' in src or 'hero' in src or 'slide' in src):
            slider_imgs.append(src)

    print(f"Found {len(slider_imgs)} slider-like images.")

    for i, img_url in enumerate(slider_imgs):
        full_url = urljoin(URL, img_url)
        file_name = os.path.join(DEST_DIR, f"slide{i+1}.jpg")

        try:
            img_data = requests.get(full_url).content
            with open(file_name, 'wb') as f:
                f.write(img_data)
            print(f"Saved {file_name}")
        except Exception as e:
            print(f"Failed to save {img_url}: {e}")

if __name__ == '__main__':
    download_slider_images()
