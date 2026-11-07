import os
import asyncio
import edge_tts

SAMPLE_DIR = "audio/samples"
os.makedirs(SAMPLE_DIR, exist_ok=True)

test_text = (
    "Every summer, cities across the Global South turn into furnaces. "
    "In Pune, pre-monsoon surface temperatures breach 46.3 degrees Celsius. "
    "Select the 1 Crore benchmark preset, that is 10 million rupees. "
    "The HiGHS solver isolates the optimal 28 priority cells across Pune, "
    "allocating exactly 2,695 shade trees to shelter over 118,000 citizens."
)

voices = [
    ("en-US-AndrewMultilingualNeural", "01_andrew_deep_documentary.mp3"),
    ("en-US-BrianMultilingualNeural", "02_brian_modern_keynote.mp3"),
    ("en-US-ChristopherNeural", "03_christopher_authoritative.mp3"),
    ("en-GB-RyanNeural", "04_ryan_british_documentary.mp3"),
    ("en-IN-NeerjaExpressiveNeural", "05_neerja_indian_expressive.mp3"),
]

async def make_samples():
    for voice, filename in voices:
        out_path = os.path.join(SAMPLE_DIR, filename)
        print(f"Generating sample for {voice} -> {out_path}...")
        comm = edge_tts.Communicate(test_text, voice)
        await comm.save(out_path)
        print(f"Done: {out_path} ({os.path.getsize(out_path)} bytes)")

if __name__ == "__main__":
    asyncio.run(make_samples())

