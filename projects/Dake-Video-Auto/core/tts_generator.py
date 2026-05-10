"""
TTS 语音生成模块 - 基于 edge-tts (免费微软语音)
支持多音色、语速调节
"""
import asyncio
import edge_tts
from pathlib import Path
import json


class TTSGenerator:
    """TTS 语音生成器"""
    
    # 可用音色列表 - 仅英语
    VOICES = {
        # 美式英语 - 女声
        "en-US-AnaNeural": {"name": "Ana", "gender": "Female", "desc": "Young & Cheerful"},
        "en-US-AriaNeural": {"name": "Aria", "gender": "Female", "desc": "Professional & Confident"},
        "en-US-AvaNeural": {"name": "Ava", "gender": "Female", "desc": "Natural & Elegant"},
        "en-US-AvaMultilingualNeural": {"name": "Ava (Multilingual)", "gender": "Female", "desc": "Multilingual"},
        "en-US-EmmaNeural": {"name": "Emma", "gender": "Female", "desc": "Warm & Friendly"},
        "en-US-EmmaMultilingualNeural": {"name": "Emma (Multilingual)", "gender": "Female", "desc": "Multilingual"},
        "en-US-JennyNeural": {"name": "Jenny", "gender": "Female", "desc": "Clear & Friendly"},
        "en-US-MichelleNeural": {"name": "Michelle", "gender": "Female", "desc": "Warm & Pleasant"},
        # 美式英语 - 男声
        "en-US-AndrewNeural": {"name": "Andrew", "gender": "Male", "desc": "Steady & Professional"},
        "en-US-AndrewMultilingualNeural": {"name": "Andrew (Multilingual)", "gender": "Male", "desc": "Multilingual"},
        "en-US-BrianNeural": {"name": "Brian", "gender": "Male", "desc": "Clear & Powerful"},
        "en-US-BrianMultilingualNeural": {"name": "Brian (Multilingual)", "gender": "Male", "desc": "Multilingual"},
        "en-US-ChristopherNeural": {"name": "Christopher", "gender": "Male", "desc": "Authoritative & Confident"},
        "en-US-EricNeural": {"name": "Eric", "gender": "Male", "desc": "Young & Energetic"},
        "en-US-GuyNeural": {"name": "Guy", "gender": "Male", "desc": "Professional & Steady"},
        "en-US-RogerNeural": {"name": "Roger", "gender": "Male", "desc": "Deep & Mature"},
        "en-US-SteffanNeural": {"name": "Steffan", "gender": "Male", "desc": "Warm & Reliable"},
        # 英式英语
        "en-GB-LibbyNeural": {"name": "Libby", "gender": "Female", "desc": "Elegant & Professional"},
        "en-GB-MaisieNeural": {"name": "Maisie", "gender": "Female", "desc": "Lively & Young"},
        "en-GB-SoniaNeural": {"name": "Sonia", "gender": "Female", "desc": "Friendly & Clear"},
        "en-GB-RyanNeural": {"name": "Ryan", "gender": "Male", "desc": "Steady & Natural"},
        "en-GB-ThomasNeural": {"name": "Thomas", "gender": "Male", "desc": "Mature & Steady"},
    }
    
    def __init__(self, output_dir="assets/tts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_async(self, text, output_path, voice="en-US-AriaNeural", 
                             rate="+0%", volume="+0%", pitch="+0Hz"):
        """
        异步生成语音
        
        Args:
            text: 要转换的文本
            output_path: 输出文件路径
            voice: 音色ID
            rate: 语速调节 (+50% 加快50%, -20% 减慢20%)
            volume: 音量调节
            pitch: 音调调节
        
        Returns:
            输出文件路径
        """
        import edge_tts.exceptions
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 验证文本
        if not text or not text.strip():
            raise ValueError("文本内容不能为空")
        
        # 清理文本（移除可能导致问题的字符）
        text = text.strip()
        
        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate,
                volume=volume,
                pitch=pitch
            )
            
            await communicate.save(str(output_path))
            
            # 验证文件是否成功生成
            if not output_path.exists():
                raise RuntimeError("语音文件未生成")
            if output_path.stat().st_size == 0:
                output_path.unlink()
                raise RuntimeError("语音文件为空")
            
            return str(output_path)
            
        except edge_tts.exceptions.NoAudioReceived:
            raise RuntimeError("微软TTS服务未返回音频，请检查音色是否有效或稍后重试")
        except edge_tts.exceptions.VoiceNotFound:
            raise ValueError(f"音色 '{voice}' 不存在，请使用有效的音色ID")
        except Exception as e:
            # 如果文件已生成但可能损坏，删除它
            if output_path.exists():
                try:
                    output_path.unlink()
                except:
                    pass
            raise
    
    def generate(self, text, output_path=None, voice="en-US-AriaNeural",
                 rate="+0%", volume="+0%", pitch="+0Hz"):
        """
        同步生成语音（阻塞方式）
        
        Args:
            text: 要转换的文本
            output_path: 输出文件路径，None则自动生成
            voice: 音色ID
            rate: 语速调节
            volume: 音量调节
            pitch: 音调调节
        
        Returns:
            输出文件路径
        """
        if not text or not text.strip():
            raise ValueError("文本内容不能为空")

        if output_path is None:
            import hashlib
            import time
            # 生成唯一文件名
            text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
            timestamp = int(time.time())
            output_path = self.output_dir / f"tts_{voice.split('-')[-1]}_{timestamp}_{text_hash}.mp3"

        try:
            return asyncio.run(self.generate_async(text, output_path, voice, rate, volume, pitch))
        except RuntimeError as e:
            # 如果在已有事件循环中运行，尝试直接使用事件循环
            if "cannot be called from a running event loop" in str(e):
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 使用 run_coroutine_threadsafe 或 nest_asyncio
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            self.generate_async(text, output_path, voice, rate, volume, pitch)
                        )
                        return future.result()
            raise
    
    def generate_with_speed(self, text, output_path=None, voice="en-US-AriaNeural", 
                           speed=1.0):
        """
        使用速度倍数生成语音
        
        Args:
            text: 要转换的文本
            output_path: 输出文件路径
            voice: 音色ID
            speed: 速度倍数 (0.5-2.0)
        
        Returns:
            输出文件路径
        """
        # 转换速度倍数为 edge-tts 的 rate 格式（使用 round 避免浮点精度问题，如 1-0.8=0.1999...）
        if speed > 1.0:
            rate = f"+{round((speed - 1) * 100)}%"
        elif speed < 1.0:
            rate = f"-{round((1 - speed) * 100)}%"
        else:
            rate = "+0%"
        
        return self.generate(text, output_path, voice, rate)
    
    def get_voices_list(self):
        """获取可用音色列表"""
        return [
            {
                "id": voice_id,
                "name": info["name"],
                "gender": info["gender"],
                "desc": info["desc"]
            }
            for voice_id, info in self.VOICES.items()
        ]
    
    def get_voice_by_name(self, name):
        """根据名称查找音色ID"""
        for voice_id, info in self.VOICES.items():
            if info["name"] == name:
                return voice_id
        return "en-US-AriaNeural"  # 默认


