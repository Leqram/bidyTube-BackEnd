from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import tempfile
import os

app = Flask(__name__)
CORS(app)


from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route("/resolutions", methods=["GET"])
def get_resolutions():
    url = request.args.get("url")
    if not url:
        return jsonify({
            "status": False,
            "message": "Parameter URL wajib diisi",
            "data": None
        }), 400

    try:
        ydl_opts = {"quiet": True, "skip_download": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        formats = []
        for f in info["formats"]:
            if f.get("vcodec") != "none" and f.get("acodec") != "none" and f.get("ext") == "mp4":
                size_bytes = f.get("filesize") or f.get("filesize_approx")
                size = round(size_bytes / (1024 * 1024), 2) if size_bytes else None

                formats.append({
                    "format_id": f["format_id"],
                    "resolution": f.get("format_note") or f"{f.get('height')}p",
                    "filesize_mb": size,
                    "url": f["url"]
                })

        return jsonify({
            "status": True,
            "message": "Berhasil mendapatkan daftar resolusi video",
            "data": {
                "title": info["title"],
                "thumbnail": info["thumbnail"],
                "resolutions": formats
            }
        }), 200

    except Exception as e:
        return jsonify({
            "status": False,
            "message": f"Gagal memproses video: {str(e)}",
            "data": None
        }), 500

@app.route("/download", methods=["GET"])
def download_video():
    url = request.args.get("url")
    format_id = request.args.get("format_id")

    if not url or not format_id:
        return jsonify({
            "status": False,
            "message": "Parameter 'url' dan 'format_id' wajib diisi",
            "data": None
        }), 400

    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, "%(title)s.%(ext)s")

    ydl_opts = {
        "quiet": True,
        "format": format_id,
        "outtmpl": output_path,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/137.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
        "cookiefile": None,
        "cachedir": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        return send_file(
            file_path,
            as_attachment=True,
            download_name=os.path.basename(file_path),
            mimetype="video/mp4"
        )

    except Exception as e:
        return jsonify({
            "status": False,
            "message": f"Gagal mengunduh video: {str(e)}",
            "data": None
        }), 500

    finally:
        try:
            for f in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, f))
            os.rmdir(temp_dir)
        except:
            pass

if __name__ == "__main__":
    app.run(debug=True)