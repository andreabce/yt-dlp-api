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
    format = data.get('format', 'mp4')  # format demandé (mp4 par défaut)

    if not url:
        return jsonify({"error": "URL manquante"}), 400

    output_basename = str(uuid4())
    output_filename = f"{output_basename}.%(ext)s"

    # Choix des options selon le format
    if format == "mp3":
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_filename,
            "quiet": True,
            "cookiefile": os.path.join(os.getcwd(), 'cookies.txt'),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
        final_filename = f"{output_basename}.mp3"

    elif format == "wav":
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_filename,
            "quiet": True,
            "cookiefile": os.path.join(os.getcwd(), 'cookies.txt'),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }],
        }
        final_filename = f"{output_basename}.wav"

    elif format == "mp4":
        ydl_opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
            "outtmpl": output_filename,
            "quiet": True,
            "merge_output_format": "mp4",
            "cookiefile": os.path.join(os.getcwd(), 'cookies.txt'),
        }
        final_filename = f"{output_basename}.mp4"

    else:
        return jsonify({"error": f"Format '{format}' non supporté"}), 400

    try:
        print("Cookie file exists:", os.path.exists(ydl_opts["cookiefile"]))
        print("Absolute path:", ydl_opts["cookiefile"])

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return send_file(final_filename, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        # Nettoyage des fichiers temporaires
        if os.path.exists(final_filename):
            os.remove(final_filename)

@app.route('/')
def index():
    return 'API yt-dlp opérationnelle'

@app.route('/test-cookie')
def test_cookie():
    cookie_path = os.path.join(os.getcwd(), 'cookies.txt')
    if os.path.exists(cookie_path):
        with open(cookie_path, 'r') as f:
            content = f.read(1000)
        return f"cookies.txt trouvé ✅\n\nExtrait:\n{content}"
    else:
        return "cookies.txt non trouvé ❌"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(debug=False, host='0.0.0.0', port=port)
