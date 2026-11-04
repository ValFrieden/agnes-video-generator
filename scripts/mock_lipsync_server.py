#!/usr/bin/env python3
"""scripts/mock_lipsync_server.py — Локальный Mock/Тест-сервер для микросервиса LivePortrait/EchoMimic.

Имитирует API микросервиса LivePortrait для отладки и тестирования режима lipsync в Agnes Video Generator.
Запуск:
    python scripts/mock_lipsync_server.py --port 8000
"""

import argparse
import cgi
import http.server
import json
import logging
import os
import subprocess
import sys
import tempfile

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [MockLivePortrait] %(message)s")
logger = logging.getLogger("mock_lipsync")


class LipSyncHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/health", "/"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "service": "LivePortrait-Mock", "version": "1.0"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path != "/lipsync":
            self.send_response(404)
            self.end_headers()
            return

        ctype, pdict = cgi.parse_header(self.headers.get("content-type", ""))
        if ctype != "multipart/form-data":
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Expected multipart/form-data")
            return

        pdict["boundary"] = bytes(pdict["boundary"], "utf-8")
        fields = cgi.parse_multipart(self.rfile, pdict)

        image_data = fields.get("image", [None])[0]
        audio_data = fields.get("audio", [None])[0]

        if not image_data or not audio_data:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing 'image' or 'audio' field")
            return

        logger.info(f"Received lipsync request: image={len(image_data)} bytes, audio={len(audio_data)} bytes")

        with tempfile.TemporaryDirectory() as tmp_dir:
            img_path = os.path.join(tmp_dir, "input.png")
            aud_path = os.path.join(tmp_dir, "input.mp3")
            out_path = os.path.join(tmp_dir, "output.mp4")

            with open(img_path, "wb") as f:
                f.write(image_data)
            with open(aud_path, "wb") as f:
                f.write(audio_data)

            # Синтезируем тестовое видео через ffmpeg: статичное изображение + звук
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", img_path,
                "-i", aud_path,
                "-c:v", "libx264",
                "-tune", "stillimage",
                "-c:a", "aac",
                "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-shortest",
                out_path,
            ]
            res = subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            if res.returncode != 0:
                logger.error(f"FFmpeg error: {res.stderr.decode(errors='replace')[:300]}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"FFmpeg generation failed")
                return

            with open(out_path, "rb") as out_f:
                video_bytes = out_f.read()

            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(len(video_bytes)))
            self.end_headers()
            self.wfile.write(video_bytes)
            logger.info(f"Successfully returned lipsync video ({len(video_bytes)} bytes)")


def main():
    parser = argparse.ArgumentParser(description="Mock LivePortrait Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    args = parser.parse_args()

    server = http.server.HTTPServer(("0.0.0.0", args.port), LipSyncHandler)
    logger.info(f"Mock LivePortrait server running on http://127.0.0.1:{args.port}/lipsync")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped.")


if __name__ == "__main__":
    main()
