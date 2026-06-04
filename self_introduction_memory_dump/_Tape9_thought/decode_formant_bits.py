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

# The 8 formant frequencies we identified
formant_freqs = [409.1, 442.8, 453.5, 528.9, 613.7, 702.5, 819.6, 912.5]

# Find the exact bin index for each formant
formant_bins = []
for f in formant_freqs:
    idx = np.argmin(np.abs(freqs - f))
    formant_bins.append(idx)
    print(f"Formant {f:.1f} Hz -> bin {idx} ({freqs[idx]:.1f} Hz)")

# Extract the energy at each formant over time
formant_energies = np.array([S_db[b, :] for b in formant_bins])

# For each formant, determine the threshold for "on" vs "off"
thresholds = []
for i in range(len(formant_bins)):
    median = np.median(formant_energies[i, :])
    std = np.std(formant_energies[i, :])
    threshold = median + 0.8 * std  # Slightly above median
    thresholds.append(threshold)
    print(f"Formant {i+1} threshold: {threshold:.1f} dB (median={median:.1f}, std={std:.1f})")

# Create binary matrix: which formants are on at each time frame
binary_matrix = np.zeros((len(formant_bins), S_db.shape[1]), dtype=int)
for i in range(len(formant_bins)):
    binary_matrix[i, :] = (formant_energies[i, :] > thresholds[i]).astype(int)

# Find time regions where the binary pattern changes
# These change points indicate new "characters"
changes = np.sum(np.abs(np.diff(binary_matrix, axis=1)), axis=0)
change_points = np.where(changes > 0)[0]

print(f"\nTotal change points: {len(change_points)}")

# Group consecutive frames with the same pattern into "characters"
# Use a minimum duration to filter out noise
min_duration_frames = 10  # ~145 ms

characters = []
current_start = 0
current_pattern = tuple(binary_matrix[:, 0])

for t in range(1, binary_matrix.shape[1]):
    new_pattern = tuple(binary_matrix[:, t])
    if new_pattern != current_pattern:
        # Pattern changed, save the previous character if it was long enough
        duration = t - current_start
        if duration >= min_duration_frames:
            characters.append({
                'start': current_start,
                'end': t - 1,
                'start_time': times[current_start],
                'end_time': times[t - 1],
                'duration': duration * hop / sr,
                'pattern': current_pattern,
                'active_formants': [i+1 for i, v in enumerate(current_pattern) if v == 1]
            })
        current_start = t
        current_pattern = new_pattern

# Don't forget the last one
duration = binary_matrix.shape[1] - current_start
if duration >= min_duration_frames:
    characters.append({
        'start': current_start,
        'end': binary_matrix.shape[1] - 1,
        'start_time': times[current_start],
        'end_time': times[-1],
        'duration': duration * hop / sr,
        'pattern': current_pattern,
        'active_formants': [i+1 for i, v in enumerate(current_pattern) if v == 1]
    })

print(f"\nCharacters found: {len(characters)}")
print(f"\nFirst 30 characters:")
for i, char in enumerate(characters[:30]):
    pattern_str = ''.join(map(str, char['pattern']))
    byte_val = int(pattern_str, 2)
    ascii_char = chr(byte_val) if 32 <= byte_val <= 126 else '.'
    print(f"  Char {i:2d}: t={char['start_time']:.3f}-{char['end_time']:.3f}s "
          f"pattern={pattern_str} byte={byte_val:3d} ascii='{ascii_char}' "
          f"formants={char['active_formants']}")

# Try different bit orderings
print(f"\n=== Trying different bit orderings ===")

# Standard order (formant 1 = MSB, formant 8 = LSB)
print("\nStandard bit order (F1=MSB, F8=LSB):")
for i, char in enumerate(characters[:20]):
    pattern_str = ''.join(map(str, char['pattern']))
    byte_val = int(pattern_str, 2)
    ascii_char = chr(byte_val) if 32 <= byte_val <= 126 else '.'
    print(f"  {ascii_char}", end='')
print()

# Reverse bit order (formant 8 = MSB, formant 1 = LSB)
print("\nReverse bit order (F8=MSB, F1=LSB):")
for i, char in enumerate(characters[:20]):
    pattern_str = ''.join(map(str, char['pattern'][::-1]))
    byte_val = int(pattern_str, 2)
    ascii_char = chr(byte_val) if 32 <= byte_val <= 126 else '.'
    print(f"  {ascii_char}", end='')
print()

# Try with 7 bits (ignore last formant)
print("\n7-bit order (F1=MSB, F7=LSB):")
for i, char in enumerate(characters[:20]):
    pattern_str = ''.join(map(str, char['pattern'][:7]))
    byte_val = int(pattern_str, 2)
    ascii_char = chr(byte_val) if 32 <= byte_val <= 126 else '.'
    print(f"  {ascii_char}", end='')
print()

# Try with 7 bits reversed
print("\n7-bit reverse (F7=MSB, F1=LSB):")
for i, char in enumerate(characters[:20]):
    pattern_str = ''.join(map(str, char['pattern'][:7][::-1]))
    byte_val = int(pattern_str, 2)
    ascii_char = chr(byte_val) if 32 <= byte_val <= 126 else '.'
    print(f"  {ascii_char}", end='')
print()

# Save all decoded characters to a file
with open(r'C:\stack\arg\tapes_man_2\formant_decode_all.txt', 'w') as f:
    f.write("=== Formant Shelf Decoding - All Characters ===\n\n")
    
    f.write("Standard 8-bit (F1=MSB, F8=LSB):\n")
    for char in characters:
        pattern_str = ''.join(map(str, char['pattern']))
        byte_val = int(pattern_str, 2)
        ascii_char = chr(byte_val) if 32 <= byte_val <= 126 else '.'
        f.write(ascii_char)
    f.write("\n\n")
    
    f.write("Reversed 8-bit (F8=MSB, F1=LSB):\n")
    for char in characters:
        pattern_str = ''.join(map(str, char['pattern'][::-1]))
        byte_val = int(pattern_str, 2)
        ascii_char = chr(byte_val) if 32 <= byte_val <= 126 else '.'
        f.write(ascii_char)
    f.write("\n\n")
    
    f.write("Standard 7-bit (F1=MSB, F7=LSB):\n")
    for char in characters:
        pattern_str = ''.join(map(str, char['pattern'][:7]))
        byte_val = int(pattern_str, 2)
        ascii_char = chr(byte_val) if 32 <= byte_val <= 126 else '.'
        f.write(ascii_char)
    f.write("\n\n")
    
    f.write("Reversed 7-bit (F7=MSB, F1=LSB):\n")
    for char in characters:
        pattern_str = ''.join(map(str, char['pattern'][:7][::-1]))
        byte_val = int(pattern_str, 2)
        ascii_char = chr(byte_val) if 32 <= byte_val <= 126 else '.'
        f.write(ascii_char)
    f.write("\n\n")

print(f"\nFull decode saved to formant_decode_all.txt")
