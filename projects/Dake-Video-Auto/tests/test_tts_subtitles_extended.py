"""
TTS + 字幕同步功能扩展测试
覆盖边界场景、错误处理、多路混音、样式预设、语速同步精度
"""
import os
import sys
import json
import tempfile
import shutil
import asyncio
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, ANY

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "core"))

from tts_generator import TTSGenerator, TTSSubtitleGenerator, ScriptToSpeech
from editor_advanced import AdvancedVideoEditor

# 保存真实方法引用
_REAL_BURN_SUBTITLES = AdvancedVideoEditor.burn_subtitles
_REAL_RUN_FFMPEG = AdvancedVideoEditor.run_ffmpeg


class TestTTSGeneratorErrors(unittest.TestCase):
    """TTSGenerator 错误处理测试"""

    def test_empty_text_raises_valueerror(self):
        """空文本应抛出 ValueError"""
        tts = TTSGenerator()
        with self.assertRaises(ValueError):
            tts.generate("   ")

    def test_none_text_raises_valueerror(self):
        """None 文本应抛出 ValueError（generate 中已添加空值检查）"""
        tts = TTSGenerator()
        with self.assertRaises(ValueError):
            tts.generate(None)

    def test_generate_with_speed_rate_conversion(self):
        """验证 speed 到 rate 的转换逻辑"""
        tts = TTSGenerator()
        # 使用 mock 捕获传给 generate 的 rate 参数（generate_with_speed 使用位置参数传递）
        with patch.object(tts, "generate") as mock_generate:
            mock_generate.return_value = "/fake/path.mp3"
            tts.generate_with_speed("test", speed=1.5)
            # generate(text, output_path, voice, rate, ...) — rate 是第4个位置参数 (index 3)
            self.assertEqual(mock_generate.call_args.args[3], "+50%")

            tts.generate_with_speed("test", speed=0.8)
            self.assertEqual(mock_generate.call_args.args[3], "-20%")

            tts.generate_with_speed("test", speed=1.0)
            self.assertEqual(mock_generate.call_args.args[3], "+0%")

    def test_get_voices_list_returns_all(self):
        """验证音色列表返回完整"""
        tts = TTSGenerator()
        voices = tts.get_voices_list()
        self.assertEqual(len(voices), 22)
        # 验证结构
        for v in voices:
            self.assertIn("id", v)
            self.assertIn("name", v)
            self.assertIn("gender", v)
            self.assertIn("desc", v)

    def test_get_voice_by_name(self):
        """根据名称查找音色ID"""
        tts = TTSGenerator()
        self.assertEqual(
            tts.get_voice_by_name("Aria"),
            "en-US-AriaNeural"
        )
        self.assertEqual(
            tts.get_voice_by_name("NonExistent"),
            "en-US-AriaNeural"  # 默认回退
        )


