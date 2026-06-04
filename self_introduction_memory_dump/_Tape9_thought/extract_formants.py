import librosa
import numpy as np
from scipy import signal as sig
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

audio_path = r'C:\stack\arg\self_introduction_memory_dump.mp3'
y, sr = librosa.load(audio_path, sr=None, mono=False)

# Use mono for cleaner analysis
y_mono = (y[0] + y[1]) / 2

# High-resolution STFT for precise frequency measurement
n_fft = 32768  # Very high frequency resolution (~1.35 Hz bins)
hop = 64

D = librosa.stft(y_mono, n_fft=n_fft, hop_length=hop)
S = np.abs(D)
S_db = librosa.amplitude_to_db(S, ref=np.max)
freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
times = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr, hop_length=hop)

print(f"Audio: {len(y_mono)} samples @ {sr} Hz")
print(f"Duration: {len(y_mono)/sr:.3f} s")
print(f"STFT: {S.shape[1]} frames, freq resolution {freqs[1]-freqs[0]:.2f} Hz")

# Focus on the formant shelf region: ~400-1000 Hz
f_low, f_high = 350, 1050
mask = (freqs >= f_low) & (freqs <= f_high)
freqs_region = freqs[mask]
S_region = S[mask, :]
S_db_region = S_db[mask, :]

print(f"\nFormant shelf region: {f_low}-{f_high} Hz")
print(f"  Bins: {len(freqs_region)}")
print(f"  Time frames: {S_region.shape[1]}")

# Find the sustained horizontal bars (formant shelves)
# These are frequencies that have consistently high energy across time

# Method: Find rows where median energy is high and consistent
row_median = np.median(S_db_region, axis=1)
row_std = np.std(S_db_region, axis=1)

# A formant shelf has high median energy AND low std (consistent across time)
# But in this case, the shelves may have gaps, so let's use a different approach

# Find peaks in the median energy profile
peaks, props = sig.find_peaks(row_median, height=np.max(row_median)-30, distance=5, prominence=5)

print(f"\nFormant peaks found: {len(peaks)}")
print("Peak frequencies:")
for i, peak in enumerate(peaks):
    print(f"  {i+1:2d}: {freqs_region[peak]:.1f} Hz (median={row_median[peak]:.1f} dB, std={row_std[peak]:.1f})")

# Now let's analyze the time structure at these formant frequencies
# The formant shelves appear and disappear over time, creating a pattern

print(f"\n=== Time Pattern Analysis at Formant Frequencies ===")

# For each peak frequency, extract the energy over time and find on/off regions
for i, peak_idx in enumerate(peaks[:10]):  # Top 10 peaks
    freq = freqs_region[peak_idx]
    energy = S_db_region[peak_idx, :]
    
    # Threshold to find on/off
    threshold = np.median(energy) + 0.5 * np.std(energy)
    is_on = energy > threshold
    
    # Find on regions
    on_regions = []
    in_on = False
    on_start = 0
    for j in range(len(is_on)):
        if is_on[j] and not in_on:
            in_on = True
            on_start = j
        elif not is_on[j] and in_on:
            in_on = False
            if j - on_start > 5:
                on_regions.append((on_start, j-1))
    if in_on and len(is_on) - on_start > 5:
        on_regions.append((on_start, len(is_on)-1))
    
    print(f"\n  Formant {i+1}: {freq:.1f} Hz")
    print(f"    On regions: {len(on_regions)}")
    if on_regions:
        print(f"    Times: {[(f'{times[s]:.3f}', f'{times[e]:.3f}') for s, e in on_regions[:5]]}")

# Let's try to find the "3 strokes" structure
# The green circle in the image shows 3 bright vertical strokes
# These are likely 3 formants active at the same time

print(f"\n=== Looking for 3-Formant Combinations ===")

# Sample at regular time intervals and find which formants are active
sample_interval = 100  # frames
sample_points = range(0, S_region.shape[1], sample_interval)

formant_active = []
for t in sample_points:
    active = []
    for peak_idx in peaks:
        energy = S_db_region[peak_idx, t]
        threshold = np.median(S_db_region[peak_idx, :]) + 0.5 * np.std(S_db_region[peak_idx, :])
        if energy > threshold:
            active.append(freqs_region[peak_idx])
    formant_active.append((times[t], active))

print(f"\nSampled at {len(formant_active)} time points:")
for t, active in formant_active[:20]:
    print(f"  t={t:.3f}s: {len(active)} formants active")
    if len(active) > 0:
        print(f"    Frequencies: {[f'{f:.0f}' for f in active[:5]]}")

# Save a focused spectrogram
plt.figure(figsize=(24, 6))
plt.imshow(S_db_region, aspect='auto', origin='lower',
           extent=[times[0], times[-1], freqs_region[0], freqs_region[-1]],
           cmap='magma', vmin=np.max(S_db_region)-50, vmax=np.max(S_db_region))
plt.colorbar(label='dB')
plt.xlabel('Time (s)')
plt.ylabel('Frequency (Hz)')
plt.title('Formant Shelf Region (350-1050 Hz)')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\formant_shelf_spectrogram.png', dpi=200)
plt.close()

# Also save with enhanced contrast
plt.figure(figsize=(24, 6))
plt.imshow(S_db_region, aspect='auto', origin='lower',
           extent=[times[0], times[-1], freqs_region[0], freqs_region[-1]],
           cmap='magma', vmin=np.max(S_db_region)-30, vmax=np.max(S_db_region))
plt.colorbar(label='dB')
plt.xlabel('Time (s)')
plt.ylabel('Frequency (Hz)')
plt.title('Formant Shelf Region - Enhanced Contrast')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\formant_shelf_enhanced.png', dpi=200)
plt.close()
