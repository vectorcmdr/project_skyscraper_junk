import librosa
import numpy as np

audio_path = r'C:\stack\arg\self_introduction_memory_dump.mp3'
y, sr = librosa.load(audio_path, sr=None, mono=False)
n_fft = 16384
hop = 256
freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)

# MONO
D = librosa.stft((y[0] + y[1])/2, n_fft=n_fft, hop_length=hop)
S = np.abs(D)

segments = [
    (0.627, 0.720, '1'),
    (3.402, 3.483, '2'),
    (6.548, 6.629, '3'),
    (8.626, 8.731, '4'),
    (9.567, 9.787, '5'),
    (10.542, 10.820, '6'),
    (11.447, 11.494, '7'),
    (11.540, 11.831, '8'),
    (11.854, 11.935, '9'),
    (12.365, 12.423, '10'),
    (12.434, 12.527, '11'),
    (12.539, 12.829, '12'),
    (12.852, 12.875, '13'),
    (13.189, 13.305, '14'),
    (13.317, 13.421, '15'),
    (13.433, 13.526, '16'),
    (13.537, 13.827, '17'),
    (13.851, 13.944, '18'),
    (13.955, 14.002, '19'),
    (14.060, 14.118, '20'),
    (14.187, 14.303, '21'),
    (14.338, 14.431, '22'),
    (14.443, 14.536, '23'),
    (14.547, 14.710, '24'),
    (14.838, 14.942, '25'),
    (14.954, 15.000, '26'),
    (15.058, 15.116, '27'),
    (15.186, 15.302, '28'),
    (15.314, 15.430, '29'),
    (15.476, 15.534, '30'),
    (15.546, 15.801, '31'),
    (15.836, 15.940, '32'),
    (15.952, 16.068, '33'),
]

print('Segment   Top2 Peaks (Hz)          Top2 Mags')
for start, end, label in segments:
    s_idx = int(start * sr)
    e_idx = int(end * sr)
    chunk = (y[0] + y[1])[s_idx:e_idx]
    if len(chunk) < n_fft:
        chunk = np.pad(chunk, (0, n_fft - len(chunk)), mode='constant')
    fft = np.abs(np.fft.rfft(chunk, n=n_fft))
    # find top 2 peaks in 50-1000 Hz
    mask = (freqs >= 50) & (freqs <= 1000)
    f_masked = freqs[mask]
    m_masked = fft[mask]
    # simple peak finding: local maxima
    peaks = []
    for i in range(1, len(m_masked)-1):
        if m_masked[i] > m_masked[i-1] and m_masked[i] > m_masked[i+1]:
            peaks.append((f_masked[i], m_masked[i]))
    peaks.sort(key=lambda x: x[1], reverse=True)
    top2 = peaks[:2] if len(peaks) >= 2 else (peaks[0] if peaks else (0,0))
    print(f'{label:>3}     {top2[0][0]:.2f} ({top2[0][1]:.2e})   {top2[1][0]:.2f} ({top2[1][1]:.2e})' if len(top2)==2 else f'{label:>3}     {top2[0][0]:.2f} ({top2[0][1]:.2e})')
