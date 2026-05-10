import os
from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
import subprocess
import sys
import json
import asyncio
from pathlib import Path
from werkzeug.utils import secure_filename
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dake-video-auto-secret-key-2026')
# 整合部署时 Nginx 传递 X-Forwarded-Prefix，ProxyFix 将其转为 SCRIPT_NAME
app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)
BASE_DIR = Path(__file__).parent

# 登录验证装饰器 - 信任 Nginx auth_request 传递的 X-User-Id header
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.headers.get('X-User-Id')
        if user_id:
            session['logged_in'] = True
            session['username'] = user_id
            return f(*args, **kwargs)
        # 兜底：本地开发时允许 session 鉴权
        if 'logged_in' in session:
            return f(*args, **kwargs)
        return redirect(url_for('login'))
    return decorated_function

# 添加路径
sys.path.insert(0, str(BASE_DIR / "core"))

# ========== 登录相关路由 ==========

@app.route("/login", methods=["GET", "POST"])
def login():
    """SSO 登录入口 - Nginx auth_request 已确保用户已登录"""
    user_id = request.headers.get('X-User-Id')
    if user_id:
        session['logged_in'] = True
        session['username'] = user_id
        return redirect(url_for('index'))
    # 兜底：允许本地开发时通过任意密码登录
    if request.method == "POST":
        session['logged_in'] = True
        session['username'] = request.form.get('username', 'user')
        return redirect(url_for('index'))
    if 'logged_in' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route("/logout")
def logout():
    """登出 - 清除本地 session，前端负责调用 SSO logout 清除 Cookie"""
    session.clear()
    return redirect(url_for('login'))

# ========== TTS 相关导入 ==========
from tts_generator import TTSGenerator, ScriptToSpeech

# ========== 二维码导入 ==========
from qr_generator import generate_video_qr, get_local_ip

# TTS 生成器实例
tts_generator = TTSGenerator(output_dir=str(BASE_DIR / "assets" / "tts"))

@app.route("/")
@login_required
def index():
    return render_template("index.html", username=session.get('username'))

@app.route("/api/logos/list")
def list_logos():
    logos_dir = BASE_DIR / "assets" / "logos"
    logos = []
    if logos_dir.exists():
        for f in logos_dir.glob("*.png"):
            logos.append({"name": f.name, "size_kb": round(f.stat().st_size/1024, 1)})
    return jsonify({"logos": logos})

@app.route("/api/bgm/list")
def list_bgm():
    bgm_dir = BASE_DIR / "assets" / "bgm"
    bgms = []
    if bgm_dir.exists():
        for f in bgm_dir.glob("*"):
            if f.suffix.lower() in [".mp3", ".m4a", ".wav"]:
                bgms.append({"name": f.name, "size_mb": round(f.stat().st_size/1024/1024, 2)})
        # 按文件名排序
        bgms.sort(key=lambda x: x["name"])
    return jsonify({"bgms": bgms})

@app.route("/api/download", methods=["POST"])
def download_video():
    data = request.json
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"success": False, "error": "URL 不能为空"})

    (BASE_DIR / ".temp_url.txt").write_text(url, encoding='utf-8')

    try:
        result = subprocess.run(
            [sys.executable, str(BASE_DIR / "download_worker.py")],
            capture_output=True, text=True, timeout=90, cwd=str(BASE_DIR)
        )

        result_file = BASE_DIR / ".temp_result.json"
        if result_file.exists():
            download_result = json.loads(result_file.read_text(encoding='utf-8'))
            result_file.unlink()
        else:
            return jsonify({"success": False, "error": "下载器未返回结果"})

        if download_result.get("status") == "success":
            return jsonify({
                "success": True,
                "data": {
                    "note_id": download_result["note_id"],
                    "size_mb": round(download_result.get("size_mb", 0), 2)
                }
            })
        else:
            return jsonify({"success": False, "error": download_result.get("error", "下载失败")})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/edit", methods=["POST"])
