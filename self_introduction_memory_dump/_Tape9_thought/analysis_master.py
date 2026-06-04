#!/usr/bin/env python3
"""
Comprehensive forensic audio analysis for self_introduction_memory_dump.mp3
Outputs all results to tapes_man_2/
"""
import os, sys, warnings
import numpy as np
import librosa
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')

AUDIO_PATH = r'C:\stack\arg\self_introduction_memory_dump.mp3'
TAPE_PATH = r'C:\stack\arg\tape_9_16_final_b_side.wav'
OUTDIR = r'C:\stack\arg\tapes_man_2'
os.makedirs(OUTDIR, exist_ok=True)

def hz_to_midi(freq, ref=440.0):
    return 69.0 + 12.0 * np.log2(freq / ref)

def save_report(name, lines):
    path = os.path.join(OUTDIR, name)
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'Report saved: {path}')

# ============================================================
# 1. Load audio
# ============================================================
y_stereo, sr = librosa.load(AUDIO_PATH, sr=None, mono=False)
y_mono = librosa.to_mono(y_stereo)
dur = y_mono.shape[0] / sr

report = []
report.append('='*70)
report.append('FORENSIC AUDIO ANALYSIS REPORT')
report.append('Target: self_introduction_memory_dump.mp3')
report.append(f'Duration: {dur:.3f}s  SR: {sr} Hz  Channels: {y_stereo.shape[0]}')
report.append('='*70)

# ============================================================
# 2. Spectrograms (focused low-freq + log)
# ============================================================
print('Generating spectrograms...')

fig, axes = plt.subplots(2, 1, figsize=(18, 8))
for ax, ch, label in zip(axes, [y_stereo[0], y_stereo[1]], ['LEFT', 'RIGHT']):
    D = librosa.stft(ch, n_fft=8192, hop_length=256)
    S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)
    librosa.display.specshow(S_db, sr=sr, hop_length=256, n_fft=8192,
                             x_axis='time', y_axis='linear', ax=ax, cmap='inferno')
    ax.set_ylim(0, 1200)
    ax.set_title(f'{label} channel (0-1200 Hz)')
plt.tight_layout()
spec_path = os.path.join(OUTDIR, 'spectrogram_stereo_0_1200.png')
fig.savefig(spec_path, dpi=150)
plt.close(fig)
report.append(f'Saved stereo low-freq spectrogram: {spec_path}')

fig, ax = plt.subplots(figsize=(20, 6))
D = librosa.stft(y_mono, n_fft=16384, hop_length=512)
S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)
librosa.display.specshow(S_db, sr=sr, hop_length=512, n_fft=16384,
                         x_axis='time', y_axis='linear', ax=ax, cmap='inferno')
ax.set_ylim(0, 1000)
ax.set_title('MONO high-res 0-1000 Hz')
plt.tight_layout()
spec_path = os.path.join(OUTDIR, 'spectrogram_mono_0_1000_hires.png')
fig.savefig(spec_path, dpi=150)
plt.close(fig)
report.append(f'Saved mono high-res spectrogram: {spec_path}')

fig, ax = plt.subplots(figsize=(20, 6))
librosa.display.specshow(S_db, sr=sr, hop_length=512, n_fft=16384,
                         x_axis='time', y_axis='log', ax=ax, cmap='inferno')
ax.set_ylim(50, 4000)
ax.set_title('MONO log scale 50-4000 Hz')
plt.tight_layout()
spec_path = os.path.join(OUTDIR, 'spectrogram_mono_log_50_4000.png')
fig.savefig(spec_path, dpi=150)
plt.close(fig)
report.append(f'Saved mono log spectrogram: {spec_path}')

# ============================================================
# 3. Sustained tone extraction (peak tracking)
# ============================================================
def extract_sustained_tones(y_ch, sr, n_fft=16384, hop_length=512,
                            low_hz=50, high_hz=1200,
                            min_frames=5, freq_tol_hz=5.0):
    D = librosa.stft(y_ch, n_fft=n_fft, hop_length=hop_length)
    S = np.abs(D)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    times = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr, hop_length=hop_length)
    band_mask = (freqs >= low_hz) & (freqs <= high_hz)
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
        while j < len(peak_freq) and strong[j] and abs(peak_freq[j] - freq0) <= freq_tol_hz:
            j += 1
        if j - start >= min_frames:
            segments.append({
                'start': float(times[start]),
                'end': float(times[j-1]),
                'freq': float(np.median(peak_freq[start:j])),
                'dur': float(times[j-1] - times[start]),
                'nframes': j - start
            })
        i = j
    return segments

