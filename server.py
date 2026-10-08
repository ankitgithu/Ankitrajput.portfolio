import http.server
import socketserver
import json
import os

PORT = 3000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

YOUTUBE_REELS = [
    {"id": "m4MJV9_BFkw", "url": "https://youtube.com/shorts/m4MJV9_BFkw", "name": "Featured Reel 01"},
    {"id": "jBYWbSXNLeQ", "url": "https://youtube.com/shorts/jBYWbSXNLeQ", "name": "Featured Reel 02"},
    {"id": "Be-HGltJ4Gs", "url": "https://youtube.com/shorts/Be-HGltJ4Gs", "name": "Featured Reel 03"},
    {"id": "m4MJV9_BFkw", "url": "https://youtube.com/shorts/m4MJV9_BFkw", "name": "Featured Reel 04"},
    {"id": "xFdG1F6j6SE", "url": "https://youtube.com/shorts/xFdG1F6j6SE", "name": "Featured Reel 05"}
]

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path.startswith('/api/reels'):
            data = json.dumps(YOUTUBE_REELS).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        super().do_GET()

def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
