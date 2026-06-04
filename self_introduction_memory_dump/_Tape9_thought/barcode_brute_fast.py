import librosa
import numpy as np

audio_path = r'C:\stack\arg\self_introduction_memory_dump.mp3'
y, sr = librosa.load(audio_path, sr=None, mono=False)

n_fft = 8192
hop = 512
D_left = librosa.stft(y[0], n_fft=n_fft, hop_length=hop)
D_right = librosa.stft(y[1], n_fft=n_fft, hop_length=hop)
S_left = np.abs(D_left)
S_right = np.abs(D_right)
freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)

def decode_barcode(S, f0, num_harmonics, bw, thr):
    barcode = []
    for frame_idx in range(S.shape[1]):
        bits = []
        mag = S[:, frame_idx]
        for h in range(1, num_harmonics+1):
            fc = f0 * h
            mask = (freqs >= fc - bw) & (freqs <= fc + bw)
            energy = np.mean(mag[mask]) if np.any(mask) else 0
            bits.append(energy)
        barcode.append(bits)
    barcode = np.array(barcode)
    binary = np.zeros((barcode.shape[0], num_harmonics), dtype=int)
    for i in range(barcode.shape[0]):
        med = np.median(barcode[i])
        for h in range(num_harmonics):
            binary[i, h] = 1 if barcode[i, h] > med * thr and barcode[i, h] > 0.001 else 0
    # group symbols
    symbols = []
    if len(binary) == 0:
        return symbols
    current = binary[0].copy()
    start = 0
    for i in range(1, len(binary)):
        if not np.array_equal(binary[i], current):
            dur = i - start
            if dur >= 2:
                symbols.append(current.copy())
            current = binary[i].copy()
            start = i
    dur = len(binary) - start
    if dur >= 2:
        symbols.append(current.copy())
    return symbols

def to_ascii(symbols, num_h, reverse=False, offset=0):
    s = ''
    for bits in symbols:
        b = bits[::-1] if reverse else bits
        v = sum(int(b[j]) << (num_h - 1 - j) for j in range(num_h))
        adj = v + offset
        if 32 <= adj <= 126:
            s += chr(adj)
        else:
            s += '.'
    return s

best = []
for ch_name, S in [('LEFT', S_left), ('RIGHT', S_right)]:
    for f0 in np.arange(100, 201, 5):
        for num_h in [5, 6, 7, 8]:
            for bw in [10, 15, 20]:
                for thr in [1.5, 2.0, 2.5]:
                    symbols = decode_barcode(S, f0, num_h, bw, thr)
                    if not symbols:
                        continue
                    for rev in [False, True]:
                        for off in [0, 32, 64, -32]:
                            s = to_ascii(symbols, num_h, rev, off)
                            if s.count('.') > len(s) * 0.3:
                                continue
                            # score
                            words = ['JOURNEY','HELLO','WORLD','ATLAS','TRACE','SKY','TAPE','MEMORY','SELF','NAME','WAKE','FIND','LOST','MIND','TIME','SPACE','LOVE','FEEL','FEAR','DREAM','HOPE','HOME','HELP','HERE','THERE']
                            score = 0
                            for w in words:
                                if w in s:
                                    score += 10
                            vowels = sum(1 for ch in s if ch in 'AEIOU')
                            if 0.15 < vowels/len(s) < 0.45:
                                score += 2
                            if score > 1:
                                best.append((score, ch_name, f0, num_h, bw, thr, rev, off, s))

best.sort(key=lambda x: x[0], reverse=True)
print(f'Found {len(best)} promising results')
for score, ch_name, f0, num_h, bw, thr, rev, off, s in best[:30]:
    print(f'score={score} {ch_name} f0={f0:.0f} n={num_h} bw={bw} thr={thr} rev={rev} off={off} -> {s}')