def edit_video():
    data = request.json
    note_id = data.get("note_id")
    config = data.get("config", {})

    if not note_id:
        return jsonify({"success": False, "error": "未指定视频"})

    # 处理 TTS 配置
    if config.get("use_tts") and config.get("tts_filename"):
        tts_path = BASE_DIR / "assets" / "tts" / config["tts_filename"]
        if tts_path.exists():
            config["tts_audio_path"] = str(tts_path)
        else:
            return jsonify({"success": False, "error": "TTS 音频文件不存在，请重新生成"})

    (BASE_DIR / ".temp_config.json").write_text(
        json.dumps({"note_id": note_id, "config": config}), encoding='utf-8'
    )

    try:
        result = subprocess.run(
            [sys.executable, str(BASE_DIR / "edit_worker.py")],
            capture_output=True, text=True, timeout=120, cwd=str(BASE_DIR)
        )

        # 捕获 stderr 作为日志
        stderr_logs = result.stderr.strip().split('\n') if result.stderr else []

        result_file = BASE_DIR / ".temp_edit_result.json"
        if result_file.exists():
            edit_result = json.loads(result_file.read_text(encoding='utf-8'))
            result_file.unlink()
        else:
            return jsonify({
                "success": False,
                "error": "剪辑器未返回结果",
                "logs": stderr_logs
            })

        if edit_result.get("success"):
            output_name = edit_result["output_name"]

            # 生成二维码便于手机下载
            try:
                from qr_generator import generate_video_qr
                base_url = request.url_root.rstrip('/')
                qr_result = generate_video_qr(
                    output_name,
                    output_dir=str(BASE_DIR / "static"),
                    base_url=base_url
                )
                qr_url = url_for('static', filename=qr_result['qr_filename'])
                local_ip = qr_result['local_ip']
            except Exception as e:
                qr_url = None
                local_ip = get_local_ip()
                print(f"二维码生成失败: {e}")

            response_data = {
                "output_name": output_name,
                "preview_url": url_for('preview_video', filename=output_name),
                "download_url": url_for('download_edited', filename=output_name),
                "local_ip": local_ip
            }
            if qr_url:
                response_data["qr_url"] = qr_url
                response_data["qr_tip"] = "📱 手机扫码直接下载"

            return jsonify({"success": True, "data": response_data})
        else:
            # 返回详细的错误信息和日志
            response = {
                "success": False,
                "error": edit_result.get("error", "剪辑失败"),
                "logs": edit_result.get("logs", stderr_logs)
            }
            if "detail" in edit_result:
                response["detail"] = edit_result["detail"]
            if "traceback" in edit_result:
                response["traceback"] = edit_result["traceback"]
            return jsonify(response)
    except subprocess.TimeoutExpired:
        return jsonify({
            "success": False,
            "error": "剪辑超时 (超过120秒)",
            "logs": ["剪辑任务超时，可能是视频太大或处理复杂"]
        })
    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        })

@app.route("/api/upload/logo", methods=["POST"])
def upload_logo():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "没有文件"})
    file = request.files["file"]
    if file.filename.lower().endswith((".png", ".jpg", ".jpeg")):
        logos_dir = BASE_DIR / "assets" / "logos"
        logos_dir.mkdir(exist_ok=True)
        file.save(logos_dir / secure_filename(file.filename))
        return jsonify({"success": True, "message": "Logo 上传成功"})
    return jsonify({"success": False, "error": "仅支持 PNG/JPG"})

@app.route("/api/upload/bgm", methods=["POST"])
def upload_bgm():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "没有文件"})
    file = request.files["file"]
    if file.filename.lower().endswith((".mp3", ".m4a", ".wav")):
        bgm_dir = BASE_DIR / "assets" / "bgm"
        bgm_dir.mkdir(exist_ok=True)
        file.save(bgm_dir / secure_filename(file.filename))
        return jsonify({"success": True, "message": "BGM 上传成功"})
    return jsonify({"success": False, "error": "仅支持 MP3/M4A/WAV"})


# ========== TTS 脚本配音 API ==========

