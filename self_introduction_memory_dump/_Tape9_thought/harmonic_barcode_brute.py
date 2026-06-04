import librosa
import numpy as np
import os
from collections import Counter

audio_path = r'C:\stack\arg\self_introduction_memory_dump.mp3'
outdir = r'C:\stack\arg\tapes_man_2'

y, sr = librosa.load(audio_path, sr=None, mono=False)
print(f'Audio: {y.shape[1]/sr:.3f}s, {y.shape[0]} ch, {sr} Hz')

n_fft = 16384
hop = 256
freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
times = librosa.frames_to_time(np.arange(int(np.ceil(y.shape[1]/hop)) + 1), sr=sr, hop_length=hop)

# English scoring helpers
common_words = {'THE','AND','FOR','ARE','BUT','NOT','YOU','ALL','ANY','CAN','HAD','HER','WAS','ONE','OUR','OUT','DAY','GET','HAS','HIM','HIS','HOW','MAN','NEW','NOW','OLD','SEE','TWO','WAY','WHO','BOY','DID','ITS','LET','PUT','SAY','SHE','TOO','USE','JOURNEY','HELLO','WORLD','ATLAS','TRACE','SKY','TAPE','MEMORY','SELF','PORTAL','NAME','WAKE','FIND','LOST','MIND','TIME','SPACE','VOID','NULL','ZERO','ONE','UNIT','MAIN','USER','ROOT','SYSTEM','ERROR','DEBUG','RESET','START','BEGIN','OPEN','CLOSE','ENTER','LEAVE','KNOW','LEARN','THINK','FEEL','HEAR','SPEAK','TELL','SAY','CALL','CODE','KEY','LOCK','DOOR','WAY','OUT','IN','UP','DOWN','LEFT','RIGHT','HERE','THERE','NOW','THEN','AGAIN','FOREVER','ALWAYS','NEVER','ONCE','TWICE'}
bigrams = ['TH','HE','IN','ER','AN','RE','ON','AT','EN','ND','TI','ES','OR','TE','OF','ED','IS','IT','AL','AR','ST','TO','NT','NG','SE','HA','AS','OU','IO','LE','VE','CO','ME','DE','HI','RI','RO','IC','NE','EA','RA','CE','LI','CH','LL','BE','MA','SI','OM','UR']

def score_alpha(s):
    if not s or not s.isalpha():
        return -1
    score = 0
    for w in common_words:
        if w in s:
            score += 10
    vowels = sum(1 for ch in s if ch in 'AEIOU')
    if 0.15 < vowels/len(s) < 0.45:
        score += 2
    for i in range(len(s)-1):
        if s[i:i+2] in bigrams:
            score += 1
    # penalize repetition
    unique = len(set(s))
    if unique < 4:
        score -= 5
    return score

def extract_barcode(S, f0, num_harmonics, bw, threshold_factor):
    barcode = []
    for frame_idx in range(S.shape[1]):
        frame_bits = []
        mag = S[:, frame_idx]
        for h in range(1, num_harmonics + 1):
            fc = f0 * h
            mask = (freqs >= fc - bw) & (freqs <= fc + bw)
            energy = np.mean(mag[mask]) if np.any(mask) else 0
            frame_bits.append(energy)
        barcode.append(frame_bits)
    barcode = np.array(barcode)
    binary = np.zeros((barcode.shape[0], num_harmonics), dtype=int)
    for frame_idx in range(barcode.shape[0]):
        med = np.median(barcode[frame_idx])
        for h in range(num_harmonics):
            binary[frame_idx, h] = 1 if barcode[frame_idx, h] > med * threshold_factor and barcode[frame_idx, h] > 0.001 else 0
    return binary

def group_symbols(binary, min_dur_frames=3):
    symbols = []
    if len(binary) == 0:
        return symbols
    current = binary[0].copy()
    start = 0
    for i in range(1, len(binary)):
        if not np.array_equal(binary[i], current):
            dur = i - start
            if dur >= min_dur_frames:
                symbols.append(current.copy())
            current = binary[i].copy()
            start = i
    dur = len(binary) - start
    if dur >= min_dur_frames:
        symbols.append(current.copy())
    return symbols

def decode_symbols(symbols, num_harmonics, reverse_bits=False, offset=0):
    vals = []
    for bits in symbols:
        b = bits[::-1] if reverse_bits else bits
        v = sum(int(b[j]) << (num_harmonics - 1 - j) for j in range(num_harmonics))
        vals.append(v)
    s = ''.join(chr(v + offset) if 32 <= v + offset <= 126 else '.' for v in vals)
    return s, vals

best_results = []

for ch_idx, ch_name in [(0, 'LEFT'), (1, 'RIGHT')]:
    D = librosa.stft(y[ch_idx], n_fft=n_fft, hop_length=hop)
    S = np.abs(D)
    for f0 in np.arange(120, 145.5, 0.5):
        for num_harmonics in [5, 6, 7, 8]:
            for bw in [10, 15, 20]:
                for threshold_factor in [1.2, 1.5, 2.0]:
                    binary = extract_barcode(S, f0, num_harmonics, bw, threshold_factor)
                    symbols = group_symbols(binary, min_dur_frames=3)
                    if not symbols:
                        continue
                    for reverse_bits in [False, True]:
                        for offset in [0, 32, 64, -32]:
                            s, vals = decode_symbols(symbols, num_harmonics, reverse_bits, offset)
                            # only consider strings that are mostly printable
                            if s.count('.') > len(s) * 0.3:
                                continue
                            score = score_alpha(s)
                            if score >= 5:
                                best_results.append((score, ch_name, f0, num_harmonics, bw, threshold_factor, reverse_bits, offset, s, vals))

best_results.sort(key=lambda x: x[0], reverse=True)
print(f'Total promising results: {len(best_results)}')

report_path = os.path.join(outdir, 'harmonic_barcode_brute.txt')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write('HARMONIC BARCODE BRUTE-FORCE RESULTS\n')
    f.write('='*80 + '\n')
    for score, ch_name, f0, num_h, bw, tf, rev, off, s, vals in best_results[:50]:
        f.write(f'\nscore={score}  {ch_name}  f0={f0:.1f}  n_harm={num_h}  bw={bw}  thr={tf}  rev={rev}  off={off}\n')
        f.write(f'  vals={vals[:40]}\n')
        f.write(f'  str={s[:100]}\n')

print(f'Report saved to {report_path}')
