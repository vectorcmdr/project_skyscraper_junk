import librosa
import numpy as np

audio_path = r'C:\stack\arg\self_introduction_memory_dump.mp3'
y, sr = librosa.load(audio_path, sr=None, mono=False)
y_mono = (y[0] + y[1]) / 2

n_fft = 32768
hop = 64
D = librosa.stft(y_mono, n_fft=n_fft, hop_length=hop)
S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)
freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
times = librosa.frames_to_time(np.arange(S_db.shape[1]), sr=sr, hop_length=hop)

formant_freqs = [409.1, 442.8, 453.5, 528.9, 613.7, 702.5, 819.6, 912.5]
formant_bins = [np.argmin(np.abs(freqs - f)) for f in formant_freqs]

formant_energies = np.array([S_db[b, :] for b in formant_bins])

thresholds = []
for i in range(len(formant_bins)):
    median = np.median(formant_energies[i, :])
    std = np.std(formant_energies[i, :])
    thresholds.append(median + 0.8 * std)

binary_matrix = np.zeros((len(formant_bins), S_db.shape[1]), dtype=int)
for i in range(len(formant_bins)):
    binary_matrix[i, :] = (formant_energies[i, :] > thresholds[i]).astype(int)

print("=" * 70)
print("=== ACTIVE FORMANT COUNT ENCODING ===")
print("=" * 70)

# Find all segments (consecutive frames with same pattern)
segments = []
in_seg = False
seg_start = 0
seg_pattern = None

for t in range(binary_matrix.shape[1]):
    pattern = tuple(binary_matrix[:, t])
    if not in_seg:
        in_seg = True
        seg_start = t
        seg_pattern = pattern
    elif pattern != seg_pattern:
        # End previous segment
        seg_end = t - 1
        active_count = sum(seg_pattern)
        segments.append({
            'start': seg_start,
            'end': seg_end,
            'start_time': times[seg_start],
            'end_time': times[seg_end],
            'duration': (seg_end - seg_start + 1) * hop / sr,
            'active_count': active_count,
            'pattern': seg_pattern,
            'active_formants': [i+1 for i, v in enumerate(seg_pattern) if v == 1]
        })
        seg_start = t
        seg_pattern = pattern

# Handle last segment
if in_seg:
    seg_end = binary_matrix.shape[1] - 1
    active_count = sum(seg_pattern)
    segments.append({
        'start': seg_start,
        'end': seg_end,
        'start_time': times[seg_start],
        'end_time': times[seg_end],
        'duration': (seg_end - seg_start + 1) * hop / sr,
        'active_count': active_count,
        'pattern': seg_pattern,
        'active_formants': [i+1 for i, v in enumerate(seg_pattern) if v == 1]
    })

# Filter out very short segments (noise)
min_dur = 0.05  # 50ms
segments = [s for s in segments if s['duration'] >= min_dur]

print(f"\nTotal segments (min duration {min_dur}s): {len(segments)}")

# Get the active count sequence
counts = [s['active_count'] for s in segments]
print(f"\nActive count sequence: {counts}")

# Try decoding the counts
print("\n=== DECODING ATTEMPTS ===")

# 1. Direct count -> A-H (1=A, 8=H)
print("\n1. Count -> A-H (1=A, 8=H):")
decoded = []
for c in counts:
    if 1 <= c <= 8:
        decoded.append(chr(ord('A') + c - 1))
    else:
        decoded.append('?')
print(''.join(decoded))

# 2. Count -> 1-8 as digits
print("\n2. Count as digits:")
print(''.join(map(str, counts)))

# 3. Count + 64 -> ASCII (1+64=65=A, etc.)
print("\n3. Count + 64 -> ASCII:")
decoded = []
for c in counts:
    val = c + 64
    if 32 <= val <= 126:
        decoded.append(chr(val))
    else:
        decoded.append('.')
print(''.join(decoded))

# 4. Count * 8 -> ASCII range
print("\n4. Count * 8:")
for c in counts:
    val = c * 8
    print(f"{val:3d} ", end="")
print()