@app.route("/api/tts/voices", methods=["GET"])
def get_tts_voices():
    """获取可用 TTS 音色列表"""
    try:
        voices = tts_generator.get_voices_list()
        return jsonify({"success": True, "data": {"voices": voices}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/tts/generate", methods=["POST"])
def generate_tts():
    """生成 TTS 语音"""
    data = request.json
    text = data.get("text", "").strip()
    voice = data.get("voice", "en-US-AriaNeural")
    speed = data.get("speed", 1.0)
    
    if not text:
        return jsonify({"success": False, "error": "文本内容不能为空"})
    
    # 验证音色是否有效
    if voice not in tts_generator.VOICES:
        return jsonify({
            "success": False, 
            "error": f"无效的音色: {voice}，请从可用音色列表中选择"
        })
    
    # 验证语速范围
    try:
        speed = float(speed)
        if speed < 0.5 or speed > 2.0:
            return jsonify({
                "success": False, 
                "error": "语速必须在 0.5x - 2.0x 之间"
            })
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "语速参数无效"})
    
    try:
        # 生成文件名
        import hashlib
        import time
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        timestamp = int(time.time())
        filename = f"tts_{timestamp}_{text_hash}.mp3"
        output_path = BASE_DIR / "assets" / "tts" / filename
        
        # 确保目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 生成语音
        print(f"[TTS] 生成语音: voice={voice}, speed={speed}, text={text[:30]}...")
        tts_generator.generate_with_speed(text, str(output_path), voice, speed)
        
        # 验证文件是否成功生成
        if not output_path.exists():
            return jsonify({"success": False, "error": "语音生成失败，文件未创建"})
        
        file_size = output_path.stat().st_size
        if file_size == 0:
            output_path.unlink()  # 删除空文件
            return jsonify({"success": False, "error": "语音生成失败，文件为空"})
        
        print(f"[TTS] 生成成功: {filename} ({file_size} bytes)")
        
        return jsonify({
            "success": True,
            "data": {
                "filename": filename,
                "path": str(output_path),
                "preview_url": url_for('preview_tts', filename=filename),
                "text": text,
                "voice": voice,
                "speed": speed,
                "size_bytes": file_size
            }
        })
    except ValueError as e:
        # 处理参数错误（如无效音色）
        error_msg = str(e)
        if "Invalid voice" in error_msg:
            error_msg = f"音色 '{voice}' 不可用，请尝试其他音色"
        return jsonify({
            "success": False, 
            "error": error_msg
        })
    except Exception as e:
        import traceback
        error_msg = str(e)
        # 处理常见的 edge-tts 错误
        if "No audio was received" in error_msg:
            error_msg = "语音生成失败：微软TTS服务暂时不可用，请稍后重试或更换音色"
        elif "WebSocket" in error_msg:
            error_msg = "网络连接失败，请检查网络或稍后重试"
        
        print(f"[TTS] 生成失败: {error_msg}")
        return jsonify({
            "success": False, 
            "error": error_msg,
            "traceback": traceback.format_exc()
        })


@app.route("/api/tts/preview/<filename>")
def preview_tts(filename):
    """TTS 音频试听"""
    from werkzeug.utils import secure_filename
    safe_filename = secure_filename(filename)
    tts_path = BASE_DIR / "assets" / "tts" / safe_filename

    if not tts_path.exists():
        return jsonify({"error": "文件不存在"}), 404

    return send_from_directory(BASE_DIR / "assets" / "tts", safe_filename)


@app.route("/api/tts/list")
def list_tts():
    """列出所有已生成的 TTS 文件"""
    tts_dir = BASE_DIR / "assets" / "tts"
    tts_files = []
    if tts_dir.exists():
        for f in tts_dir.glob("*.mp3"):
            tts_files.append({
                "name": f.name,
                "size_mb": round(f.stat().st_size / 1024 / 1024, 2),
                "created": f.stat().st_mtime
            })
        tts_files.sort(key=lambda x: x["created"], reverse=True)
    return jsonify({"success": True, "data": {"tts_files": tts_files}})


