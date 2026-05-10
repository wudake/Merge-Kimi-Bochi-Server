"""
高级视频编辑器 - v2.2
添加字幕功能：语音识别、样式配置、自适应大小
"""
import json
import subprocess
import whisper
import re
from pathlib import Path


class AdvancedVideoEditor:
    """高级视频剪辑器 v2.2 - 支持字幕"""
    
    PRESETS = {
        "light": {"name": "轻度", "desc": "画幅+调速",
            "config": {"crop_top": 0, "crop_bottom": 0, "speed": 1.0, "hflip": False, "zoom": 1.0,
                "brightness": 0, "contrast": 0, "saturation": 0,
                "add_logo": False, "replace_audio": False, "original_volume": 1.0}},
        "medium": {"name": "中度", "desc": "镜像+缩放+调色+Logo",
            "config": {"crop_top": 0.5, "crop_bottom": 0.5, "speed": 1.05, "hflip": True, "zoom": 1.05,
                "brightness": 0.05, "contrast": 0.1, "saturation": 0.05,
                "add_logo": True, "logo_select": "logo_default.png", "logo_position": "bottom_right",
                "logo_size": 0.10, "logo_opacity": 0.85,
                "replace_audio": False, "original_volume": 1.0}},
        "heavy": {"name": "重度", "desc": "全效果+BGM+Logo",
            "config": {"crop_top": 2, "crop_bottom": 1, "speed": 1.25, "hflip": True, "zoom": 1.08,
                "brightness": 0.08, "contrast": 0.15, "saturation": 0.1,
                "add_logo": True, "logo_select": "logo_default.png", "logo_position": "bottom_center", 
                "logo_size": 0.15, "logo_opacity": 0.9,
                "replace_audio": True, "bgm_select": "", "bgm_volume": 0.8, "original_volume": 0.0}}
    }
    
    # 字幕样式预设
    SUBTITLE_STYLES = {
        "yellow_classic": {
            "name": "经典黄字",
            "font_color": "#FFD700",
            "outline_color": "#000000",
            "outline_width": 2,
            "shadow": 1,
            "border_style": 1,
            "bold": True
        },
        "tiktok_box": {
            "name": "TikTok风格",
            "font_color": "#FFFFFF",
            "outline_color": "#000000",
            "outline_width": 0,
            "shadow": 0,
            "border_style": 3,
            "bold": True,
            "back_color": "#CC000000"
        },
        "neon_cyan": {
            "name": "霓虹青光",
            "font_color": "#00FFFF",
            "outline_color": "#0088FF",
            "outline_width": 3,
            "shadow": 2,
            "border_style": 1,
            "bold": True
        },
        "neon_pink": {
            "name": "霓虹粉光",
            "font_color": "#FF69B4",
            "outline_color": "#CC00FF",
            "outline_width": 3,
            "shadow": 2,
            "border_style": 1,
            "bold": True
        },
        "movie_clean": {
            "name": "影视字幕",
            "font_color": "#FFFFFF",
            "outline_color": "#000000",
            "outline_width": 1,
            "shadow": 0,
            "border_style": 1,
            "bold": False
        },
        "variety_bold": {
            "name": "综艺风格",
            "font_color": "#FFD700",
            "outline_color": "#000000",
            "outline_width": 4,
            "shadow": 2,
            "border_style": 1,
            "bold": True
        },
        "minimal_white": {
            "name": "极简白字",
            "font_color": "#FFFFFF",
            "outline_color": "#000000",
            "outline_width": 1,
            "shadow": 0,
            "border_style": 1,
            "bold": True
        },
        "white_outline": {
            "name": "白字黑边",
            "font_color": "#FFFFFF",
            "outline_color": "#000000",
            "outline_width": 2,
            "shadow": 1,
            "border_style": 1,
            "bold": True
        },
        "dark_box": {
            "name": "黑底白字",
            "font_color": "#FFFFFF",
            "outline_color": "#333333",
            "outline_width": 0,
            "shadow": 0,
            "border_style": 3,
            "bold": True,
            "back_color": "#DD000000"
        }
    }
    
    # TTS 配音延迟时间（毫秒）
    TTS_DELAY_MS = 700

    def __init__(self, raw_dir="videos/raw", edited_dir="output",
                 assets_dir="assets", logos_dir="assets/logos", bgm_dir="assets/bgm"):
        self.raw_dir = Path(raw_dir)
        self.edited_dir = Path(edited_dir)
        self.assets_dir = Path(assets_dir)
        self.logos_dir = Path(logos_dir)
        self.bgm_dir = Path(bgm_dir)
        
        for d in [self.raw_dir, self.edited_dir, self.assets_dir, self.logos_dir, self.bgm_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # Whisper 模型（延迟加载）
        self._whisper_model = None
    
    def _get_whisper_model(self, model_size="base"):
        """获取 Whisper 模型"""
        if self._whisper_model is None:
            print(f"   加载 Whisper 模型 ({model_size})...")
            self._whisper_model = whisper.load_model(model_size)
        return self._whisper_model
    
    def generate_subtitles(self, video_path, output_srt=None, language="zh", model_size="base"):
        """
        使用 Whisper 生成 SRT 字幕
        
        Args:
            video_path: 视频路径
            output_srt: 输出 SRT 路径，None则自动生成
            language: 语言代码 (zh, en, ja, ko, auto)
            model_size: 模型大小 (tiny, base, small, medium, large)
            
        Returns:
            SRT 文件路径
        """
        video_path = Path(video_path)
        if output_srt is None:
            output_srt = video_path.with_suffix('.srt')
        else:
            output_srt = Path(output_srt)
        
        print(f"\n📝 生成字幕: {video_path.name}")
        
        model = self._get_whisper_model(model_size)
        
        # 转录
        result = model.transcribe(
            str(video_path),
            language=None if language == "auto" else language,
            verbose=False
        )
        
        # 生成 SRT
        srt_lines = []
        for i, segment in enumerate(result["segments"], 1):
            start = self._seconds_to_srt_time(segment["start"])
            end = self._seconds_to_srt_time(segment["end"])
            text = segment["text"].strip()
            
            srt_lines.append(f"{i}")
            srt_lines.append(f"{start} --> {end}")
            srt_lines.append(text)
            srt_lines.append("")
        
        output_srt.write_text("\n".join(srt_lines), encoding='utf-8')
        print(f"   ✅ 字幕生成: {output_srt.name} ({len(result['segments'])} 句)")
        
        return output_srt
    
    def _seconds_to_srt_time(self, seconds):
        """秒转 SRT 时间格式"""
        total_ms = max(0, round(seconds * 1000))
        hrs = total_ms // 3600000
        mins = (total_ms % 3600000) // 60000
        secs = (total_ms % 60000) // 1000
        ms = total_ms % 1000
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"
    
    def calculate_font_size(self, text, video_width=1080, max_font_size=12, min_font_size=10, fixed_size=None):
        """
        根据字幕长度计算自适应字体大小
        
        Args:
            text: 字幕文本
            video_width: 视频宽度
            max_font_size: 最大字体大小 (默认12)
            min_font_size: 最小字体大小 (默认10)
            fixed_size: 固定字体大小 (如果指定则使用固定值)
            
        Returns:
            计算后的字体大小
        """
        # 如果指定了固定大小，直接返回
        if fixed_size is not None:
            return fixed_size
        
        # 按字符数计算
        char_count = len(text)
        
        if char_count <= 10:
            return max_font_size
        elif char_count <= 20:
            return int(max_font_size * 0.9)
        elif char_count <= 30:
            return int(max_font_size * 0.8)
        else:
            return min_font_size
    
    def burn_subtitles(self, video_path, srt_path, output_path, style_config=None):
        """
        将字幕烧录到视频
        
        Args:
            video_path: 输入视频路径
            srt_path: SRT 字幕路径
            output_path: 输出视频路径
            style_config: 样式配置字典
                - style_preset: 预设样式名称
                - font_color: 字体颜色 (#RRGGBB)
                - outline_color: 描边颜色
                - outline_width: 描边宽度
                - font_size: 字体大小 (None则自动计算)
                - position: 位置 (bottom, middle, top)
                - max_width: 最大行宽百分比 (0-1)
        """
        video_path = Path(video_path)
        srt_path = Path(srt_path)
        output_path = Path(output_path)
        
        if style_config is None:
            style_config = {}
        
        print(f"\n🔥 烧录字幕: {srt_path.name}")

        # 获取样式
        preset_name = style_config.get("style_preset", "yellow_classic")
        preset = self.SUBTITLE_STYLES.get(preset_name, self.SUBTITLE_STYLES["yellow_classic"])

        font_color = style_config.get("font_color", preset["font_color"])
        outline_color = style_config.get("outline_color", preset["outline_color"])
        outline_width = style_config.get("outline_width", preset["outline_width"])
        shadow = style_config.get("shadow", preset["shadow"])
        border_style = style_config.get("border_style", preset.get("border_style", 1))
        bold = style_config.get("bold", preset.get("bold", True))

        # 字体大小（自动计算或使用指定值，包括固定大小）
        font_size = style_config.get("font_size")
        custom_size = style_config.get("custom_font_size")

        if custom_size is not None and custom_size > 0:
            # 使用自定义固定大小
            font_size = int(custom_size)
            print(f"   字体大小: 自定义 {font_size}px")
        elif font_size is None:
            # 读取 SRT 计算平均长度
            srt_content = srt_path.read_text(encoding='utf-8')
            texts = re.findall(r'\n\n(\d+)\n.*?\n(.*?)(?=\n\n|\Z)', srt_content, re.DOTALL)
            if texts:
                avg_length = sum(len(t[1].strip()) for t in texts) / len(texts)
                font_size = self.calculate_font_size("x" * int(avg_length))
            else:
                font_size = 12
            print(f"   字体大小: 自适应 {font_size}px")

        # 位置和对齐
        position = style_config.get("position", "bottom")
        align = style_config.get("align", "center")

        # ASS Alignment: 1=左下, 2=中下, 3=右下, 4=左中, 5=中中, 6=右中, 7=左上, 8=中上, 9=右上
        alignment_map = {
            ("top", "left"): 7, ("top", "center"): 8, ("top", "right"): 9,
            ("middle", "left"): 4, ("middle", "center"): 5, ("middle", "right"): 6,
            ("bottom", "left"): 1, ("bottom", "center"): 2, ("bottom", "right"): 3
        }
        alignment = alignment_map.get((position, align), 2)

        # 转换颜色格式
        def hex_to_ass(hex_color):
            hex_color = hex_color.lstrip('#')
            if len(hex_color) == 8:
                # 带透明度的格式 #AARRGGBB → &HBBGGRR (ASS alpha 单独处理)
                a = hex_color[0:2]
                r = hex_color[2:4]
                g = hex_color[4:6]
                b = hex_color[6:8]
                return f"&H{a}{b}{g}{r}"
            r = hex_color[0:2]
            g = hex_color[2:4]
            b = hex_color[4:6]
            return f"&H{b}{g}{r}"


        font_color_ass = hex_to_ass(font_color)
        outline_color_ass = hex_to_ass(outline_color)
        
        # 垂直边距
        margin_v_map = {"top": 50, "middle": 540, "bottom": 100}
        margin_v = margin_v_map.get(position, 100)

        # 水平安全边距：9:16 竖屏视频左右留出 60px 安全区，防止字幕贴边或被设备刘海/圆角裁剪
        margin_l = 60
        margin_r = 60
        
        # 构建 force_style 字符串
        bold_val = -1 if bold else 0
        style_parts = [
            f"FontName=WenQuanYi Zen Hei",
            f"FontSize={font_size}",
            f"PrimaryColour={font_color_ass}",
            f"OutlineColour={outline_color_ass}",
            f"Outline={outline_width}",
            f"Shadow={shadow}",
            f"Alignment={alignment}",
            f"MarginV={margin_v}",
            f"MarginL={margin_l}",
            f"MarginR={margin_r}",
            f"WrapStyle=0",
            f"BorderStyle={border_style}",
            f"Bold={bold_val}"
        ]

        # BorderStyle=3 时添加背景色
        if border_style == 3 and "back_color" in preset:
            back_color_ass = hex_to_ass(preset["back_color"])
            style_parts.append(f"BackColour={back_color_ass}")

        style_str = ",".join(style_parts)
        
        vf_filter = f"subtitles={srt_path}:force_style='{style_str}'"
        
        # 如果需要限制行宽，使用 wrap 处理
        # 这里我们使用 ASS 的 WrapStyle=0 自动换行
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf", vf_filter,
            "-c:a", "copy",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-movflags", "+faststart",
            str(output_path)
        ]
        
        if self.run_ffmpeg(cmd):
            print(f"   ✅ 字幕烧录完成: {output_path.name}")
            return output_path
        return None
    
    def get_info(self, video_path):
        """获取视频信息"""
        cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0",
               "-show_entries", "stream=width,height,duration,r_frame_rate",
               "-show_entries", "format=duration,size",
               "-of", "json", str(video_path)]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True)
            d = json.loads(r.stdout)
            s = d.get("streams", [{}])[0]
            f = d.get("format", {})
            return {
                "width": s.get("width", 0), "height": s.get("height", 0),
                "duration": float(s.get("duration") or f.get("duration", 0)),
                "fps": s.get("r_frame_rate", "30/1"),
                "size_mb": int(f.get("size", 0)) / 1024 / 1024
            }
        except:
            return {"width": 0, "height": 0, "duration": 0, "fps": "30/1", "size_mb": 0}
    
    def list_logos(self):
        """列出所有 Logo"""
        logos = []
        if self.logos_dir.exists():
            for f in self.logos_dir.glob("*.png"):
                logos.append({"name": f.name, "path": str(f)})
        return logos
    
    def list_bgms(self):
        """列出所有 BGM"""
        bgms = []
        if self.bgm_dir.exists():
            for f in self.bgm_dir.glob("*"):
                if f.suffix.lower() in [".mp3", ".m4a", ".wav"]:
                    bgms.append({"name": f.name, "path": str(f), "size_mb": round(f.stat().st_size/1024/1024, 2)})
        return bgms
    
    def run_ffmpeg(self, cmd):
        """运行 FFmpeg"""
        try:
            print(f"   FFmpeg: {' '.join(cmd[:8])}...")
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            if r.returncode != 0:
                print(f"❌ FFmpeg 错误: {r.stderr[:500]}")
                return False
            return True
        except Exception as e:
            print(f"❌ FFmpeg 异常: {e}")
            return False
    
    def edit_video(self, video_path, config):
        """
        剪辑视频 - 支持字幕
        """
        video_path = Path(video_path)
        note_id = video_path.stem
        
        # 生成新文件名: Dake_Video_Auto_YYYYMMDDhhmm.mp4
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        output_filename = f"Dake_Video_Auto_{timestamp}.mp4"
        output = self.edited_dir / output_filename
        
        info = self.get_info(video_path)
        duration = info["duration"]
        w, h = info["width"], info["height"]
        
        if duration <= 0:
            print("❌ 无效视频")
            return None
        
        # 参数
        crop_start = config.get("crop_top", 0)
        crop_end = config.get("crop_bottom", 0)
        speed = config.get("speed", 1.0)
        new_duration = (duration - crop_start - crop_end) / speed
        
        if new_duration <= 0:
            print("❌ 视频太短")
            return None
        
        # Logo 和 BGM 选择
        logo_name = config.get("logo_select", "")
        logo_path = self.logos_dir / logo_name if logo_name else None
        use_logo = config.get("add_logo", False) and logo_path and logo_path.exists()
        
        # BGM 选择
        bgm_name = config.get("bgm_select", "")
        bgm_path = self.bgm_dir / bgm_name if bgm_name else None
        if bgm_path and not bgm_path.exists():
            bgms = self.list_bgms()
            if bgms:
                bgm_path = Path(bgms[0]["path"])
        use_bgm = bgm_path and bgm_path.exists()
        
        # TTS 音频选择
        use_tts = config.get("use_tts", False)
        tts_path = config.get("tts_audio_path", "")
        tts_voice = config.get("tts_voice", "en-US-AriaNeural")
        if use_tts and tts_path:
            tts_path = Path(tts_path)
            if not tts_path.exists():
                use_tts = False
                tts_path = None
        else:
            use_tts = False
            tts_path = None
        
        # 判断是否替换原声
        replace_audio = config.get("replace_audio", False)
        original_volume = config.get("original_volume", 0.0 if replace_audio else 1.0)
        bgm_volume = config.get("bgm_volume", 0.8)
        tts_volume = config.get("tts_volume", 1.0)
        
        # 字幕配置
        add_subtitles = config.get("add_subtitles", False)
        subtitle_text = config.get("subtitle_text", "")
        subtitle_start = config.get("subtitle_start", 0)
        subtitle_end = config.get("subtitle_end", None)  # None表示到视频结尾
        subtitle_style_preset = config.get("subtitle_style", "yellow_classic")
        subtitle_font_size = config.get("subtitle_font_size", 9)
        subtitle_position = config.get("subtitle_position", "bottom")
        subtitle_align = config.get("subtitle_align", "center")  # left/center/right
        subtitle_outline_width = config.get("subtitle_outline_width", 1)

        # TTS 同步字幕
        use_tts_subtitles = config.get("use_tts_subtitles", False)
        
        print(f"\n🎬 剪辑: {note_id}")
        print(f"   输入: {w}x{h} | {duration:.1f}s")
        if crop_start > 0 or crop_end > 0:
            print(f"   裁剪: 头部-{crop_start}s, 尾部-{crop_end}s")
        print(f"   输出: 1080x1920 (9:16) | {new_duration:.1f}s")
        
        target_width = 1080
        target_height = 1920
        
        # ====== 构建 FFmpeg 命令 ======
        inputs = ["-i", str(video_path)]
        input_idx = 1
        
        if use_logo:
            inputs.extend(["-i", str(logo_path)])
            print(f"   Logo: {logo_path.name}")
            logo_idx = input_idx
            input_idx += 1
        
        if use_bgm:
            inputs.extend(["-i", str(bgm_path)])
            print(f"   BGM: {bgm_path.name}")
            bgm_idx = input_idx
            input_idx += 1
        
        # 构建视频滤镜
        vf_parts = []
        
        if config.get("hflip", False):
            vf_parts.append("hflip")
        
        zoom = config.get("zoom", 1.0)
        if zoom != 1.0:
            vf_parts.append(f"scale=iw*{zoom}:ih*{zoom}")
        
        target_ratio = 9/16
        current_ratio = w / h
        
        if current_ratio > target_ratio:
            new_w = int(h * target_ratio * zoom)
            off = (int(w * zoom) - new_w) // 2
            vf_parts.append(f"crop={new_w}:ih:{off}:0")
        else:
            new_h = int(w / target_ratio * zoom)
            off = (int(h * zoom) - new_h) // 2
            vf_parts.append(f"crop=iw:{new_h}:0:{off}")
        
        b, c, s = config.get("brightness", 0), config.get("contrast", 0), config.get("saturation", 0)
        if b or c or s:
            vf_parts.append(f"eq=brightness={b}:contrast={1+c}:saturation={1+s}")
        
        vf_parts.append(f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:black")
        
        if speed != 1.0:
            vf_parts.append(f"setpts=PTS/{speed}")
        
        # 构建 filter_complex
        filter_chains = []
        base_vf = ",".join(vf_parts)
        
        if use_logo:
            ls = config.get("logo_size", 0.12)
            op = config.get("logo_opacity", 0.85)
            pos = config.get("logo_position", "bottom_right")
            lw = int(target_width * ls)
            m = 30
            
            pos_map = {
                "bottom_right": (f"W-w-{m}", f"H-h-{m}"),
                "bottom_left": (str(m), f"H-h-{m}"),
                "top_right": (f"W-w-{m}", str(m)),
                "top_left": (str(m+54), str(m+144)),
                "bottom_center": ("(W-w)/2", f"H-h-{m}")
            }
            x, y = pos_map.get(pos, pos_map["bottom_right"])
            
            filter_chains.append(f"[{logo_idx}:v]scale={lw}:-1,format=rgba,colorchannelmixer=aa={op}[logo]")
            filter_chains.append(f"[0:v]{base_vf}[v]")
            filter_chains.append(f"[v][logo]overlay={x}:{y}[outv]")
            video_out = "[outv]"
        else:
            filter_chains.append(f"[0:v]{base_vf}[v]")
            video_out = "[v]"
        
        # 音频处理 - 支持原声、TTS、BGM三路混音
        audio_inputs = []  # 音频输入列表 [(输入索引, 音量, 类型), ...]
        
        # 1. 原声
        if original_volume > 0 and not replace_audio:
            audio_inputs.append((0, original_volume, "原声"))
        
        # 2. TTS音频
        if use_tts and tts_path:
            inputs.extend(["-i", str(tts_path)])
            tts_idx = input_idx
            input_idx += 1
            audio_inputs.append((tts_idx, tts_volume, "TTS配音"))
            print(f"   TTS: {tts_path.name} (延迟{self.TTS_DELAY_MS}ms)")
        
        # 3. BGM - 需要循环播放以匹配视频时长
        if use_bgm and bgm_path:
            inputs.extend(["-i", str(bgm_path)])
            bgm_idx = input_idx
            input_idx += 1
            audio_inputs.append((bgm_idx, bgm_volume, "BGM"))
            print(f"   BGM: {bgm_path.name}")
        
        # 构建音频滤镜链
        if len(audio_inputs) == 0:
            # 没有音频源，只用原声（静音）
            filter_chains.append(f"[0:a]volume=0[a]")
            audio_out = "[a]"
        elif len(audio_inputs) == 1:
            # 只有一个音频源
            idx, vol, name = audio_inputs[0]
            if idx == 0 and speed != 1.0 and speed <= 2.0:
                filter_chains.append(f"[0:a]atempo={speed},volume={vol}[a]")
            else:
                # BGM需要循环播放直到视频结束
                if name == "BGM":
                    # 使用aloop循环BGM，然后裁剪到视频时长
                    filter_chains.append(f"[{idx}:a]aloop=loop=-1:size=0,atrim=0:{new_duration},asetpts=PTS-STARTPTS,volume={vol}[a]")
                elif name == "TTS配音":
                    # TTS 音频延迟 0.7 秒开始播放，先延迟再裁剪避免末尾被截断
                    filter_chains.append(f"[{idx}:a]adelay={self.TTS_DELAY_MS}|{self.TTS_DELAY_MS},atrim=0:{new_duration},asetpts=PTS-STARTPTS,volume={vol}[a]")
                else:
                    filter_chains.append(f"[{idx}:a]atrim=0:{new_duration},asetpts=PTS-STARTPTS,volume={vol}[a]")
            audio_out = "[a]"
        else:
            # 多路音频混音
            audio_labels = []
            for idx, vol, name in audio_inputs:
                label = f"[a{idx}]"
                audio_labels.append(label)
                
                if idx == 0 and speed != 1.0 and speed <= 2.0:
                    # 原声需要变速
                    filter_chains.append(f"[0:a]atempo={speed},volume={vol}{label}")
                elif name == "BGM":
                    # BGM循环播放并裁剪到视频时长
                    filter_chains.append(f"[{idx}:a]aloop=loop=-1:size=0,atrim=0:{new_duration},asetpts=PTS-STARTPTS,volume={vol}{label}")
                elif name == "TTS配音":
                    # TTS 音频延迟 0.7 秒开始播放，先延迟再裁剪避免末尾被截断
                    filter_chains.append(f"[{idx}:a]adelay={self.TTS_DELAY_MS}|{self.TTS_DELAY_MS},atrim=0:{new_duration},asetpts=PTS-STARTPTS,volume={vol}{label}")
                else:
                    # 其他音频（如TTS）裁剪到视频时长
                    filter_chains.append(f"[{idx}:a]atrim=0:{new_duration},asetpts=PTS-STARTPTS,volume={vol}{label}")
            
            # 混音 - 使用longest确保BGM持续整个视频
            num_inputs = len(audio_inputs)
            filter_chains.append(f"{''.join(audio_labels)}amix=inputs={num_inputs}:duration=longest:dropout_transition=3[a]")
            audio_out = "[a]"
        
        filter_complex = ";".join(filter_chains)
        
        cmd = ["ffmpeg", "-y"]
        cmd.extend(["-ss", str(crop_start)])
        cmd.extend(["-t", str(duration - crop_start - crop_end)])
        cmd.extend(inputs)
        
        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", video_out,
            "-map", audio_out,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-r", "30",
            "-movflags", "+faststart",
            str(output)
        ])
        
        if self.run_ffmpeg(cmd):
            # 生成并烧录字幕
            srt_path = None
            try:
                if add_subtitles and subtitle_text:
                    print(f"\n📝 处理手动字幕...")
                    # 如果未指定结束时间，使用视频时长
                    if subtitle_end is None:
                        subtitle_end = new_duration

                    srt_path = self.edited_dir / f"edited_{note_id}.srt"
                    srt_content = f"1\n{self._seconds_to_srt_time(subtitle_start)} --> {self._seconds_to_srt_time(subtitle_end)}\n{subtitle_text}\n"
                    srt_path.write_text(srt_content, encoding='utf-8')
                    print(f"   字幕内容: '{subtitle_text}' ({subtitle_start}s - {subtitle_end}s)")

                elif use_tts and tts_path and use_tts_subtitles:
                    print(f"\n📝 处理 TTS 同步字幕...")
                    from tts_generator import TTSSubtitleGenerator
                    gen = TTSSubtitleGenerator(model_size="base")
                    # 根据 TTS 音色推断语言
                    if tts_voice.startswith("zh-"):
                        tts_lang = "zh"
                    elif tts_voice.startswith("en-"):
                        tts_lang = "en"
                    elif tts_voice.startswith("ja-"):
                        tts_lang = "ja"
                    elif tts_voice.startswith("ko-"):
                        tts_lang = "ko"
                    else:
                        tts_lang = "zh"
                    print(f"   识别语言: {tts_lang} (音色: {tts_voice})")
                    srt_path = Path(gen.generate_srt_from_tts(tts_path, language=tts_lang, delay_ms=self.TTS_DELAY_MS))

                if srt_path and srt_path.exists():
                    # 样式配置
                    style_cfg = {
                        "style_preset": subtitle_style_preset,
                        "position": subtitle_position,
                        "align": subtitle_align,
                        "font_size": subtitle_font_size,
                    }
                    # 仅当用户修改了描边宽度时才覆盖预设值
                    preset = self.SUBTITLE_STYLES.get(subtitle_style_preset, self.SUBTITLE_STYLES["yellow_classic"])
                    if subtitle_outline_width != preset.get("outline_width", 1):
                        style_cfg["outline_width"] = subtitle_outline_width

                    # 烧录字幕到新文件
                    final_output = self.edited_dir / f"Dake_Video_Auto_{timestamp}_sub.mp4"
                    result = self.burn_subtitles(output, srt_path, final_output, style_cfg)

                    if result:
                        # 删除无字幕版本，重命名有字幕版本
                        output.unlink()
                        final_output.rename(output)
                        print(f"✅ 字幕添加完成")
                    else:
                        print(f"⚠️ 字幕烧录失败，使用无字幕版本")

                    # 清理 SRT 文件
                    srt_path.unlink(missing_ok=True)

            except Exception as e:
                print(f"⚠️ 字幕处理失败: {e}")

            out_info = self.get_info(output)
            print(f"✅ 完成: {output.name} ({out_info['size_mb']:.1f}MB, {out_info['duration']:.1f}s)")
            return output

        return None


if __name__ == "__main__":
    import sys
    editor = AdvancedVideoEditor()
    
    if len(sys.argv) > 1:
        cfg = {
            "crop_top": 2, "crop_bottom": 2, "speed": 1.2,
            "hflip": True, "zoom": 1.05, "brightness": 0.05,
            "contrast": 0.1, "add_logo": True, 
            "logo_select": "logo_default.png", "logo_position": "bottom_right", "logo_size": 0.12,
            "replace_audio": False, "original_volume": 0.5,
            "add_subtitles": True,
            "subtitle_style": "white_black",
            "subtitle_position": "bottom"
        }
        editor.edit_video(sys.argv[1], cfg)
    else:
        print("可用的 Logos:", [l["name"] for l in editor.list_logos()])
        print("可用的 BGM:", [b["name"] for b in editor.list_bgms()])
        print("字幕样式:", list(editor.SUBTITLE_STYLES.keys()))
