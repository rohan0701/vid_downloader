# 🎬 YouTube Video Downloader Pro

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-2.3-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/rohan0701/video-downloader?style=social)](https://github.com/yourusername/video-downloader/stargazers)
[![Forks](https://img.shields.io/github/forks/rohan0701/video-downloader?style=social)](https://github.com/yourusername/video-downloader/network/members)
[![Issues](https://img.shields.io/github/issues/rohan0701/video-downloader)](https://github.com/yourusername/video-downloader/issues)

A **powerful, user-friendly YouTube downloader** built with **Flask** and **yt-dlp**, supporting **video, audio, or both** downloads in **1080p by default**, with download history and server monitoring.

---

## 🚀 Features

- ✅ Download **videos in 1080p** or lower resolutions  
- ✅ Download **audio only** (MP3)  
- ✅ Download **video + audio combined**  
- ✅ Tracks **download history** (title, uploader, size, date)  
- ✅ **Thread-safe** downloads  
- ✅ **Cross-platform**: Windows, Linux, Mac, server deployments  
- ✅ Clean **web interface** with CSS/JS  
- ✅ Health check endpoint for server monitoring  

---

## 📂 Folder Structure

VID_DONL/
│── .venv/
│── templates/
│ └── index.html
│── static/
│ ├── style.css
│ └── script.js
│── downloads/
│── app.py
│── download_history.json


---

## ⚙️ Requirements

- Python 3.8+  
- Flask  
- yt-dlp  
- FFmpeg (for merging video/audio and MP3 conversion)  

Install dependencies:

```bash
pip install flask yt-dlp

Run the Flask app:

python app.py

📧 Contact

Created by Rohan Sutar
GitHub: https://github.com/rohan0701

Email: sutarrohan49@gmail.com
