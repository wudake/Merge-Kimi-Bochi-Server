import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.audio_extractor import AudioExtractor
from src.downloader import VideoDownloader
from src.formatter import save
from src.local_transcriber import LocalTranscriber
from src.transcriber import Transcriber
from src.utils import extract_video_id, is_valid_video_url


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Video Script Extractor (Facebook / YouTube)")
    parser.add_argument("url", help="Facebook 或 YouTube 视频链接")
    parser.add_argument("--output", "-o", default="./output/result.txt", help="输出文件路径")
    parser.add_argument("--format", "-f", choices=["txt", "srt", "vtt", "json"], default="txt", help="输出格式")
    parser.add_argument("--language", "-l", default="en", help="音频语言 (如 zh, en)，auto 为自动检测")
    parser.add_argument("--temp-dir", default="./temp", help="临时文件目录")
    parser.add_argument("--keep-temp", action="store_true", help="保留临时文件")
    parser.add_argument("--local", action="store_true", help="使用本地 Whisper 模型（免费，无需 API Key）")
    parser.add_argument("--model-size", default="small", choices=["tiny", "base", "small", "medium", "large-v3"],
                        help="本地模型大小（仅 --local 生效）：tiny 最快，large-v3 最准")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"],
                        help="本地推理设备（仅 --local 生效）")
    args = parser.parse_args()

    if not is_valid_video_url(args.url):
        print(f"错误: 无效的视频链接，仅支持 Facebook 和 YouTube: {args.url}")
        sys.exit(1)

    video_id = extract_video_id(args.url) or "unknown"
    print(f"[1/4] 解析链接成功，视频标识: {video_id}")

    # 选择转录引擎
    if args.local:
        print("[模式] 本地 Whisper（免费）")
        transcriber = LocalTranscriber(
            model_size=args.model_size,
            device=args.device,
            language=None if args.language == "auto" else args.language,
        )
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("错误: 未设置 OPENAI_API_KEY 环境变量。如需免费方案，请加 --local 参数")
            sys.exit(1)
        print("[模式] OpenAI Whisper API（付费）")
        transcriber = Transcriber(api_key=api_key, language=args.language)

    downloader = VideoDownloader(temp_dir=args.temp_dir)
    extractor = AudioExtractor(temp_dir=args.temp_dir)

    try:
        print("[2/4] 正在下载视频...")
        video_path = downloader.download(args.url)
        print(f"      视频已下载: {video_path}")

        print("[3/4] 正在提取音频...")
        audio_path = extractor.extract(video_path)
        print(f"      音频已提取: {audio_path}")

        print("[4/4] 正在语音识别（可能需要几分钟）...")
        result = transcriber.transcribe(audio_path)
        print(f"      识别完成，语言: {result['language']}, 时长: {result['duration']:.1f}s")

        output_path = save(result, args.output, fmt=args.format)
        print(f"\n结果已保存: {output_path}")

    except Exception as e:
        print(f"处理失败: {e}")
        sys.exit(1)
    finally:
        if not args.keep_temp:
            for f in Path(args.temp_dir).iterdir():
                if f.is_file():
                    f.unlink()
            print("临时文件已清理")


if __name__ == "__main__":
    main()
