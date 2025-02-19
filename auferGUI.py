import sys
import os
import time
import random
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
    QLineEdit, QLabel, QComboBox, QTextEdit, QCheckBox, QProgressBar,
    QFileDialog
)
from PyQt6.QtCore import QThread, pyqtSignal

SUPPORTED_EXTENSIONS = {
    "video": [".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv"],
    "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
    "audio": [".mp3", ".wav", ".ogg", ".flac", ".aac", ".oga"],
    "document": [".pdf", ".docx", ".txt", ".ppt", ".xls"]
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
MIN_DELAY = 1
MAX_DELAY = 5

class DownloadThread(QThread):
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)

    def __init__(self, url, file_type, folder, recursive=False):
        super().__init__()
        self.url = url
        self.file_type = file_type
        self.folder = folder
        self.recursive = recursive
    
    def run(self):
        files_downloaded = self.scrape_files(self.url, self.file_type, self.folder, self.recursive)
        self.log_signal.emit(f"Downloaded {len(files_downloaded)} files.")

    def scrape_files(self, url, file_type, folder, recursive):
        try:
            headers = {"User-Agent": USER_AGENT, "Accept": "*/*", "Referer": url}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            file_urls = []

            if file_type == "image":
                file_urls = [urljoin(url, tag["src"]) for tag in soup.find_all("img") if "src" in tag.attrs]
            elif file_type == "video":
                file_urls = [urljoin(url, tag["src"]) for tag in soup.find_all("video") if "src" in tag.attrs]
                file_urls += [urljoin(url, tag["src"]) for tag in soup.find_all("source") if "src" in tag.attrs]
                file_urls += [urljoin(url, tag["href"]) for tag in soup.find_all("a", href=True)
                              if any(tag["href"].endswith(ext) for ext in SUPPORTED_EXTENSIONS["video"])]
            elif file_type == "audio":
                file_urls = [urljoin(url, tag["src"]) for tag in soup.find_all("audio") if "src" in tag.attrs]
                file_urls += [urljoin(url, tag["src"]) for tag in soup.find_all("source") if "src" in tag.attrs]
                file_urls += [urljoin(url, tag["href"]) for tag in soup.find_all("a", href=True)
                              if any(tag["href"].endswith(ext) for ext in SUPPORTED_EXTENSIONS["audio"])]
            elif file_type == "document":
                file_urls = [urljoin(url, tag["href"]) for tag in soup.find_all("a", href=True)
                             if any(tag["href"].endswith(ext) for ext in SUPPORTED_EXTENSIONS["document"])]
            else:
                self.log_signal.emit(f"Unsupported file type: {file_type}")
                return []

            file_urls = list(set(file_urls))
            os.makedirs(folder, exist_ok=True)
            downloaded_files = []

            for i, file_url in enumerate(file_urls):
                file_name = self.download_file(file_url, folder)
                if file_name:
                    downloaded_files.append(file_name)
                self.progress_signal.emit(int((i + 1) / len(file_urls) * 100))
                time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
            
            if recursive:
                links = self.get_internal_links(url, soup)
                for link in links:
                    self.log_signal.emit(f"Recursively scraping: {link}")
                    downloaded_files += self.scrape_files(link, file_type, folder, recursive=False)

            return downloaded_files
        except Exception as e:
            self.log_signal.emit(f"Error: {str(e)}")
            return []

    def get_internal_links(self, base_url, soup):
        links = []
        for anchor in soup.find_all("a", href=True):
            link = urljoin(base_url, anchor["href"])
            if urlparse(base_url).netloc == urlparse(link).netloc:
                links.append(link)
        return list(set(links))

    def download_file(self, url, folder):
        try:
            file_name = os.path.basename(urlparse(url).path)
            file_path = os.path.join(folder, file_name)
            if os.path.exists(file_path):
                return None

            headers = {"User-Agent": USER_AGENT, "Accept": "*/*", "Referer": url}
            with requests.get(url, stream=True, headers=headers) as response:
                response.raise_for_status()
                with open(file_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
            return file_name
        except Exception as e:
            self.log_signal.emit(f"Download failed: {url} - {str(e)}")
            return None

class Aufer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aufer")
        self.setGeometry(200, 200, 500, 400)
        
        layout = QVBoxLayout()
        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText("Enter URL")
        layout.addWidget(QLabel("URL:"))
        layout.addWidget(self.url_input)
        
        self.file_type_combo = QComboBox(self)
        self.file_type_combo.addItems(SUPPORTED_EXTENSIONS.keys())
        layout.addWidget(QLabel("File Type:"))
        layout.addWidget(self.file_type_combo)
        
        self.recursive_check = QCheckBox("Recursive Search")
        layout.addWidget(self.recursive_check)
        
        self.folder_button = QPushButton("Select Download Folder")
        self.folder_button.clicked.connect(self.select_folder)
        layout.addWidget(self.folder_button)
        
        self.download_button = QPushButton("Start Download")
        self.download_button.clicked.connect(self.start_download)
        layout.addWidget(self.download_button)
        
        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar)
        
        self.log_output = QTextEdit(self)
        self.log_output.setReadOnly(True)
        layout.addWidget(QLabel("Log:"))
        layout.addWidget(self.log_output)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.download_folder = "downloads"

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.download_folder = folder
    
    def start_download(self):
        url = self.url_input.text()
        file_type = self.file_type_combo.currentText()
        recursive = self.recursive_check.isChecked()

        if not url:
            self.log_output.append("Error: Please enter a valid URL.")
            return
        
        self.download_thread = DownloadThread(url, file_type, self.download_folder, recursive)
        self.download_thread.progress_signal.connect(self.progress_bar.setValue)
        self.download_thread.log_signal.connect(self.log_output.append)
        self.download_thread.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Aufer()
    window.show()
    sys.exit(app.exec())
