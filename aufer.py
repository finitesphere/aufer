import os
import sys
import time
import random
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from tqdm import tqdm
from colorama import Fore, init

init()

SUPPORTED_EXTENSIONS = {
    "video": [".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv"],
    "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
    "audio": [".mp3", ".wav", ".ogg", ".flac", ".aac", ".oga"],
    "document": [".pdf", ".docx", ".txt", ".ppt", ".xls"]
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
MIN_DELAY = 1
MAX_DELAY = 5

def log_download(file_name, file_path, log_file="download_log.txt"):
    try:
        file_size = os.path.getsize(file_path)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        with open(log_file, "a") as log:
            log.write(f"{file_name}, {file_size} bytes, {timestamp}\n")
    except Exception as e:
        print(f"{Fore.RED}Failed to log download for {file_name}: {e}{Fore.RESET}")

def get_file_extension(url):
    return os.path.splitext(urlparse(url).path)[1].lower()

def get_file_type(url):
    ext = get_file_extension(url)
    for file_type, extensions in SUPPORTED_EXTENSIONS.items():
        if ext in extensions:
            return file_type
    return "unsupported"

def download_file(url, folder_name):
    try:
        file_name = os.path.basename(urlparse(url).path)
        file_path = os.path.join(folder_name, file_name)
        if os.path.exists(file_path):
            return None
        with requests.get(url, stream=True, headers={'User-Agent': USER_AGENT}) as response:
            response.raise_for_status()
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=1024):
                    file.write(chunk)
        log_download(file_name, file_path)
        return file_name
    except Exception as e:
        print(f"{Fore.RED}Failed to download {url}: {e}{Fore.RESET}")
        return None

def scrape_files(url, file_type, folder_name, recursive=False):
    try:
        response = requests.get(url, headers={'User-Agent': USER_AGENT})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        file_urls = []
        if file_type == "image":
            tags = soup.find_all("img")
            file_urls = [urljoin(url, tag["src"]) for tag in tags if "src" in tag.attrs]
        elif file_type == "video":
            tags = soup.find_all("video")
            file_urls.extend([urljoin(url, tag["src"]) for tag in tags if "src" in tag.attrs])
            for video_tag in tags:
                source_tags = video_tag.find_all("source")
                file_urls.extend([urljoin(url, source_tag["src"]) for source_tag in source_tags if "src" in source_tag.attrs])
            anchor_tags = soup.find_all("a", href=True)
            file_urls.extend([urljoin(url, tag["href"]) for tag in anchor_tags if any(tag["href"].endswith(ext) for ext in SUPPORTED_EXTENSIONS["video"])])
        elif file_type == "audio":
            tags = soup.find_all("audio")
            file_urls.extend([urljoin(url, tag["src"]) for tag in tags if "src" in tag.attrs])
            for audio_tag in tags:
                source_tags = audio_tag.find_all("source")
                file_urls.extend([urljoin(url, source_tag["src"]) for source_tag in source_tags if "src" in source_tag.attrs])
            anchor_tags = soup.find_all("a", href=True)
            file_urls.extend([urljoin(url, tag["href"]) for tag in anchor_tags if any(tag["href"].endswith(ext) for ext in SUPPORTED_EXTENSIONS["audio"])])
        elif file_type == "document":
            tags = soup.find_all("a", href=True)
            file_urls = [urljoin(url, tag["href"]) for tag in tags if any(tag["href"].endswith(ext) for ext in SUPPORTED_EXTENSIONS["document"])]
        else:
            print(f"{Fore.RED}Unsupported file type: {file_type}{Fore.RESET}")
            return []
        file_urls = list(set(file_urls))
        os.makedirs(folder_name, exist_ok=True)
        downloaded_files = []
        with tqdm(total=len(file_urls), desc="Downloading files", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}', colour='green') as pbar:
            for file_url in file_urls:
                file_name = download_file(file_url, folder_name)
                if file_name:
                    downloaded_files.append(file_name)
                pbar.update(1)
                time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
        if recursive:
            links = get_internal_links(url, soup)
            for link in links:
                print(f"Recursively scraping: {link}")
                scrape_files(link, file_type, folder_name, recursive=False)
        return downloaded_files
    except Exception as e:
        print(f"{Fore.RED}Error while processing {url}: {e}{Fore.RESET}")
        return []

def get_internal_links(base_url, soup):
    links = []
    for anchor in soup.find_all("a", href=True):
        link = urljoin(base_url, anchor["href"])
        if urlparse(base_url).netloc == urlparse(link).netloc:
            links.append(link)
    return list(set(links))

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  To download a single file: python aufer.py <file_url>")
        print("  To scrape and download files: python aufer.py <url> <file_type> [--recursive]")
        sys.exit(1)
    url = sys.argv[1]
    folder_name = "downloads"
    os.makedirs(folder_name, exist_ok=True)
    if len(sys.argv) == 2:
        downloaded_files = [download_file(url, folder_name)]
    elif len(sys.argv) >= 3:
        file_type = sys.argv[2].lower()
        recursive = "--recursive" in sys.argv
        downloaded_files = scrape_files(url, file_type, folder_name, recursive)
    downloaded_files = [file for file in downloaded_files if file]
    if downloaded_files:
        print(f"\nDownloaded the following files:")
        for file in downloaded_files:
            print(f"{Fore.GREEN}{file}{Fore.RESET}")
    else:
        print(f"{Fore.RED}No files were downloaded.{Fore.RESET}")

if __name__ == "__main__":
    main()