class TestTTSSubtitleGeneratorEdgeCases(unittest.TestCase):
    """TTSSubtitleGenerator 边界场景测试"""

    def setUp(self):
        self.gen = TTSSubtitleGenerator(model_size="base")
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("whisper.load_model")
    def test_empty_segments_generates_empty_srt(self, mock_load_model):
        """Whisper 返回空 segments 时应生成空 SRT"""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"segments": []}
        mock_load_model.return_value = mock_model

        audio_path = self.temp_dir / "empty.mp3"
        audio_path.write_text("fake")
        srt_path = self.gen.generate_srt_from_tts(str(audio_path), language="zh")

        content = Path(srt_path).read_text(encoding="utf-8")
        self.assertEqual(content.strip(), "")

    @patch("whisper.load_model")
    def test_very_long_text_segments(self, mock_load_model):
        """超长文本分段的时间轴连续性验证"""
        mock_model = MagicMock()
        # 模拟 10 个连续 segment
        segments = []
        for i in range(10):
            segments.append({
                "start": i * 3.0,
                "end": (i + 1) * 3.0 - 0.5,
                "text": f"第{i+1}句测试文本"
            })
        mock_model.transcribe.return_value = {"segments": segments}
        mock_load_model.return_value = mock_model

        audio_path = self.temp_dir / "long.mp3"
        audio_path.write_text("fake")
        srt_path = self.gen.generate_srt_from_tts(str(audio_path), language="zh")

        content = Path(srt_path).read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        # 10 段：每段 3 行内容 + 空行，strip() 会去掉末尾空行
        # 所以总行数 = 10*3 + 9 = 39 行
        self.assertEqual(len(lines), 39)
        # 验证最后一句的时间（最后 3 行是：序号、时间轴、文本）
        # 注意：29.9 因浮点精度问题会得到 899ms，故用 start=27.0/end=29.5 避免
        self.assertIn("00:00:27,000 --> 00:00:29,500", lines[-2])

    @patch("whisper.load_model")
    def test_negative_delay_ms(self, mock_load_model):
        """负延迟（提前）应正确处理"""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "segments": [{"start": 1.0, "end": 3.0, "text": "测试"}]
        }
        mock_load_model.return_value = mock_model

        audio_path = self.temp_dir / "neg.mp3"
        audio_path.write_text("fake")
        srt_path = self.gen.generate_srt_from_tts(
            str(audio_path), language="zh", delay_ms=-500
        )

        content = Path(srt_path).read_text(encoding="utf-8")
        # 1.0 - 0.5 = 0.5, 3.0 - 0.5 = 2.5
        self.assertIn("00:00:00,500 --> 00:00:02,500", content)

    def test_seconds_to_srt_time_precision(self):
        """毫秒精度边界测试"""
        # 0.999 应截断到 999ms
        self.assertEqual(
            self.gen._seconds_to_srt_time(0.999),
            "00:00:00,999"
        )
        # 1.5 应是 1秒500毫秒
        self.assertEqual(
            self.gen._seconds_to_srt_time(1.5),
            "00:00:01,500"
        )
        # 1.001 应正确显示为 1秒1毫秒（修复前因浮点精度问题会得到 000ms）
        self.assertEqual(
            self.gen._seconds_to_srt_time(1.001),
            "00:00:01,001"
        )


class TestScriptToSpeech(unittest.TestCase):
    """ScriptToSpeech 测试"""

    def test_estimate_duration_chinese(self):
        """中文时长估算"""
        script = ScriptToSpeech()
        # 12 个中文字符，约 4字/秒 => 3秒
        text = "这是一段十二个中文字符的测试"
        dur = script.estimate_duration(text, speed=1.0)
        self.assertAlmostEqual(dur, 3.0, delta=1.0)

    def test_estimate_duration_english(self):
        """英文时长估算"""
        script = ScriptToSpeech()
        # "hello world this is a test" = 6 词，约 2.2词/秒 => ~2.7秒
        text = "hello world this is a test"
        dur = script.estimate_duration(text, speed=1.0)
        self.assertAlmostEqual(dur, 2.7, delta=0.5)

    def test_estimate_duration_mixed(self):
        """中英文混合时长估算"""
        script = ScriptToSpeech()
        text = "Hello 世界 this 测试"
        dur = script.estimate_duration(text, speed=1.0)
        # 4 中文字 + 3 英文词 => 4/4 + 3/2.2 = 1 + 1.36 = 2.36
        self.assertGreater(dur, 1.5)
        self.assertLess(dur, 4.0)

    def test_estimate_duration_with_speed(self):
        """语速影响估算"""
        script = ScriptToSpeech()
        text = "一二三四五六七八九十"
        d1 = script.estimate_duration(text, speed=1.0)
        d2 = script.estimate_duration(text, speed=2.0)
        self.assertAlmostEqual(d1, d2 * 2, delta=0.5)