@app.route("/api/tts/edit", methods=["POST"])
def edit_with_tts():
    """
    使用 TTS 音频剪辑视频
    类似 /api/edit，但使用 TTS 生成的音频替代原声/BGM
    """
    data = request.json
    note_id = data.get("note_id")
    tts_filename = data.get("tts_filename")
    config = data.get("config", {})

    if not note_id:
        return jsonify({"success": False, "error": "未指定视频"})

    if not tts_filename:
        return jsonify({"success": False, "error": "未指定 TTS 音频"})

    tts_path = BASE_DIR / "assets" / "tts" / tts_filename
    if not tts_path.exists():
        return jsonify({"success": False, "error": "TTS 音频文件不存在"})

    # 将 TTS 音频路径写入配置，供 edit_worker 使用
    config["tts_audio_path"] = str(tts_path)
    config["use_tts"] = True

    (BASE_DIR / ".temp_config.json").write_text(
        json.dumps({"note_id": note_id, "config": config}), encoding='utf-8'
    )

    try:
        result = subprocess.run(
            [sys.executable, str(BASE_DIR / "edit_worker.py")],
            capture_output=True, text=True, timeout=120, cwd=str(BASE_DIR)
        )

        stderr_logs = result.stderr.strip().split('\n') if result.stderr else []

        result_file = BASE_DIR / ".temp_edit_result.json"
        if result_file.exists():
            edit_result = json.loads(result_file.read_text(encoding='utf-8'))
            result_file.unlink()
        else:
            return jsonify({
                "success": False,
                "error": "剪辑器未返回结果",
                "logs": stderr_logs
            })

        if edit_result.get("success"):
            output_name = edit_result["output_name"]
            return jsonify({
                "success": True,
                "data": {
                    "output_name": output_name,
                    "preview_url": url_for('preview_video', filename=output_name),
                    "download_url": url_for('download_edited', filename=output_name)
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": edit_result.get("error", "剪辑失败"),
                "logs": edit_result.get("logs", stderr_logs)
            })
    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        })


@app.route("/api/bgm/preview/<filename>")
def preview_bgm(filename):
    """BGM 试听 - 支持 range 请求"""
    from werkzeug.utils import secure_filename
    safe_filename = secure_filename(filename)
    bgm_path = BASE_DIR / "assets" / "bgm" / safe_filename

    if not bgm_path.exists():
        return jsonify({"error": "文件不存在"}), 404

    return send_from_directory(BASE_DIR / "assets" / "bgm", safe_filename)

@app.route("/api/upload/video", methods=["POST"])
def upload_video():
    """本地上传视频文件用于剪辑"""
    if "file" not in request.files:
        return jsonify({"success": False, "error": "没有文件"})

    file = request.files["file"]
    if not file.filename:
        return jsonify({"success": False, "error": "文件名不能为空"})

    # 检查文件扩展名
    allowed_extensions = ('.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v')
    if not file.filename.lower().endswith(allowed_extensions):
        return jsonify({"success": False, "error": f"仅支持视频格式: {', '.join(allowed_extensions)}"})

    # 保存上传的视频
    raw_dir = BASE_DIR / "videos" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # 生成安全的文件名，保留原始扩展名
    import uuid
    ext = Path(file.filename).suffix
    video_id = f"upload_{uuid.uuid4().hex[:12]}"
    filename = f"{video_id}{ext}"

    save_path = raw_dir / filename
    file.save(save_path)

    # 获取文件大小
    file_size = save_path.stat().st_size / 1024 / 1024

    print(f"📤 视频上传成功: {filename} ({file_size:.2f}MB)")

    return jsonify({
        "success": True,
        "data": {
            "note_id": video_id,
            "filename": filename,
            "size_mb": round(file_size, 2),
            "message": f"上传成功！{round(file_size, 2)}MB"
        }
    })

