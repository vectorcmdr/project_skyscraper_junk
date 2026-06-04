import librosa
import numpy as np
from scipy import signal as sig

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

# Extract energy at each formant
formant_energies = np.array([S_db[b, :] for b in formant_bins])

# Calculate thresholds
thresholds = []
for i in range(len(formant_bins)):
    median = np.median(formant_energies[i, :])
    std = np.std(formant_energies[i, :])
    threshold = median + 0.8 * std
    thresholds.append(threshold)

# Binary on/off matrix
binary_matrix = np.zeros((len(formant_bins), S_db.shape[1]), dtype=int)
for i in range(len(formant_bins)):
    binary_matrix[i, :] = (formant_energies[i, :] > thresholds[i]).astype(int)

# Find all unique patterns and their frequencies
patterns = {}
for t in range(binary_matrix.shape[1]):
    pattern = tuple(binary_matrix[:, t])
    if pattern not in patterns:
        patterns[pattern] = {'count': 0, 'times': []}
    patterns[pattern]['count'] += 1
    if len(patterns[pattern]['times']) < 5:
        patterns[pattern]['times'].append(times[t])

print(f"Total unique patterns: {len(patterns)}")
print("\nMost common patterns:")
sorted_patterns = sorted(patterns.items(), key=lambda x: x[1]['count'], reverse=True)
for pattern, info in sorted_patterns[:20]:
    active = [i+1 for i, v in enumerate(pattern) if v == 1]
    pattern_str = ''.join(map(str, pattern))
    byte = int(pattern_str, 2)
    ascii_char = chr(byte) if 32 <= byte <= 126 else '.'
    print(f"  {pattern_str} (active={active}): {info['count']} frames, "
          f"byte={byte}, ascii='{ascii_char}', times={info['times'][:3]}")

# Now let's look for the "3 stroke" structure
# This would be patterns with exactly 3 active formants
print("\n=== Patterns with exactly 3 active formants (3 strokes) ===")
three_stroke = [(p, i) for p, i in patterns.items() if sum(p) == 3]
for pattern, info in sorted(three_stroke, key=lambda x: x[1]['count'], reverse=True)[:10]:
    active = [i+1 for i, v in enumerate(pattern) if v == 1]
    pattern_str = ''.join(map(str, pattern))
    print(f"  {pattern_str}: formants {active}, {info['count']} frames")

# Let's also look at patterns with 2, 4, 5, 6 active formants
for count in [1, 2, 4, 5, 6]:
    stroke_patterns = [(p, i) for p, i in patterns.items() if sum(p) == count]
    print(f"\nPatterns with {count} active formants:")
    for pattern, info in sorted(stroke_patterns, key=lambda x: x[1]['count'], reverse=True)[:5]:
        active = [i+1 for i, v in enumerate(pattern) if v == 1]
        pattern_str = ''.join(map(str, pattern))
        print(f"  {pattern_str}: formants {active}, {info['count']} frames")

# Create a mapping: assign each unique pattern to a character
# Try mapping by frequency rank
print("\n=== Pattern-to-Character Mapping Attempts ===")

# Method 1: Sort by frequency and assign A-Z
unique_patterns = list(patterns.keys())
pattern_rank = {p: i for i, p in enumerate(sorted(unique_patterns, key=lambda p: patterns[p]['count'], reverse=True))}

print("\nMethod 1: Rank by frequency -> A-Z:")
for p in sorted(unique_patterns, key=lambda p: patterns[p]['count'], reverse=True)[:26]:
    rank = pattern_rank[p]
    letter = chr(ord('A') + rank) if rank < 26 else '?'
    active = [i+1 for i, v in enumerate(p) if v == 1]
    print(f"  Pattern {''.join(map(str, p))} (formants {active}) -> {letter}")

# Apply this mapping to decode the sequence
print("\n=== Decoded Sequence ===")
decoded = []
for t in range(binary_matrix.shape[1]):
    pattern = tuple(binary_matrix[:, t])
    if pattern in pattern_rank and pattern_rank[pattern] < 26:
        decoded.append(chr(ord('A') + pattern_rank[pattern]))
    else:
        decoded.append('.')

# Group consecutive same letters
message = []
prev = ''
for ch in decoded:
    if ch != prev:
        message.append(ch)
        prev = ch
    elif ch == '.':
        message.append(ch)

print(f"Message (grouped): {''.join(message[:100])}")

# Save to file
with open(r'C:\stack\arg\tapes_man_2\formant_pattern_decode.txt', 'w') as f:
    f.write("=== Formant Pattern Decoding ===\n\n")
    f.write("Unique patterns and their rankings:\n")
    for p in sorted(unique_patterns, key=lambda p: patterns[p]['count'], reverse=True):
        rank = pattern_rank[p]
        letter = chr(ord('A') + rank) if rank < 26 else '?'
        active = [i+1 for i, v in enumerate(p) if v == 1]
        f.write(f"  {''.join(map(str, p))} (formants {active}) -> {letter} ({patterns[p]['count']} frames)\n")
    
    f.write(f"\nDecoded sequence (first 500 chars):\n")
    f.write(''.join(decoded[:500]))
    f.write("\n")
