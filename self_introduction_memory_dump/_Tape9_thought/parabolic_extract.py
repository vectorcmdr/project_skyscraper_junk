import librosa
import numpy as np
import os

audio_path = r'C:\stack\arg\self_introduction_memory_dump.mp3'
outdir = r'C:\stack\arg\tapes_man_2'

y, sr = librosa.load(audio_path, sr=None, mono=False)

n_fft = 16384
hop = 512
freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
times = librosa.frames_to_time(np.arange(int(np.ceil(y.shape[1]/hop)) + 1), sr=sr, hop_length=hop)

def parabolic_interpolation(mag, bin_idx):
    if bin_idx == 0 or bin_idx == len(mag) - 1:
        return float(bin_idx)
    alpha = mag[bin_idx - 1]
    beta = mag[bin_idx]
    gamma = mag[bin_idx + 1]
    p = 0.5 * (alpha - gamma) / (alpha - 2*beta + gamma + 1e-10)
    return bin_idx + p

def hz_to_midi(freq, ref=440.0):
    return 69.0 + 12.0 * np.log2(freq / ref)

for ch_idx, ch_name in [(0, 'LEFT'), (1, 'RIGHT')]:
    D = librosa.stft(y[ch_idx], n_fft=n_fft, hop_length=hop)
    S = np.abs(D)
    band_mask = (freqs >= 50) & (freqs <= 1200)
    freqs_b = freqs[band_mask]
    S_b = S[band_mask, :]
    
    # For each frame, find peak and interpolate
    peak_bin = np.argmax(S_b, axis=0)
    peak_mag = np.max(S_b, axis=0)
    median_mag = np.median(peak_mag)
    strong = peak_mag > median_mag * 2.0
    
    segments = []
    i = 0
    while i < len(peak_bin):
        if not strong[i]:
            i += 1
            continue
        start = i
        bin0 = peak_bin[i]
        # interpolate start
        interp0 = parabolic_interpolation(S_b[:, i], bin0)
        j = i + 1
        while j < len(peak_bin) and strong[j]:
            # allow drift up to 2 bins
            if abs(peak_bin[j] - bin0) <= 2:
                j += 1
            else:
                break
        if j - start >= 5:
            # compute median interpolated frequency
            interp_bins = []
            for k in range(start, j):
                b = peak_bin[k]
                interp_bins.append(parabolic_interpolation(S_b[:, k], b))
            med_bin = float(np.median(interp_bins))
            # map back to global freq
            # band_mask indices correspond to freqs_b indices
            # med_bin is relative to freqs_b (0 = first in band)
            # So actual freq = freqs_b[0] + med_bin * (freqs_b[1]-freqs_b[0])
            freq_est = freqs_b[0] + med_bin * (freqs_b[1] - freqs_b[0])
            segments.append({
                'start': float(times[start]),
                'end': float(times[j-1]),
                'freq': float(freq_est),
                'dur': float(times[j-1] - times[start]),
                'nframes': j - start,
                'med_bin': med_bin,
            })
        i = j
    
    print(f'=== {ch_name} PARABOLIC INTERPOLATION ===')
    print(f'Segments: {len(segments)}')
    for idx, s in enumerate(segments):
        m = hz_to_midi(s['freq'])
        print(f'  #{idx:3d}  t={s["start"]:.3f}-{s["end"]:.3f}s  f={s["freq"]:.2f}Hz  MIDI={int(round(m)):3d} ({m:.2f})  dur={s["dur"]:.3f}s')
    if segments:
        midi = [int(round(hz_to_midi(s['freq']))) for s in segments]
        ascii_str = ''.join(chr(m) if 32 <= m <= 126 else '.' for m in midi)
        print(f'Direct ASCII: {ascii_str}')
        hex_str = ''.join(f'{m:02x}' for m in midi)
        print(f'Hex: {hex_str}')
        for shift in range(26):
            alpha = ''.join(chr(65 + ((m % 26 + shift) % 26)) for m in midi)
            # quick score
            vowels = sum(1 for ch in alpha if ch in 'AEIOU')
            score = 0
            if 0.15 < vowels/len(alpha) < 0.45:
                score += 1
            words = ['JOURNEY','HELLO','WORLD','ATLAS','TRACE','SKY','TAPE','MEMORY','SELF','NAME','WAKE','FIND','LOST','MIND','TIME','SPACE']
            for w in words:
                if w in alpha:
                    score += 10
            if score > 1:
                print(f'  shift={shift:2d} score={score:3d}: {alpha}')
    print()
