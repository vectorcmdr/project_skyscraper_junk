import librosa
import numpy as np

audio_path = r'C:\stack\arg\self_introduction_memory_dump.mp3'
y, sr = librosa.load(audio_path, sr=None, mono=False)

n_fft = 8192
hop = 256

for ch_idx, ch_name in [(0, 'LEFT'), (1, 'RIGHT')]:
    D = librosa.stft(y[ch_idx], n_fft=n_fft, hop_length=hop)
    S = np.abs(D)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    times = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr, hop_length=hop)
    band_mask = (freqs >= 500) & (freqs <= 4000)
    freqs_b = freqs[band_mask]
    S_b = S[band_mask, :]
    peak_bin = np.argmax(S_b, axis=0)
    peak_freq = freqs_b[peak_bin]
    peak_mag = np.max(S_b, axis=0)
    median_mag = np.median(peak_mag)
    strong = peak_mag > median_mag * 2.0
    segments = []
    i = 0
    while i < len(peak_freq):
        if not strong[i]:
            i += 1
            continue
        start = i
        freq0 = peak_freq[i]
        j = i + 1
        while j < len(peak_freq) and strong[j] and abs(peak_freq[j] - freq0) <= 20:
            j += 1
        if j - start >= 3:
            segments.append({
                'start': float(times[start]),
                'end': float(times[j-1]),
                'freq': float(np.median(peak_freq[start:j])),
                'dur': float(times[j-1] - times[start]),
            })
        i = j
    print(f'=== {ch_name} HIGH BAND (500-4000 Hz) ===')
    print(f'Segments: {len(segments)}')
    for s in segments:
        m = 69 + 12 * np.log2(s['freq'] / 440.0)
        print(f"  t={s['start']:.3f}-{s['end']:.3f}s f={s['freq']:.2f}Hz MIDI={int(round(m)):3d}")
    if segments:
        midi = [int(round(69 + 12 * np.log2(s['freq']/440.0))) for s in segments]
        ascii_str = ''.join(chr(m) if 32 <= m <= 126 else '.' for m in midi)
        print(f'Direct ASCII: {ascii_str}')
        for shift in range(26):
            alpha = ''.join(chr(65 + ((m % 26 + shift) % 26)) for m in midi)
            vowels = sum(1 for ch in alpha if ch in 'AEIOU')
            if 0.15 < vowels/len(alpha) < 0.45:
                print(f'  shift={shift:2d}: {alpha}')
    print()
