import librosa
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

audio_path = r'C:\stack\arg\self_introduction_memory_dump.mp3'
y, sr = librosa.load(audio_path, sr=None, mono=False)

n_fft = 32768
hop = 64
y_mono = (y[0] + y[1]) / 2

D = librosa.stft(y_mono, n_fft=n_fft, hop_length=hop)
S = np.abs(D)
S_db = librosa.amplitude_to_db(S, ref=np.max)
freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
times = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr, hop_length=hop)

print(f"Frequencies: {freqs[0]:.1f} - {freqs[-1]:.1f} Hz")
print(f"Freq resolution: {freqs[1]-freqs[0]:.2f} Hz")
print(f"Time: {times[0]:.4f} - {times[-1]:.4f} s ({len(times)} frames)")

# Focus on 150-1000 Hz
mask = (freqs >= 100) & (freqs <= 1200)
freqs_r = freqs[mask]
S_r = S_db[mask, :]

print(f"\n100-1200 Hz region: {S_r.shape} ({len(freqs_r)} freq bins, {S_r.shape[1]} time frames)")

# Save spectrogram
plt.figure(figsize=(24, 6))
plt.imshow(S_r, aspect='auto', origin='lower', cmap='magma',
           extent=[times[0], times[-1], freqs_r[0], freqs_r[-1]],
           vmin=S_r.max()-50, vmax=S_r.max())
plt.colorbar(label='dB')
plt.xlabel('Time (s)')
plt.ylabel('Frequency (Hz)')
plt.title('Spectrogram 100-1200 Hz (High Resolution)')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\spec_100_1200_hires.png', dpi=200)
plt.close()

# Also save with enhanced contrast
plt.figure(figsize=(24, 6))
plt.imshow(S_r, aspect='auto', origin='lower', cmap='magma',
           extent=[times[0], times[-1], freqs_r[0], freqs_r[-1]],
           vmin=S_r.max()-30, vmax=S_r.max())
plt.colorbar(label='dB')
plt.xlabel('Time (s)')
plt.ylabel('Frequency (Hz)')
plt.title('Spectrogram 100-1200 Hz (High Contrast)')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\spec_100_1200_contrast.png', dpi=200)
plt.close()

# Binary threshold
threshold = S_r.max() - 20
binary = S_r > threshold
plt.figure(figsize=(24, 6))
plt.imshow(binary, aspect='auto', origin='lower', cmap='binary',
           extent=[times[0], times[-1], freqs_r[0], freqs_r[-1]])
plt.xlabel('Time (s)')
plt.ylabel('Frequency (Hz)')
plt.title('Binary Spectrogram 100-1200 Hz')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\spec_100_1200_binary.png', dpi=200)
plt.close()

# Now let's look at the vertical stroke pattern in this range
# Find columns where there's energy at specific harmonic frequencies
# Focus on the most active frequency bands

# Find the rows (frequencies) with the most energy
row_energy = np.mean(S_r, axis=1)
top_rows = np.argsort(row_energy)[-20:]
print(f"\nTop 20 frequency bins by average energy:")
for r in sorted(top_rows):
    print(f"  {freqs_r[r]:.1f} Hz (row {r}): energy = {row_energy[r]:.1f} dB")

# Now look at the time pattern at the most active frequencies
# Find the column pattern (strokes) at each frequency
print(f"\nStroke patterns at key frequencies:")
for target_freq in [150, 200, 250, 300, 350, 400, 500, 600]:
    # Find the closest row
    closest_row = np.argmin(np.abs(freqs_r - target_freq))
    actual_freq = freqs_r[closest_row]
    
    # Get the energy at this frequency over time
    freq_energy = S_r[closest_row, :]
    
    # Find peaks (strokes)
    from scipy import signal
    peaks, properties = signal.find_peaks(freq_energy, height=S_r.max()-25, distance=5, prominence=5)
    
    if len(peaks) > 0:
        peak_times = times[peaks] if peaks[-1] < len(times) else times[-1]
        print(f"\n  {actual_freq:.1f} Hz (row {closest_row}): {len(peaks)} strokes")
        print(f"    Stroke times (s): {[f'{t:.3f}' for t in times[peaks[:15]]]}")
        if len(peaks) > 15:
            print(f"    ... and {len(peaks)-15} more")
    else:
        print(f"\n  {actual_freq:.1f} Hz (row {closest_row}): no strokes found")
