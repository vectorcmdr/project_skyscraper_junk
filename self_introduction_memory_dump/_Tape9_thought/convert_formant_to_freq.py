import numpy as np

# The formant shelf region spans rows 80-180 in the image
# This corresponds to approximately 400-1000 Hz based on the frequency labels

# Row mapping: row 80 ≈ 400 Hz, row 180 ≈ 1000 Hz (linear mapping)
row_min, row_max = 80, 180
freq_min, freq_max = 400, 1000

def row_to_freq(row):
    """Convert image row to frequency in Hz"""
    return freq_min + (row - row_min) * (freq_max - freq_min) / (row_max - row_min)

def freq_to_midi(freq):
    """Convert frequency to MIDI note number"""
    if freq <= 0:
        return 0
    return 69 + 12 * np.log2(freq / 440.0)

def midi_to_ascii(midi):
    """Convert MIDI note to ASCII character using the ARG cipher method"""
    # The previous ARG used: (midi % 26 + 16) % 26 -> letter index
    # Let's try this and also direct ASCII mapping
    note_index = int(round(midi)) % 26
    letter = chr(ord('A') + note_index)
    return letter

# Character bar positions (from the previous analysis)
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

# Note: The row numbers are relative to the shelf region (row 0 = row 80 in full image)
# So row 0 in shelf = 400 Hz, row 100 in shelf = 1000 Hz

print("=== Formant Shelf to Frequency/MIDI/ASCII Conversion ===\n")

decoded_chars = []

for char_idx in sorted(characters.keys()):
    groups = characters[char_idx]
    
    # Get the center row of each bar (relative to shelf region)
    bar_centers = [(start + end) / 2 for start, end in groups]
    
    # Convert to frequencies
    bar_freqs = [row_to_freq(row) for row in bar_centers]
    
    # Convert to MIDI notes
    bar_midis = [freq_to_midi(freq) for freq in bar_freqs]
    
    # Convert to ASCII using the ARG method
    bar_letters = [midi_to_ascii(midi) for midi in bar_midis]
    
    # Create a string from the letters
    char_string = ''.join(bar_letters)
    
    decoded_chars.append((char_idx, bar_centers, bar_freqs, bar_midis, bar_letters, char_string))
    
    print(f"Char {char_idx:2d}:")
    print(f"  Bar positions (rows): {[f'{c:.0f}' for c in bar_centers]}")
    print(f"  Frequencies (Hz): {[f'{f:.0f}' for f in bar_freqs]}")
    print(f"  MIDI notes: {[f'{m:.1f}' for m in bar_midis]}")
    print(f"  Letters: {bar_letters}")
    print(f"  String: {char_string}")
    print()

# Now let's see if we can form words from these decoded characters
print("\n=== Potential Message Decoding ===")
print("\nMethod 1: Use the first letter of each character's string:")
first_letters = ''.join([chars[4][0] for chars in decoded_chars])
print(f"First letters: {first_letters}")

print("\nMethod 2: Use all letters concatenated:")
all_letters = ''.join([chars[5] for chars in decoded_chars])
print(f"All letters: {all_letters}")

print("\nMethod 3: Try different interpretations of the bars:")
print("If bars represent Braille dots (2x3 grid):")
for char_idx, groups in sorted(characters.items()):
    num_bars = len(groups)
    print(f"  Char {char_idx}: {num_bars} bars")