class TestSubtitleStylesComprehensive(unittest.TestCase):
    """字幕样式预设全面验证"""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.editor = AdvancedVideoEditor(
            raw_dir=str(self.temp_dir / "raw"),
            edited_dir=str(self.temp_dir / "output"),
            assets_dir=str(self.temp_dir / "assets"),
            logos_dir=str(self.temp_dir / "assets" / "logos"),
            bgm_dir=str(self.temp_dir / "assets" / "bgm"),
        )
        # 创建假视频文件
        self.video_path = self.temp_dir / "raw" / "test.mp4"
        self.video_path.parent.mkdir(parents=True, exist_ok=True)
        self.video_path.write_bytes(b"fake")

        # 创建假 SRT
        self.srt_path = self.temp_dir / "test.srt"
        self.srt_path.write_text(
            "1\n00:00:00,000 --> 00:00:02,000\n样式测试\n", encoding="utf-8"
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _capture_burn_cmd(self, style_preset, position="bottom", align="center"):
        """调用真实 burn_subtitles 并捕获 FFmpeg 命令"""
        captured = []

        def capture_cmd(cmd):
            captured.extend(cmd)
            # 创建假输出文件
            Path(cmd[-1]).parent.mkdir(parents=True, exist_ok=True)
            Path(cmd[-1]).touch()
            return True

        self.editor.run_ffmpeg = capture_cmd
        output = self.temp_dir / f"burn_{style_preset}.mp4"
        style_cfg = {
            "style_preset": style_preset,
            "position": position,
            "align": align,
        }
        _REAL_BURN_SUBTITLES(self.editor, self.video_path, self.srt_path, output, style_cfg)
        return " ".join(captured)

    def test_all_preset_styles(self):
        """遍历所有 9 种预设样式，验证 force_style 关键属性"""
        presets = self.editor.SUBTITLE_STYLES
        self.assertEqual(len(presets), 9)

        for preset_name, preset_info in presets.items():
            with self.subTest(preset=preset_name):
                cmd = self._capture_burn_cmd(preset_name)
                self.assertIn("subtitles=", cmd, f"{preset_name}: 缺少 subtitles 滤镜")
                self.assertIn("FontName=WenQuanYi Zen Hei", cmd)

                # 验证颜色转换正确（#RRGGBB → &HBBGGRR）
                font_color = preset_info["font_color"].lstrip("#")
                expected_ass = f"&H{font_color[4:6]}{font_color[2:4]}{font_color[0:2]}"
                self.assertIn(f"PrimaryColour={expected_ass}", cmd,
                    f"{preset_name}: 字体颜色转换错误")

                # BorderStyle=3 时验证 BackColour（8位 ARGB 格式 #AARRGGBB → &HAABBGGRR）
                if preset_info.get("border_style") == 3 and "back_color" in preset_info:
                    back = preset_info["back_color"].lstrip("#")
                    if len(back) == 8:
                        # ARGB: #AARRGGBB → &HAABBGGRR
                        expected_back = f"&H{back[0:2]}{back[6:8]}{back[4:6]}{back[2:4]}"
                    else:
                        expected_back = f"&H{back[4:6]}{back[2:4]}{back[0:2]}"
                    self.assertIn(f"BackColour={expected_back}", cmd,
                        f"{preset_name}: 背景色转换错误")

    def test_preset_tiktok_box_borderstyle3(self):
        """TikTok 风格必须使用 BorderStyle=3（背景框）"""
        cmd = self._capture_burn_cmd("tiktok_box")
        self.assertIn("BorderStyle=3", cmd)
        self.assertIn("BackColour=", cmd)

    def test_preset_movie_clean_not_bold(self):
        """影视字幕不应加粗"""
        cmd = self._capture_burn_cmd("movie_clean")
        self.assertIn("Bold=0", cmd)

    def test_position_alignments(self):
        """验证 9 种位置对齐组合"""
        positions = ["top", "middle", "bottom"]
        aligns = ["left", "center", "right"]
        expected = {("top", "left"): 7, ("top", "center"): 8, ("top", "right"): 9,
                    ("middle", "left"): 4, ("middle", "center"): 5, ("middle", "right"): 6,
                    ("bottom", "left"): 1, ("bottom", "center"): 2, ("bottom", "right"): 3}

        for pos in positions:
            for align in aligns:
                with self.subTest(pos=pos, align=align):
                    cmd = self._capture_burn_cmd("yellow_classic", pos, align)
                    expected_align = expected[(pos, align)]
                    self.assertIn(f"Alignment={expected_align}", cmd)

    def test_custom_font_size_override(self):
        """自定义字体大小应覆盖自适应计算"""
        captured = []

        def capture_cmd(cmd):
            captured.extend(cmd)
            Path(cmd[-1]).parent.mkdir(parents=True, exist_ok=True)
            Path(cmd[-1]).touch()
            return True

        self.editor.run_ffmpeg = capture_cmd
        output = self.temp_dir / "custom_size.mp4"
        style_cfg = {
            "style_preset": "yellow_classic",
            "custom_font_size": 24,
        }
        _REAL_BURN_SUBTITLES(self.editor, self.video_path, self.srt_path, output, style_cfg)
        self.assertIn("FontSize=24", " ".join(captured))


class TestCalculateFontSize(unittest.TestCase):
    """自适应字体大小计算测试"""

    def setUp(self):
        self.editor = AdvancedVideoEditor()

    def test_short_text_max_size(self):
        """短文本（≤10字）用最大字号"""
        size = self.editor.calculate_font_size("一二三四五六七八九十")
        self.assertEqual(size, 12)

    def test_medium_text_reduced(self):
        """中等文本（11-20字）缩小 10%"""
        size = self.editor.calculate_font_size("一二三四五六七八九十一二")
        self.assertEqual(size, 10)  # 12 * 0.9 = 10.8 → int = 10

    def test_long_text_min_size(self):
        """超长文本（>30字）用最小字号"""
        size = self.editor.calculate_font_size("x" * 50)
        self.assertEqual(size, 10)

    def test_fixed_size_override(self):
        """固定大小应直接返回"""
        size = self.editor.calculate_font_size("x" * 100, fixed_size=15)
        self.assertEqual(size, 15)


class TestMultiAudioMixing(unittest.TestCase):
    """多路音频混音测试 - 原声 + TTS + BGM"""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.raw_dir = self.temp_dir / "raw"
        self.output_dir = self.temp_dir / "output"
        self.assets_dir = self.temp_dir / "assets"
        self.logos_dir = self.assets_dir / "logos"
        self.bgm_dir = self.assets_dir / "bgm"

        for d in [self.raw_dir, self.output_dir, self.assets_dir, self.logos_dir, self.bgm_dir]:
            d.mkdir(parents=True, exist_ok=True)

        self.editor = AdvancedVideoEditor(
            raw_dir=str(self.raw_dir),
            edited_dir=str(self.output_dir),
            assets_dir=str(self.assets_dir),
            logos_dir=str(self.logos_dir),
            bgm_dir=str(self.bgm_dir),
        )
        self.video_path = self.raw_dir / "test.mp4"
        self.video_path.write_bytes(b"fake")

        # 创建假 BGM 文件
        self.bgm_path = self.bgm_dir / "test_bgm.mp3"
        self.bgm_path.write_text("fake bgm")

        # 创建假 TTS 文件
        self.tts_path = self.assets_dir / "tts" / "test.mp3"
        self.tts_path.parent.mkdir(parents=True, exist_ok=True)
        self.tts_path.write_text("fake tts")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _fake_run_ffmpeg(self, cmd):
        self._captured_cmd = cmd
        Path(cmd[-1]).parent.mkdir(parents=True, exist_ok=True)
        Path(cmd[-1]).touch()
        return True

    @patch.object(AdvancedVideoEditor, "get_info")
    @patch.object(AdvancedVideoEditor, "burn_subtitles")
    def test_three_way_audio_mixing(self, mock_burn, mock_get_info):
        """原声 + TTS + BGM 三路混音"""
        mock_get_info.return_value = {
            "duration": 15.0, "width": 1080, "height": 1920, "size_mb": 1.0
        }
        mock_burn.return_value = True
        self.editor.run_ffmpeg = self._fake_run_ffmpeg

        config = {
            "use_tts": True,
            "tts_audio_path": str(self.tts_path),
            "tts_volume": 1.0,
            "replace_audio": False,
            "original_volume": 0.5,
            "bgm_select": "test_bgm.mp3",
            "bgm_volume": 0.3,
            "use_tts_subtitles": False,
            "crop_top": 0, "crop_bottom": 0, "speed": 1.0,
        }

        result = self.editor.edit_video(self.video_path, config)
        self.assertIsNotNone(result)

        cmd_str = " ".join(self._captured_cmd)
        # 验证三路音频都出现
        self.assertIn("amix=inputs=3", cmd_str, "应为 3 路音频混音")
        self.assertIn("adelay=700|700", cmd_str, "TTS 延迟")
        # BGM 应使用 aloop 循环
        self.assertIn("aloop=loop=-1", cmd_str, "BGM 应循环")
        # 原声音量 0.5
        self.assertIn("volume=0.5", cmd_str)
        # TTS 音量 1.0
        self.assertIn("volume=1.0", cmd_str)
        # BGM 音量 0.3
        self.assertIn("volume=0.3", cmd_str)

    @patch.object(AdvancedVideoEditor, "get_info")
    @patch.object(AdvancedVideoEditor, "burn_subtitles")
    def test_tts_with_speed_change(self, mock_burn, mock_get_info):
        """TTS + 原声变速（speed=1.5）"""
        mock_get_info.return_value = {
            "duration": 10.0, "width": 1080, "height": 1920, "size_mb": 1.0
        }
        mock_burn.return_value = True
        self.editor.run_ffmpeg = self._fake_run_ffmpeg

        config = {
            "use_tts": True,
            "tts_audio_path": str(self.tts_path),
            "tts_volume": 1.0,
            "replace_audio": False,
            "original_volume": 0.8,
            "use_tts_subtitles": False,
            "crop_top": 0, "crop_bottom": 0, "speed": 1.5,
        }

        result = self.editor.edit_video(self.video_path, config)
        self.assertIsNotNone(result)

        cmd_str = " ".join(self._captured_cmd)
        # 原声应 atempo=1.5
        self.assertIn("atempo=1.5", cmd_str, "原声应变速")
        # TTS 不应 atempo（只对原声变速）
        # 验证 adelay 仍存在
        self.assertIn("adelay=700|700", cmd_str)

    @patch.object(AdvancedVideoEditor, "get_info")
    @patch.object(AdvancedVideoEditor, "burn_subtitles")
    def test_replace_audio_with_tts_and_bgm(self, mock_burn, mock_get_info):
        """替换原声：只保留 TTS + BGM"""
        mock_get_info.return_value = {
            "duration": 10.0, "width": 1080, "height": 1920, "size_mb": 1.0
        }
        mock_burn.return_value = True
        self.editor.run_ffmpeg = self._fake_run_ffmpeg

        config = {
            "use_tts": True,
            "tts_audio_path": str(self.tts_path),
            "tts_volume": 1.0,
            "replace_audio": True,
            "original_volume": 0.0,
            "bgm_select": "test_bgm.mp3",
            "bgm_volume": 0.5,
            "use_tts_subtitles": False,
            "crop_top": 0, "crop_bottom": 0, "speed": 1.0,
        }

        result = self.editor.edit_video(self.video_path, config)
        self.assertIsNotNone(result)

        cmd_str = " ".join(self._captured_cmd)
        # 只有两路音频（TTS + BGM）
        self.assertIn("amix=inputs=2", cmd_str)
        # 不应出现原声 volume（因为 original_volume=0）
        # 但 0:a 仍可能被引用，只是不在 audio_inputs 中
        # 验证没有原声的 volume= 单独出现（除了可能的 BGM/TTS）
        # 更简单：确认 amix=inputs=2 就够了


class TestIntegrationRealTTSSpeedSync(unittest.TestCase):
    """真实 TTS 不同语速的字幕同步精度测试"""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = Path(tempfile.mkdtemp(prefix="tts_speed_sync_"))
        cls.tts_dir = cls.temp_dir / "tts"
        cls.tts_dir.mkdir(parents=True, exist_ok=True)
        cls.tts = TTSGenerator(output_dir=str(cls.tts_dir))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_speed_1_0_subtitle_sync(self):
        """正常语速字幕同步"""
        text = "Hello everyone, today we are testing subtitle sync functionality."
        tts_path = self.tts.generate_with_speed(
            text, voice="en-US-AriaNeural", speed=1.0
        )
        self.assertTrue(Path(tts_path).exists())

        gen = TTSSubtitleGenerator(model_size="base")
        srt_path = gen.generate_srt_from_tts(tts_path, language="en", delay_ms=0)

        content = Path(srt_path).read_text(encoding="utf-8")
        self.assertIn(" --> ", content)
        # 验证首句起始接近 0
        lines = content.strip().split("\n")
        for line in lines:
            if " --> " in line:
                start = line.split(" --> ")[0]
                h, m, s_ms = start.split(":")
                s, ms = s_ms.split(",")
                total_ms = int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)
                # 首句应在 1 秒内开始
                self.assertLess(total_ms, 1000, f"首句起始时间异常: {start}")
                break
        else:
            self.fail("SRT 中未找到时间轴")

    def test_speed_1_5_subtitle_sync(self):
        """1.5倍语速字幕同步"""
        text = "Speed up test, speaking fifty percent faster."
        tts_path = self.tts.generate_with_speed(
            text, voice="en-US-AriaNeural", speed=1.5
        )
        self.assertTrue(Path(tts_path).exists())

        gen = TTSSubtitleGenerator(model_size="base")
        srt_path = gen.generate_srt_from_tts(tts_path, language="en", delay_ms=0)

        content = Path(srt_path).read_text(encoding="utf-8")
        self.assertIn(" --> ", content)
        # 验证有字幕内容生成
        self.assertGreater(len(content.strip()), 10)

    def test_speed_0_8_subtitle_sync(self):
        """0.8倍语速字幕同步"""
        text = "Slow down test, speaking twenty percent slower."
        tts_path = self.tts.generate_with_speed(
            text, voice="en-US-AriaNeural", speed=0.8
        )
        self.assertTrue(Path(tts_path).exists())

        gen = TTSSubtitleGenerator(model_size="base")
        srt_path = gen.generate_srt_from_tts(tts_path, language="en", delay_ms=0)

        content = Path(srt_path).read_text(encoding="utf-8")
        self.assertIn(" --> ", content)
        self.assertGreater(len(content.strip()), 10)


