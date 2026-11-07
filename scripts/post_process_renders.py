import subprocess
import os
import sys

FFMPEG = r"C:\Users\lenovo\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"

def post_process():
    input_1080p = "out/climora_1080p.mp4"
    output_4k = "out/climora_4k.mp4"
    output_captions = "out/climora_1080p_captions.mp4"
    srt_file = "out/climora_captions.srt"

    if not os.path.exists(input_1080p):
        print(f"Error: {input_1080p} does not exist yet.")
        sys.exit(1)

    # 1. Generate 4K Master (3840x2160) using high-quality Lanczos scaling + pristine CRF 17
    print(f"Generating 4K Master: {output_4k}...")
    cmd_4k = [
        FFMPEG, "-y",
        "-i", input_1080p,
        "-vf", "scale=3840:2160:flags=lanczos",
        "-c:v", "libx264",
        "-crf", "17",
        "-preset", "medium",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        output_4k
    ]
    subprocess.run(cmd_4k, check=True)
    print(f"Successfully generated {output_4k} ({os.path.getsize(output_4k)} bytes)")

    # 2. Generate Burned-in Captions Proxy
    if os.path.exists(srt_file):
        print(f"Generating Burned-in Captions Proxy: {output_captions}...")
        # Escape path for FFmpeg subtitles filter on Windows
        srt_escaped = srt_file.replace("\\", "/").replace(":", "\\:")
        cmd_sub = [
            FFMPEG, "-y",
            "-i", input_1080p,
            "-vf", f"subtitles='{srt_escaped}':force_style='Fontname=Arial,Fontsize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=4,MarginV=35'",
            "-c:v", "libx264",
            "-crf", "20",
            "-preset", "fast",
            "-c:a", "copy",
            output_captions
        ]
        try:
            subprocess.run(cmd_sub, check=True)
            print(f"Successfully generated {output_captions} ({os.path.getsize(output_captions)} bytes)")
        except Exception as e:
            print(f"Subtitles filter warning: {e}. Copying proxy.")
            subprocess.run([FFMPEG, "-y", "-i", input_1080p, "-c", "copy", output_captions], check=True)

if __name__ == "__main__":
    post_process()

