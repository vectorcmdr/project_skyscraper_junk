import librosa
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

# Load audio
audio_path = r'C:\stack\arg\self_introduction_memory_dump.mp3'
y, sr = librosa.load(audio_path, sr=None, mono=False)
y_mono = (y[0] + y[1]) / 2

# Generate spectrogram
n_fft = 8192
hop = 128
D = librosa.stft(y_mono, n_fft=n_fft, hop_length=hop)
S = np.abs(D)
S_db = librosa.amplitude_to_db(S, ref=np.max)

freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
times = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr, hop_length=hop)

# Focus on 1000-4000 Hz range
freq_min, freq_max = 1000, 4000
freq_mask = (freqs >= freq_min) & (freqs <= freq_max)
S_region = S_db[freq_mask, :]

# Threshold to binary
threshold_db = S_region.max() - 20
binary_region = S_region > threshold_db

# Character groups from previous analysis
characters = [
    (149, 177), (187, 285), (604, 651), (664, 707), (1184, 1217),
    (1229, 1247), (1266, 1377), (1545, 1569), (1686, 1726), (1992, 2033),
    (2121, 2154), (2272, 2310), (2386, 2419), (2533, 2534), (2536, 2540),
    (2648, 2689), (2697, 2728), (2822, 2830), (2920, 2943), (3051, 3074),
    (3188, 3205), (3847, 3891), (3991, 4021), (4048, 4050), (4051, 4052),
    (4475, 4498), (4645, 4666), (5282, 5306)
]

# Filter out very small character groups (width < 10)
valid_characters = [(s, e) for s, e in characters if (e - s) >= 10]
print(f"Valid character groups (width >= 10): {len(valid_characters)}")

# Extract and visualize each character
fig, axes = plt.subplots(len(valid_characters), 1, figsize=(20, 2*len(valid_characters)))
if len(valid_characters) == 1:
    axes = [axes]

for i, (start, end) in enumerate(valid_characters):
    # Extract the character pattern
    char_pattern = binary_region[:, start:end]
    
    # Plot
    axes[i].imshow(char_pattern, aspect='auto', origin='lower', cmap='binary')
    axes[i].set_ylabel(f'Char {i}\n{start}-{end}')
    axes[i].set_xlabel('Frequency bins')
    
    # Find the most common pattern (row distribution)
    row_sums = np.sum(char_pattern, axis=1)
    max_row = np.argmax(row_sums)
    axes[i].axhline(y=max_row, color='r', alpha=0.3, linewidth=0.5)
    
    print(f"Char {i:2d}: frames {start:4d}-{end:4d}, width={end-start:3d}, "
          f"rows with energy: {np.sum(row_sums > 0)}, "
          f"max row: {max_row}")

plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\character_patterns.png', dpi=150)
plt.close()

# Let's try to decode the characters by looking at their vertical structure
# Each character seems to be encoded as a set of horizontal bars at specific frequencies

print("\n\nAnalyzing character patterns for decoding:")
print("=" * 60)

# For each character, find the rows with significant energy
for i, (start, end) in enumerate(valid_characters):
    char_pattern = binary_region[:, start:end]
    row_energy = np.sum(char_pattern, axis=1)
    
    # Find rows with energy
    active_rows = np.where(row_energy > 0)[0]
    
    if len(active_rows) > 0:
        # Group consecutive active rows
        groups = []
        group_start = active_rows[0]
        prev = active_rows[0]
        for row in active_rows[1:]:
            if row == prev + 1:
                prev = row
            else:
                groups.append((group_start, prev))
                group_start = row
                prev = row
        groups.append((group_start, prev))
        
        # Convert to frequency range
        freq_indices = np.where(freq_mask)[0]
        freq_start = freqs[freq_indices[groups[0][0]]] if groups[0][0] < len(freq_indices) else 0
        freq_end = freqs[freq_indices[groups[-1][1]]] if groups[-1][1] < len(freq_indices) else 0
        
        print(f"\nChar {i:2d} (frames {start:4d}-{end:4d}):")
        print(f"  Active groups: {len(groups)}")
        print(f"  Frequency range: {freq_start:.0f} - {freq_end:.0f} Hz")
        print(f"  Group details: {groups[:5]}{'...' if len(groups) > 5 else ''}")
