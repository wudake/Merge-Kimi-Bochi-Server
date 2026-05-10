#!/usr/bin/env python3
"""
视频传输模块 - 生成二维码便于手机下载
"""
import qrcode
import socket
from pathlib import Path
from urllib.parse import quote


def get_lan_ip():
    """获取局域网 IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def generate_video_qr(video_filename: str, port: int = 5000, output_dir: str = "static") -> dict:
    """
    为视频生成二维码
    
    Args:
        video_filename: 视频文件名
        port: 服务端口
        output_dir: 二维码输出目录
    
    Returns:
        {
            "qr_path": 二维码图片路径,
            "download_url": 下载链接,
            "lan_ip": 局域网IP
        }
    """
    lan_ip = get_lan_ip()
    
    # 构建下载链接
    encoded_name = quote(video_filename)
    download_url = f"http://{lan_ip}:{port}/api/download/edited/{encoded_name}"
    
    # 生成二维码
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(download_url)
    qr.make(fit=True)
    
    # 保存二维码
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    qr_filename = f"qr_{video_filename}.png"
    qr_path = output_path / qr_filename
    
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(qr_path)
    
    return {
        "qr_path": str(qr_path),
        "qr_filename": qr_filename,
        "download_url": download_url,
        "lan_ip": lan_ip,
        "port": port
    }


def generate_snapdrop_url() -> str:
    """生成 Snapdrop 链接，用于快速传输"""
    return "https://snapdrop.net"


if __name__ == "__main__":
    # 测试
    result = generate_video_qr("test_video.mp4")
    print(f"二维码已生成: {result['qr_path']}")
    print(f"下载地址: {result['download_url']}")
