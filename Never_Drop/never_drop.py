"""
⚡ NEVER DROP - Ultra-fast AirDrop for PC to Phone / Phone to PC
Part of the Never Ecosystem.
"""

import os
import sys
import time
import socket
import threading
import mimetypes
import html
import subprocess
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
import qrcode

try:
    import windnd
    HAS_WINDND = True
except ImportError:
    HAS_WINDND = False

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RECEIVED_DIR = os.path.join(SCRIPT_DIR, "Received")
os.makedirs(RECEIVED_DIR, exist_ok=True)
ICON_PATH = os.path.join(SCRIPT_DIR, "never_drop.ico")

def get_lan_ip():
    """Detect local LAN IP (e.g. 192.168.x.x or 172.x.x.x)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None):
            ip = info[4][0]
            if ip.startswith(('192.168.', '10.', '172.')):
                return ip
    except Exception:
        pass
    return "127.0.0.1"

def format_size(bytes_num):
    """Format bytes to human readable string (KB, MB, GB)."""
    if bytes_num is None:
        return "Unknown size"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:.1f} {unit}" if unit != 'B' else f"{int(bytes_num)} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.1f} PB"

def get_file_category(filename):
    """Return category and icon representation."""
    ext = os.path.splitext(filename)[1].lower()
    if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp', '.ico']:
        return 'image', '🖼️'
    elif ext in ['.mp4', '.mkv', '.webm', '.mov', '.avi']:
        return 'video', '🎬'
    elif ext in ['.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac']:
        return 'audio', '🎵'
    elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
        return 'archive', '📦'
    elif ext in ['.pdf', '.doc', '.docx', '.txt', '.md', '.csv', '.xlsx']:
        return 'document', '📄'
    elif ext in ['.py', '.js', '.html', '.css', '.json', '.c', '.cpp', '.java']:
        return 'code', '💻'
    elif ext in ['.apk']:
        return 'android', '📱'
    elif ext in ['.exe', '.msi']:
        return 'application', '⚙️'
    return 'file', '📁'

# ==============================================================================
# HTTP SERVER & MOBILE WEB INTERFACE
# ==============================================================================

class DropHTTPHandler(BaseHTTPRequestHandler):
    shared_file = None      # Absolute path to shared file
    shared_files = []      # List of shared files if multiple
    on_upload_callback = None

    def log_message(self, format, *args):
        # Silent or lightweight logging
        pass

    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Range')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)

        if path in ['/', '/index.html']:
            self.serve_landing_page()
        elif path == '/download':
            self.serve_file(as_attachment=True)
        elif path.startswith('/download/'):
            self.serve_file(as_attachment=True)
        elif path == '/preview':
            self.serve_file(as_attachment=False)
        elif path == '/status':
            self.serve_status()
        else:
            self.send_error(404, "Not Found")

    def serve_landing_page(self):
        if not self.shared_file or not os.path.exists(self.shared_file):
            content = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Never Drop</title>
<style>
body { background:#0a0b10; color:#fff; font-family:system-ui,sans-serif; text-align:center; padding:40px 20px; }
.card { background:#151828; padding:30px; border-radius:20px; border:1px solid #222942; max-width:400px; margin:0 auto; }
</style></head>
<body>
<div class="card">
  <h2>⚡ Never Drop</h2>
  <p style="color:#94a3b8">Файл ещё не выбран на ПК.<br>Перетащите файл в окно Never Drop на компьютере.</p>
</div>
</body></html>"""
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(content.encode('utf-8'))))
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
            return

        filename = os.path.basename(self.shared_file)
        file_size = os.path.getsize(self.shared_file)
        size_str = format_size(file_size)
        category, cat_icon = get_file_category(filename)
        safe_name = html.escape(filename)
        encoded_name = urllib.parse.quote(filename)

        preview_html = ""
        if category == 'image':
            preview_html = f'''
            <div class="preview-box">
                <img src="/preview" alt="{safe_name}" class="img-preview" />
            </div>
            '''
        elif category == 'audio':
            preview_html = f'''
            <div class="preview-box">
                <audio controls src="/preview" class="media-preview"></audio>
            </div>
            '''
        elif category == 'video':
            preview_html = f'''
            <div class="preview-box">
                <video controls playsinline src="/preview" class="media-preview"></video>
            </div>
            '''

        html_template = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Never Drop ⚡ {safe_name}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: radial-gradient(circle at top, #15162a 0%, #08090e 100%);
            color: #f8fafc;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 24px 16px;
        }}
        .container {{
            width: 100%;
            max-width: 440px;
            animation: fadeIn 0.4s ease-out;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(12px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .brand {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            margin-bottom: 24px;
        }}
        .brand-icon {{
            font-size: 28px;
            filter: drop-shadow(0 0 12px #00f0ff);
        }}
        .brand-title {{
            font-size: 22px;
            font-weight: 800;
            background: linear-gradient(135deg, #00f0ff, #a855f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.5px;
        }}
        .card {{
            background: rgba(22, 27, 46, 0.75);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 26px;
            padding: 26px 22px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1);
            text-align: center;
            margin-bottom: 20px;
        }}
        .file-icon-wrap {{
            width: 72px;
            height: 72px;
            margin: 0 auto 16px;
            border-radius: 20px;
            background: linear-gradient(135deg, rgba(0, 240, 255, 0.15), rgba(168, 85, 247, 0.15));
            border: 1px solid rgba(0, 240, 255, 0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 34px;
            box-shadow: 0 0 20px rgba(0, 240, 255, 0.2);
        }}
        .filename {{
            font-size: 18px;
            font-weight: 700;
            line-height: 1.35;
            word-break: break-all;
            margin-bottom: 8px;
            color: #ffffff;
        }}
        .filesize {{
            font-size: 13px;
            font-weight: 600;
            color: #38bdf8;
            margin-bottom: 18px;
            display: inline-block;
            background: rgba(56, 189, 248, 0.12);
            padding: 4px 14px;
            border-radius: 20px;
            border: 1px solid rgba(56, 189, 248, 0.2);
        }}
        .preview-box {{
            margin: 14px 0 20px;
            border-radius: 16px;
            overflow: hidden;
            background: #000;
            max-height: 260px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .img-preview {{
            max-width: 100%;
            max-height: 260px;
            object-fit: contain;
            display: block;
        }}
        .media-preview {{
            width: 100%;
            border-radius: 10px;
        }}
        .btn-download {{
            display: block;
            width: 100%;
            padding: 16px 20px;
            font-size: 16px;
            font-weight: 700;
            color: #030712;
            background: linear-gradient(135deg, #00f0ff 0%, #38bdf8 100%);
            border: none;
            border-radius: 16px;
            text-decoration: none;
            cursor: pointer;
            box-shadow: 0 8px 24px rgba(0, 240, 255, 0.35);
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        .btn-download:active {{
            transform: scale(0.97);
            filter: brightness(0.9);
        }}
        /* Two-way transfer / Upload from Phone */
        .upload-card {{
            background: rgba(18, 22, 38, 0.6);
            border: 1px dashed rgba(255, 255, 255, 0.15);
            border-radius: 22px;
            padding: 20px;
            text-align: center;
        }}
        .upload-title {{
            font-size: 14px;
            font-weight: 700;
            color: #cbd5e1;
            margin-bottom: 4px;
        }}
        .upload-desc {{
            font-size: 12px;
            color: #64748b;
            margin-bottom: 14px;
        }}
        .btn-upload-label {{
            display: inline-block;
            background: #1e243b;
            color: #a855f7;
            border: 1px solid rgba(168, 85, 247, 0.35);
            padding: 10px 18px;
            border-radius: 12px;
            font-size: 13px;
            font-weight: 700;
            cursor: pointer;
            transition: 0.2s;
        }}
        .btn-upload-label:active {{
            background: #2b3353;
        }}
        #uploadInput {{
            display: none;
        }}
        .upload-status {{
            margin-top: 10px;
            font-size: 12px;
            display: none;
        }}
        .footer {{
            text-align: center;
            font-size: 11px;
            color: #475569;
            margin-top: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="brand">
            <span class="brand-icon">⚡</span>
            <span class="brand-title">NEVER DROP</span>
        </div>

        <div class="card">
            <div class="file-icon-wrap">{cat_icon}</div>
            <div class="filename">{safe_name}</div>
            <div class="filesize">💾 {size_str}</div>

            {preview_html}

            <a href="/download/{encoded_name}" download="{safe_name}" class="btn-download">
                📥 Скачать файл на телефон
            </a>
        </div>

        <!-- Phone to PC Reverse AirDrop -->
        <div class="upload-card">
            <div class="upload-title">📤 Отправить файл обратно на ПК</div>
            <div class="upload-desc">Выберите фото или документ со своего телефона</div>
            
            <label for="uploadInput" class="btn-upload-label" id="uploadBtnLabel">
                📱 Выбрать и отправить на ПК
            </label>
            <input type="file" id="uploadInput" onchange="uploadFile(this)">
            <div class="upload-status" id="uploadStatus"></div>
        </div>

        <div class="footer">
            Never Ecosystem • Локальная передача данных по Wi-Fi
        </div>
    </div>

    <script>
        function uploadFile(input) {{
            if (!input.files || input.files.length === 0) return;
            const file = input.files[0];
            const statusDiv = document.getElementById("uploadStatus");
            const btnLabel = document.getElementById("uploadBtnLabel");

            statusDiv.style.display = "block";
            statusDiv.style.color = "#38bdf8";
            statusDiv.innerHTML = "⏳ Отправка <b>" + file.name + "</b> (" + (file.size/1024/1024).toFixed(1) + " MB)...";
            btnLabel.style.opacity = "0.5";
            btnLabel.style.pointerEvents = "none";

            const xhr = new XMLHttpRequest();
            xhr.open("POST", "/upload", true);
            xhr.setRequestHeader("X-Filename", encodeURIComponent(file.name));

            xhr.upload.onprogress = function(e) {{
                if (e.lengthComputable) {{
                    const pct = Math.round((e.loaded / e.total) * 100);
                    statusDiv.innerHTML = "⏳ Отправка: " + pct + "% (" + file.name + ")";
                }}
            }};

            xhr.onload = function() {{
                btnLabel.style.opacity = "1";
                btnLabel.style.pointerEvents = "auto";
                if (xhr.status === 200) {{
                    statusDiv.style.color = "#4ade80";
                    statusDiv.innerHTML = "✅ Успешно доставлено на ПК в папку Received!";
                }} else {{
                    statusDiv.style.color = "#f87171";
                    statusDiv.innerHTML = "❌ Ошибка при передаче: " + xhr.statusText;
                }}
            }};

            xhr.onerror = function() {{
                btnLabel.style.opacity = "1";
                btnLabel.style.pointerEvents = "auto";
                statusDiv.style.color = "#f87171";
                statusDiv.innerHTML = "❌ Ошибка соединения!";
            }};

            xhr.send(file);
        }}
    </script>
</body>
</html>"""
        data = html_template.encode('utf-8')
        self.send_response(200)
        self.send_cors_headers()
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def serve_file(self, as_attachment=True):
        if not self.shared_file or not os.path.exists(self.shared_file):
            self.send_error(404, "File not found")
            return

        file_path = self.shared_file
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = 'application/octet-stream'

        # Check Range header
        range_header = self.headers.get('Range')
        start = 0
        end = file_size - 1

        if range_header and range_header.startswith('bytes='):
            try:
                ranges = range_header[6:].split('-')
                if ranges[0]:
                    start = int(ranges[0])
                if len(ranges) > 1 and ranges[1]:
                    end = int(ranges[1])
            except Exception:
                start = 0
                end = file_size - 1

        if start > end or start >= file_size:
            self.send_response(416, "Requested Range Not Satisfiable")
            self.send_header('Content-Range', f'bytes */{file_size}')
            self.end_headers()
            return

        chunk_size = end - start + 1
        is_partial = (start > 0 or end < file_size - 1)

        self.send_response(206 if is_partial else 200)
        self.send_cors_headers()
        self.send_header('Content-Type', mime_type)
        self.send_header('Accept-Ranges', 'bytes')

        if is_partial:
            self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')

        self.send_header('Content-Length', str(chunk_size))

        if as_attachment:
            # RFC 5987 encoded filename for all languages
            encoded = urllib.parse.quote(filename)
            self.send_header('Content-Disposition', f"attachment; filename*=UTF-8''{encoded}")
        else:
            self.send_header('Content-Disposition', 'inline')

        self.end_headers()

        # Stream chunk
        with open(file_path, 'rb') as f:
            f.seek(start)
            remaining = chunk_size
            buf_size = 64 * 1024
            while remaining > 0:
                read_len = min(remaining, buf_size)
                buf = f.read(read_len)
                if not buf:
                    break
                try:
                    self.wfile.write(buf)
                except (ConnectionResetError, BrokenPipeError):
                    break
                remaining -= len(buf)

    def serve_status(self):
        filename = os.path.basename(self.shared_file) if self.shared_file else None
        size = os.path.getsize(self.shared_file) if self.shared_file and os.path.exists(self.shared_file) else 0
        import json
        payload = json.dumps({
            "filename": filename,
            "size": size,
            "size_str": format_size(size)
        }).encode('utf-8')
        self.send_response(200)
        self.send_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/upload':
            raw_filename = self.headers.get('X-Filename')
            if raw_filename:
                filename = urllib.parse.unquote(raw_filename)
            else:
                filename = f"upload_{int(time.time())}.bin"

            # Clean filename
            filename = os.path.basename(filename)
            target_path = os.path.join(RECEIVED_DIR, filename)
            
            # Avoid overwriting
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(target_path):
                target_path = os.path.join(RECEIVED_DIR, f"{base}_{counter}{ext}")
                counter += 1

            content_length = int(self.headers.get('Content-Length', 0))
            bytes_left = content_length

            try:
                with open(target_path, 'wb') as f:
                    while bytes_left > 0:
                        chunk = self.rfile.read(min(bytes_left, 64 * 1024))
                        if not chunk:
                            break
                        f.write(chunk)
                        bytes_left -= len(chunk)

                if DropHTTPHandler.on_upload_callback:
                    DropHTTPHandler.on_upload_callback(target_path)

                resp = b'{"status": "ok"}'
                self.send_response(200)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(resp)))
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_error(500, f"Upload failed: {e}")
        else:
            self.send_error(404, "Not Found")


# ==============================================================================
# DROP SERVER CONTROLLER
# ==============================================================================

class NeverDropServer:
    def __init__(self, port=8848):
        self.lan_ip = get_lan_ip()
        self.port = port
        self.httpd = None
        self.server_thread = None
        self.current_file = None
        self._start_server()

    def _start_server(self):
        ports_to_try = [self.port, 8849, 8850, 8080, 8088, 0]
        for p in ports_to_try:
            try:
                self.httpd = HTTPServer(('0.0.0.0', p), DropHTTPHandler)
                self.port = self.httpd.server_port
                break
            except Exception:
                continue

        if not self.httpd:
            raise RuntimeError("Could not bind HTTP server to any port")

        self.server_thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.server_thread.start()

    def set_file(self, file_path):
        self.current_file = os.path.abspath(file_path) if file_path else None
        DropHTTPHandler.shared_file = self.current_file

    def get_url(self):
        return f"http://{self.lan_ip}:{self.port}/"

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()


# ==============================================================================
# NEVER DROP GUI (GLASSMORPHIC CUSTOMTKINTER)
# ==============================================================================

class NeverDropUI(ctk.CTk):
    def __init__(self, initial_file=None):
        super().__init__()

        self.server = NeverDropServer(port=8848)
        self.current_file = None

        self.title("⚡ Never Drop - AirDrop for PC")
        self.geometry("440x630")
        self.resizable(False, False)
        
        # Center on screen
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        cx = int((sw - 440) / 2)
        cy = int((sh - 630) / 2)
        self.geometry(f"+{cx}+{cy}")

        if os.path.exists(ICON_PATH):
            try:
                self.iconbitmap(ICON_PATH)
            except Exception:
                pass

        ctk.set_appearance_mode("dark")
        self.configure(fg_color="#0a0b12")

        # Top Bar
        self.top_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.top_bar.pack(fill="x", padx=20, pady=(18, 10))

        self.logo_lbl = ctk.CTkLabel(
            self.top_bar,
            text="⚡ NEVER DROP",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#00f0ff"
        )
        self.logo_lbl.pack(side="left")

        self.status_pill = ctk.CTkLabel(
            self.top_bar,
            text=f"● {self.server.lan_ip}:{self.server.port}",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#141829",
            text_color="#4ade80",
            corner_radius=12,
            padx=10,
            pady=3
        )
        self.status_pill.pack(side="right")

        # QR Code Card
        self.qr_card = ctk.CTkFrame(
            self,
            fg_color="#121526",
            border_width=1,
            border_color="#1e2440",
            corner_radius=18
        )
        self.qr_card.pack(fill="x", padx=20, pady=6)

        self.qr_label = tk.Label(self.qr_card, bg="#121526", highlightthickness=0)
        self.qr_label.pack(pady=(16, 8))

        self.qr_hint = ctk.CTkLabel(
            self.qr_card,
            text="📱 Отсканируйте камерой смартфона (iPhone / Android)",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#94a3b8"
        )
        self.qr_hint.pack(pady=(0, 14))

        # File Info Card
        self.file_card = ctk.CTkFrame(
            self,
            fg_color="#121526",
            border_width=1,
            border_color="#1e2440",
            corner_radius=16
        )
        self.file_card.pack(fill="x", padx=20, pady=8)

        self.file_icon_lbl = ctk.CTkLabel(
            self.file_card,
            text="📁",
            font=ctk.CTkFont(size=26),
            width=36
        )
        self.file_icon_lbl.pack(side="left", padx=(14, 8), pady=12)

        self.file_meta_frame = ctk.CTkFrame(self.file_card, fg_color="transparent")
        self.file_meta_frame.pack(side="left", fill="both", expand=True, pady=10)

        self.filename_lbl = ctk.CTkLabel(
            self.file_meta_frame,
            text="Перетащите файл сюда",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#ffffff",
            anchor="w"
        )
        self.filename_lbl.pack(fill="x")

        self.filesize_lbl = ctk.CTkLabel(
            self.file_meta_frame,
            text="или нажмите кнопку «Выбрать файл»",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#64748b",
            anchor="w"
        )
        self.filesize_lbl.pack(fill="x")

        # URL and Copy row
        self.url_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.url_frame.pack(fill="x", padx=20, pady=(4, 8))

        self.url_entry = ctk.CTkEntry(
            self.url_frame,
            height=34,
            corner_radius=10,
            fg_color="#121526",
            border_color="#1e2440",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color="#38bdf8"
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.copy_btn = ctk.CTkButton(
            self.url_frame,
            text="📋 Копировать",
            width=110,
            height=34,
            corner_radius=10,
            fg_color="#1e2440",
            hover_color="#2b345c",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#f8fafc",
            command=self.copy_link
        )
        self.copy_btn.pack(side="right")

        # Bottom Actions Frame
        self.btn_row = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_row.pack(fill="x", padx=20, pady=8)

        self.pick_btn = ctk.CTkButton(
            self.btn_row,
            text="📂 Выбрать файл",
            height=38,
            corner_radius=12,
            fg_color="#0284c7",
            hover_color="#0369a1",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self.browse_file
        )
        self.pick_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.browser_btn = ctk.CTkButton(
            self.btn_row,
            text="🌐 В браузере",
            height=38,
            corner_radius=12,
            fg_color="#1e2440",
            hover_color="#2b345c",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self.open_in_browser
        )
        self.browser_btn.pack(side="right", fill="x", expand=True, padx=(6, 0))

        # Received files folder link
        self.received_btn = ctk.CTkButton(
            self,
            text="📥 Открыть полученные файлы (Received)",
            height=30,
            corner_radius=10,
            fg_color="transparent",
            hover_color="#121526",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#94a3b8",
            command=self.open_received_folder
        )
        self.received_btn.pack(fill="x", padx=20, pady=(2, 6))

        # Hook upload callback
        DropHTTPHandler.on_upload_callback = self.on_file_received_from_phone

        # Hook Windows Drag & Drop if available
        if HAS_WINDND:
            try:
                windnd.hook_dropfiles(self, func=self.on_files_dropped, force_unicode=True)
            except Exception as e:
                print("windnd hook notice:", e)

        # Initial file load
        if initial_file and os.path.exists(initial_file):
            self.load_file(initial_file)
        else:
            self.update_qr_and_info()

    def generate_qr(self, text):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=6,
            border=2,
        )
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#00f0ff", back_color="#121526").convert("RGB")
        return ImageTk.PhotoImage(img)

    def update_qr_and_info(self):
        url = self.server.get_url()
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, url)

        self.qr_photo = self.generate_qr(url)
        self.qr_label.configure(image=self.qr_photo)

        if self.current_file and os.path.exists(self.current_file):
            name = os.path.basename(self.current_file)
            size = os.path.getsize(self.current_file)
            cat, icon = get_file_category(name)

            self.file_icon_lbl.configure(text=icon)
            display_name = name if len(name) <= 32 else name[:16] + "..." + name[-13:]
            self.filename_lbl.configure(text=display_name)
            self.filesize_lbl.configure(text=f"Размер: {format_size(size)} • Готов к передаче")
        else:
            self.file_icon_lbl.configure(text="📥")
            self.filename_lbl.configure(text="Перетащите файл в это окно")
            self.filesize_lbl.configure(text="Любые фото, видео, документы или архивы")

    def load_file(self, file_path):
        if not file_path or not os.path.exists(file_path):
            return
        self.current_file = os.path.abspath(file_path)
        self.server.set_file(self.current_file)
        self.update_qr_and_info()
        self.lift()
        self.focus_force()

    def on_files_dropped(self, files):
        if files:
            first_file = files[0]
            if isinstance(first_file, bytes):
                first_file = first_file.decode('utf-8', errors='ignore')
            self.after(0, lambda: self.load_file(first_file))

    def browse_file(self):
        file_selected = filedialog.askopenfilename(title="Выберите файл для Never Drop")
        if file_selected:
            self.load_file(file_selected)

    def copy_link(self):
        url = self.server.get_url()
        self.clipboard_clear()
        self.clipboard_append(url)
        self.copy_btn.configure(text="✨ Скопировано!", fg_color="#059669")
        self.after(2000, lambda: self.copy_btn.configure(text="📋 Копировать", fg_color="#1e2440"))

    def open_in_browser(self):
        import webbrowser
        webbrowser.open(self.server.get_url())

    def open_received_folder(self):
        os.startfile(RECEIVED_DIR)

    def on_file_received_from_phone(self, saved_path):
        fname = os.path.basename(saved_path)
        self.after(0, lambda: self.show_received_toast(fname))

    def show_received_toast(self, filename):
        self.received_btn.configure(
            text=f"🎉 Получен файл с телефона: {filename}! Нажмите, чтобы открыть",
            text_color="#4ade80"
        )
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass


# ==============================================================================
# INTEGRATION API
# ==============================================================================

def share_file(file_path):
    """
    Launch Never Drop to share a file.
    Can be called directly from Python modules (Dynamic Island, Cyber Pet, etc.).
    Spawns Never Drop as an independent process so caller UI never blocks.
    """
    file_path = os.path.abspath(file_path)
    python_exe = sys.executable
    script_path = os.path.abspath(__file__)

    # Prefer pythonw.exe if available to hide console
    pythonw = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
    exe = pythonw if os.path.exists(pythonw) else python_exe

    subprocess.Popen([exe, script_path, file_path], cwd=SCRIPT_DIR)
    return True

if __name__ == "__main__":
    target_file = None
    if len(sys.argv) > 1:
        target_file = sys.argv[1]

    app = NeverDropUI(initial_file=target_file)
    app.mainloop()