channels = {
    'LEFT': y_stereo[0],
    'RIGHT': y_stereo[1],
    'MONO': y_mono,
    'DIFF': y_stereo[0] - y_stereo[1]
}

all_segments = {}
for ch_name, ch_data in channels.items():
    segs = extract_sustained_tones(ch_data, sr, n_fft=16384, hop_length=512,
                                   low_hz=50, high_hz=1200, min_frames=5, freq_tol_hz=5.0)
    all_segments[ch_name] = segs
    report.append(f'')
    report.append(f'--- {ch_name} channel sustained tones (50-1200 Hz) ---')
    report.append(f'Count: {len(segs)}')
    for idx, s in enumerate(segs):
        m = hz_to_midi(s['freq'])
        report.append(f'  #{idx:3d}  t={s["start"]:.3f}-{s["end"]:.3f}s  f={s["freq"]:.2f} Hz  MIDI={int(round(m)):3d} ({m:.1f})  dur={s["dur"]:.3f}s')

# ============================================================
# 4. Transformations on sustained tones
# ============================================================
report.append('')
report.append('='*70)
report.append('TRANSFORMATION RESULTS (sustained tones)')
report.append('='*70)

for ch_name, segs in all_segments.items():
    if not segs:
        continue
    freqs = [s['freq'] for s in segs]
    midi = [int(round(hz_to_midi(f))) for f in freqs]
    report.append('')
    report.append(f'--- {ch_name} ---')
    report.append(f'MIDI sequence: {midi}')
    # Direct ASCII
    ascii_str = ''.join(chr(m) if 32 <= m <= 126 else '.' for m in midi)
    report.append(f'Direct ASCII:  {ascii_str}')
    # Hex
    hex_str = ''.join(f'{m:02x}' for m in midi)
    report.append(f'Hex string:    {hex_str}')
    # Pairwise hex->ASCII
    if len(hex_str) % 2 == 0:
        hex_ascii = ''.join(chr(int(hex_str[i:i+2], 16)) for i in range(0, len(hex_str), 2))
        report.append(f'Hex->ASCII:    {hex_ascii}')
    else:
        report.append(f'Hex->ASCII:    (odd length)')

    # NMS
    best_nms = []
    for shift in range(26):
        alpha = ''.join(chr(65 + ((m % 26 + shift) % 26)) for m in midi)
        vowels = sum(1 for ch in alpha if ch in 'AEIOU')
        vratio = vowels / max(len(alpha), 1)
        score = 0
        test_words = ['JOURNEY','HELLO','WORLD','ATLAS','TRACE','SKY','TAPE','MEMORY',
                      'SELF','PORTAL','NAME','WAKE','FIND','LOST','MIND','TIME','SPACE',
                      'VOID','NULL','ZERO','ONE','UNIT','MAIN','USER','ROOT','SYSTEM',
                      'ERROR','DEBUG','RESET','START','BEGIN','OPEN','CLOSE','ENTER',
                      'LEAVE','KNOW','LEARN','THINK','FEEL','HEAR','SPEAK','TELL','SAY',
                      'CALL','CODE','KEY','LOCK','DOOR','WAY','OUT','IN','UP','DOWN',
                      'LEFT','RIGHT','HERE','THERE','NOW','THEN','AGAIN','FOREVER',
                      'ALWAYS','NEVER','ONCE','TWICE']
        for w in test_words:
            if w in alpha:
                score += 10
        if 0.15 < vratio < 0.45:
            score += 2
        if score > 0:
            best_nms.append((shift, alpha, score))
    best_nms.sort(key=lambda x: x[2], reverse=True)
    report.append('Best NMS (MIDI%26+shift):')
    for shift, alpha, score in best_nms[:12]:
        report.append(f'  shift={shift:2d} score={score:3d}: {alpha}')

    # MIDI offset to ASCII
    report.append('MIDI offset -> ASCII (low dot ratio):')
    for offset in range(-60, 30):
        s = ''.join(chr(m + offset) if 32 <= m + offset <= 126 else '.' for m in midi)
        if s.count('.') < len(s) * 0.3:
            report.append(f'  offset={offset:3d}: {s}')

    # MIDI - base -> A-Z
    report.append('MIDI - base -> A-Z (bases with <50% unknown):')
    for base in range(20, 70):
        s = ''.join(chr(64 + (m - base)) if 1 <= (m - base) <= 26 else '?' for m in midi)
        if s.count('?') < len(s) * 0.5:
            report.append(f'  base={base:2d}: {s}')

