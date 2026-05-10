"""
TTS 同步字幕功能单元测试
覆盖: TTSSubtitleGenerator, AdvancedVideoEditor 字幕分支与互斥逻辑
"""
import os
import sys
import json
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, ANY

# 将项目根目录和 core 目录加入路径
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "core"))

from tts_generator import TTSSubtitleGenerator
from editor_advanced import AdvancedVideoEditor

# 保存真实方法引用，供需要绕过 mock 的测试使用
_REAL_BURN_SUBTITLES = AdvancedVideoEditor.burn_subtitles
_REAL_RUN_FFMPEG = AdvancedVideoEditor.run_ffmpeg


class TestTTSSubtitleGenerator(unittest.TestCase):
    """TTSSubtitleGenerator 核心测试"""

    def setUp(self):
        self.gen = TTSSubtitleGenerator(model_size="base")
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_seconds_to_srt_time(self):
        """时间格式转换边界值测试"""
        self.assertEqual(self.gen._seconds_to_srt_time(0), "00:00:00,000")
        self.assertEqual(self.gen._seconds_to_srt_time(1.5), "00:00:01,500")
        self.assertEqual(self.gen._seconds_to_srt_time(3661.123), "01:01:01,123")
        self.assertEqual(self.gen._seconds_to_srt_time(59.999), "00:00:59,999")

    @patch("whisper.load_model")
    def test_generate_srt_from_tts_mock(self, mock_load_model):
        """Mock Whisper 转录，验证 SRT 输出格式与内容"""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "segments": [
                {"start": 0.0, "end": 2.5, "text": "  大家好  "},
                {"start": 2.5, "end": 5.0, "text": "这是测试语音"},
                {"start": 5.0, "end": 7.88, "text": "谢谢观看"},
            ]
        }
        mock_load_model.return_value = mock_model

        audio_path = self.temp_dir / "test.mp3"
        audio_path.write_text("fake audio")  # 仅用于存在性检查
        srt_path = self.temp_dir / "test.srt"

        result = self.gen.generate_srt_from_tts(str(audio_path), str(srt_path), language="zh")

        self.assertEqual(Path(result), srt_path)
        self.assertTrue(srt_path.exists())

        content = srt_path.read_text(encoding="utf-8")
        lines = content.strip().split("\n")

        # 验证整体结构: 3 段 × 4 行 = 12 行（无末尾空行时）
        # 实际文件末尾有一个 ""，split 后不会多出空行
        self.assertIn("1", lines[0])
        self.assertIn("00:00:00,000 --> 00:00:02,500", lines[1])
        self.assertEqual("大家好", lines[2])

        self.assertIn("2", lines[4])
        self.assertIn("00:00:02,500 --> 00:00:05,000", lines[5])
        self.assertEqual("这是测试语音", lines[6])

        self.assertIn("3", lines[8])
        # 7.88s 应正确转换为 07,880（修复前因浮点精度可能得到 07,879）
        self.assertTrue(
            lines[9].startswith("00:00:05,000 --> 00:00:07,880"),
            f"Unexpected time line: {lines[9]}"
        )
        self.assertEqual("谢谢观看", lines[10])

        # 验证 Whisper 调用参数
        mock_model.transcribe.assert_called_once_with(
            str(audio_path), language="zh", verbose=False
        )

    @patch("whisper.load_model")
    def test_generate_srt_with_delay(self, mock_load_model):
        """验证 delay_ms 能正确偏移字幕时间轴"""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "segments": [
                {"start": 0.0, "end": 2.0, "text": "你好"},
                {"start": 2.0, "end": 4.5, "text": "世界"},
            ]
        }
        mock_load_model.return_value = mock_model

        audio_path = self.temp_dir / "delay.mp3"
        audio_path.write_text("fake audio")
        srt_path = self.temp_dir / "delay.srt"

        result = self.gen.generate_srt_from_tts(
            str(audio_path), str(srt_path), language="zh", delay_ms=700
        )

        content = Path(result).read_text(encoding="utf-8")
        lines = content.strip().split("\n")

        # 0.0+0.7=0.7, 2.0+0.7=2.7
        self.assertIn("00:00:00,700 --> 00:00:02,700", lines[1])
        # 2.0+0.7=2.7, 4.5+0.7=5.2
        self.assertIn("00:00:02,700 --> 00:00:05,200", lines[5])

    @patch("whisper.load_model")
    def test_lazy_load_whisper(self, mock_load_model):
        """验证 Whisper 模型懒加载且仅加载一次"""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"segments": []}
        mock_load_model.return_value = mock_model

        # 首次调用触发加载
        audio_path = self.temp_dir / "a.mp3"
        audio_path.write_text("fake")
        self.gen.generate_srt_from_tts(str(audio_path))
        self.assertEqual(mock_load_model.call_count, 1)

        # 第二次调用不再加载
        audio_path2 = self.temp_dir / "b.mp3"
        audio_path2.write_text("fake")
        self.gen.generate_srt_from_tts(str(audio_path2))
        self.assertEqual(mock_load_model.call_count, 1)


