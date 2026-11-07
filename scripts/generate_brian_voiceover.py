import os
import re
import asyncio
import soundfile as sf
import numpy as np
import scipy.signal
import edge_tts
from faster_whisper import WhisperModel

VOICE = "en-US-BrianMultilingualNeural"
SAMPLE_RATE = 44100

SCENE_SLOTS = {
    "scene_01": 20.0,
    "scene_02": 25.0,
    "scene_03": 25.0,
    "scene_04": 20.0,
    "scene_05": 30.0,
    "scene_06": 30.0,
    "scene_07": 30.0,
    "scene_08": 25.0,
    "scene_09": 20.0,
    "scene_10": 15.0,
}

def parse_vo_script(script_path):
    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"### (SCENE \d+):.*?\n(.*?)(?=\n###|\Z)"
    matches = re.findall(pattern, content, re.DOTALL)
    scenes = {}
    for scene_id_raw, text in matches:
        sid_num = scene_id_raw.replace("SCENE ", "").strip()
        sid = f"scene_{int(sid_num):02d}"
        clean_text = text.strip()
        scenes[sid] = clean_text
    return scenes

async def synth_scene(sid, text, target_duration):
    # Ensure no dashes exist
    clean_text = text.replace("—", ", ").replace("–", ", ").replace("-", " ")
    clean_text = re.sub(r"\s+", " ", clean_text).strip()
    
    tmp_wav = f"audio/{sid}_raw.mp3"
    comm = edge_tts.Communicate(clean_text, VOICE, rate="+0%")
    await comm.save(tmp_wav)
    data, sr = sf.read(tmp_wav)
    dur = len(data) / sr

    # If longer than target duration - 0.5s, calculate needed rate boost
    if dur > (target_duration - 0.5):
        needed_ratio = dur / (target_duration - 1.2)
        rate_pct = int(min(18, max(2, (needed_ratio - 1.0) * 100)))
        print(f"  [{sid}] dur {dur:.2f}s > {target_duration}s. Re-synthesizing at rate=+{rate_pct}%...", flush=True)
        comm = edge_tts.Communicate(clean_text, VOICE, rate=f"+{rate_pct}%")
        await comm.save(tmp_wav)
        data, sr = sf.read(tmp_wav)
        dur = len(data) / sr

    if os.path.exists(tmp_wav):
        os.remove(tmp_wav)

    if len(data.shape) > 1:
        data = data[:, 0]
    data = data.astype(np.float32)

    # Fast polyphase resample if needed
    if sr != SAMPLE_RATE:
        if sr == 24000 and SAMPLE_RATE == 44100:
            data = scipy.signal.resample_poly(data, 147, 80)
        else:
            gcd = np.gcd(SAMPLE_RATE, sr)
            data = scipy.signal.resample_poly(data, SAMPLE_RATE // gcd, sr // gcd)

    actual_dur = len(data) / SAMPLE_RATE
    print(f"  [{sid}] finalized speech: {actual_dur:.2f}s (Slot: {target_duration:.2f}s)", flush=True)

    target_samples = int(target_duration * SAMPLE_RATE)
    if len(data) < target_samples:
        pad_len = target_samples - len(data)
        # Apply smooth 40ms fade out to speech tail
        fade_samples = min(int(SAMPLE_RATE * 0.04), len(data))
        fade_curve = np.linspace(1.0, 0.0, fade_samples, dtype=np.float32)
        data[-fade_samples:] *= fade_curve
        final_audio = np.concatenate([data, np.zeros(pad_len, dtype=np.float32)])
    else:
        final_audio = data[:target_samples]

    return final_audio

def mix_master_soundtrack():
    print("Mixing Master Soundtrack with Brian VO + Ducked Bed + SFX...", flush=True)
    vo_data, sr = sf.read("audio/climora_master_vo_brian.wav")
    assert sr == SAMPLE_RATE
    total_samples = int(240.0 * SAMPLE_RATE)
    vo_data = vo_data[:total_samples]

    # Music Bed
    music_data, msr = sf.read("audio/climora_110bpm_music_bed.wav")
    if len(music_data.shape) > 1:
        music_data = music_data[:, 0]
    if msr != SAMPLE_RATE:
        music_data = scipy.signal.resample_poly(music_data, 147, 80)
    music_data = music_data[:total_samples]

    # Voice Activity Detector for dynamic sidechain ducking (-14 dB)
    env = np.abs(vo_data)
    win_len = int(SAMPLE_RATE * 0.25)
    kernel = np.ones(win_len) / win_len
    smoothed_env = np.convolve(env, kernel, mode="same")
    is_speaking = smoothed_env > 0.015

    # Ducking gain curve
    ducking_gain = np.ones(total_samples, dtype=np.float32)
    # Target ducking: -14.5 dB (0.19 gain) when speaking, 0.42 when quiet
    duck_target = np.where(is_speaking, 0.19, 0.42)

    # Smooth the ducking transitions (300ms time constant)
    smooth_win = int(SAMPLE_RATE * 0.3)
    smooth_kernel = np.ones(smooth_win) / smooth_win
    ducking_gain = np.convolve(duck_target, smooth_kernel, mode="same")

    music_ducked = music_data * ducking_gain

    # Assemble SFX tracks at exact scene cue timestamps
    sfx_layer = np.zeros(total_samples, dtype=np.float32)
    sfx_cues = [
        ("audio/sfx_sub_boom.wav", 0.0, 0.65),     # Scene 01 kickoff
        ("audio/sfx_riser.wav", 18.0, 0.45),        # Transition to Scene 02
        ("audio/sfx_chime.wav", 45.0, 0.40),        # Stage 03 Lineage reveal
        ("audio/sfx_click.wav", 90.0, 0.45),        # Geospatial click hex
        ("audio/sfx_click.wav", 120.0, 0.45),       # Optimizer preset click
        ("audio/sfx_stamp.wav", 150.0, 0.60),       # Cedar SHA-256 seal
        ("audio/sfx_sub_boom.wav", 225.0, 0.70),    # Crescendo brand drop
    ]

    for sfx_path, start_sec, vol in sfx_cues:
        if os.path.exists(sfx_path):
            sdata, ssr = sf.read(sfx_path)
            if len(sdata.shape) > 1:
                sdata = sdata[:, 0]
            start_idx = int(start_sec * SAMPLE_RATE)
            end_idx = min(start_idx + len(sdata), total_samples)
            sfx_layer[start_idx:end_idx] += (sdata[:end_idx - start_idx] * vol)

    # Master Sum: VO (0.92) + Ducked Bed + SFX
    master_mix = (vo_data * 0.95) + music_ducked + sfx_layer

    # Soft Limiter & True Peak Protection (< -1.0 dBTP)
    # Tanh soft ceiling at 0.88 (-1.1 dB)
    master_limited = np.tanh(master_mix * 1.05) * 0.88

    # Final stereo output
    stereo_out = np.column_stack([master_limited, master_limited])
    sf.write("audio/climora_master_soundtrack.wav", stereo_out, SAMPLE_RATE)
    # Also copy to video/public
    sf.write("video/public/climora_master_soundtrack.wav", stereo_out, SAMPLE_RATE)
    print("Master Soundtrack successfully saved to audio/ and video/public/!", flush=True)

def generate_srt_subtitles():
    print("Generating Whisper Subtitles for Brian VO...", flush=True)
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        "audio/climora_master_vo_brian.wav",
        beam_size=5,
        word_timestamps=True,
        language="en"
    )

    srt_path = "out/climora_captions.srt"
    with open(srt_path, "w", encoding="utf-8") as f:
        idx = 1
        for segment in segments:
            start_m, start_s = divmod(segment.start, 60)
            start_h, start_m = divmod(start_m, 60)
            start_ms = int((segment.start % 1) * 1000)

            end_m, end_s = divmod(segment.end, 60)
            end_h, end_m = divmod(end_m, 60)
            end_ms = int((segment.end % 1) * 1000)

            clean_text = segment.text.strip().replace("—", ", ").replace("–", ", ").replace("-", " ")
            f.write(f"{idx}\n")
            f.write(f"{int(start_h):02d}:{int(start_m):02d}:{int(start_s):02d},{start_ms:03d} --> {int(end_h):02d}:{int(end_m):02d}:{int(end_s):02d},{end_ms:03d}\n")
            f.write(f"{clean_text}\n\n")
            idx += 1

    print(f"SRT Subtitles written to {srt_path} ({os.path.getsize(srt_path)} bytes)", flush=True)

async def main():
    os.makedirs("audio", exist_ok=True)
    os.makedirs("out", exist_ok=True)
    scenes = parse_vo_script("docs/vo_script.md")
    master_audio = []

    for sid, target_duration in SCENE_SLOTS.items():
        print(f"Synthesizing {sid} ({target_duration}s)...", flush=True)
        text = scenes[sid]
        audio = await synth_scene(sid, text, target_duration)
        master_audio.append(audio)
        sf.write(f"audio/{sid}_brian.wav", audio, SAMPLE_RATE)

    concatenated_vo = np.concatenate(master_audio)
    total_dur = len(concatenated_vo) / SAMPLE_RATE
    print(f"Total Brian VO Duration: {total_dur:.2f}s", flush=True)
    sf.write("audio/climora_master_vo_brian.wav", concatenated_vo, SAMPLE_RATE)

    mix_master_soundtrack()
    generate_srt_subtitles()

if __name__ == "__main__":
    asyncio.run(main())