@app.route("/api/logs/edit/latest")
def get_latest_edit_logs():
    """获取最新的剪辑日志"""
    logs_dir = BASE_DIR / "logs"
    if not logs_dir.exists():
        return jsonify({"logs": [], "error": "日志目录不存在"})

    # 找到最新的剪辑日志
    log_files = sorted(logs_dir.glob("edit_*.log"), key=lambda x: x.stat().st_mtime, reverse=True)

    if not log_files:
        return jsonify({"logs": []})

    try:
        # 读取最新的日志文件
        latest_log = log_files[0]
        content = latest_log.read_text(encoding='utf-8')
        lines = [l for l in content.split('\n') if l.strip()]
        return jsonify({"logs": lines[-100:]})  # 返回最后100行
    except Exception as e:
        return jsonify({"logs": [], "error": str(e)})


@app.route("/api/download/edited/<filename>")
def download_edited(filename):
    return send_from_directory(BASE_DIR / "output", filename, as_attachment=True)

@app.route("/api/preview/<filename>")
def preview_video(filename):
    return send_from_directory(BASE_DIR / "output", filename)


# ========== 发布平台 API ==========

@app.route("/api/publish/accounts", methods=["GET"])
def get_publish_accounts():
    """获取已配置的发布平台账号"""
    config_file = BASE_DIR / "config" / "publish_accounts.json"
    accounts = []
    if config_file.exists():
        with open(config_file, 'r') as f:
            data = json.load(f)
            for acc in data:
                accounts.append({
                    "platform": acc["platform"],
                    "username": acc["username"],
                })
    return jsonify({"accounts": accounts})


@app.route("/api/publish/accounts", methods=["POST"])
def add_publish_account():
    """添加发布平台账号"""
    data = request.json
    platform = data.get("platform")
    username = data.get("username")
    password = data.get("password")

    if not all([platform, username, password]):
        return jsonify({"success": False, "error": "缺少必要参数"})

    config_file = BASE_DIR / "config" / "publish_accounts.json"
    config_file.parent.mkdir(parents=True, exist_ok=True)

    accounts = []
    if config_file.exists():
        with open(config_file, 'r') as f:
            accounts = json.load(f)

    found = False
    for acc in accounts:
        if acc["platform"] == platform:
            acc["username"] = username
            acc["password"] = password
            found = True
            break

    if not found:
        accounts.append({
            "platform": platform,
            "username": username,
            "password": password,
            "session_file": ""
        })

    with open(config_file, 'w') as f:
        json.dump(accounts, f, indent=2)

    return jsonify({"success": True, "message": f"{platform} 账号已保存"})


@app.route("/api/publish", methods=["POST"])
def publish_video():
    """发布视频到平台"""
    data = request.json
    video_name = data.get("video_name")
    platforms = data.get("platforms", [])
    caption = data.get("caption", "")
    hashtags = data.get("hashtags", [])

    if not video_name:
        return jsonify({"success": False, "error": "未指定视频"})

    if not platforms:
        return jsonify({"success": False, "error": "未选择平台"})

    video_path = BASE_DIR / "output" / video_name
    if not video_path.exists():
        return jsonify({"success": False, "error": "视频文件不存在"})

    publish_data = {
        "video_path": str(video_path),
        "platforms": platforms,
        "caption": caption,
        "hashtags": hashtags
    }

    temp_file = BASE_DIR / ".temp_publish.json"
    temp_file.write_text(json.dumps(publish_data), encoding='utf-8')

    # 清空旧日志
    log_file = BASE_DIR / "logs" / "publish.log"
    if log_file.exists():
        log_file.unlink()

    try:
        result = subprocess.run(
            [sys.executable, str(BASE_DIR / "publish_worker.py")],
            capture_output=True, text=True, timeout=300, cwd=str(BASE_DIR)
        )

        # 读取日志
        logs = []
        if log_file.exists():
            logs = log_file.read_text(encoding='utf-8').split('\n')
            logs = [l for l in logs if l.strip()]

        result_file = BASE_DIR / ".temp_publish_result.json"
        if result_file.exists():
            publish_result = json.loads(result_file.read_text(encoding='utf-8'))
            result_file.unlink()
            temp_file.unlink(missing_ok=True)
            publish_result["logs"] = logs
            return jsonify(publish_result)
        else:
            temp_file.unlink(missing_ok=True)
            return jsonify({"success": False, "error": "发布器未返回结果", "logs": logs})
    except subprocess.TimeoutExpired:
        # 读取已产生的日志
        logs = []
        if log_file.exists():
            logs = log_file.read_text(encoding='utf-8').split('\n')
            logs = [l for l in logs if l.strip()]
        temp_file.unlink(missing_ok=True)
        return jsonify({"success": False, "error": "发布超时", "logs": logs})
    except Exception as e:
        logs = []
        if log_file.exists():
            logs = log_file.read_text(encoding='utf-8').split('\n')
            logs = [l for l in logs if l.strip()]
        temp_file.unlink(missing_ok=True)
        return jsonify({"success": False, "error": str(e), "logs": logs})


