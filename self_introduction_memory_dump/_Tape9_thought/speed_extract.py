import librosa
import numpy as np

audio_path = r'C:\stack\arg\self_introduction_memory_dump.mp3'
y, sr = librosa.load(audio_path, sr=None, mono=False)

for ch_idx, ch_name in [(0, 'LEFT'), (1, 'RIGHT')]:
    for speed in [1.0, 2.0, 5.0, 0.5]:
        # Resample by speed factor
        if speed != 1.0:
            y_resamp = librosa.resample(y[ch_idx], orig_sr=sr, target_sr=int(sr * speed))
        else:
            y_resamp = y[ch_idx]
        sr_eff = int(sr * speed)
        n_fft = 2048
        hop = 64
        D = librosa.stft(y_resamp, n_fft=n_fft, hop_length=hop)
        S = np.abs(D)
        freqs = librosa.fft_frequencies(sr=sr_eff, n_fft=n_fft)
        times = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr_eff, hop_length=hop)
        band_mask = (freqs >= 50) & (freqs <= 1000)
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
            while j < len(peak_freq) and strong[j] and abs(peak_freq[j] - freq0) <= 10:
                j += 1
            if j - start >= 2:
                segments.append({
                    'start': float(times[start]),
                    'end': float(times[j-1]),
                    'freq': float(np.median(peak_freq[start:j])),
                    'dur': float(times[j-1] - times[start]),
                })
            i = j
        if segments:
            midi = [int(round(69 + 12 * np.log2(s['freq']/440.0))) for s in segments]
            ascii_str = ''.join(chr(m) if 32 <= m <= 126 else '.' for m in midi)
            print(f'{ch_name} speed={speed:.1f} segments={len(segments):3d} ASCII={ascii_str}')