class TTSSubtitleGenerator:
    """TTS 字幕生成器 - 基于 Whisper 将 TTS 音频转为带时间轴的字幕"""

    def __init__(self, model_size="base"):
        self.model_size = model_size
        self._whisper_model = None

    def _get_whisper_model(self):
        """懒加载 Whisper 模型"""
        if self._whisper_model is None:
            import whisper
            print(f"   加载 Whisper 模型 ({self.model_size})...")
            self._whisper_model = whisper.load_model(self.model_size)
        return self._whisper_model

    def _seconds_to_srt_time(self, seconds):
        """秒转 SRT 时间格式"""
        total_ms = max(0, round(seconds * 1000))
        hrs = total_ms // 3600000
        mins = (total_ms % 3600000) // 60000
        secs = (total_ms % 60000) // 1000
        ms = total_ms % 1000
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"

    def generate_srt_from_tts(self, audio_path, output_srt=None, language="zh", delay_ms=0):
        """
        对 TTS 音频进行 Whisper 转录，生成精准时间轴 SRT 字幕

        Args:
            audio_path: TTS 音频文件路径
            output_srt: 输出 SRT 路径，None 则自动生成
            language: 语言代码 (zh, en, ja, ko)
            delay_ms: 时间轴整体偏移量（毫秒），用于匹配被延迟的 TTS 音频

        Returns:
            SRT 文件路径
        """
        audio_path = Path(audio_path)
        if output_srt is None:
            output_srt = audio_path.with_suffix('.srt')
        else:
            output_srt = Path(output_srt)

        delay_sec = delay_ms / 1000.0
        if delay_sec > 0:
            print(f"\n📝 生成 TTS 同步字幕: {audio_path.name} (偏移 {delay_ms}ms)")
        else:
            print(f"\n📝 生成 TTS 同步字幕: {audio_path.name}")

        model = self._get_whisper_model()
        result = model.transcribe(
            str(audio_path),
            language=language,
            verbose=False
        )

        srt_lines = []
        for i, segment in enumerate(result["segments"], 1):
            start = self._seconds_to_srt_time(segment["start"] + delay_sec)
            end = self._seconds_to_srt_time(segment["end"] + delay_sec)
            text = segment["text"].strip()

            srt_lines.append(f"{i}")
            srt_lines.append(f"{start} --> {end}")
            srt_lines.append(text)
            srt_lines.append("")

        output_srt.write_text("\n".join(srt_lines), encoding='utf-8')
        print(f"   ✅ 字幕生成: {output_srt.name} ({len(result['segments'])} 句)")

        return str(output_srt)


