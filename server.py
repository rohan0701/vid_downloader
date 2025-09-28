from flask import Flask, request, send_file, jsonify, render_template
import yt_dlp
import os, uuid

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download_video():
    data = request.get_json()
    url = data.get("url", "").strip()

    if not url.startswith("http"):
        return jsonify({"error": "Invalid URL"}), 400

    filename = f"{uuid.uuid4()}.mp4"

    # try bestvideo+bestaudio, then fallback to best
    ydl_opts_list = [
        {"outtmpl": filename, "format": "bestvideo+bestaudio/best", "merge_output_format": "mp4"},
        {"outtmpl": filename, "format": "best"}  # fallback
    ]

    try:
        for opts in ydl_opts_list:
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])
                return send_file(filename, as_attachment=True)
            except Exception as e:
                print("yt-dlp failed with opts:", opts, "error:", e)
                continue
        return jsonify({"error": "Download failed with all formats"}), 500

    except Exception as e:
        print("yt-dlp error:", str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == "__main__":
    app.run(debug=True)
