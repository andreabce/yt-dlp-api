from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from yt_dlp import YoutubeDL
import os
from uuid import uuid4

app = Flask(__name__)
CORS(app)

@app.route('/api/download', methods=['POST'])
def download_video():
    data = request.get_json()
    url = data.get('url')
    format_choice = data.get('format', 'mp4')
    tc_in = data.get('tc_in', '00:00:00')
    tc_out = data.get('tc_out', '00:00:00')

    if not url:
        return jsonify({"error": "URL manquante"}), 400

    uid = str(uuid4())
    output_filename = f"{uid}.{format_choice}"

    postprocessors = []
    if format_choice in ['mp3', 'wav']:
        postprocessors = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': format_choice,
            'preferredquality': '192',
        }]
        output_filename = f"{uid}.{format_choice}"

    ydl_opts = {
        'format': 'bestaudio/best' if format_choice in ['mp3', 'wav'] else 'bestvideo+bestaudio/best',
        'outtmpl': output_filename,
        'quiet': True,
        'merge_output_format': 'mp4',
        'postprocessors': postprocessors,
        'allow_unplayable_formats': True
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return send_file(output_filename, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if os.path.exists(output_filename):
            os.remove(output_filename)

@app.route('/')
def index():
    return 'API yt-dlp opérationnelle (sans cookies.txt) ✅'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(debug=False, host='0.0.0.0', port=port)
