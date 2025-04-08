from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from yt_dlp import YoutubeDL
import os
import uuid
import subprocess

app = Flask(__name__)
CORS(app)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route("/api/download", methods=["POST"])
def download_video():
    data = request.get_json()
    url = data.get("url")
    tcin = data.get("tcin", "00:00:00")
    tcout = data.get("tcout", "00:00:00")
    format = data.get("format", "mp4").lower()

    if not url:
        return jsonify({"error": "Missing URL"}), 400

    tmp_id = str(uuid.uuid4())
    base_path = os.path.join(DOWNLOAD_FOLDER, tmp_id)
    os.makedirs(base_path, exist_ok=True)
    output_path = os.path.join(base_path, "%(title).80s.%(ext)s")

    ydl_opts = {
        'outtmpl': output_path,
        'quiet': True,
        'format': 'bestaudio/best' if format in ['mp3', 'wav'] else 'best',
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # si pas de découpage
        if tcin == "00:00:00" and tcout == "00:00:00":
            final_ext = format
            if format == "mp4":
                final_file = filename
            else:
                final_file = os.path.splitext(filename)[0] + f".{format}"
                convert_to_audio(filename, final_file, format)
        else:
            # découpage nécessaire
            final_file = os.path.join(base_path, f"{tmp_id}.{format}")
            cut_media(filename, final_file, tcin, tcout, format)

        return send_file(final_file, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def cut_media(input_file, output_file, tcin, tcout, format):
    codec = "copy" if format == "mp4" else "aac"
    cmd = [
        "ffmpeg", "-y",
        "-ss", tcin,
        "-to", tcout,
        "-i", input_file,
        "-c", "copy" if format == "mp4" else "aac",
        output_file
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def convert_to_audio(input_file, output_file, format):
    codec = "libmp3lame" if format == "mp3" else "pcm_s16le"
    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-vn",
        "-acodec", codec,
        output_file
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(debug=False, host='0.0.0.0', port=port)
