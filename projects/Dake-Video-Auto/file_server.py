#!/usr/bin/env python3
"""
简单文件传输服务器 - 用于局域网手机下载
"""
import http.server
import socketserver
import os
from pathlib import Path

PORT = 8080
DIRECTORY = "/home/dake/Dake-Video-Auto/output"

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # 允许跨域访问
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

if __name__ == "__main__":
    import socket
    
    # 获取局域网 IP
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        lan_ip = s.getsockname()[0]
    except:
        lan_ip = "127.0.0.1"
    finally:
        s.close()
    
    os.chdir(DIRECTORY)
    
    with socketserver.TCPServer(("0.0.0.0", PORT), MyHTTPRequestHandler) as httpd:
        print(f"🚀 文件服务器已启动!")
        print(f"📱 手机访问地址: http://{lan_ip}:{PORT}")
        print(f"📁 共享目录: {DIRECTORY}")
        print(f"\n可用文件:")
        
        for f in sorted(Path(DIRECTORY).glob("*.mp4")):
            size_mb = f.stat().st_size / 1024 / 1024
            print(f"  - {f.name} ({size_mb:.1f}MB)")
        
        print(f"\n按 Ctrl+C 停止服务")
        httpd.serve_forever()
