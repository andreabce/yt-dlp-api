from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from yt_dlp import YoutubeDL
import os
from uuid import uuid4
import subprocess

app = Flask(__name__)
CORS(app)


@app.route('/api/download', methods=['POST'])
def download_video():
    data = request.get_json()
    url = data.get('url')
    format_requested = data.get('format', 'mp4').lower()
    tc_in = data.get('tc_in', '00:00:00')
    tc_out = data.get('tc_out', '00:00:00')

    if not url:
        return jsonify({"error": "URL manquante"}), 400

    # Nom du fichier de sortie initial
    temp_filename = f"{uuid4()}"
    output_filename = f"{temp_filename}.{format_requested}"

    # Choix du format
    ydl_opts = {
        'format': get_format_code(format_requested),
        'outtmpl': f"{temp_filename}.%(ext)s",
        'quiet': True,
        'noplaylist': True,
        'force_ipv4': True,
    }

    if format_requested in ['mp3', 'wav']:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': format_requested,
            'preferredquality': '192',
        }]
        ydl_opts['merge_output_format'] = format_requested
    else:
        ydl_opts['merge_output_format'] = 'mp4'

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # On trouve le vrai fichier téléchargé
        downloaded_file = find_downloaded_file(temp_filename)

        # Si timecode est spécifié, on découpe avec ffmpeg
        if tc_out != "00:00:00":
            cut_filename = f"{uuid4()}.{format_requested}"
            cmd = [
                "ffmpeg", "-y",
                "-i", downloaded_file,
                "-ss", tc_in,
                "-to", tc_out,
                "-c", "copy",
                cut_filename
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.remove(downloaded_file)
            final_file = cut_filename
        else:
            final_file = downloaded_file

        return send_file(final_file, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        # Nettoyage
        for file in os.listdir():
            if file.startswith(temp_filename):
                try:
                    os.remove(file)
                except:
                    pass


def get_format_code(fmt):
    if fmt == 'mp3' or fmt == 'wav':
        return 'bestaudio'
    else:
        return 'best'


def find_downloaded_file(base):
    for file in os.listdir():
        if file.startswith(base):
            return file
    raise FileNotFoundError("Fichier téléchargé introuvable.")


@app.route('/')
def index():
    return '✅ API yt-dlp opérationnelle sans cookies'


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(debug=False, host='0.0.0.0', port=port)