class TestAdvancedVideoEditorTTSSubtitles(unittest.TestCase):
    """AdvancedVideoEditor TTS 字幕剪辑分支测试"""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.raw_dir = self.temp_dir / "videos" / "raw"
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

        # 构造一个合法的假视频文件（FFmpeg 不需要真正解析它，因为我们 mock get_info）
        self.video_path = self.raw_dir / "test_note.mp4"
        self.video_path.write_bytes(b"fake mp4")

        # 初始化测试捕获变量
        self._captured_srt_content = None
        self._captured_ffmpeg_cmd = None

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _make_burn_create_file(self, *args, **kwargs):
        """side_effect：让 burn_subtitles 调用时创建 final_output 文件，避免 rename 失败，同时捕获 SRT 内容"""
        srt_path = Path(args[1])
        if srt_path.exists():
            self._captured_srt_content = srt_path.read_text(encoding="utf-8")
        Path(args[2]).parent.mkdir(parents=True, exist_ok=True)
        Path(args[2]).touch()
        return True

    def _fake_run_ffmpeg(self, cmd):
        """模拟 FFmpeg 成功执行，并创建输出文件，同时捕获命令用于断言"""
        self._captured_ffmpeg_cmd = cmd
        output_path = Path(cmd[-1])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.touch()
        return True

    @patch.object(AdvancedVideoEditor, "get_info")
    @patch.object(AdvancedVideoEditor, "run_ffmpeg")
    @patch.object(AdvancedVideoEditor, "burn_subtitles")
    @patch.object(TTSSubtitleGenerator, "generate_srt_from_tts")
    def test_edit_video_with_tts_subtitles(
        self, mock_gen_srt, mock_burn, mock_run_ffmpeg, mock_get_info
    ):
        """开启 use_tts_subtitles 时，应生成 SRT 并调用 burn_subtitles"""
        mock_get_info.return_value = {
            "duration": 10.0, "width": 1080, "height": 1920, "size_mb": 1.0
        }
        mock_run_ffmpeg.side_effect = self._fake_run_ffmpeg
        mock_burn.side_effect = self._make_burn_create_file

        # 模拟生成的 SRT 文件
        srt_path = self.output_dir / "test_note.srt"
        srt_path.write_text(
            "1\n00:00:00,000 --> 00:00:02,500\n大家好\n", encoding="utf-8"
        )
        mock_gen_srt.return_value = str(srt_path)

        tts_path = self.assets_dir / "tts" / "tts_test.mp3"
        tts_path.parent.mkdir(parents=True, exist_ok=True)
        tts_path.write_text("fake tts")

        config = {
            "use_tts": True,
            "tts_audio_path": str(tts_path),
            "use_tts_subtitles": True,
            "subtitle_style": "yellow_classic",
            "subtitle_font_size": 12,
            "subtitle_position": "bottom",
            "subtitle_align": "center",
            "subtitle_outline_width": 2,
            "crop_top": 0,
            "crop_bottom": 0,
            "speed": 1.0,
        }

        result = self.editor.edit_video(self.video_path, config)

        self.assertIsNotNone(result)
        self.assertTrue(Path(result).exists())
        mock_gen_srt.assert_called_once()
        mock_burn.assert_called_once()

        # 验证生成字幕时传入了 700ms 延迟
        self.assertEqual(mock_gen_srt.call_args.kwargs.get("delay_ms"), 700)

        # 验证传给 burn_subtitles 的样式配置
        _, _, _, style_cfg = mock_burn.call_args[0]
        self.assertEqual(style_cfg["style_preset"], "yellow_classic")
        self.assertEqual(style_cfg["font_size"], 12)
        self.assertEqual(style_cfg["position"], "bottom")

        # 验证 FFmpeg 命令中包含 TTS 延迟滤镜
        filter_complex = " ".join(self._captured_ffmpeg_cmd)
        self.assertIn("adelay=700|700", filter_complex)

    @patch.object(AdvancedVideoEditor, "get_info")
    @patch.object(AdvancedVideoEditor, "run_ffmpeg")
    @patch.object(AdvancedVideoEditor, "burn_subtitles")
    @patch.object(TTSSubtitleGenerator, "generate_srt_from_tts")
    def test_manual_subtitle_takes_priority_over_tts(
        self, mock_gen_srt, mock_burn, mock_run_ffmpeg, mock_get_info
    ):
        """手动字幕与 TTS 同步字幕同时开启时，优先使用手动字幕"""
        mock_get_info.return_value = {
            "duration": 10.0, "width": 1080, "height": 1920, "size_mb": 1.0
        }
        mock_run_ffmpeg.side_effect = self._fake_run_ffmpeg
        mock_burn.side_effect = self._make_burn_create_file

        tts_path = self.assets_dir / "tts" / "tts_test.mp3"
        tts_path.parent.mkdir(parents=True, exist_ok=True)
        tts_path.write_text("fake tts")

        config = {
            "add_subtitles": True,
            "subtitle_text": "手动字幕内容",
            "subtitle_start": 1.0,
            "subtitle_end": 5.0,
            "subtitle_style": "movie_clean",
            "subtitle_font_size": 10,
            "subtitle_position": "middle",
            "subtitle_align": "left",
            "subtitle_outline_width": 1,
            "use_tts": True,
            "tts_audio_path": str(tts_path),
            "use_tts_subtitles": True,  # 同时开启
            "crop_top": 0,
            "crop_bottom": 0,
            "speed": 1.0,
        }

        result = self.editor.edit_video(self.video_path, config)

        self.assertIsNotNone(result)
        self.assertTrue(Path(result).exists())
        mock_burn.assert_called_once()
        mock_gen_srt.assert_not_called()  # TTS 字幕生成不应被触发

        # 验证 burn_subtitles 传入的 SRT 内容包含手动字幕
        self.assertIn("手动字幕内容", self._captured_srt_content)
        self.assertIn("00:00:01,000 --> 00:00:05,000", self._captured_srt_content)

        # 验证 FFmpeg 命令中仍包含 TTS 延迟（只是没走 TTS 字幕生成）
        filter_complex = " ".join(self._captured_ffmpeg_cmd)
        self.assertIn("adelay=700|700", filter_complex)

    @patch.object(AdvancedVideoEditor, "get_info")
    @patch.object(AdvancedVideoEditor, "run_ffmpeg")
    @patch.object(AdvancedVideoEditor, "burn_subtitles")
    @patch.object(TTSSubtitleGenerator, "generate_srt_from_tts")
    def test_no_tts_subtitles_when_unchecked(
        self, mock_gen_srt, mock_burn, mock_run_ffmpeg, mock_get_info
    ):
        """未勾选 use_tts_subtitles 时，仅使用 TTS 音频但不生成字幕"""
        mock_get_info.return_value = {
            "duration": 10.0, "width": 1080, "height": 1920, "size_mb": 1.0
        }
        mock_run_ffmpeg.side_effect = self._fake_run_ffmpeg
        mock_burn.return_value = True

        tts_path = self.assets_dir / "tts" / "tts_test.mp3"
        tts_path.parent.mkdir(parents=True, exist_ok=True)
        tts_path.write_text("fake tts")

        config = {
            "use_tts": True,
            "tts_audio_path": str(tts_path),
            "use_tts_subtitles": False,
            "crop_top": 0,
            "crop_bottom": 0,
            "speed": 1.0,
        }

        result = self.editor.edit_video(self.video_path, config)

        self.assertIsNotNone(result)
        mock_gen_srt.assert_not_called()
        mock_burn.assert_not_called()

        # 验证 FFmpeg 命令中仍包含 TTS 延迟滤镜
        filter_complex = " ".join(self._captured_ffmpeg_cmd)
        self.assertIn("adelay=700|700", filter_complex)

    @patch.object(AdvancedVideoEditor, "get_info")
    @patch.object(AdvancedVideoEditor, "run_ffmpeg")
    @patch.object(AdvancedVideoEditor, "burn_subtitles")
    @patch.object(TTSSubtitleGenerator, "generate_srt_from_tts")
    def test_tts_subtitle_burn_failure_fallback(
        self, mock_gen_srt, mock_burn, mock_run_ffmpeg, mock_get_info
    ):
        """字幕烧录失败时，应回退到无字幕版本"""
        mock_get_info.return_value = {
            "duration": 10.0, "width": 1080, "height": 1920, "size_mb": 1.0
        }
        mock_run_ffmpeg.side_effect = self._fake_run_ffmpeg
        mock_burn.return_value = False  # 模拟烧录失败

        srt_path = self.output_dir / "test_note.srt"
        srt_path.write_text("1\n00:00:00,000 --> 00:00:01,000\n测试\n", encoding="utf-8")
        mock_gen_srt.return_value = str(srt_path)

        tts_path = self.assets_dir / "tts" / "tts_test.mp3"
        tts_path.parent.mkdir(parents=True, exist_ok=True)
        tts_path.write_text("fake tts")

        config = {
            "use_tts": True,
            "tts_audio_path": str(tts_path),
            "use_tts_subtitles": True,
            "subtitle_style": "yellow_classic",
            "subtitle_font_size": 9,
            "subtitle_position": "bottom",
            "subtitle_align": "center",
            "subtitle_outline_width": 1,
            "crop_top": 0,
            "crop_bottom": 0,
            "speed": 1.0,
        }

        result = self.editor.edit_video(self.video_path, config)

        self.assertIsNotNone(result)
        mock_gen_srt.assert_called_once()
        mock_burn.assert_called_once()

        # 验证生成字幕时传入了 700ms 延迟
        self.assertEqual(mock_gen_srt.call_args.kwargs.get("delay_ms"), 700)

        # 由于 burn_subtitles 返回 False，最终输出文件仍应保留原始文件名（无 _sub）
        output_name = Path(result).name
        self.assertNotIn("_sub", output_name)

        # 验证 FFmpeg 命令中包含 TTS 延迟滤镜
        filter_complex = " ".join(self._captured_ffmpeg_cmd)
        self.assertIn("adelay=700|700", filter_complex)

    @patch.object(AdvancedVideoEditor, "get_info")
    @patch.object(AdvancedVideoEditor, "run_ffmpeg")
    @patch.object(AdvancedVideoEditor, "burn_subtitles")
    def test_no_tts_no_adelay(
        self, mock_burn, mock_run_ffmpeg, mock_get_info
    ):
        """未使用 TTS 时，FFmpeg 命令中不应出现 adelay 滤镜"""
        mock_get_info.return_value = {
            "duration": 10.0, "width": 1080, "height": 1920, "size_mb": 1.0
        }
        mock_run_ffmpeg.side_effect = self._fake_run_ffmpeg
        mock_burn.return_value = True

        config = {
            "use_tts": False,
            "crop_top": 0,
            "crop_bottom": 0,
            "speed": 1.0,
        }

        result = self.editor.edit_video(self.video_path, config)

        self.assertIsNotNone(result)
        filter_complex = " ".join(self._captured_ffmpeg_cmd)
        self.assertNotIn("adelay", filter_complex)

    @patch.object(AdvancedVideoEditor, "get_info")
    @patch.object(AdvancedVideoEditor, "run_ffmpeg")
    @patch.object(AdvancedVideoEditor, "burn_subtitles")
    def test_subtitle_safe_margins(
        self, mock_burn, mock_run_ffmpeg, mock_get_info
    ):
        """验证字幕左右安全边距为 60px，居中对齐时也生效"""
        mock_get_info.return_value = {
            "duration": 10.0, "width": 1080, "height": 1920, "size_mb": 1.0
        }
        mock_run_ffmpeg.side_effect = self._fake_run_ffmpeg
        mock_burn.side_effect = self._make_burn_create_file

        config = {
            "add_subtitles": True,
            "subtitle_text": "安全边距测试文案",
            "subtitle_style": "yellow_classic",
            "subtitle_position": "bottom",
            "subtitle_align": "center",
            "crop_top": 0,
            "crop_bottom": 0,
            "speed": 1.0,
        }

        result = self.editor.edit_video(self.video_path, config)

        self.assertIsNotNone(result)
        mock_burn.assert_called_once()

        # 验证 burn_subtitles 的 force_style 包含 60px 安全边距
        _, actual_srt_path, _, style_cfg = mock_burn.call_args[0]
        # 通过重新调用 burn_subtitles 内部的逻辑来验证最终 MarginL/MarginR
        # 更简单：直接检查 style_cfg 是否被正确构建
        # 但 style_cfg 是用户传入的，真正生成在 burn_subtitles 内部
        # 我们 patch burn_subtitles 来检查传入的参数
        # 这里我们直接验证 _captured_srt_content 即可，同时确认调用发生
        self.assertIn("安全边距测试文案", self._captured_srt_content)

        # 再直接调用一次 burn_subtitles 的入口，捕获其构建的 FFmpeg 命令
        import subprocess
        captured_cmd = []
        original_run = self.editor.run_ffmpeg

        def capture_cmd(cmd):
            captured_cmd.extend(cmd)
            return True

        self.editor.run_ffmpeg = capture_cmd
        test_srt = Path(actual_srt_path)
        test_output = self.output_dir / "margin_test.mp4"
        # 调用真实的 burn_subtitles（绕过 mock）
        _REAL_BURN_SUBTITLES(self.editor, self.video_path, test_srt, test_output, style_cfg)
        self.editor.run_ffmpeg = original_run

        cmd_str = " ".join(captured_cmd)
        self.assertIn("MarginL=60", cmd_str)
        self.assertIn("MarginR=60", cmd_str)
        print(f"\n✅ 安全边距验证通过: MarginL=60, MarginR=60")


if __name__ == "__main__":
    unittest.main()
