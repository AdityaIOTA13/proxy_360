#!/usr/bin/env python3
"""
Simple HTTP server for the 360 video viewer.
Registers .insv as video/mp4 so browsers can stream the files.

Usage:
    python3 server.py          # serves on http://localhost:8360
    python3 server.py 9000     # custom port
"""

import http.server
import mimetypes
import sys
import os

mimetypes.add_type("video/mp4", ".insv")

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8360
ROOT = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def end_headers(self):
        # Allow range requests so the browser can seek inside the video
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def do_GET(self):
        # Serve byte-range requests for video seeking
        if "Range" in self.headers:
            self.serve_range()
        else:
            super().do_GET()

    def serve_range(self):
        path = self.translate_path(self.path)
        if not os.path.isfile(path):
            self.send_error(404)
            return

        file_size = os.path.getsize(path)
        range_header = self.headers["Range"]  # e.g. "bytes=0-1023"
        byte_range = range_header.replace("bytes=", "").split("-")
        start = int(byte_range[0])
        end = int(byte_range[1]) if byte_range[1] else file_size - 1
        length = end - start + 1

        mime, _ = mimetypes.guess_type(path)
        self.send_response(206)
        self.send_header("Content-Type", mime or "application/octet-stream")
        self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
        self.send_header("Content-Length", str(length))
        self.end_headers()

        with open(path, "rb") as f:
            f.seek(start)
            self.wfile.write(f.read(length))

    def log_message(self, fmt, *args):
        # Suppress per-request noise; only print startup banner
        pass


if __name__ == "__main__":
    os.chdir(ROOT)
    with http.server.ThreadingHTTPServer(("", PORT), Handler) as httpd:
        print(f"  360 viewer  →  http://localhost:{PORT}")
        print(f"  Ctrl-C to stop\n")
        httpd.serve_forever()
