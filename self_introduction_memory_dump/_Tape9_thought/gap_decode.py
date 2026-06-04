import librosa
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import signal as sig

audio_path = r'C:\stack\arg\self_introduction_memory_dump.mp3'
y, sr = librosa.load(audio_path, sr=None, mono=False)
y_mono = (y[0] + y[1]) / 2

n_fft = 32768
hop = 64
D = librosa.stft(y_mono, n_fft=n_fft, hop_length=hop)
S = np.abs(D)
S_db = librosa.amplitude_to_db(S, ref=np.max)
freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
times = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr, hop_length=hop)

print(f"Freq resolution: {freqs[1]-freqs[0]:.2f} Hz")
print(f"Time resolution: {(times[1]-times[0])*1000:.2f} ms")

# The vertical gaps (strokes) are most visible in the bright bands
# Let's extract the energy at specific frequencies over time
# and look for dips (gaps)

target_bands = [
    (120, 130, "120-130 Hz band"),
    (185, 200, "185-200 Hz band"),
    (245, 260, "245-260 Hz band"),
    (345, 360, "345-360 Hz band"),
]

fig, axes = plt.subplots(len(target_bands), 1, figsize=(24, 3*len(target_bands)))

for idx, (f_low, f_high, label) in enumerate(target_bands):
    mask = (freqs >= f_low) & (freqs <= f_high)
    band_energy = np.mean(S_db[mask, :], axis=0)
    
    # Find gaps (dips in energy)
    # A gap is a local minimum that's significantly below the local mean
    median_energy = np.median(band_energy)
    std_energy = np.std(band_energy)
    
    # Find where energy drops below threshold
    gap_threshold = median_energy - 0.5 * std_energy
    is_gap = band_energy < gap_threshold
    
    # Find contiguous gap regions
    gap_regions = []
    in_gap = False
    gap_start = 0
    for i in range(len(is_gap)):
        if is_gap[i] and not in_gap:
            in_gap = True
            gap_start = i
        elif not is_gap[i] and in_gap:
            in_gap = False
            gap_regions.append((gap_start, i-1))
    if in_gap:
        gap_regions.append((gap_start, len(is_gap)-1))
    
    # Filter out very short gaps (noise)
    min_gap_width = 5
    significant_gaps = [(s, e) for s, e in gap_regions if (e - s) >= min_gap_width]
    
    print(f"\n{label}:")
    print(f"  Median energy: {median_energy:.1f} dB")
    print(f"  Gap threshold: {gap_threshold:.1f} dB")
    print(f"  Total gaps: {len(gap_regions)}, Significant gaps (width >= {min_gap_width}): {len(significant_gaps)}")
    
    if significant_gaps:
        print(f"  Gap times (s): {[(f'{times[s]:.3f}', f'{times[e]:.3f}') for s, e in significant_gaps[:20]]}")
        if len(significant_gaps) > 20:
            print(f"    ... and {len(significant_gaps)-20} more")
    
    # Plot
    axes[idx].plot(times, band_energy, 'b-', linewidth=0.5, alpha=0.7)
    axes[idx].axhline(y=median_energy, color='g', linestyle='--', alpha=0.5, label=f'Median: {median_energy:.1f} dB')
    axes[idx].axhline(y=gap_threshold, color='r', linestyle='--', alpha=0.5, label=f'Gap threshold: {gap_threshold:.1f} dB')
    
    # Mark gaps
    for s, e in significant_gaps:
        axes[idx].axvspan(times[s], times[e], alpha=0.3, color='red')
    
    axes[idx].set_ylabel('dB')
    axes[idx].set_title(f'{label} - {len(significant_gaps)} gaps found')
    axes[idx].legend(loc='upper right', fontsize=8)
    axes[idx].set_xlim(0, times[-1])

axes[-1].set_xlabel('Time (s)')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\gap_analysis.png', dpi=150)
plt.close()

# Now let's try to convert the gap pattern to a binary string
# Use the 120-130 Hz band as the primary channel
mask = (freqs >= 120) & (freqs <= 130)
band_energy = np.mean(S_db[mask, :], axis=0)
median_energy = np.median(band_energy)
std_energy = np.std(band_energy)
gap_threshold = median_energy - 0.5 * std_energy

# Sample at a fixed rate to create a bitstream
sample_rate = 20  # frames between samples (128 frames/sec @ hop=64, sr=44100 => ~344 samples/sec)
is_gap = band_energy < gap_threshold

# Sample the gap pattern
sampled_gaps = is_gap[::sample_rate]
binary_string = ''.join(['1' if g else '0' for g in sampled_gaps])

print(f"\n=== Gap Pattern as Binary ===")
print(f"Sample rate: {sample_rate} frames ({sample_rate*64/44100*1000:.1f} ms per bit)")
print(f"Binary length: {len(binary_string)} bits")
print(f"Binary: {binary_string}")

# Try to decode as 7-bit ASCII
print(f"\nTrying 7-bit ASCII:")
for start in range(0, len(binary_string) - 6, 7):
    byte = binary_string[start:start+7]
    value = int(byte, 2)
    char = chr(value) if 32 <= value <= 126 else '.'
    print(f"  {byte} = {value:3d} = '{char}'")

# Try to decode as 8-bit ASCII
print(f"\nTrying 8-bit ASCII:")
for start in range(0, len(binary_string) - 7, 8):
    byte = binary_string[start:start+8]
    value = int(byte, 2)
    char = chr(value) if 32 <= value <= 126 else '.'
    print(f"  {byte} = {value:3d} = '{char}'")
