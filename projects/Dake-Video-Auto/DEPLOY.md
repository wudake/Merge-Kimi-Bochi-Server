# Dake-Video-Auto 远程服务器部署指南

## 📋 部署概述

本文档详细介绍如何将 Dake-Video-Auto 部署到远程服务器（VPS/云服务器），支持 Ubuntu 20.04+/CentOS 7+ 系统。

---

## 🖥️ 服务器要求

### 最低配置
| 项目 | 要求 |
|------|------|
| **CPU** | 2核+ |
| **内存** | 4GB+ (推荐 8GB) |
| **磁盘** | 50GB+ SSD |
| **带宽** | 5Mbps+ |
| **系统** | Ubuntu 20.04+ / CentOS 7+ / Debian 10+ |

### 推荐配置
| 项目 | 推荐配置 |
|------|----------|
| **CPU** | 4核+ |
| **内存** | 8GB+ |
| **磁盘** | 100GB+ SSD |
| **带宽** | 10Mbps+ |
| **系统** | Ubuntu 22.04 LTS |

---

## 🔧 第一步：服务器初始化

### 1.1 连接服务器

```bash
# 使用 SSH 连接服务器
ssh root@你的服务器IP

# 或使用密钥
ssh -i ~/.ssh/your_key.pem user@你的服务器IP
```

### 1.2 更新系统

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS
sudo yum update -y
```

### 1.3 安装基础工具

```bash
# Ubuntu/Debian
sudo apt install -y git curl wget vim htop net-tools unzip

# CentOS
sudo yum install -y git curl wget vim htop net-tools unzip
```

---

## 🐍 第二步：安装 Python 环境

### 2.1 安装 Python 3.10+

```bash
# Ubuntu 22.04 自带 Python 3.10
python3 --version

# Ubuntu 20.04 需要安装 Python 3.10
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3.10-dev python3-pip

# 设置默认 Python
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
```

### 2.2 安装 FFmpeg

```bash
# Ubuntu/Debian
sudo apt install -y ffmpeg

# 验证安装
ffmpeg -version

# 如果版本太旧，使用以下方式安装最新版
# Ubuntu
sudo add-apt-repository ppa:jonathonf/ffmpeg-4
sudo apt update
sudo apt install -y ffmpeg

# 或使用 snap
sudo snap install ffmpeg
```

---

## 📦 第三步：部署项目

### 3.1 创建项目目录

```bash
# 创建项目目录（建议使用非 root 用户）
sudo useradd -m -s /bin/bash videoauto
sudo usermod -aG sudo videoauto
su - videoauto

# 创建应用目录
mkdir -p ~/apps
cd ~/apps
```

### 3.2 克隆项目

```bash
# 克隆项目
git clone https://github.com/wudake/Dake-Video-Auto.git
cd Dake-Video-Auto

# 切换到最新版本
git checkout v5.0.0
```

### 3.3 创建虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 验证 Python 路径
which python
# 应该输出: /home/videoauto/apps/Dake-Video-Auto/venv/bin/python
```

### 3.4 安装依赖

```bash
# 升级 pip
pip install --upgrade pip

# 安装依赖（使用清华镜像加速）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 如果遇到权限问题
pip install -r requirements.txt --user
```

### 3.5 安装 Playwright

```bash
# 安装 Playwright
pip install playwright -i https://pypi.tuna.tsinghua.edu.cn/simple

# 安装 Chromium 浏览器
playwright install chromium

# 安装系统依赖（Ubuntu/Debian）
playwright install-deps chromium
```

---

## 🚀 第四步：启动服务

### 4.1 测试启动

```bash
# 确保在虚拟环境中
source venv/bin/activate

# 测试启动
python app_simple.py

# 看到以下输出表示成功：
# 🚀 启动服务: http://你的服务器IP:5000
#  * Running on all addresses (0.0.0.0)
```

**按 Ctrl+C 停止测试**

### 4.2 获取服务器IP

```bash
# 查看服务器公网IP
curl -s ifconfig.me
# 或
curl -s ip.sb
```

---

## ⚙️ 第五步：配置 systemd 服务（推荐）

### 5.1 创建服务文件

```bash
# 创建 systemd 服务文件
sudo tee /etc/systemd/system/videoauto.service > /dev/null <<EOF
[Unit]
Description=Dake Video Auto Service
After=network.target

[Service]
Type=simple
User=videoauto
Group=videoauto
WorkingDirectory=/home/videoauto/apps/Dake-Video-Auto
Environment=PATH=/home/videoauto/apps/Dake-Video-Auto/venv/bin
ExecStart=/home/videoauto/apps/Dake-Video-Auto/venv/bin/python app_simple.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=videoauto

[Install]
WantedBy=multi-user.target
EOF
```

### 5.2 启动并启用服务

```bash
# 重新加载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start videoauto

# 设置开机自启
sudo systemctl enable videoauto

# 查看服务状态
sudo systemctl status videoauto

# 查看日志
sudo journalctl -u videoauto -f
```

### 5.3 常用命令

```bash
# 启动服务
sudo systemctl start videoauto

# 停止服务
sudo systemctl stop videoauto

# 重启服务
sudo systemctl restart videoauto

# 查看状态
sudo systemctl status videoauto

# 查看日志
sudo journalctl -u videoauto -f --no-pager

# 查看最近100行日志
sudo journalctl -u videoauto -n 100 --no-pager
```

---

## 🌐 第六步：配置 Nginx 反向代理（可选）

### 6.1 安装 Nginx

