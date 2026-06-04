import librosa
import numpy as np
from scipy import signal as sig
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

audio_path = r'C:\stack\arg\self_introduction_memory_dump.mp3'

# Load and reverse the audio
y, sr = librosa.load(audio_path, sr=None, mono=False)
print(f"Original audio: {y.shape}, SR: {sr}, duration: {y.shape[1]/sr:.3f}s")

# Reverse each channel
y_reversed = np.zeros_like(y)
y_reversed[0] = y[0][::-1]  # Reverse LEFT channel
y_reversed[1] = y[1][::-1]  # Reverse RIGHT channel

# Save reversed audio for verification
import soundfile as sf
sf.write(r'C:\stack\arg\tapes_man_2\reversed_audio.wav', y_reversed.T, sr)
print(f"Saved reversed audio to tapes_man_2/reversed_audio.wav")

# Use mono reversed for analysis
y_mono_rev = (y_reversed[0] + y_reversed[1]) / 2

# High-resolution STFT
n_fft = 32768
hop = 64
D = librosa.stft(y_mono_rev, n_fft=n_fft, hop_length=hop)
S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)
freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
times = librosa.frames_to_time(np.arange(S_db.shape[1]), sr=sr, hop_length=hop)

print(f"\nReversed STFT shape: {S_db.shape}")

# The 8 formant frequencies (same physical frequencies)
formant_freqs = [409.1, 442.8, 453.5, 528.9, 613.7, 702.5, 819.6, 912.5]
formant_bins = [np.argmin(np.abs(freqs - f)) for f in formant_freqs]

print("\n=== REVERSED AUDIO ANALYSIS ===")
print("=" * 70)

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

# Find segments with specific active formant counts
for target_count in [1, 2, 3]:
    print(f"\n=== {target_count}-STROKE SEGMENTS IN REVERSED AUDIO ===")
    segments = []
    in_seg = False
    seg_start = 0
    seg_pattern = None
    
    for t in range(binary_matrix.shape[1]):
        pattern = tuple(binary_matrix[:, t])
        active_count = sum(pattern)
        
        if active_count == target_count and not in_seg:
            in_seg = True
            seg_start = t
            seg_pattern = pattern
        elif (active_count != target_count) and in_seg:
            in_seg = False
            seg_end = t - 1
            if seg_end - seg_start >= 2:  # Min 3 frames
                segments.append({
                    'start_time': times[seg_start],
                    'end_time': times[seg_end],
                    'duration': (seg_end - seg_start + 1) * hop / sr,
                    'pattern': seg_pattern,
                    'active_formants': [i+1 for i, v in enumerate(seg_pattern) if v == 1],
                    'frequencies': [formant_freqs[i] for i, v in enumerate(seg_pattern) if v == 1]
                })
    
    if in_seg:
        seg_end = binary_matrix.shape[1] - 1
        if seg_end - seg_start >= 2:
            segments.append({
                'start_time': times[seg_start],
                'end_time': times[seg_end],
                'duration': (seg_end - seg_start + 1) * hop / sr,
                'pattern': seg_pattern,
                'active_formants': [i+1 for i, v in enumerate(seg_pattern) if v == 1],
                'frequencies': [formant_freqs[i] for i, v in enumerate(seg_pattern) if v == 1]
            })
    
    print(f"Total {target_count}-stroke segments: {len(segments)}")
    
    if target_count == 3:
        # Show the 3-stroke events
        print("\nThree-stroke events in REVERSED audio:")
        for i, seg in enumerate(segments):
            active = seg['active_formants']
            freqs = [int(round(f)) for f in seg['frequencies']]
            
            # Convert to ASCII
            ascii_letters = []
            for f in freqs:
                midi = 69 + 12 * np.log2(f / 440.0)
                ascii_letters.append(chr(int(round(midi))))
            
            print(f"  Event {i:2d}: t={seg['start_time']:6.3f}s, "
                  f"formants={active}, freqs={freqs}, "
                  f"letters={ascii_letters}, dur={seg['duration']:.3f}s")

# Also analyze the full sequence in reversed audio
print("\n=== FULL SEQUENCE IN REVERSED AUDIO ===")
segments_all = []
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
        seg_end = t - 1
        if seg_end - seg_start >= 2:
            segments_all.append({
                'start_time': times[seg_start],
                'end_time': times[seg_end],
                'duration': (seg_end - seg_start + 1) * hop / sr,
                'active_count': sum(seg_pattern),
                'pattern': seg_pattern,
                'active_formants': [i+1 for i, v in enumerate(seg_pattern) if v == 1]
            })
        seg_start = t
        seg_pattern = pattern

# Handle last
if in_seg:
    seg_end = binary_matrix.shape[1] - 1
    if seg_end - seg_start >= 2:
        segments_all.append({
            'start_time': times[seg_start],
            'end_time': times[seg_end],
            'duration': (seg_end - seg_start + 1) * hop / sr,
            'active_count': sum(seg_pattern),
            'pattern': seg_pattern,
            'active_formants': [i+1 for i, v in enumerate(seg_pattern) if v == 1]
        })

counts = [s['active_count'] for s in segments_all]
print(f"Total segments: {len(segments_all)}")
print(f"Active count sequence: {counts}")

print("\nDecode 1 (count->A-H):")
print(''.join(chr(ord('A') + c - 1) if 1 <= c <= 8 else '?' for c in counts))

print("\nDecode 2 (count as digits):")
print(''.join(map(str, counts)))

# Generate spectrogram of reversed audio
print("\nGenerating reversed spectrogram...")

# Focus on formant shelf region
f_low, f_high = 350, 1050
mask = (freqs >= f_low) & (freqs <= f_high)
S_db_region = S_db[mask, :]
freqs_region = freqs[mask]

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

print("Saved reversed spectrogram to tapes_man_2/reversed_spectrogram.png")