# ============================================================
# 5. pYIN fundamental extraction
# ============================================================
report.append('')
report.append('='*70)
report.append('PYIN FUNDAMENTAL FREQUENCY EXTRACTION')
report.append('='*70)

for ch_name, ch_data in channels.items():
    f0, voiced_flag, _ = librosa.pyin(ch_data,
                                        fmin=librosa.note_to_hz('A2'),
                                        fmax=librosa.note_to_hz('E5'),
                                        sr=sr,
                                        frame_length=2048,
                                        hop_length=256)
    times = librosa.times_like(f0, sr=sr, hop_length=256)
    voiced = f0[voiced_flag]
    vtimes = times[voiced_flag]
    notes = []
    if len(voiced) > 0:
        cur_freq = voiced[0]
        start_t = vtimes[0]
        start_idx = 0
        for i in range(1, len(voiced)):
            if abs(voiced[i] - cur_freq) / cur_freq > 0.05:
                freq = float(np.median(voiced[start_idx:i]))
                dur = vtimes[i-1] - start_t
                if dur >= 0.05:
                    notes.append({'freq': freq, 'start': start_t, 'dur': dur})
                cur_freq = voiced[i]
                start_t = vtimes[i]
                start_idx = i
        freq = float(np.median(voiced[start_idx:]))
        dur = vtimes[-1] - start_t
        if dur >= 0.05:
            notes.append({'freq': freq, 'start': start_t, 'dur': dur})

    report.append('')
    report.append(f'--- {ch_name} pYIN notes ---')
    report.append(f'Count: {len(notes)}')
    for n in notes:
        m = hz_to_midi(n['freq'])
        report.append(f'  t={n["start"]:.3f}s  f={n["freq"]:.2f}Hz  dur={n["dur"]:.3f}s  MIDI={int(round(m)):3d}')
    if notes:
        freqs = [n['freq'] for n in notes]
        midi = [int(round(hz_to_midi(f))) for f in freqs]
        report.append(f'MIDI: {midi}')
        report.append(f'Direct ASCII: {"".join(chr(m) if 32<=m<=126 else "." for m in midi)}')
        best = []
        for shift in range(26):
            alpha = ''.join(chr(65 + ((m % 26 + shift) % 26)) for m in midi)
            vowels = sum(1 for ch in alpha if ch in 'AEIOU')
            score = 0
            if 0.15 < vowels/len(alpha) < 0.45:
                score += 1
            test_words = ['JOURNEY','HELLO','WORLD','ATLAS','TRACE','SKY','TAPE','MEMORY','SELF','PORTAL','NAME','WAKE','FIND','LOST','MIND','TIME','SPACE','VOID','NULL','ZERO','ONE','UNIT','MAIN','USER','ROOT','SYSTEM','ERROR','DEBUG','RESET','START','BEGIN','OPEN','CLOSE','ENTER','LEAVE','KNOW','LEARN','THINK','FEEL','HEAR','SPEAK','TELL','SAY','CALL','CODE','KEY','LOCK','DOOR','WAY','OUT','IN','UP','DOWN','LEFT','RIGHT','HERE','THERE','NOW','THEN','AGAIN','FOREVER','ALWAYS','NEVER','ONCE','TWICE']
            for w in test_words:
                if w in alpha:
                    score += 10
            if score > 0:
                best.append((shift, alpha, score))
        best.sort(key=lambda x: x[2], reverse=True)
        report.append('Best NMS:')
        for shift, alpha, score in best[:8]:
            report.append(f'  shift={shift:2d} score={score:3d}: {alpha}')

# ============================================================
# 6. Validation on tape_9_16_final_b_side.wav (first 5 min)
# ============================================================
report.append('')
report.append('='*70)
report.append('VALIDATION ON tape_9_16_final_b_side.wav (first 5 minutes)')
report.append('='*70)
try:
    y_tape, sr_tape = librosa.load(TAPE_PATH, sr=44100, mono=True)
    max_samples = 5 * 60 * 44100
    y_tape = y_tape[:max_samples]
    segs_tape = extract_sustained_tones(y_tape, sr_tape, n_fft=16384, hop_length=512,
                                        low_hz=50, high_hz=1000, min_frames=5, freq_tol_hz=5.0)
    report.append(f'Tape segments found: {len(segs_tape)}')
    for idx, s in enumerate(segs_tape[:20]):
        m = hz_to_midi(s['freq'])
        report.append(f'  #{idx:3d}  t={s["start"]:.3f}s  f={s["freq"]:.2f}Hz  MIDI={int(round(m)):3d}')
    if segs_tape:
        freqs = [s['freq'] for s in segs_tape]
        midi = [int(round(hz_to_midi(f))) for f in freqs]
        report.append(f'MIDI (first 30): {midi[:30]}')
        report.append(f'Direct ASCII:    {"".join(chr(m) if 32<=m<=126 else "." for m in midi[:30])}')
        shifts_with_journey = []
        for shift in range(26):
            alpha = ''.join(chr(65 + ((m % 26 + shift) % 26)) for m in midi)
            if 'JOURNEY' in alpha:
                shifts_with_journey.append(shift)
        report.append(f'Shifts containing JOURNEY in first 5 min: {shifts_with_journey}')