```bash
# Ubuntu/Debian
sudo apt install -y nginx

# CentOS
sudo yum install -y nginx

# 启动 Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 6.2 配置 Nginx

```bash
# 创建配置文件
sudo tee /etc/nginx/sites-available/videoauto > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名或服务器IP

    client_max_body_size 500M;  # 允许上传大文件

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
    }

    location /static {
        alias /home/videoauto/apps/Dake-Video-Auto/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# 启用配置
sudo ln -s /etc/nginx/sites-available/videoauto /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6.3 配置 HTTPS（使用 Let's Encrypt）

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期测试
sudo certbot renew --dry-run
```

---

## 🔥 第七步：配置防火墙

### 7.1 UFW（Ubuntu）

```bash
# 安装 UFW
sudo apt install -y ufw

# 允许 SSH
sudo ufw allow 22/tcp

# 允许 HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 允许应用端口（如果不用 Nginx）
sudo ufw allow 5000/tcp

# 启用防火墙
sudo ufw enable

# 查看状态
sudo ufw status
```

### 7.2 Firewalld（CentOS）

```bash
# 允许端口
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload

# 查看状态
sudo firewall-cmd --list-all
```

---

## 📁 第八步：目录权限设置

```bash
# 确保目录权限正确
sudo chown -R videoauto:videoauto /home/videoauto/apps/Dake-Video-Auto

# 创建必要的目录
mkdir -p ~/apps/Dake-Video-Auto/{videos/raw,output,assets/{logos,bgm,tts},static,logs,config}

# 设置权限
chmod 755 ~/apps/Dake-Video-Auto
chmod 777 ~/apps/Dake-Video-Auto/output
chmod 777 ~/apps/Dake-Video-Auto/videos/raw
chmod 777 ~/apps/Dake-Video-Auto/static
chmod 777 ~/apps/Dake-Video-Auto/logs
```

---

## 🔄 第九步：更新项目

```bash
# 进入项目目录
cd ~/apps/Dake-Video-Auto

# 拉取最新代码
git pull origin main

# 更新依赖
source venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 重启服务
sudo systemctl restart videoauto

# 查看状态
sudo systemctl status videoauto
```

---

## 🐛 第十步：常见问题排查

### 问题1: 服务无法启动

```bash
# 检查日志
sudo journalctl -u videoauto -n 50 --no-pager

# 检查端口占用
sudo netstat -tlnp | grep 5000
# 或
sudo ss -tlnp | grep 5000

# 检查权限
ls -la ~/apps/Dake-Video-Auto/
```

### 问题2: FFmpeg 未找到

```bash
# 检查 FFmpeg
which ffmpeg
ffmpeg -version

# 如果没有安装
sudo apt install -y ffmpeg
```

### 问题3: Playwright 浏览器未安装

```bash
# 激活虚拟环境
source venv/bin/activate

# 重新安装浏览器
playwright install chromium
playwright install-deps chromium
```

### 问题4: 防火墙阻止访问

```bash
# 检查防火墙状态
sudo ufw status
# 或
sudo iptables -L

# 临时关闭防火墙测试（仅测试）
sudo ufw disable
```

### 问题5: 磁盘空间不足

```bash
# 查看磁盘空间
df -h

# 查看大文件
du -sh ~/apps/Dake-Video-Auto/*

# 清理日志
sudo journalctl --vacuum-time=7d
```

---

## 📝 第十一步：监控与维护

### 11.1 查看系统资源

```bash
# CPU/内存监控
htop

# 磁盘使用
df -h

# 内存使用
free -h

# 查看进程
ps aux | grep python
```

### 11.2 日志轮转

```bash
# 创建日志轮转配置
sudo tee /etc/logrotate.d/videoauto > /dev/null <<EOF
/home/videoauto/apps/Dake-Video-Auto/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 videoauto videoauto
}
EOF

# 测试配置
sudo logrotate -d /etc/logrotate.d/videoauto
```

### 11.3 自动备份（可选）

```bash
# 创建备份脚本
tee ~/backup.sh > /dev/null <<'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR="/home/videoauto/backups"
mkdir -p $BACKUP_DIR

tar czf $BACKUP_DIR/videoauto_$DATE.tar.gz \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='*.mp4' \
  ~/apps/Dake-Video-Auto/

# 保留最近7天备份
find $BACKUP_DIR -name "videoauto_*.tar.gz" -mtime +7 -delete
EOF

chmod +x ~/backup.sh

# 添加定时任务
crontab -l | { cat; echo "0 3 * * * /home/videoauto/backup.sh"; } | crontab -
```

---

## ✅ 部署检查清单

- [ ] 服务器系统更新完成
- [ ] Python 3.10+ 已安装
- [ ] FFmpeg 已安装并可用
- [ ] 项目代码已克隆
- [ ] 虚拟环境已创建
- [ ] 所有依赖已安装
- [ ] Playwright Chromium 已安装
- [ ] 目录权限已设置
- [ ] systemd 服务已配置
- [ ] 服务已启动并启用
- [ ] 防火墙已配置
- [ ] 可以通过浏览器访问
- [ ] 二维码下载功能正常
- [ ] TTS 语音生成功能正常

---

## 🔗 访问地址

部署完成后，可以通过以下地址访问：

```
# 直接访问（未配置 Nginx）
http://你的服务器IP:5000

# 通过 Nginx 访问
http://your-domain.com

# HTTPS（配置了 SSL）
https://your-domain.com
```

---

## 📞 技术支持

如有部署问题，请检查：
1. 服务器日志：`sudo journalctl -u videoauto -f`
2. 应用日志：`~/apps/Dake-Video-Auto/logs/`
3. GitHub Issues: https://github.com/wudake/Dake-Video-Auto/issues

---

**部署完成！🎉**
