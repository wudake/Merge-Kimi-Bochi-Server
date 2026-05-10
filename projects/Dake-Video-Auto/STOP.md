# Dake-Video-Auto 远程服务器停止/重启指南

## 方法一：前台运行停止（Ctrl+C）

如果你在终端直接运行 `python app_simple.py`：

```bash
# 在运行终端按 Ctrl+C
# 或者找到进程并终止

# 查找 Python 进程
ps aux | grep app_simple.py

# 终止进程
kill -9 <进程ID>
```

---

## 方法二：使用 systemd 服务停止（推荐）

如果你按照 DEPLOY.md 配置了 systemd 服务：

```bash
# 停止服务
sudo systemctl stop videoauto

# 查看状态
sudo systemctl status videoauto

# 禁止开机自启
sudo systemctl disable videoauto

# 重新启用
sudo systemctl enable videoauto
sudo systemctl start videoauto
```

---

## 方法三：Docker 停止

如果你使用 Docker 部署：

```bash
# 停止容器
cd ~/Openclaw-Video-Auto
docker-compose down

# 或者停止单个容器
docker stop openclaw-video-auto

# 查看容器状态
docker ps -a

# 重启
docker-compose up -d
```

---

## 方法四：查找并停止所有相关进程

```bash
# 查找所有 Python 相关进程
ps aux | grep python

# 查找占用 5000 端口的进程
sudo lsof -i :5000
sudo netstat -tlnp | grep 5000

# 强制终止
sudo kill -9 $(sudo lsof -t -i :5000)

# 或者批量终止
pkill -f "app_simple.py"
```

---

## 方法五：使用脚本停止

创建一个停止脚本：

```bash
# 创建停止脚本
cat > ~/stop_videoauto.sh << 'EOF'
#!/bin/bash

echo "🔍 查找 Dake-Video-Auto 进程..."

# 方法1: 查找特定进程
PID=$(ps aux | grep "app_simple.py" | grep -v grep | awk '{print $2}')

if [ -n "$PID" ]; then
    echo "🛑 找到进程 PID: $PID，正在停止..."
    kill -9 $PID
    echo "✅ 进程已停止"
else
    echo "ℹ️ 未找到运行中的进程"
fi

# 方法2: 检查端口占用
echo "🔍 检查端口 5000..."
PORT_PID=$(sudo lsof -t -i :5000 2>/dev/null)
if [ -n "$PORT_PID" ]; then
    echo "🛑 端口 5000 被 PID $PORT_PID 占用，正在释放..."
    sudo kill -9 $PORT_PID
    echo "✅ 端口已释放"
fi

# 方法3: 检查 systemd 服务
if systemctl is-active --quiet videoauto 2>/dev/null; then
    echo "🛑 停止 systemd 服务..."
    sudo systemctl stop videoauto
    echo "✅ 服务已停止"
fi

# 方法4: 检查 Docker
if docker ps | grep -q "openclaw-video-auto"; then
    echo "🛑 停止 Docker 容器..."
    docker stop openclaw-video-auto
    echo "✅ 容器已停止"
fi

echo "✅ 所有相关进程已清理完成"
EOF

chmod +x ~/stop_videoauto.sh

# 使用
~/stop_videoauto.sh
```

---

## 验证是否停止成功

```bash
# 检查进程
ps aux | grep app_simple

# 检查端口
sudo lsof -i :5000

# 尝试访问（应该无法连接）
curl http://localhost:5000
```

---

## 快速命令汇总

| 操作 | 命令 |
|------|------|
| **前台停止** | `Ctrl+C` 或 `kill -9 <PID>` |
| **Systemd 停止** | `sudo systemctl stop videoauto` |
| **Docker 停止** | `docker-compose down` |
| **强制停止** | `sudo kill -9 $(sudo lsof -t -i :5000)` |
| **一键停止** | `pkill -f "app_simple.py"` |

---

## 常见问题

### Q: 停止后端口仍被占用？
```bash
# 强制释放端口
sudo fuser -k 5000/tcp
```

### Q: 如何查看是否在运行？
```bash
# 检查进程
pgrep -f "app_simple.py" && echo "运行中" || echo "已停止"

# 检查端口
sudo lsof -i :5000
```

### Q: 停止后如何重新启动？
```bash
cd ~/Openclaw-Video-Auto
source venv/bin/activate
python app_simple.py

# 或使用 systemd
sudo systemctl start videoauto

# 或使用 Docker
docker-compose up -d
```

---

**停止完成！** 🛑
