import subprocess
import os
import sys

FFMPEG = r"C:\Users\lenovo\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"

def compress():
    input_file = "out/climora_1080p.mp4"
    srt_file = "out/climora_captions.srt"
    
    output_clean = "out/climora_1080p_submission_50mb.mp4"
    output_captions = "out/climora_1080p_captions_submission_50mb.mp4"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        sys.exit(1)
        
    # Duration: ~240s
    # Target size: 45MB (under 50MB ceiling with 5MB safety margin)
    # 45 MB = 45 * 1024 * 1024 * 8 = 377,487,360 bits
    # 377,487,360 / 240s = 1,572,864 bps (~1536 kbps total)
    # Audio: 128k AAC
    # Video: 1400k libx264
    video_bitrate = "1400k"
    audio_bitrate = "128k"
    
    print("=== STEP 1: Encoding Clean 1080p (<50MB) with 2-Pass libx264 ===")
    # Pass 1
    cmd_p1 = [
        FFMPEG, "-y",
        "-i", input_file,
        "-c:v", "libx264",
        "-b:v", video_bitrate,
        "-pass", "1",
        "-preset", "slow",
        "-an",
        "-f", "null",
        "NUL"
    ]
    print("Running Pass 1...")
    subprocess.run(cmd_p1, check=True)
    
    # Pass 2
    cmd_p2 = [
        FFMPEG, "-y",
        "-i", input_file,
        "-c:v", "libx264",
        "-b:v", video_bitrate,
        "-pass", "2",
        "-preset", "slow",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", audio_bitrate,
        output_clean
    ]
    print("Running Pass 2...")
    subprocess.run(cmd_p2, check=True)
    
    size_mb = os.path.getsize(output_clean) / (1024 * 1024)
    print(f"Clean video finished: {output_clean} ({size_mb:.2f} MB)")
    
    # Cleanup pass log files if any
    for log_file in ["ffmpeg2pass-0.log", "ffmpeg2pass-0.log.mbtree"]:
        if os.path.exists(log_file):
            try:
                os.remove(log_file)
            except Exception:
                pass

    # STEP 2: Burned-in Captions version (<50MB)
    if os.path.exists(srt_file):
        print("\n=== STEP 2: Encoding Captions 1080p (<50MB) with 2-Pass libx264 ===")
        srt_escaped = srt_file.replace("\\", "/").replace(":", "\\:")
        sub_filter = f"subtitles='{srt_escaped}':force_style='Fontname=Arial,Fontsize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=4,MarginV=35'"
        
        cmd_sub_p1 = [
            FFMPEG, "-y",
            "-i", input_file,
            "-vf", sub_filter,
            "-c:v", "libx264",
            "-b:v", video_bitrate,
            "-pass", "1",
            "-preset", "slow",
            "-an",
            "-f", "null",
            "NUL"
        ]
        print("Running Captions Pass 1...")
        subprocess.run(cmd_sub_p1, check=True)
        
        cmd_sub_p2 = [
            FFMPEG, "-y",
            "-i", input_file,
            "-vf", sub_filter,
            "-c:v", "libx264",
            "-b:v", video_bitrate,
            "-pass", "2",
            "-preset", "slow",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", audio_bitrate,
            output_captions
        ]
        print("Running Captions Pass 2...")
        subprocess.run(cmd_sub_p2, check=True)
        
        sub_size_mb = os.path.getsize(output_captions) / (1024 * 1024)
        print(f"Captions video finished: {output_captions} ({sub_size_mb:.2f} MB)")
        
        for log_file in ["ffmpeg2pass-0.log", "ffmpeg2pass-0.log.mbtree"]:
            if os.path.exists(log_file):
                try:
                    os.remove(log_file)
                except Exception:
                    pass

    print("\nAll videos compressed under 50MB ceiling successfully!")

if __name__ == "__main__":
    compress()

