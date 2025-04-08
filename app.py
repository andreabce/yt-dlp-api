from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from yt_dlp import YoutubeDL
import os
from uuid import uuid4

app = Flask(__name__)
CORS(app)  # Autorise toutes les origines (à restreindre si besoin)

@app.route('/api/download', methods=['POST'])
def download_video():
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({"error": "URL manquante"}), 400

    output_filename = f"{uuid4()}.mp4"
    ydl_opts = {
        'format': 'bv*+ba/best',
        'outtmpl': output_filename,
        'quiet': True,
        'cookiefile': 'cookies.txt',
        'merge_output_format': 'mp4'
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
    return 'API yt-dlp opérationnelle'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(debug=False, host='0.0.0.0', port=port)
