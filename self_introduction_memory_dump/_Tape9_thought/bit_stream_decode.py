import librosa
import numpy as np

audio_path = r'C:\stack\arg\self_introduction_memory_dump.mp3'
y, sr = librosa.load(audio_path, sr=None, mono=False)

n_fft = 16384
hop = 256
freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)

f0 = 130.0
num_h = 7
bw = 15
thr = 1.5

for ch_idx, ch_name in [(0, 'LEFT'), (1, 'RIGHT')]:
    D = librosa.stft(y[ch_idx], n_fft=n_fft, hop_length=hop)
    S = np.abs(D)
    barcode = []
    for frame_idx in range(S.shape[1]):
        bits = []
        mag = S[:, frame_idx]
        for h in range(1, num_h+1):
            fc = f0 * h
            mask = (freqs >= fc - bw) & (freqs <= fc + bw)
            energy = np.mean(mag[mask]) if np.any(mask) else 0
            bits.append(energy)
        barcode.append(bits)
    barcode = np.array(barcode)
    binary = np.zeros((barcode.shape[0], num_h), dtype=int)
    for i in range(barcode.shape[0]):
        med = np.median(barcode[i])
        for h in range(num_h):
            binary[i, h] = 1 if barcode[i, h] > med * thr and barcode[i, h] > 0.001 else 0
    
    # Concatenate all binary rows into a single bit string
    bit_string = ''.join(str(b) for row in binary for b in row)
    print(f'=== {ch_name} bit string length = {len(bit_string)} ===')
    
    # Try decoding as 8-bit bytes with various offsets
    for offset in range(8):
        bits = bit_string[offset:]
        # pad to multiple of 8
        if len(bits) % 8 != 0:
            bits = bits[:-(len(bits) % 8)]
        chars = []
        for i in range(0, len(bits), 8):
            byte = int(bits[i:i+8], 2)
            if 32 <= byte <= 126:
                chars.append(chr(byte))
            else:
                chars.append('.')
        s = ''.join(chars)
        # look for long printable runs
        import re
        matches = re.findall(r'[A-Za-z0-9 /\\.,;:!?+=-_]{8,}', s)
        if matches:
            print(f'  offset={offset} matches: {matches[:10]}')
        else:
            # print first 80 chars if mostly printable
            if s.count('.') < len(s) * 0.3:
                print(f'  offset={offset}: {s[:80]}')
    print()
