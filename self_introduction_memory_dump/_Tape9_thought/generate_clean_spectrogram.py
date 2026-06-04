import librosa
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from PIL import Image

# Load audio
audio_path = r'C:\stack\arg\self_introduction_memory_dump.mp3'
y, sr = librosa.load(audio_path, sr=None, mono=False)

# Generate spectrogram for the 1000-4000 Hz range with high resolution
n_fft = 8192
hop = 128

# Use mono for cleaner analysis
y_mono = (y[0] + y[1]) / 2

# Compute STFT
D = librosa.stft(y_mono, n_fft=n_fft, hop_length=hop)
S = np.abs(D)
S_db = librosa.amplitude_to_db(S, ref=np.max)

freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
times = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr, hop_length=hop)

print(f"Frequencies range: {freqs[0]:.1f} - {freqs[-1]:.1f} Hz")
print(f"Time range: {times[0]:.3f} - {times[-1]:.3f} s")
print(f"Spectrogram shape: {S.shape}")

# Focus on 1000-4000 Hz range (where the text patterns appear to be)
freq_min, freq_max = 1000, 4000
freq_mask = (freqs >= freq_min) & (freqs <= freq_max)
freqs_region = freqs[freq_mask]
S_region = S_db[freq_mask, :]

print(f"\nRegion {freq_min}-{freq_max} Hz:")
print(f"  Shape: {S_region.shape}")
print(f"  dB range: {S_region.min():.1f} to {S_region.max():.1f}")

# Create a high-contrast version for analysis
# Threshold to find the strongest peaks
threshold_db = S_region.max() - 20  # Top 20 dB
binary_region = S_region > threshold_db

print(f"  Binary pixels above threshold: {np.sum(binary_region)} out of {binary_region.size}")

# Save the region as an image
plt.figure(figsize=(24, 4))
plt.imshow(S_region, aspect='auto', origin='lower', cmap='magma', vmin=S_region.max()-60, vmax=S_region.max())
plt.colorbar(label='dB')
plt.xlabel('Time (frames)')
plt.ylabel('Frequency (Hz)')
plt.title(f'Spectrogram {freq_min}-{freq_max} Hz')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\spectrogram_1k_4k.png', dpi=150)
plt.close()

# Save the binary version
plt.figure(figsize=(24, 4))
plt.imshow(binary_region, aspect='auto', origin='lower', cmap='binary')
plt.xlabel('Time (frames)')
plt.ylabel('Frequency (Hz)')
plt.title(f'Binary Spectrogram {freq_min}-{freq_max} Hz')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\spectrogram_1k_4k_binary.png', dpi=150)
plt.close()

# Let's look at the pattern in more detail
# The text seems to be encoded in vertical bars
# Let's analyze the time-domain pattern

# Find columns (time frames) with many bright pixels
col_sums = np.sum(binary_region, axis=0)
print(f"\nColumn statistics:")
print(f"  Mean: {np.mean(col_sums):.1f}")
print(f"  Std: {np.std(col_sums):.1f}")
print(f"  Max: {np.max(col_sums)}")

# Find time frames with significant energy
bright_frames = col_sums > np.mean(col_sums) + np.std(col_sums)
print(f"  Bright frames: {np.sum(bright_frames)}")

# Group consecutive bright frames into "characters"
characters = []
in_char = False
char_start = 0

for i in range(len(bright_frames)):
    if bright_frames[i] and not in_char:
        in_char = True
        char_start = i
    elif not bright_frames[i] and in_char:
        in_char = False
        characters.append((char_start, i, i - char_start))
if in_char:
    characters.append((char_start, len(bright_frames), len(bright_frames) - char_start))

print(f"\nDetected character groups (start, end, width):")
for i, (start, end, width) in enumerate(characters[:50]):
    time_start = times[start] if start < len(times) else times[-1]
    time_end = times[end-1] if end-1 < len(times) else times[-1]
    print(f"  Char {i:3d}: frames {start:4d}-{end:4d}, width={width:3d}, time={time_start:.3f}-{time_end:.3f}s")
