import http.server
import socketserver
import urllib.request
import re
import json
import time
import os

PORT = 3000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
DRIVE_FOLDER_ID = "1dJ0XPs_FFFI615obXlhAMeFwj7ID9s9J"
DRIVE_URL = f"https://drive.google.com/drive/folders/{DRIVE_FOLDER_ID}?usp=sharing"

# Cache for drive videos (refresh every 20 seconds or on demand)
_cache_time = 0
_cached_videos = []

def clean_title(n):
    n = n.replace(r'\u0026', '&')
    n = re.sub(r'\.(?:mp4|mov|webm|m4v|avi|mkv)', '', n, flags=re.IGNORECASE)
    n = n.replace('_', ' ').replace('-', ' ').strip()
    words = [w.capitalize() for w in n.split()]
    return ' '.join(words)

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s['name'])]

def fetch_drive_videos():
    global _cache_time, _cached_videos
    if time.time() - _cache_time < 20 and _cached_videos:
        return _cached_videos

    try:
        req = urllib.request.Request(DRIVE_URL, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        })
        with urllib.request.urlopen(req, timeout=12) as response:
            html = response.read().decode('utf-8', errors='ignore')

        items = []
        seen = set()

        # Method 1: <tr data-id="..."
        rows = re.findall(r'<tr[^>]*?data-id=\"([a-zA-Z0-9_-]{25,45})\"[^>]*?>([\s\S]*?)<\/tr>', html)
        for idx, (fid, row_html) in enumerate(rows, 1):
            if fid not in seen and fid != DRIVE_FOLDER_ID:
                seen.add(fid)
                name_m = re.search(r'data-tooltip-unhoverable=\"true\"[^>]*?>([^<]+)<', row_html)
                if not name_m:
                    name_m = re.search(r'\[\[\[\"([^\"]+)\"', row_html)
                name = clean_title(name_m.group(1)) if name_m else f"Reel {idx:02d}"
                items.append({'id': fid, 'name': name})

        # Method 2: Regex pattern for data items
        pattern1 = re.compile(r'\[\[null,\"([a-zA-Z0-9_-]{25,45})\"]\].*?\[\[\[\"([^\"]+)\"', re.DOTALL)
        for m in pattern1.finditer(html):
            fid = m.group(1)
            name = clean_title(m.group(2))
            if fid not in seen and fid != DRIVE_FOLDER_ID:
                seen.add(fid)
                items.append({'id': fid, 'name': name})

        # Method 3: Any data-id elements in table/grid
        for m in re.finditer(r'data-id=\"([a-zA-Z0-9_-]{25,45})\"', html):
            fid = m.group(1)
            if fid not in seen and fid != DRIVE_FOLDER_ID:
                seen.add(fid)
                items.append({'id': fid, 'name': f"Reel {len(items)+1:02d}"})

        # Strictly sort by Name in ascending A to Z order
        items.sort(key=natural_sort_key)

        if items:
            _cached_videos = items
            _cache_time = time.time()
            return _cached_videos
    except Exception as e:
        print(f"Error fetching from Drive: {e}")

    return _cached_videos

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path.startswith('/api/reels'):
            videos = fetch_drive_videos()
            data = json.dumps(videos).encode('utf-8')
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
        print(f"Dynamic Reel Server running at http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
