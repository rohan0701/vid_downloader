from flask import Flask, render_template, request, jsonify, send_from_directory
import yt_dlp
import os
import json
import shutil
from datetime import datetime
import re
import logging
import threading
import time
import platform

# ---------------- App Setup ---------------- #
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

# ---------------- Configuration ---------------- #
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")  # Server-local folder for downloads
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

HISTORY_FILE = os.path.join(BASE_DIR, "download_history.json")
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "w") as f:
        json.dump([], f)

# ---------------- Logging ---------------- #
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------- Globals ---------------- #
active_downloads = {}
download_lock = threading.Lock()

# ---------------- Utility Functions ---------------- #
def ffmpeg_installed():
    return shutil.which("ffmpeg") is not None

def sanitize_filename(filename):
    if not filename:
        return "unknown_file"
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = filename.strip('. ')
    filename = re.sub(r'_+', '_', filename)
    return filename[:200] if len(filename) > 200 else filename

def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except:
        return []

def save_history(entry):
    try:
        history = load_history()
        history = [h for h in history if not (h.get('url') == entry.get('url') and h.get('choice') == entry.get('choice'))]
        history.insert(0, entry)
        history = history[:50]
        with open(HISTORY_FILE, "w", encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving history: {e}")

def format_filesize(size_bytes):
    if not size_bytes or size_bytes <= 0:
        return "Unknown size"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def progress_hook(d):
    if d['status'] == 'downloading':
        logger.info(f"Downloading {os.path.basename(d.get('filename',''))}: {d.get('_percent_str','')} at {d.get('_speed_str','')}")
    elif d['status'] == 'finished':
        logger.info(f"Download finished: {os.path.basename(d.get('filename',''))}")

def get_basic_ydl_opts(choice, resolution="1080"):
    """ yt-dlp options for Audio/Video/Both with default 1080p """
    has_ffmpeg = ffmpeg_installed()
    base_opts = {
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
        "restrictfilenames": True,
        "windowsfilenames": True,
        "ignoreerrors": False,
        "no_warnings": False,
        "progress_hooks": [progress_hook],
        "noplaylist": True,
    }

    if choice == "audio":
        base_opts["format"] = "bestaudio/best"
        if has_ffmpeg:
            base_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }]
    elif choice == "video":
        if has_ffmpeg:
            base_opts["format"] = f"bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]"
            base_opts["merge_output_format"] = "mp4"
        else:
            base_opts["format"] = f"best[height<={resolution}]"
    elif choice == "both":
        if has_ffmpeg:
            base_opts["format"] = f"bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]"
            base_opts["merge_output_format"] = "mp4"
        else:
            base_opts["format"] = f"best[height<={resolution}]"
    return base_opts

def find_downloaded_file(expected_path, choice):
    if choice == "audio" and ffmpeg_installed():
        expected_path = os.path.splitext(expected_path)[0] + ".mp3"
    if os.path.exists(expected_path):
        return expected_path
    try:
        files = [(f, os.path.getctime(os.path.join(DOWNLOAD_DIR, f))) for f in os.listdir(DOWNLOAD_DIR)]
        files.sort(key=lambda x: x[1], reverse=True)
        for file, ctime in files:
            if time.time() - ctime < 120:
                return os.path.join(DOWNLOAD_DIR, file)
    except:
        pass
    return None

# ---------------- Routes ---------------- #
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download():
    try:
        data = request.get_json()
        url = data.get("url", "").strip()
        choice = data.get("choice", "").strip()
        resolution = data.get("resolution", "1080").strip()

        if not url or choice not in ["audio", "video", "both"]:
            return jsonify({"error": "Invalid URL or choice"}), 400

        with download_lock:
            if url in active_downloads:
                return jsonify({"error": "This URL is already downloading"}), 400
            active_downloads[url] = True

        ydl_opts = get_basic_ydl_opts(choice, resolution)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get("title", "Unknown Title")
                expected_path = ydl.prepare_filename(info)
                downloaded_file = find_downloaded_file(expected_path, choice)
                if not downloaded_file or not os.path.exists(downloaded_file):
                    return jsonify({"error": "Downloaded file not found"}), 500

                filename = os.path.basename(downloaded_file)
                filesize = os.path.getsize(downloaded_file)

                save_history({
                    "title": title,
                    "filename": filename,
                    "filepath": downloaded_file,
                    "url": url,
                    "choice": choice,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "filesize": filesize,
                    "uploader": info.get("uploader", "Unknown")
                })

                return jsonify({
                    "success": True,
                    "title": title,
                    "file": filename,
                    "download_url": f"/files/{filename}",
                    "filesize": format_filesize(filesize),
                    "uploader": info.get("uploader", "Unknown")
                })
        finally:
            with download_lock:
                active_downloads.pop(url, None)

    except Exception as e:
        with download_lock:
            active_downloads.pop(url, None)
        return jsonify({"error": str(e)}), 500

@app.route("/files/<path:filename>")
def files(filename):
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)

@app.route("/history", methods=["GET"])
def get_history():
    history = load_history()
    for item in history:
        filepath = item.get("filepath", "")
        if filepath and os.path.exists(filepath):
            item["file_exists"] = True
            item["filesize_formatted"] = format_filesize(item.get("filesize", 0))
            item["filename"] = os.path.basename(filepath)
        else:
            item["file_exists"] = False
            item["filesize_formatted"] = "File not found"
    return jsonify(history)

@app.route("/clear_history", methods=["POST"])
def clear_history():
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)
    return jsonify({"success": True})

@app.route("/health", methods=["GET"])
def health_check():
    total_size = sum(os.path.getsize(os.path.join(DOWNLOAD_DIR, f))
                     for f in os.listdir(DOWNLOAD_DIR)
                     if os.path.isfile(os.path.join(DOWNLOAD_DIR, f)))
    return jsonify({
        "status": "healthy",
        "ffmpeg_installed": ffmpeg_installed(),
        "download_dir": DOWNLOAD_DIR,
        "files_count": len(os.listdir(DOWNLOAD_DIR)),
        "total_size": format_filesize(total_size),
        "active_downloads": len(active_downloads),
        "timestamp": datetime.now().isoformat(),
        "platform": platform.system()
    })

# ---------------- Run ---------------- #
if __name__ == "__main__":
    print("YouTube Downloader Pro Starting...")
    print(f"Download directory: {DOWNLOAD_DIR}")
    print(f"FFmpeg installed: {ffmpeg_installed()}")
    app.run(debug=True, host="0.0.0.0", port=5000)
