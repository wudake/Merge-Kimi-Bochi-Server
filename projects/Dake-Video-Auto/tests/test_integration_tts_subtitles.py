"""
TTS 同步字幕全流程集成测试
端到端验证：生成测试视频 → TTS 语音生成 → Whisper 字幕生成 → FFmpeg 剪辑 → 输出检查
"""
import os
import sys
import json
import shutil
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from tts_generator import TTSGenerator, TTSSubtitleGenerator
from editor_advanced import AdvancedVideoEditor


class TestTTSSubtitleIntegration(unittest.TestCase):
    """TTS 同步字幕端到端集成测试"""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = Path(tempfile.mkdtemp(prefix="tts_sub_integration_"))
        cls.raw_dir = cls.temp_dir / "videos" / "raw"
        cls.output_dir = cls.temp_dir / "output"
        cls.assets_dir = cls.temp_dir / "assets"
        cls.logos_dir = cls.assets_dir / "logos"
        cls.bgm_dir = cls.assets_dir / "bgm"
        cls.tts_dir = cls.assets_dir / "tts"

        for d in [cls.raw_dir, cls.output_dir, cls.assets_dir, cls.logos_dir, cls.bgm_dir, cls.tts_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # 生成一个 5 秒 1080x1920 的测试视频（黑色背景 + 正弦波音轨）
        cls.video_path = cls.raw_dir / "integration_test.mp4"
        cls._generate_test_video(str(cls.video_path), duration=5)

        # 初始化编辑器
        cls.editor = AdvancedVideoEditor(
            raw_dir=str(cls.raw_dir),
            edited_dir=str(cls.output_dir),
            assets_dir=str(cls.assets_dir),
            logos_dir=str(cls.logos_dir),
            bgm_dir=str(cls.bgm_dir),
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    @classmethod
    def _generate_test_video(cls, output_path, duration=5):
        """用 FFmpeg 生成测试视频"""
        import subprocess
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:d={duration}",
            "-f", "lavfi", "-i", f"sine=frequency=1000:duration={duration}",
            "-shortest",
            "-c:v", "libx264", "-preset", "ultrafast",
            "-c:a", "aac", "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg 生成测试视频失败: {result.stderr}")

    def test_01_tts_generation(self):
        """步骤1：真实 TTS 语音生成"""
        tts = TTSGenerator(output_dir=str(self.tts_dir))
        self.tts_path = tts.generate_with_speed(
            text="Hello everyone, this is the Dake video automation tool integration test.",
            output_path=str(self.tts_dir / "integration_tts.mp3"),
            voice="en-US-AriaNeural",
            speed=1.0
        )
        self.assertTrue(Path(self.tts_path).exists())
        self.assertGreater(Path(self.tts_path).stat().st_size, 0)
        print(f"\n✅ TTS 生成成功: {self.tts_path} ({Path(self.tts_path).stat().st_size} bytes)")

    def test_02_subtitle_generation_with_delay(self):
        """步骤2：Whisper 生成同步字幕，并验证 700ms 延迟偏移"""
        # 复用步骤1 生成的 TTS
        tts_path = self.tts_dir / "integration_tts.mp3"
        if not tts_path.exists():
            self.skipTest("跳过：TTS 文件未生成")

        gen = TTSSubtitleGenerator(model_size="base")
        srt_path = gen.generate_srt_from_tts(
            str(tts_path),
            language="en",
            delay_ms=700
        )

        self.assertTrue(Path(srt_path).exists())
        content = Path(srt_path).read_text(encoding="utf-8")
        self.assertIn(" --> ", content)

        # 解析第一行时间，验证 >= 00:00:00,700
        lines = [l.strip() for l in content.split("\n") if l.strip()]
        for i, line in enumerate(lines):
            if " --> " in line:
                start_time = line.split(" --> ")[0]
                # 转换为毫秒
                h, m, s_ms = start_time.split(":")
                s, ms = s_ms.split(",")
                total_ms = int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)
                self.assertGreaterEqual(
                    total_ms, 700,
                    f"字幕起始时间 {start_time} 未偏移 700ms"
                )
                print(f"\n✅ 字幕首句时间: {start_time} (已偏移 700ms)")
                break
        else:
            self.fail("SRT 中未找到时间轴行")

        self.__class__.srt_path = srt_path

    def test_03_full_video_edit_with_tts_subtitles(self):
        """步骤3：完整视频剪辑，验证最终输出视频存在且时长合理"""
        tts_path = self.tts_dir / "integration_tts.mp3"
        if not tts_path.exists():
            self.skipTest("跳过：TTS 文件未生成")

        config = {
            "crop_top": 0,
            "crop_bottom": 0,
            "speed": 1.0,
            "hflip": False,
            "zoom": 1.0,
            "brightness": 0,
            "contrast": 0,
            "saturation": 0,
            "add_logo": False,
            "replace_audio": True,
            "original_volume": 0.0,
            "bgm_select": "",
            "bgm_volume": 0.0,
            "use_tts": True,
            "tts_audio_path": str(tts_path),
            "tts_volume": 1.0,
            "use_tts_subtitles": True,
            "subtitle_style": "yellow_classic",
            "subtitle_font_size": 12,
            "subtitle_position": "bottom",
            "subtitle_align": "center",
            "subtitle_outline_width": 1,
        }

        result = self.editor.edit_video(self.video_path, config)
        self.assertIsNotNone(result, "剪辑失败，返回 None")
        result_path = Path(result)
        self.assertTrue(result_path.exists(), f"输出视频不存在: {result}")
        self.assertGreater(result_path.stat().st_size, 0)

        # 验证视频信息
        info = self.editor.get_info(result_path)
        self.assertGreater(info["duration"], 0, "输出视频时长异常")
        self.assertEqual(info["width"], 1080)
        self.assertEqual(info["height"], 1920)

        print(f"\n✅ 剪辑成功: {result_path.name}")
        print(f"   时长: {info['duration']:.2f}s | 分辨率: {info['width']}x{info['height']}")

    def test_04_verify_tts_delay_in_ffmpeg_filter(self):
        """步骤4：通过复现剪辑验证 FFmpeg filter_complex 包含 adelay=700|700"""
        # 由于 edit_video 内部构建命令后传给 run_ffmpeg，
        # 我们可以通过 patch run_ffmpeg 来捕获最终命令
        from unittest.mock import patch

        captured_cmd = []

        def capture_run_ffmpeg(cmd):
            captured_cmd.extend(cmd)
            # 创建假的输出文件以让流程继续
            output_path = Path(cmd[-1])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            # 复制原视频假装剪辑完成
            shutil.copy(str(self.video_path), str(output_path))
            return True

        tts_path = self.tts_dir / "integration_tts.mp3"
        if not tts_path.exists():
            self.skipTest("跳过：TTS 文件未生成")

        config = {
            "use_tts": True,
            "tts_audio_path": str(tts_path),
            "tts_volume": 1.0,
            "use_tts_subtitles": False,  # 不触发字幕，只测音频延迟
            "crop_top": 0,
            "crop_bottom": 0,
            "speed": 1.0,
            "hflip": False,
            "zoom": 1.0,
        }

        with patch.object(self.editor, "run_ffmpeg", side_effect=capture_run_ffmpeg):
            self.editor.edit_video(self.video_path, config)

        cmd_str = " ".join(captured_cmd)
        self.assertIn("adelay=700|700", cmd_str, "FFmpeg 命令中未找到 TTS 延迟滤镜")
        print(f"\n✅ FFmpeg 命令验证通过: 包含 adelay=700|700")


if __name__ == "__main__":
    unittest.main()
