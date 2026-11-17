import os
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = 8088
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if __name__ == "__main__":
    os.chdir(ROOT)
    url = f"http://localhost:{PORT}/index.html"
    print(f"Serving Pokemon Game Land at {url}")
    webbrowser.open(url)
    HTTPServer(("0.0.0.0", PORT), SimpleHTTPRequestHandler).serve_forever()
