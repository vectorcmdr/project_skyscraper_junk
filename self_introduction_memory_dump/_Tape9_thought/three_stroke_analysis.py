import librosa
import numpy as np
from scipy import signal as sig
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

audio_path = r'C:\stack\arg\self_introduction_memory_dump.mp3'
y, sr = librosa.load(audio_path, sr=None, mono=False)
y_mono = (y[0] + y[1]) / 2

n_fft = 32768
hop = 64
D = librosa.stft(y_mono, n_fft=n_fft, hop_length=hop)
S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)
freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
times = librosa.frames_to_time(np.arange(S_db.shape[1]), sr=sr, hop_length=hop)

# The 8 formant frequencies
formant_freqs = [409.1, 442.8, 453.5, 528.9, 613.7, 702.5, 819.6, 912.5]
formant_bins = [np.argmin(np.abs(freqs - f)) for f in formant_freqs]

# Extract energy at each formant
formant_energies = np.array([S_db[b, :] for b in formant_bins])

# Calculate thresholds
thresholds = []
for i in range(len(formant_bins)):
    median = np.median(formant_energies[i, :])
    std = np.std(formant_energies[i, :])
    thresholds.append(median + 0.8 * std)

# Binary on/off matrix
binary_matrix = np.zeros((len(formant_bins), S_db.shape[1]), dtype=int)
for i in range(len(formant_bins)):
    binary_matrix[i, :] = (formant_energies[i, :] > thresholds[i]).astype(int)

print("=" * 70)
print("=== THREE-STROKE PATTERN FORENSIC ANALYSIS ===")
print("=" * 70)

# Find ALL segments with exactly 3 active formants
segments = []
in_segment = False
seg_start = 0
seg_pattern = None

for t in range(binary_matrix.shape[1]):
    pattern = tuple(binary_matrix[:, t])
    active_count = sum(pattern)
    
    if active_count == 3 and not in_segment:
        in_segment = True
        seg_start = t
        seg_pattern = pattern
    elif (active_count != 3) and in_segment:
        in_segment = False
        seg_end = t - 1
        segments.append({
            'start_frame': seg_start,
            'end_frame': seg_end,
            'start_time': times[seg_start],
            'end_time': times[seg_end],
            'duration_frames': seg_end - seg_start + 1,
            'duration_sec': (seg_end - seg_start + 1) * hop / sr,
            'pattern': seg_pattern,
            'active_formants': [i+1 for i, v in enumerate(seg_pattern) if v == 1],
            'frequencies': [formant_freqs[i] for i, v in enumerate(seg_pattern) if v == 1]
        })

# Handle case where last frame is a 3-stroke
if in_segment:
    seg_end = binary_matrix.shape[1] - 1
    segments.append({
        'start_frame': seg_start,
        'end_frame': seg_end,
        'start_time': times[seg_start],
        'end_time': times[seg_end],
        'duration_frames': seg_end - seg_start + 1,
        'duration_sec': (seg_end - seg_start + 1) * hop / sr,
        'pattern': seg_pattern,
        'active_formants': [i+1 for i, v in enumerate(seg_pattern) if v == 1],
        'frequencies': [formant_freqs[i] for i, v in enumerate(seg_pattern) if v == 1]
    })

print(f"\nTotal 3-stroke segments found: {len(segments)}")

# Group segments by their specific pattern
pattern_groups = {}
for seg in segments:
    p = seg['pattern']
    if p not in pattern_groups:
        pattern_groups[p] = []
    pattern_groups[p].append(seg)

print(f"\nUnique 3-stroke patterns: {len(pattern_groups)}")
for pattern, segs in sorted(pattern_groups.items(), key=lambda x: len(x[1]), reverse=True):
    active = [i+1 for i, v in enumerate(pattern) if v == 1]
    freqs_active = [formant_freqs[i] for i, v in enumerate(pattern) if v == 1]
    print(f"  Pattern {''.join(map(str, pattern))}: formants {active}")
    print(f"    Frequencies: {[f'{f:.1f}' for f in freqs_active]} Hz")
    print(f"    Occurrences: {len(segs)}")
    
    # Average duration
    avg_dur = np.mean([s['duration_sec'] for s in segs])
    print(f"    Average duration: {avg_dur:.3f} sec")
    
    # Time positions
    time_positions = [s['start_time'] for s in segs]
    print(f"    Time positions: {[f'{t:.2f}' for t in time_positions[:10]]}{'...' if len(time_positions) > 10 else ''}")
    print()

# Now analyze the sequence of 3-stroke patterns
print("\n" + "=" * 70)
print("=== 3-STROKE SEQUENCE ANALYSIS ===")
print("=" * 70)

# Create a sequence where each entry is the pattern of a 3-stroke segment
sequence = []
for seg in segments:
    # Convert pattern to various representations
    pattern = seg['pattern']
    active = tuple(seg['active_formants'])
    freqs_tuple = tuple(int(round(f)) for f in seg['frequencies'])
    
    # Try to encode as a character
    # Use the 3 active formant indices as a code
    # Formants are numbered 1-8, so 3 active ones could be a combination code
    
    sequence.append({
        'time': seg['start_time'],
        'active': active,
        'frequencies': freqs_tuple,
        'pattern': ''.join(map(str, pattern)),
        'duration': seg['duration_sec']
    })

