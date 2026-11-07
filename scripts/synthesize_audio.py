import numpy as np
import soundfile as sf
import os

SAMPLE_RATE = 44100

def synthesize_sub_boom(out_path):
    duration = 2.5
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    # Pitch sweep from 140 Hz down to 35 Hz
    freq = 35 + 105 * np.exp(-4 * t)
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    envelope = np.exp(-2.2 * t)
    audio = 0.85 * np.sin(phase) * envelope
    # Add a touch of saturation/warmth
    audio = np.tanh(audio * 1.5)
    sf.write(out_path, audio.astype(np.float32), SAMPLE_RATE)
    print(f"Generated {out_path}")

def synthesize_riser(out_path):
    duration = 3.0
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    # Exponential frequency sweep from 150 Hz to 2400 Hz
    freq = 150 * ((2400 / 150) ** (t / duration))
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    envelope = (t / duration) ** 1.8
    # Add filtered noise
    noise = np.random.normal(0, 0.2, len(t)) * envelope
    audio = 0.5 * np.sin(phase) * envelope + 0.25 * noise
    sf.write(out_path, audio.astype(np.float32), SAMPLE_RATE)
    print(f"Generated {out_path}")

def synthesize_click(out_path):
    duration = 0.04
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    freq = 2400 * np.exp(-120 * t)
    envelope = np.exp(-180 * t)
    audio = 0.7 * np.sin(2 * np.pi * freq * t) * envelope
    sf.write(out_path, audio.astype(np.float32), SAMPLE_RATE)
    print(f"Generated {out_path}")

def synthesize_stamp(out_path):
    duration = 1.0
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    freq = 80 * np.exp(-8 * t)
    envelope = np.exp(-6 * t)
    body = 0.8 * np.sin(2 * np.pi * freq * t) * envelope
    noise_env = np.exp(-40 * t)
    click = 0.3 * np.random.normal(0, 1, len(t)) * noise_env
    audio = np.tanh((body + click) * 1.8)
    sf.write(out_path, audio.astype(np.float32), SAMPLE_RATE)
    print(f"Generated {out_path}")

def synthesize_chime(out_path):
    duration = 2.0
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    # Frequencies: E5, G#5, B5, E6 (Sparkling major chord)
    notes = [659.25, 830.61, 987.77, 1318.51]
    audio = np.zeros_like(t)
    for i, freq in enumerate(notes):
        delay = i * 0.04
        t_note = np.maximum(0, t - delay)
        envelope = np.where(t >= delay, np.exp(-3.0 * t_note), 0)
        audio += 0.25 * np.sin(2 * np.pi * freq * t_note) * envelope
    audio = np.tanh(audio)
    sf.write(out_path, audio.astype(np.float32), SAMPLE_RATE)
    print(f"Generated {out_path}")

def synthesize_music_bed(out_path, duration=244.0):
    bpm = 110.0
    beat_sec = 60.0 / bpm
    total_samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, total_samples, endpoint=False)
    
    # Base chords in D minor (Dm - Bb - F - C)
    chord_freqs = [
        [146.83, 174.61, 220.00],  # Dm (D3, F3, A3)
        [116.54, 146.83, 174.61],  # Bb (Bb2, D3, F3)
        [174.61, 220.00, 261.63],  # F (F3, A3, C4)
        [130.81, 164.81, 196.00],  # C (C3, E3, G3)
    ]
    chord_duration = beat_sec * 8 # 2 bars per chord
    
    bed = np.zeros(total_samples, dtype=np.float32)
    
    # Generate warm analog pad
    for sample_idx in range(0, total_samples, int(SAMPLE_RATE * 0.1)):
        # block processing
        pass
        
    num_blocks = int(np.ceil(duration / chord_duration))
    for b in range(num_blocks):
        chord_idx = b % len(chord_freqs)
        notes = chord_freqs[chord_idx]
        start_t = b * chord_duration
        end_t = min(duration, (b + 1) * chord_duration)
        s_start = int(start_t * SAMPLE_RATE)
        s_end = int(end_t * SAMPLE_RATE)
        t_seg = t[s_start:s_end] - start_t
        seg_len = len(t_seg)
        
        # Smooth attack and release envelope for pad
        attack = 0.5
        release = 0.5
        seg_env = np.ones(seg_len, dtype=np.float32)
        att_len = int(attack * SAMPLE_RATE)
        if seg_len > att_len:
            seg_env[:att_len] = np.linspace(0, 1, att_len)
            seg_env[-att_len:] = np.linspace(1, 0, att_len)
            
        pad = np.zeros(seg_len, dtype=np.float32)
        for f in notes:
            # Fundamental + soft harmonics
            pad += 0.08 * np.sin(2 * np.pi * f * t_seg)
            pad += 0.03 * np.sin(2 * np.pi * (f * 2.01) * t_seg)
            pad += 0.015 * np.sin(2 * np.pi * (f * 3.00) * t_seg)
        bed[s_start:s_end] += pad * seg_env

    # Add gentle pulsing sub bass on each quarter note
    quarter_len = int(beat_sec * SAMPLE_RATE)
    num_quarters = int(duration / beat_sec)
    for q in range(num_quarters):
        q_start = int(q * beat_sec * SAMPLE_RATE)
        q_end = min(total_samples, q_start + quarter_len)
        q_t = np.linspace(0, (q_end - q_start)/SAMPLE_RATE, q_end - q_start, endpoint=False)
        # Root note based on chord
        bar = int(q / 8)
        root = chord_freqs[bar % len(chord_freqs)][0] / 2.0 # Sub octave
        bass_env = np.exp(-4.5 * q_t)
        bass = 0.15 * np.sin(2 * np.pi * root * q_t) * bass_env
        bed[q_start:q_end] += bass

    # Soft hi-hat pulse on 8th notes (starts after 30s)
    eighth_sec = beat_sec / 2.0
    num_eighths = int(duration / eighth_sec)
    for e in range(int(30.0 / eighth_sec), num_eighths):
        e_start = int(e * eighth_sec * SAMPLE_RATE)
        e_end = min(total_samples, e_start + int(0.05 * SAMPLE_RATE))
        e_len = e_end - e_start
        hat_env = np.exp(-120 * np.linspace(0, 0.05, e_len))
        hat = 0.02 * np.random.normal(0, 1, e_len) * hat_env
        bed[e_start:e_end] += hat

    # Master gentle compression/limiting
    bed = np.tanh(bed * 1.4) * 0.4
    # Fade in / Fade out
    fade_in_len = int(2.0 * SAMPLE_RATE)
    fade_out_len = int(4.0 * SAMPLE_RATE)
    bed[:fade_in_len] *= np.linspace(0, 1, fade_in_len)
    bed[-fade_out_len:] *= np.linspace(1, 0, fade_out_len)
    
    sf.write(out_path, bed.astype(np.float32), SAMPLE_RATE)
    print(f"Generated {out_path} ({duration}s at 110 BPM)")

if __name__ == "__main__":
    os.makedirs("audio", exist_ok=True)
    synthesize_sub_boom("audio/sfx_sub_boom.wav")
    synthesize_riser("audio/sfx_riser.wav")
    synthesize_click("audio/sfx_click.wav")
    synthesize_stamp("audio/sfx_stamp.wav")
    synthesize_chime("audio/sfx_chime.wav")
    synthesize_music_bed("audio/climora_110bpm_music_bed.wav", duration=242.0)

