# Dake-Video-Auto Docker 部署指南

本文档介绍如何使用 Docker 和 Docker Compose 部署 Dake-Video-Auto 项目。

---

## 📋 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- 服务器内存 4GB+ (推荐 8GB)
- 磁盘空间 50GB+

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/wudake/Dake-Video-Auto.git
cd Dake-Video-Auto
```

### 2. 启动服务

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 等待服务启动（约 30-60 秒）
```

### 3. 访问服务

```
http://你的服务器IP:5000
```

---

## 📦 部署方式

### 方式一：基础部署（推荐）

使用默认配置，直接暴露 5000 端口：

```bash
# 启动
docker-compose up -d

# 停止
docker-compose down

# 重启
docker-compose restart
```

### 方式二：使用 Nginx 反向代理

如需使用 80 端口并通过 Nginx 访问：

```bash
# 启动包含 Nginx 的配置
docker-compose --profile with-nginx up -d

# 访问
http://你的服务器IP
```

### 方式三：生产环境（含 HTTPS）

使用 Traefik 或手动配置 SSL：

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  videoauto:
    build: .
    container_name: openclaw-video-auto
    expose:
      - "5000"
    volumes:
      - video-videos:/app/videos
      - video-output:/app/output
      - video-assets:/app/assets
      - video-static:/app/static
      - video-logs:/app/logs
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    networks:
      - video-network

  traefik:
    image: traefik:v2.10
    container_name: videoauto-traefik
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik.yml:/traefik.yml:ro
      - ./letsencrypt:/letsencrypt
    networks:
      - video-network
    restart: unless-stopped

volumes:
  video-videos:
  video-output:
  video-assets:
  video-static:
  video-logs:

networks:
  video-network:
    driver: bridge
```

---

## 🔧 常用命令

### 查看状态

```bash
# 查看运行状态
docker-compose ps

# 查看日志
docker-compose logs -f videoauto

# 查看资源使用
docker stats
```

### 更新项目

```bash
# 拉取最新代码
git pull origin main

# 重新构建并启动
docker-compose down
docker-compose up -d --build

# 查看更新后的日志
docker-compose logs -f
```

### 备份数据

```bash
# 备份输出视频
docker cp openclaw-video-auto:/app/output ./backup-output-$(date +%Y%m%d)

# 或者使用卷备份
docker run --rm -v openclaw-video-auto_output:/source -v $(pwd):/backup alpine tar czf /backup/output-backup.tar.gz -C /source .
```

### 进入容器

```bash
# 进入容器内部
docker exec -it openclaw-video-auto bash

# 查看容器内文件
docker exec -it openclaw-video-auto ls -la /app/output

# 查看容器日志
docker logs -f openclaw-video-auto
```

---

## ⚙️ 配置说明

### 端口映射

| 服务 | 容器端口 | 主机端口 | 说明 |
|------|---------|---------|------|
| videoauto | 5000 | 5000 | 主应用 |
| nginx | 80 | 80 | HTTP 反向代理 |
| nginx | 443 | 443 | HTTPS 反向代理 |

### 数据卷

| 卷名 | 容器路径 | 说明 |
|------|---------|------|
| ./videos | /app/videos | 原始视频 |
| ./output | /app/output | 成品视频 |
| ./assets | /app/assets | Logo/BGM/TTS |
| ./static | /app/static | 静态文件/二维码 |
| ./logs | /app/logs | 日志文件 |
| ./config | /app/config | 配置文件 |

---

## 🐛 故障排查

### 问题1: 容器无法启动

```bash
# 查看详细日志
docker-compose logs --tail=100

# 检查端口占用
sudo netstat -tlnp | grep 5000

# 检查镜像构建
docker-compose build --no-cache
```

### 问题2: 视频无法下载

```bash
# 检查 Playwright 浏览器
docker exec -it openclaw-video-auto playwright install chromium

# 查看下载日志
docker exec -it openclaw-video-auto tail -f /app/logs/*.log
```

### 问题3: TTS 无法生成

```bash
# 检查网络连接（Edge-TTS 需要外网）
docker exec -it openclaw-video-auto curl -I https://speech.platform.bing.com

# 检查 TTS 目录权限
docker exec -it openclaw-video-auto ls -la /app/assets/tts
```

### 问题4: 磁盘空间不足

```bash
# 查看容器磁盘使用
docker system df

# 清理未使用的镜像/卷
docker system prune -a

# 清理旧视频
docker exec -it openclaw-video-auto find /app/output -name "*.mp4" -mtime +7 -delete
```

---

## 🔒 安全配置

### 使用 HTTPS

```yaml
# docker-compose.ssl.yml
version: '3.8'

services:
  videoauto:
    build: .
    expose:
      - "5000"
    volumes:
      - ./videos:/app/videos
      - ./output:/app/output
      - ./assets:/app/assets
      - ./static:/app/static
      - ./logs:/app/logs

  https-portal:
    image: steveltn/https-portal:1
    ports:
      - '80:80'
      - '443:443'
    links:
      - videoauto
    restart: always
    environment:
      DOMAINS: 'your-domain.com -> http://videoauto:5000'
      STAGE: 'production'  # 测试时用 'local'
      # STAGE: 'local'
```

### 使用 Basic Auth

```yaml
# 在 nginx.conf 中添加认证
server {
    listen 80;
    
    auth_basic "Restricted";
    auth_basic_user_file /etc/nginx/.htpasswd;
    
    location / {
        proxy_pass http://videoauto:5000;
    }
}
```

生成密码文件：
```bash
# 安装 apache2-utils
sudo apt install apache2-utils

# 生成密码
htpasswd -c .htpasswd admin
```

---

## 📊 性能优化

### 限制资源使用

```yaml
services:
  videoauto:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### 使用多阶段构建（减小镜像体积）

```dockerfile
# 构建阶段
FROM python:3.10-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# 运行阶段
FROM python:3.10-slim
COPY --from=builder /root/.local /root/.local
COPY . /app
WORKDIR /app
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "app_simple.py"]
```

---

## 🌐 部署到云服务商

### 阿里云 ECS

```bash
# 1. 购买 ECS 实例（推荐 2核4G+）
# 2. 安装 Docker
curl -fsSL https://get.docker.com | bash

# 3. 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 4. 部署
git clone https://github.com/wudake/Dake-Video-Auto.git
cd Dake-Video-Auto
docker-compose up -d

# 5. 配置安全组，开放 5000 端口
```

### 腾讯云 CVM

类似阿里云步骤，注意：
- 安全组需要开放端口
- 建议绑定域名 + HTTPS

### AWS EC2

```bash
# 安装 Docker
sudo yum update -y
sudo amazon-linux-extras install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# 安装 Docker Compose
sudo curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 部署
git clone https://github.com/wudake/Dake-Video-Auto.git
cd Dake-Video-Auto
docker-compose up -d
```

---

## 📝 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `PYTHONUNBUFFERED` | 1 | Python 无缓冲输出 |
| `PLAYWRIGHT_BROWSERS_PATH` | /ms-playwright | Playwright 浏览器路径 |
| `FLASK_ENV` | production | Flask 环境 |

---

## 🔗 相关文档

- [DEPLOY.md](./DEPLOY.md) - 传统部署方式
- [README.md](./README.md) - 项目说明
- [docs/REQUIREMENTS.md](./docs/REQUIREMENTS.md) - 功能需求

---

**Docker 部署完成！🐳**
