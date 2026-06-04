import librosa
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

audio_path = r'C:\stack\arg\self_introduction_memory_dump.mp3'
y, sr = librosa.load(audio_path, sr=None, mono=False)

# Reverse each channel
y_reversed = np.zeros_like(y)
y_reversed[0] = y[0][::-1]
y_reversed[1] = y[1][::-1]

# Use mono reversed
y_mono_rev = (y_reversed[0] + y_reversed[1]) / 2

# High-resolution STFT
n_fft = 32768
hop = 64
D = librosa.stft(y_mono_rev, n_fft=n_fft, hop_length=hop)
S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)
freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
times = librosa.frames_to_time(np.arange(S_db.shape[1]), sr=sr, hop_length=hop)

# Focus on formant shelf region
f_low, f_high = 350, 1050
freqs_arr = np.array(freqs)
mask = (freqs_arr >= f_low) & (freqs_arr <= f_high)
S_db_region = S_db[mask, :]
freqs_region = freqs_arr[mask]

# Generate spectrogram
plt.figure(figsize=(24, 6))
plt.imshow(S_db_region, aspect='auto', origin='lower',
           extent=[times[0], times[-1], freqs_region[0], freqs_region[-1]],
           cmap='magma', vmin=np.max(S_db_region)-50, vmax=np.max(S_db_region))
plt.colorbar(label='dB')
plt.xlabel('Time (s)')
plt.ylabel('Frequency (Hz)')
plt.title('REVERSED Audio - Formant Shelf Region (350-1050 Hz)')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\reversed_spectrogram.png', dpi=200)
plt.close()

# Also generate enhanced version
plt.figure(figsize=(24, 6))
plt.imshow(S_db_region, aspect='auto', origin='lower',
           extent=[times[0], times[-1], freqs_region[0], freqs_region[-1]],
           cmap='magma', vmin=np.max(S_db_region)-30, vmax=np.max(S_db_region))
plt.colorbar(label='dB')
plt.xlabel('Time (s)')
plt.ylabel('Frequency (Hz)')
plt.title('REVERSED Audio - Enhanced Contrast')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\reversed_spectrogram_enhanced.png', dpi=200)
plt.close()

# Generate binary threshold version
binary = S_db_region > (np.max(S_db_region) - 20)
plt.figure(figsize=(24, 6))
plt.imshow(binary, aspect='auto', origin='lower',
           extent=[times[0], times[-1], freqs_region[0], freqs_region[-1]],
           cmap='binary')
plt.xlabel('Time (s)')
plt.ylabel('Frequency (Hz)')
plt.title('REVERSED Audio - Binary Threshold')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\reversed_spectrogram_binary.png', dpi=200)
plt.close()

print("Saved reversed spectrograms:")
print("  reversed_spectrogram.png")
print("  reversed_spectrogram_enhanced.png")
print("  reversed_spectrogram_binary.png")