class ScriptToSpeech:
    """脚本转语音 - 支持多段落生成"""

    def __init__(self, tts_generator=None):
        self.tts = tts_generator or TTSGenerator()
    
    def generate_multi_segments(self, segments, output_path=None):
        """
        生成多段落语音并合并
        
        Args:
            segments: 段落列表，每个段落是字典 {"text": "...", "voice": "...", "speed": 1.0}
            output_path: 最终输出路径
        
        Returns:
            输出文件路径
        """
        import tempfile
        import subprocess
        import os
        
        if output_path is None:
            import time
            output_path = self.tts.output_dir / f"script_{int(time.time())}.mp3"
        else:
            output_path = Path(output_path)
        
        # 生成每个段落的语音
        temp_files = []
        try:
            for i, seg in enumerate(segments):
                text = seg.get("text", "").strip()
                if not text:
                    continue
                
                voice = seg.get("voice", "en-US-AriaNeural")
                speed = seg.get("speed", 1.0)
                
                temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                temp_file.close()
                
                self.tts.generate_with_speed(text, temp_file.name, voice, speed)
                temp_files.append(temp_file.name)
            
            if not temp_files:
                return None
            
            # 使用 FFmpeg 合并音频
            if len(temp_files) == 1:
                # 只有一个文件，直接复制
                import shutil
                shutil.copy(temp_files[0], output_path)
            else:
                # 多个文件，合并
                concat_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
                for f in temp_files:
                    concat_file.write(f"file '{f}'\n")
                concat_file.close()
                
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", concat_file.name,
                    "-c", "copy",
                    str(output_path)
                ]
                
                subprocess.run(cmd, capture_output=True, check=True)
                os.unlink(concat_file.name)
            
            return str(output_path)
            
        finally:
            # 清理临时文件
            for f in temp_files:
                try:
                    os.unlink(f)
                except:
                    pass
    
    def estimate_duration(self, text, speed=1.0):
        """
        估算语音时长（粗略估计）
        
        Args:
            text: 文本内容
            speed: 语速倍数
        
        Returns:
            估计的时长（秒）
        """
        # 中文：每分钟约200-250字
        # 英文：每分钟约130-150词
        
        import re
        
        # 统计中文字符
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        # 统计英文单词
        english_words = len(re.findall(r'[a-zA-Z]+', text))
        
        # 计算时长（秒）
        chinese_duration = chinese_chars / 4  # 约4字/秒
        english_duration = english_words / 2.2  # 约2.2词/秒
        
        total_duration = (chinese_duration + english_duration) / speed
        
        return round(total_duration, 1)


# 快捷函数
def generate_speech(text, output_path=None, voice="Aria", speed=1.0):
    """
    快速生成语音
    
    示例:
        generate_speech("大家好，今天我来介绍...", "output.mp3", "晓晓", 1.2)
    """
    tts = TTSGenerator()
    voice_id = tts.get_voice_by_name(voice)
    return tts.generate_with_speed(text, output_path, voice_id, speed)


if __name__ == "__main__":
    # 测试
    print("🎙️ 测试 TTS 生成...")
    
    tts = TTSGenerator()
    
    # 列出可用音色
    print("\n可用音色：")
    for v in tts.get_voices_list()[:5]:
        print(f"  - {v['name']} ({v['gender']}): {v['desc']}")
    
    # 生成测试语音
    test_text = "Hello, I am Dake's AI assistant, glad to be of service!"
    output = tts.generate_with_speed(test_text, voice="en-US-AriaNeural", speed=1.0)
    print(f"\n✅ 测试语音生成: {output}")
