import os
import re
import asyncio
import soundfile as sf
import numpy as np
import edge_tts
from faster_whisper import WhisperModel

VOICE = "en-IN-PrabhatNeural"
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

async def synth_segment(text, out_wav):
    # Split text on [PAUSE X.Xs]
    parts = re.split(r"\[PAUSE\s+([\d\.]+)s\]", text)
    audio_segments = []
    
    for i, part in enumerate(parts):
        if i % 2 == 1:
            # Silence pause
            pause_sec = float(part)
            silence = np.zeros(int(SAMPLE_RATE * pause_sec), dtype=np.float32)
            audio_segments.append(silence)
        else:
            text_chunk = part.strip()
            if not text_chunk:
                continue
            tmp_mp3 = f"{out_wav}_chunk_{i}.mp3"
            communicate = edge_tts.Communicate(text_chunk, VOICE, rate="-4%", pitch="-1Hz")
            await communicate.save(tmp_mp3)
            data, sr = sf.read(tmp_mp3)
            if sr != SAMPLE_RATE:
                # Basic resample or rely on soundfile
                import scipy.signal
                num_samples = int(len(data) * SAMPLE_RATE / sr)
                data = scipy.signal.resample(data, num_samples)
            if len(data.shape) > 1:
                data = data[:, 0]
            audio_segments.append(data.astype(np.float32))
            if os.path.exists(tmp_mp3):
                os.remove(tmp_mp3)

    if audio_segments:
        full_audio = np.concatenate(audio_segments)
    else:
        full_audio = np.zeros(SAMPLE_RATE, dtype=np.float32)

    return full_audio

async def generate_all_scenes():
    os.makedirs("audio", exist_ok=True)
    os.makedirs("out", exist_ok=True)
    scenes = parse_vo_script("docs/vo_script.md")

    master_audio = []
    scene_manifest = {}

    for sid, target_duration in SCENE_SLOTS.items():
        text = scenes.get(sid, "")
        print(f"Generating VO for {sid} (Target: {target_duration}s)...")
        raw_audio = await synth_segment(text, f"audio/{sid}")
        raw_dur = len(raw_audio) / SAMPLE_RATE
        print(f"  Raw audio duration: {raw_dur:.2f}s (Slot: {target_duration:.2f}s)")

        if raw_dur > target_duration:
            print(f"  WARNING: {sid} is longer than target by {raw_dur - target_duration:.2f}s! Slightly compressing...")
            import scipy.signal
            target_samples = int(target_duration * SAMPLE_RATE)
            processed_audio = scipy.signal.resample(raw_audio, target_samples)
        else:
            # Pad with silence to match exact slot duration
            pad_len = int((target_duration - raw_dur) * SAMPLE_RATE)
            processed_audio = np.concatenate([raw_audio, np.zeros(pad_len, dtype=np.float32)])

        out_path = f"audio/{sid}.wav"
        sf.write(out_path, processed_audio.astype(np.float32), SAMPLE_RATE)
        master_audio.append(processed_audio)
        scene_manifest[sid] = {
            "target_duration_s": target_duration,
            "raw_duration_s": round(raw_dur, 2),
            "file": out_path
        }

    # Master VO track
    climora_master_vo = np.concatenate(master_audio)
    master_vo_path = "audio/climora_master_vo.wav"
    sf.write(master_vo_path, climora_master_vo.astype(np.float32), SAMPLE_RATE)
    print(f"Master VO written to {master_vo_path} ({len(climora_master_vo)/SAMPLE_RATE:.2f}s)")

    # Run Whisper for word timestamps and SRT
    print("Running faster-whisper on master VO...")
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, info = model.transcribe(master_vo_path, word_timestamps=True)

    srt_lines = []
    word_timestamps = []
    seg_idx = 1

    for segment in segments:
        start_str = format_srt_time(segment.start)
        end_str = format_srt_time(segment.end)
        srt_lines.append(f"{seg_idx}\n{start_str} --> {end_str}\n{segment.text.strip()}\n")
        seg_idx += 1
        if segment.words:
            for w in segment.words:
                word_timestamps.append({
                    "word": w.word.strip(),
                    "start": round(w.start, 3),
                    "end": round(w.end, 3),
                    "probability": round(w.probability, 3)
                })

    srt_path = "out/climora_captions.srt"
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))
    print(f"Subtitles written to {srt_path}")

    import json
    with open("audio/word_timestamps.json", "w", encoding="utf-8") as f:
        json.dump(word_timestamps, f, indent=2)

    # Now mix master soundtrack: Master VO + Music Bed (-14dB ducking) + SFX
    mix_master_soundtrack(master_vo_path, "audio/climora_master_soundtrack.wav")

def mix_master_soundtrack(vo_path, out_mix_path):
    print("Mixing master soundtrack (Master VO + Music Bed + SFX)...")
    vo, sr = sf.read(vo_path)
    music, msr = sf.read("audio/climora_110bpm_music_bed.wav")
    
    # Ensure same length
    total_len = min(len(vo), len(music))
    vo = vo[:total_len]
    music = music[:total_len]

    # Duck music: -14 dB under voice (factor ~0.20)
    ducked_music = music * 0.18

    # Blend SFX at specific script timestamps:
    # 0s: sub-boom
    # 70s: riser (Scene 04 transition)
    # 92s: tactile click (Scene 05 layer toggle)
    # 135s: solver chime (Scene 06 HiGHS convergence)
    # 160s: authority stamp (Scene 07 Cedar sanction)
    sfx_events = [
        ("audio/sfx_sub_boom.wav", 0.0, 0.7),
        ("audio/sfx_riser.wav", 68.0, 0.4),
        ("audio/sfx_click.wav", 92.0, 0.5),
        ("audio/sfx_click.wav", 105.0, 0.5),
        ("audio/sfx_chime.wav", 135.0, 0.6),
        ("audio/sfx_stamp.wav", 160.0, 0.7),
        ("audio/sfx_sub_boom.wav", 225.0, 0.5),
    ]

    sfx_track = np.zeros(total_len, dtype=np.float32)
    for sfx_file, start_sec, vol in sfx_events:
        if os.path.exists(sfx_file):
            s_data, _ = sf.read(sfx_file)
            s_start = int(start_sec * sr)
            s_end = min(total_len, s_start + len(s_data))
            s_len = s_end - s_start
            sfx_track[s_start:s_end] += (s_data[:s_len] * vol).astype(np.float32)

    # Master mix: VO (0.95) + ducked music + SFX
    master = (vo * 0.95) + ducked_music + (sfx_track * 0.6)
    # Soft limiter to ensure true peak stays below -1 dBTP (approx 0.89 amplitude)
    master = np.tanh(master * 1.1) * 0.85

    sf.write(out_mix_path, master.astype(np.float32), sr)
    print(f"Master soundtrack written to {out_mix_path} ({len(master)/sr:.2f}s)")

def format_srt_time(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int(round((sec - int(sec)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

if __name__ == "__main__":
    asyncio.run(generate_all_scenes())

