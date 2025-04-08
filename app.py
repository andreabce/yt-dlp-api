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
    format_requested = data.get('format', 'mp4').lower()
    tc_in = data.get('tc_in', '00:00:00')
    tc_out = data.get('tc_out', '00:00:00')

    if not url:
        return jsonify({"error": "URL manquante"}), 400

    # Définir l'extension de sortie
    ext_map = {'mp4': 'mp4', 'mp3': 'mp3', 'wav': 'wav'}
    extension = ext_map.get(format_requested, 'mp4')
    output_filename = f"{uuid4()}.{extension}"

    # Options de base
    ydl_opts = {
        'outtmpl': output_filename,
        'quiet': True,
        'cookiefile': os.path.join(os.getcwd(), 'cookies.txt'),
    }

    # Format spécifique
    if format_requested == 'mp4':
        ydl_opts.update({
            'format': 'bv*+ba/bestvideo+bestaudio/best',
            'merge_output_format': 'mp4'
        })
    else:
        # Audio seulement
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format_requested,
                'preferredquality': '192'
            }]
        })

    try:
        print("✅ Fichier cookies.txt trouvé ?", os.path.exists(ydl_opts['cookiefile']))
        print("📂 Chemin cookies.txt :", ydl_opts['cookiefile'])

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Découpe audio/vidéo avec ffmpeg si nécessaire
        if tc_in != "00:00:00" or tc_out != "00:00:00":
            clipped_file = f"clipped_{output_filename}"
            tc_args = []
            if tc_in != "00:00:00":
                tc_args.extend(["-ss", tc_in])
            if tc_out != "00:00:00":
                tc_args.extend(["-to", tc_out])
            os.system(f"ffmpeg -y -i {output_filename} {' '.join(tc_args)} -c copy {clipped_file}")
            os.remove(output_filename)
            output_filename = clipped_file

        return send_file(output_filename, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if os.path.exists(output_filename):
            os.remove(output_filename)

@app.route('/')
def index():
    return 'API yt-dlp opérationnelle'

@app.route('/test-cookie')
def test_cookie():
    cookie_path = os.path.join(os.getcwd(), 'cookies.txt')
    if os.path.exists(cookie_path):
        with open(cookie_path, 'r') as f:
            content = f.read(1000)
        return f"✅ cookies.txt trouvé !\n\nExtrait :\n{content}"
    else:
        return "❌ cookies.txt non trouvé !"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(debug=False, host='0.0.0.0', port=port)
