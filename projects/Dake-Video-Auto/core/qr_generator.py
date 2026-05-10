"""
二维码生成模块 - 用于手机扫码下载视频
"""
import qrcode
from pathlib import Path
from PIL import Image
import socket


def get_local_ip():
    """获取本机局域网IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def generate_qr_code(data, output_path, size=10, border=2):
    """
    生成二维码
    
    Args:
        data: 二维码内容（URL）
        output_path: 输出文件路径
        size: 二维码大小
        border: 边框宽度
    
    Returns:
        输出文件路径
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_path)
    return str(output_path)


def generate_video_qr(video_filename, port=5000, output_dir="static", base_url=None):
    """
    生成视频下载二维码
    
    Args:
        video_filename: 视频文件名
        port: 服务端口
        output_dir: 二维码输出目录
        base_url: 基础URL（可选，默认自动获取局域网IP）
    
    Returns:
        dict: {
            "qr_filename": 二维码文件名,
            "qr_path": 二维码文件路径,
            "download_url": 下载URL,
            "local_ip": 本机IP
        }
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取本机IP
    local_ip = get_local_ip()
    
    # 构建下载URL
    if base_url:
        download_url = f"{base_url}/api/download/edited/{video_filename}"
    else:
        download_url = f"http://{local_ip}:{port}/api/download/edited/{video_filename}"
    
    # 生成二维码文件名
    qr_filename = f"qr_{video_filename.replace('.mp4', '')}.png"
    qr_path = output_dir / qr_filename
    
    # 生成二维码
    generate_qr_code(download_url, qr_path)
    
    return {
        "qr_filename": qr_filename,
        "qr_path": str(qr_path),
        "download_url": download_url,
        "local_ip": local_ip
    }


def generate_preview_qr(video_filename, port=5000, output_dir="static", base_url=None):
    """
    生成视频预览二维码（在线播放）
    
    Args:
        video_filename: 视频文件名
        port: 服务端口
        output_dir: 二维码输出目录
        base_url: 基础URL（可选）
    
    Returns:
        dict: 二维码信息
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    local_ip = get_local_ip()
    
    if base_url:
        preview_url = f"{base_url}/api/preview/{video_filename}"
    else:
        preview_url = f"http://{local_ip}:{port}/api/preview/{video_filename}"
    
    qr_filename = f"qr_preview_{video_filename.replace('.mp4', '')}.png"
    qr_path = output_dir / qr_filename
    
    generate_qr_code(preview_url, qr_path)
    
    return {
        "qr_filename": qr_filename,
        "qr_path": str(qr_path),
        "preview_url": preview_url,
        "local_ip": local_ip
    }


if __name__ == "__main__":
    # 测试
    result = generate_video_qr("test_video.mp4", port=5000)
    print(f"✅ 二维码生成成功!")
    print(f"📱 下载地址: {result['download_url']}")
    print(f"🖼️ 二维码文件: {result['qr_path']}")
    print(f"🌐 本机IP: {result['local_ip']}")
