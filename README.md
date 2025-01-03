## Aufer
Command-line download manager

### Requirements:
Make sure you have the following installed:
- **Python 3**: https://www.python.org/downloads/

## Instructions
1. Clone the repository
```
git clone https://github.com/finitesphere/aufer
```
2. Navigate to the project directory 
```
cd aufer
```
3. Install the required dependencies
```
pip install -r requirements.txt
```
4. Run the program to download a file or scrape a website:
   
   - **To download a single file**:
     ```
     python aufer.py <file_url>
     ```
   - **To scrape a website for specific file types**:
     ```
     python aufer.py <url> <file_type>
     ```
   - **Optional: Enable Recursive Scraping**:
     ```
     python aufer.py <url> <file_type> --recursive
     ```
   - Replace `<url>` with the website URL and `<file_type>` with one of the following file types:
      - `images` – for images: ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"
      - `videos` – for videos: ".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv", ".ogv"
      - `audio` – for audio: ".mp3", ".wav", ".ogg", ".flac", ".aac"
      - `document` – for PDFs: ".pdf", ".docx", ".txt", ".ppt", ".xls"

5. Examples
```
python aufer.py https://en.wikipedia.org/wiki/Python_(programming_language) images
```
### TO DO:
- [X] Implement support for downloading different file types (images, videos, PDFs, etc.)
- [X] Support recursive scraping to follow links to internal pages
- [X] Add download progress bar
- [X] Provide clear error messages for failed downloads
- [X] Add instructions to the README.md
- [ ] Verify video formats before downloading
- [ ] Option to download encrypted files
- [ ] Ability to download files from social media websites
- [ ] Option to download torrents
- [ ] Add more examples to README.md
