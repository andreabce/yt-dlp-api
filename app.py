from flask import Flask, request, send_file, jsonify
import yt_dlp
import os
import uuid

app = Flask(__name__)

@app.route("/api/download", methods=["POST"])
def download():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return "URL manquante", 400

    filename = f"{uuid.uuid4()}.mp4"
    filepath = f"/tmp/{filename}"  # dossier temporaire pour Render

    ydl_opts = {
        "outtmpl": filepath,
        "format": "best",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return send_file(filepath, as_attachment=True, download_name="video.mp4")

if __name__ == "__main__":
    app.run(debug=True)