# 5. Look at only the 3-stroke segments specifically
print("\n5. Only 3-stroke segments, count their sequence:")
three_stroke_segments = [s for s in segments if s['active_count'] == 3]
print(f"   {len(three_stroke_segments)} three-stroke segments")

# What comes before and after each 3-stroke?
print("\n6. Context around 3-stroke segments (prev count, 3, next count):")
for i, seg in enumerate(segments):
    if seg['active_count'] == 3:
        prev_count = segments[i-1]['active_count'] if i > 0 else 0
        next_count = segments[i+1]['active_count'] if i < len(segments)-1 else 0
        print(f"   t={seg['start_time']:.2f}s: {prev_count} -> 3 -> {next_count}")

# 7. Try encoding: prev -> 3 -> next as a 3-digit code
print("\n7. Context as 3-digit codes (prev,3,next):")
codes = []
for i, seg in enumerate(segments):
    if seg['active_count'] == 3:
        prev_count = segments[i-1]['active_count'] if i > 0 else 0
        next_count = segments[i+1]['active_count'] if i < len(segments)-1 else 0
        code = prev_count * 100 + 30 + next_count
        codes.append(code)
        print(f"   {code}", end="")
print()

# 8. Look at the specific formant combinations that appear with count=3
print("\n8. Unique 3-stroke combinations and their context:")
for i, seg in enumerate(segments):
    if seg['active_count'] == 3:
        prev_seg = segments[i-1] if i > 0 else None
        next_seg = segments[i+1] if i < len(segments)-1 else None
        print(f"\n   t={seg['start_time']:.3f}-{seg['end_time']:.3f}s, dur={seg['duration']:.3f}s")
        print(f"   Formants: {seg['active_formants']}")
        if prev_seg:
            print(f"   Previous ({prev_seg['start_time']:.3f}s): count={prev_seg['active_count']}, formants={prev_seg['active_formants']}")
        if next_seg:
            print(f"   Next ({next_seg['start_time']:.3f}s): count={next_seg['active_count']}, formants={next_seg['active_formants']}")

# 9. Try using the formant indices themselves as a code
# Each 3-stroke has 3 numbers. What if we XOR them or combine them differently?
print("\n9. XOR of active formant indices:")
for seg in segments:
    if seg['active_count'] == 3:
        xor_result = seg['active_formants'][0] ^ seg['active_formants'][1] ^ seg['active_formants'][2]
        print(f"   {seg['active_formants']} XOR = {xor_result}")

# 10. Try summing the formant frequencies (not indices)
print("\n10. Sum of formant frequencies (rounded):")
for seg in segments:
    if seg['active_count'] == 3:
        freq_sum = sum(formant_freqs[i-1] for i in seg['active_formants'])
        print(f"   {freq_sum:.0f} Hz")

# 11. Look for repeating patterns in the sequence
print("\n11. Pattern analysis of full sequence:")
seq_str = ''.join(map(str, counts))
print(f"   Sequence: {seq_str}")

# Look for common substrings
for length in [2, 3, 4, 5]:
    print(f"\n   Common patterns of length {length}:")
    patterns = {}
    for i in range(len(counts) - length + 1):
        pat = tuple(counts[i:i+length])
        if pat not in patterns:
            patterns[pat] = 0
        patterns[pat] += 1
    
    # Show most common
    for pat, count in sorted(patterns.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"      {pat}: {count} times")

print("\n" + "=" * 70)

# Save to file
with open(r'C:\stack\arg\tapes_man_2\active_count_encoding.txt', 'w') as f:
    f.write("=== ACTIVE FORMANT COUNT ENCODING ===\n\n")
    f.write(f"Total segments: {len(segments)}\n\n")
    f.write("Full sequence:\n")
    for i, seg in enumerate(segments):
        f.write(f"  {i:3d}: t={seg['start_time']:.3f}s, count={seg['active_count']}, "
                f"formants={seg['active_formants']}, dur={seg['duration']:.3f}s\n")
    
    f.write(f"\nActive count sequence: {counts}\n")
    f.write(f"\nDecode 1 (count->A-H): {''.join(chr(ord('A') + c - 1) if 1 <= c <= 8 else '?' for c in counts)}\n")
    f.write(f"Decode 2 (count as digits): {''.join(map(str, counts))}\n")
