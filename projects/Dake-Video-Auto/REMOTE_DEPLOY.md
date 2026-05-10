# Dake-Video-Auto 远程服务器部署指南

本文档介绍如何将 Dake-Video-Auto 项目部署到远程 Linux 服务器。

## 📋 系统要求

- **操作系统**: Linux (Ubuntu 20.04+ / CentOS 7+ / Debian 10+)
- **Python**: 3.8+
- **内存**: 至少 2GB RAM (推荐 4GB)
- **磁盘**: 至少 10GB 可用空间
- **网络**: 公网 IP 或域名 (用于二维码传输功能)

---

## 🚀 快速部署步骤

### 1. 连接服务器

```bash
ssh user@your-server-ip
```

### 2. 安装基础依赖

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv ffmpeg git

# Playwright 依赖
sudo apt install -y libnss3 libatk-bridge2.0-0 libxcomposite1 libxdamage1 \
    libxrandr2 libgbm1 libasound2 libxss1 libgtk-3-0
```

**CentOS/RHEL:**
```bash
sudo yum update
sudo yum install -y python3 python3-pip ffmpeg git

# Playwright 依赖
sudo yum install -y nss atk at-spi2-atk libXcomposite libXdamage \
    libXrandr mesa-libgbm alsa-lib libXScrnSaver gtk3
```

### 3. 克隆项目

```bash
cd /opt  # 或你想部署的目录
sudo git clone https://github.com/wudake/Dake-Video-Auto.git
cd Dake-Video-Auto
sudo chown -R $USER:$USER .
```

### 4. 安装 Python 依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
```

### 5. 创建目录结构

```bash
mkdir -p videos/raw videos/configs output assets/logos assets/bgm config logs static
```

### 6. 开放防火墙端口

```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 5000/tcp
sudo ufw reload

# CentOS (firewalld)
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload

# 或 iptables
sudo iptables -I INPUT -p tcp --dport 5000 -j ACCEPT
sudo iptables-save
```

---

## ⚙️ Systemd 服务配置 (推荐)

### 创建服务文件

```bash
sudo tee /etc/systemd/system/dake-video.service > /dev/null << 'EOF'
[Unit]
Description=Dake Video Auto Tool v4.6.0
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/Dake-Video-Auto
Environment="PATH=/opt/Dake-Video-Auto/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/opt/Dake-Video-Auto/venv/bin/python /opt/Dake-Video-Auto/app_simple.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
```

### 启用并启动服务

```bash
sudo systemctl daemon-reload
sudo systemctl enable dake-video
sudo systemctl start dake-video

# 检查状态
sudo systemctl status dake-video

# 查看日志
sudo journalctl -u dake-video -f
```

---

## 🔒 Nginx 反向代理 (可选)

### 安装 Nginx

```bash
# Ubuntu/Debian
sudo apt install -y nginx

# CentOS
sudo yum install -y nginx
```

### 配置 Nginx

创建配置文件 `/etc/nginx/sites-available/dake-video`:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名

    client_max_body_size 500M;  # 允许大文件上传

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 视频流优化
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # 静态文件缓存
    location /static {
        alias /opt/Dake-Video-Auto/static;
        expires 1d;
    }
}
```

启用配置:
```bash
sudo ln -s /etc/nginx/sites-available/dake-video /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # 删除默认配置
sudo nginx -t  # 测试配置
sudo systemctl restart nginx
```

---

## 🔐 HTTPS 配置 (Let's Encrypt)

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期测试
sudo certbot renew --dry-run
```

---

## 🌐 二维码传输配置

远程服务器的二维码功能需要特殊配置，因为默认使用局域网 IP。

### 方案 1: 公网 IP 直接访问

修改 `core/video_transfer.py` 中的 `get_lan_ip()` 函数，返回服务器公网 IP:

```python
def get_lan_ip():
    """获取服务器公网 IP"""
    return "your-server-public-ip"  # 替换为你的公网 IP
```

### 方案 2: 使用域名

如果使用域名，修改二维码生成逻辑:

```python
def generate_video_qr(video_filename: str, port: int = 5000, output_dir: str = "static") -> dict:
    domain = "your-domain.com"  # 替换为你的域名
    download_url = f"http://{domain}/api/download/edited/{encoded_name}"
    # ...
```

### 方案 3: 内网穿透 (开发测试)

使用 frp 或 ngrok 进行内网穿透:

```bash
# 安装 frp
wget https://github.com/fatedier/frp/releases/download/v0.52.3/frp_0.52.3_linux_amd64.tar.gz
tar -xzf frp_0.52.3_linux_amd64.tar.gz

# 配置 frpc.ini
[common]
server_addr = your-frp-server.com
server_port = 7000
token = your-token

[dake-video]
type = http
local_port = 5000
custom_domains = dake-video.your-domain.com
```

---

## 📁 目录结构

```
/opt/Dake-Video-Auto/
├── venv/                  # Python 虚拟环境
├── app_simple.py          # 主应用
├── core/                  # 核心模块
│   ├── editor_advanced.py # 视频编辑器
│   └── video_transfer.py  # 二维码传输
├── templates/             # HTML 模板
├── static/                # 二维码图片
├── videos/
│   └── raw/               # 原始下载视频
├── output/                # 剪辑后视频输出
├── assets/
│   ├── logos/             # Logo 文件
│   └── bgm/               # BGM 文件
├── config/                # 配置文件
├── logs/                  # 日志文件
├── requirements.txt       # Python 依赖
└── DEPLOY.md              # 本部署文档
```

---

## 🔧 常用命令

```bash
# 启动服务
sudo systemctl start dake-video

# 停止服务
sudo systemctl stop dake-video

# 重启服务
sudo systemctl restart dake-video

# 查看状态
sudo systemctl status dake-video

# 查看日志
sudo journalctl -u dake-video -f

# 查看最近的剪辑日志
ls -lt logs/edit_*.log | head -5
tail -f logs/edit_$(date +%Y%m%d)*.log
```

---

## 🐛 常见问题

### 1. Playwright 安装失败

```bash
# 安装完整系统依赖 (Ubuntu)
sudo apt install -y libnss3 libatk-bridge2.0-0 libxcomposite1 libxdamage1 \
    libxrandr2 libgbm1 libasound2 libxss1 libgtk-3-0 libpangocairo-1.0-0 \
    libpango-1.0-0 libatk1.0-0 libcairo-gobject2 libcairo2 libgdk-pixbuf2.0-0

# 重新安装 Playwright
playwright install chromium
```

### 2. FFmpeg 未找到

```bash
# 检查安装
which ffmpeg
ffmpeg -version

# 如果没有，安装
sudo apt install -y ffmpeg
```

### 3. 端口被占用

```bash
# 查找占用 5000 端口的进程
sudo lsof -i :5000

# 杀死进程
sudo kill -9 <PID>
```

### 4. 权限问题

```bash
# 确保目录可写
chmod -R 755 output videos assets logs static

# 更改所有者
sudo chown -R $USER:$USER /opt/Dake-Video-Auto
```

### 5. 内存不足导致剪辑失败

```bash
# 添加 Swap 空间
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 永久生效
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 6. 二维码无法访问

检查服务器防火墙和安全组设置，确保端口 5000 (或 80/443) 已开放。

---

## 🔄 更新项目

```bash
cd /opt/Dake-Video-Auto
sudo systemctl stop dake-video
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl start dake-video
```

---

## 🗑️ 卸载

```bash
# 停止并禁用服务
sudo systemctl stop dake-video
sudo systemctl disable dake-video
sudo rm /etc/systemd/system/dake-video.service
sudo systemctl daemon-reload

# 删除项目
cd /opt
sudo rm -rf Dake-Video-Auto

# 如果使用 Nginx
sudo rm /etc/nginx/sites-enabled/dake-video
sudo systemctl restart nginx
```

---

## 📞 支持与反馈

- GitHub Issues: https://github.com/wudake/Dake-Video-Auto/issues
- 版本: v4.6.0