print(f"\nSequence of {len(sequence)} 3-stroke events:\n")
for i, event in enumerate(sequence):
    print(f"  Event {i:3d}: t={event['time']:6.3f}s, "
          f"formants={event['active']}, "
          f"freqs={event['frequencies']}, "
          f"dur={event['duration']:.3f}s")

# Try decoding the sequence
print("\n" + "=" * 70)
print("=== DECODING ATTEMPTS ON 3-STROKE SEQUENCE ===")
print("=" * 70)

# Method 1: Use the first active formant number as a code
print("\n1. First active formant number -> A-H (1-8):")
for event in sequence:
    idx = event['active'][0]
    print(f"{idx}", end="")
print()

# Method 2: Use all 3 active formant numbers concatenated
print("\n2. All 3 active formant indices concatenated:")
for event in sequence:
    print(f"{''.join(map(str, event['active']))} ", end="")
print()

# Method 3: Sum the 3 active formant indices
print("\n3. Sum of active formant indices:")
for event in sequence:
    s = sum(event['active'])
    print(f"{s:2d} ", end="")
print()

# Method 4: Product of active formant indices
print("\n4. Product of active formant indices:")
for event in sequence:
    p = np.prod(event['active'])
    print(f"{p:3d} ", end="")
print()

# Method 5: Encode as a 3-digit number and map to ASCII
print("\n5. Active formants as 3-digit code (mod 128 for ASCII):")
for event in sequence:
    code = event['active'][0] * 100 + event['active'][1] * 10 + event['active'][2]
    print(f"{code:4d} ", end="")
print()

# Method 6: Use the frequency values themselves
print("\n6. Average frequency of 3 active formants -> MIDI -> ASCII:")
for event in sequence:
    avg_freq = np.mean(event['frequencies'])
    midi = 69 + 12 * np.log2(avg_freq / 440.0)
    midi_int = int(round(midi))
    if 32 <= midi_int <= 126:
        print(f"{chr(midi_int)}", end="")
    else:
        print(".", end="")
print()

# Method 7: Map each unique combination to a letter
print("\n7. Map each unique 3-formant combination to A-Z:")
unique_combos = list(set(tuple(e['active']) for e in sequence))
combo_map = {combo: chr(ord('A') + i) for i, combo in enumerate(sorted(unique_combos))}
for event in sequence:
    print(f"{combo_map[tuple(event['active'])]}", end="")
print()

# Method 8: Durations as Morse code (short < 0.1s = dot, long > 0.1s = dash)
print("\n8. Duration-based Morse code (short=. long=-):")
for event in sequence:
    if event['duration'] < 0.1:
        print(".", end="")
    else:
        print("-", end="")
print()

# Method 9: Time gaps between 3-stroke events
print("\n9. Time gaps between consecutive 3-stroke events:")
gaps = []
for i in range(1, len(sequence)):
    gap = sequence[i]['time'] - sequence[i-1]['time']
    gaps.append(gap)
    print(f"{gap:.3f} ", end="")
print()

print("\n10. Gaps as binary (short gap < 0.2s = 0, long gap >= 0.2s = 1):")
for gap in gaps:
    if gap < 0.2:
        print("0", end="")
    else:
        print("1", end="")
print()

# Try to decode gap binary as ASCII
print("\n11. Gap binary -> 7-bit ASCII:")
gap_binary = ''.join(['0' if g < 0.2 else '1' for g in gaps])
for start in range(0, len(gap_binary) - 6, 7):
    byte = gap_binary[start:start+7]
    val = int(byte, 2)
    if 32 <= val <= 126:
        print(f"{chr(val)}", end="")
    else:
        print(".", end="")
print()

print("\n" + "=" * 70)
print("=== END OF 3-STROKE ANALYSIS ===")
print("=" * 70)

# Save results to file
with open(r'C:\stack\arg\tapes_man_2\three_stroke_forensics.txt', 'w') as f:
    f.write("=== THREE-STROKE FORENSIC ANALYSIS ===\n\n")
    f.write(f"Total 3-stroke segments: {len(segments)}\n")
    f.write(f"Unique patterns: {len(pattern_groups)}\n\n")
    
    f.write("Pattern breakdown:\n")
    for pattern, segs in sorted(pattern_groups.items(), key=lambda x: len(x[1]), reverse=True):
        active = [i+1 for i, v in enumerate(pattern) if v == 1]
        f.write(f"  Formants {active}: {len(segs)} occurrences\n")
    
    f.write("\nSequence:\n")
    for i, event in enumerate(sequence):
        f.write(f"  {i:3d}: t={event['time']:.3f}s, formants={event['active']}, "
                f"freqs={event['frequencies']}, dur={event['duration']:.3f}s\n")
    
    f.write("\nDecoding attempts:\n")
    f.write("1. First formant index: " + ''.join(str(e['active'][0]) for e in sequence) + "\n")
    f.write("7. Unique combo mapping: " + ''.join(combo_map[tuple(e['active'])] for e in sequence) + "\n")
