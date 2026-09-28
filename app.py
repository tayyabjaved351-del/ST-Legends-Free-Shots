from flask import Flask, request, jsonify
import yt_dlp
import os
import uuid
import subprocess

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
OUTPUT_DIR = "outputs"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.route("/")
def home():
    return "ST Legends Shorts Backend is running!"


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()

    if not data or not data.get("url"):
        return jsonify({"error": "YouTube URL is required"}), 400

    url = data["url"]
    duration = int(data.get("duration", 30))
    clips = int(data.get("clips", 3))

    job_id = str(uuid.uuid4())
    source = os.path.join(DOWNLOAD_DIR, job_id)

    try:
        ydl_opts = {
            "format": "best[ext=mp4]/best",
            "outtmpl": source + ".%(ext)s",
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded = ydl.prepare_filename(info)

        outputs = []

        for i in range(clips):
            start = i * duration
            output = os.path.join(
                OUTPUT_DIR,
                f"{job_id}_clip_{i + 1}.mp4"
            )

            command = [
                "ffmpeg",
                "-y",
                "-ss", str(start),
                "-i", downloaded,
                "-t", str(duration),
                "-vf", "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2",
                "-c:v", "libx264",
                "-c:a", "aac",
                output
            ]

            subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            outputs.append(f"/files/{os.path.basename(output)}")

        return jsonify({
            "success": True,
            "message": "Shorts generated successfully",
            "clips": outputs
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/files/<filename>")
def files(filename):
    from flask import send_from_directory
    return send_from_directory(OUTPUT_DIR, filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