@app.route("/api/logs/publish")
def get_publish_logs():
    """获取发布日志"""
    log_file = BASE_DIR / "logs" / "publish.log"
    if log_file.exists():
        logs = log_file.read_text(encoding='utf-8').split('\n')
        logs = [l for l in logs if l.strip()]
        return jsonify({"logs": logs})
    return jsonify({"logs": []})


@app.route("/api/publish/assistant", methods=["POST"])
def publish_assistant():
    """发布助手 - 生成各平台发布信息"""
    from core.publish_assistant import PublishAssistant

    data = request.json
    video_name = data.get("video_name")
    caption = data.get("caption", "")
    hashtags = data.get("hashtags", [])

    if not video_name:
        return jsonify({"success": False, "error": "未指定视频"})

    video_path = BASE_DIR / "output" / video_name
    if not video_path.exists():
        return jsonify({"success": False, "error": "视频文件不存在"})

    try:
        # 生成各平台的发布信息
        platforms = PublishAssistant.get_platform_links(
            str(video_path), caption, hashtags
        )

        # 生成分享信息
        share_info = PublishAssistant.get_shareable_links(
            str(video_path), caption
        )

        return jsonify({
            "success": True,
            "data": {
                "video_name": video_name,
                "video_url": url_for('preview_video', filename=video_name),
                "download_url": url_for('download_edited', filename=video_name),
                "caption": caption,
                "hashtags": hashtags,
                "copy_text": PublishAssistant.generate_caption(caption, hashtags),
                "platforms": platforms,
                "share_info": share_info
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ========== 二维码 API ==========

@app.route("/api/qr/generate/<filename>")
def generate_qr(filename):
    """生成视频下载二维码"""
    from werkzeug.utils import secure_filename
    safe_filename = secure_filename(filename)

    video_path = BASE_DIR / "output" / safe_filename
    if not video_path.exists():
        return jsonify({"success": False, "error": "视频文件不存在"})

    try:
        # 生成二维码
        base_url = request.url_root.rstrip('/')
        result = generate_video_qr(
            safe_filename,
            output_dir=str(BASE_DIR / "static"),
            base_url=base_url
        )

        return jsonify({
            "success": True,
            "data": {
                "qr_url": url_for('static', filename=result['qr_filename']),
                "download_url": result['download_url'],
                "local_ip": result['local_ip']
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/qr/ip")
def get_server_ip():
    """获取服务器局域网IP"""
    return jsonify({
        "success": True,
        "data": {
            "ip": get_local_ip(),
            "port": 5000,
            "url": request.url_root.rstrip('/')
        }
    })


if __name__ == "__main__":
    # 获取服务器IP（优先环境变量，其次自动检测）
    import os
    import socket

    def get_server_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "0.0.0.0"

    server_ip = os.environ.get('SERVER_IP', get_server_ip())
    server_port = int(os.environ.get('PORT', 5000))

    print(f"🚀 启动服务: http://{server_ip}:{server_port}")
    print(f"   本地访问: http://127.0.0.1:{server_port}")
    print(f"   局域网访问: http://0.0.0.0:{server_port}")
    app.run(host="0.0.0.0", port=server_port, debug=False, threaded=False)
