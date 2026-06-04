import numpy as np

# The spectrogram has a logarithmic frequency scale
# From the labels: 100, 400, 700, 1000, 1500, 2000, 2500, 3000, 4000, 5000, 6000, 7000, 8000, 10000, 12000, 15000, 19000
# The LEFT channel spans rows 0-310

# Let me map based on the actual label positions visible in the image
# Row 0 ≈ top (high freq ~22050 Hz)
# Row 310 ≈ bottom (low freq ~0 Hz, but labels start at 100 Hz)

# From visual inspection:
# "100" label is near row 280-290 (bottom of LEFT channel)
# "400" label is near row 230-240
# "700" label is near row 190-200
# "1000" label is near row 160-170
# "1500" label is near row 130-140
# "2000" label is near row 110-120
# "2500" label is near row 95-105
# "3000" label is near row 80-90
# "4000" label is near row 60-70

# For the formant shelf region (rows 80-180 in LEFT channel):
# Row 80 ≈ 3000-4000 Hz (high end)
# Row 180 ≈ 500-600 Hz (low end)

# Let me use a logarithmic mapping
# f = f_max * (f_min/f_max)^(row/num_rows)
# Or use linear interpolation between known points

# Known mappings (row, freq):
known_points = [
    (60, 4000),
    (80, 3000),
    (100, 2500),
    (120, 2000),
    (140, 1500),
    (160, 1000),
    (180, 700),
    (200, 600),
    (220, 500),
    (240, 400),
    (280, 100),
]

# Create interpolation function
from scipy.interpolate import interp1d
rows_known = [p[0] for p in known_points]
freqs_known = [p[1] for p in known_points]
freq_interp = interp1d(rows_known, freqs_known, kind='linear', fill_value='extrapolate')

def row_to_freq(row):
    """Convert image row to frequency in Hz"""
    return float(freq_interp(row))

def freq_to_midi(freq):
    """Convert frequency to MIDI note number"""
    if freq <= 0:
        return 0
    return 69 + 12 * np.log2(freq / 440.0)

# The ARG cipher
CIPHER_KEY = "MINDFAGEBJRLHCVPQSKYUWOXTZ"
CIPHER_MAP = {}
for i, c in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
    CIPHER_MAP[c] = CIPHER_KEY[i]

def decode_cipher(letter):
    """Decode a letter using the ARG cipher"""
    # The cipher maps A->M, B->I, etc.
    # To decode, we need the reverse mapping
    for k, v in CIPHER_MAP.items():
        if v == letter:
            return k
    return letter

# Character bar positions (relative to shelf region, row 0 = row 80 in full image)
# So shelf row 0 corresponds to full image row 80
characters = {
    0: [(4,10), (12,18), (28,35), (44,51), (61,73), (83,99)],
    1: [(66,68), (70,99)],
    2: [(58,60), (63,63), (65,67), (69,99)],
    3: [(58,58), (66,99)],
    4: [(49,53), (56,56), (58,58), (61,62), (64,99)],
    5: [(48,48), (59,60), (62,99)],
    6: [(53,53), (55,99)],
    7: [(58,59), (68,99)],
    8: [(52,52), (54,56), (58,63), (66,67), (69,99)],
    9: [(54,56), (58,67), (69,99)],
    10: [(55,55), (58,63), (65,66), (68,99)],
    11: [(10,10), (12,12), (70,99)],
    12: [(71,99)],
    13: [(55,55), (71,99)],
    14: [(58,58), (67,67), (71,99)],
    15: [(70,70), (72,99)],
    16: [(55,55), (68,99)],
    17: [(59,59), (63,99)],
    18: [(50,55), (61,64), (69,99)],
    19: [(66,66), (69,69), (71,99)],
}

# Convert shelf rows to full image rows (add 80)
shelf_offset = 80

print("=== Corrected Formant Shelf Analysis ===\n")

decoded_chars = []

for char_idx in sorted(characters.keys()):
    groups = characters[char_idx]
    
    # Get the center row of each bar (convert to full image row)
    bar_centers_full = [(start + end) / 2 + shelf_offset for start, end in groups]
    
    # Convert to frequencies
    bar_freqs = [row_to_freq(row) for row in bar_centers_full]
    
    # Convert to MIDI notes
    bar_midis = [freq_to_midi(freq) for freq in bar_freqs]
    
    # Try to decode using MIDI -> ASCII
    # Method 1: Direct ASCII (MIDI as character code)
    # Method 2: ARG cipher method (MIDI % 26 -> letter)
    
    # Let's try both
    letters_midi = [chr(int(round(m)) % 26 + ord('A')) for m in bar_midis]
    
    # Also try the cipher decode
    letters_cipher = [decode_cipher(l) for l in letters_midi]
    
    decoded_chars.append({
        'idx': char_idx,
        'rows': bar_centers_full,
        'freqs': bar_freqs,
        'midis': bar_midis,
        'letters_midi': letters_midi,
        'letters_cipher': letters_cipher,
    })
    
    print(f"Char {char_idx:2d}:")
    print(f"  Rows (full image): {[f'{r:.0f}' for r in bar_centers_full]}")
    print(f"  Frequencies (Hz): {[f'{f:.0f}' for f in bar_freqs]}")
    print(f"  MIDI notes: {[f'{m:.1f}' for m in bar_midis]}")
    print(f"  Letters (MIDI%26): {letters_midi}")
    print(f"  Letters (cipher decode): {letters_cipher}")
    print()

# Now try to form words
print("\n=== Decoding Attempts ===")

# Method 1: First letter of each character
print("\n1. First letter of each character (MIDI%26):")
first_midi = ''.join([d['letters_midi'][0] for d in decoded_chars])
print(f"   {first_midi}")

print("\n2. First letter of each character (cipher decoded):")
first_cipher = ''.join([d['letters_cipher'][0] for d in decoded_chars])
print(f"   {first_cipher}")

# Method 2: Take the middle letter (if exists)
print("\n3. Middle letter of each character (MIDI%26):")
mid_letters = []
for d in decoded_chars:
    if len(d['letters_midi']) >= 2:
        mid_letters.append(d['letters_midi'][len(d['letters_midi'])//2])
    else:
        mid_letters.append(d['letters_midi'][0])
print(f"   {''.join(mid_letters)}")

# Method 3: Last letter of each character
print("\n4. Last letter of each character (MIDI%26):")
last_midi = ''.join([d['letters_midi'][-1] for d in decoded_chars])
print(f"   {last_midi}")

print("\n5. Last letter of each character (cipher decoded):")
last_cipher = ''.join([d['letters_cipher'][-1] for d in decoded_chars])
print(f"   {last_cipher}")