except Exception as e:
    report.append(f'Error: {e}')

# ============================================================
# 7. Additional: Constant-Q transform (CQT) note tracking
# ============================================================
report.append('')
report.append('='*70)
report.append('CONSTANT-Q TRANSFORM (CQT) NOTE TRACKING')
report.append('='*70)

for ch_name, ch_data in channels.items():
    C = np.abs(librosa.cqt(ch_data, sr=sr, fmin=librosa.note_to_hz('A2'),
                           n_bins=60, hop_length=512, bins_per_octave=12))
    times_cqt = librosa.frames_to_time(np.arange(C.shape[1]), sr=sr, hop_length=512)
    # Pick the loudest bin per frame
    peak_bin = np.argmax(C, axis=0)
    peak_mag = np.max(C, axis=0)
    median_mag = np.median(peak_mag)
    strong = peak_mag > median_mag * 2.0
    notes = []
    i = 0
    while i < len(peak_bin):
        if not strong[i]:
            i += 1
            continue
        start = i
        bin0 = peak_bin[i]
        j = i + 1
        while j < len(peak_bin) and strong[j] and abs(int(peak_bin[j]) - int(bin0)) <= 1:
            j += 1
        if j - start >= 5:
            midi_note = int(round(librosa.hz_to_midi(librosa.note_to_hz('A2') * (2 ** (np.median(peak_bin[start:j]) / 12.0)))))
            # Actually CQT bins are semitone steps
            midi_note = int(round(librosa.hz_to_midi(librosa.note_to_hz('A2'))) + np.median(peak_bin[start:j]))
            notes.append({
                'start': float(times_cqt[start]),
                'end': float(times_cqt[j-1]),
                'midi': int(round(midi_note)),
                'dur': float(times_cqt[j-1] - times_cqt[start])
            })
        i = j
    report.append('')
    report.append(f'--- {ch_name} CQT notes ---')
    report.append(f'Count: {len(notes)}')
    for n in notes:
        report.append(f'  t={n["start"]:.3f}-{n["end"]:.3f}s  MIDI={n["midi"]:3d}')
    if notes:
        midi = [n['midi'] for n in notes]
        report.append(f'MIDI: {midi}')
        report.append(f'Direct ASCII: {"".join(chr(m) if 32<=m<=126 else "." for m in midi)}')
        best = []
        for shift in range(26):
            alpha = ''.join(chr(65 + ((m % 26 + shift) % 26)) for m in midi)
            vowels = sum(1 for ch in alpha if ch in 'AEIOU')
            score = 0
            if 0.15 < vowels/len(alpha) < 0.45:
                score += 1
            if any(w in alpha for w in ['JOURNEY','HELLO','WORLD','ATLAS','TRACE','SKY','TAPE','MEMORY','SELF','PORTAL','NAME','WAKE','FIND','LOST','MIND','TIME','SPACE','VOID','NULL','ZERO','ONE','UNIT','MAIN','USER','ROOT','SYSTEM','ERROR','DEBUG','RESET','START','BEGIN','OPEN','CLOSE','ENTER','LEAVE','KNOW','LEARN','THINK','FEEL','HEAR','SPEAK','TELL','SAY','CALL','CODE','KEY','LOCK','DOOR','WAY','OUT','IN','UP','DOWN','LEFT','RIGHT','HERE','THERE','NOW','THEN','AGAIN','FOREVER','ALWAYS','NEVER','ONCE','TWICE']):
                score += 10
            if score > 0:
                best.append((shift, alpha, score))
        best.sort(key=lambda x: x[2], reverse=True)
        report.append('Best NMS:')
        for shift, alpha, score in best[:8]:
            report.append(f'  shift={shift:2d} score={score:3d}: {alpha}')

# ============================================================
# Save report
# ============================================================
save_report('ANALYSIS_REPORT.txt', report)
print('All analysis complete.')