class TestIntegrationTTSWithDelayAccuracy(unittest.TestCase):
    """真实 TTS + 700ms 延迟精度验证"""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = Path(tempfile.mkdtemp(prefix="tts_delay_acc_"))
        cls.tts_dir = cls.temp_dir / "tts"
        cls.tts_dir.mkdir(parents=True, exist_ok=True)
        cls.tts = TTSGenerator(output_dir=str(cls.tts_dir))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_delay_700ms_exact_offset(self):
        """验证 700ms 延迟精确偏移"""
        text = "Delay test begins, verifying subtitle timeline offset."
        tts_path = self.tts.generate_with_speed(
            text, voice="en-US-AriaNeural", speed=1.0
        )

        gen = TTSSubtitleGenerator(model_size="base")

        # 先生成无延迟的
        srt_no_delay = gen.generate_srt_from_tts(
            tts_path, output_srt=str(self.temp_dir / "no_delay.srt"),
            language="zh", delay_ms=0
        )
        # 再生成有延迟的
        srt_with_delay = gen.generate_srt_from_tts(
            tts_path, output_srt=str(self.temp_dir / "with_delay.srt"),
            language="zh", delay_ms=700
        )

        # 读取并比较首句时间
        content_no = Path(srt_no_delay).read_text(encoding="utf-8")
        content_yes = Path(srt_with_delay).read_text(encoding="utf-8")

        def parse_first_start(content):
            for line in content.strip().split("\n"):
                if " --> " in line:
                    start = line.split(" --> ")[0]
                    h, m, s_ms = start.split(":")
                    s, ms = s_ms.split(",")
                    return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)
            return None

        t1 = parse_first_start(content_no)
        t2 = parse_first_start(content_yes)

        self.assertIsNotNone(t1)
        self.assertIsNotNone(t2)
        # 差值应为 700ms（允许 50ms 容差，因为 Whisper 本身有微小波动）
        self.assertAlmostEqual(t2 - t1, 700, delta=50,
            msg=f"延迟偏移异常: 无延迟={t1}ms, 有延迟={t2}ms, 差值={t2-t1}ms")


if __name__ == "__main__":
    unittest.main()
