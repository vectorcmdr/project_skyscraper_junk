import numpy as np

# The 8 formant frequencies and their direct ASCII mapping
formants = {
    1: {'freq': 409.1, 'ascii': 'D', 'midi': 68},
    2: {'freq': 442.8, 'ascii': 'E', 'midi': 69},
    3: {'freq': 453.5, 'ascii': 'F', 'midi': 70},
    4: {'freq': 528.9, 'ascii': 'H', 'midi': 72},
    5: {'freq': 613.7, 'ascii': 'K', 'midi': 75},
    6: {'freq': 702.5, 'ascii': 'M', 'midi': 77},
    7: {'freq': 819.6, 'ascii': 'P', 'midi': 80},
    8: {'freq': 912.5, 'ascii': 'R', 'midi': 82},
}

# The Da Vinci cipher key
CIPHER_KEY = "MINDFAGEBJRLHCVPQSKYUWOXTZ"

# The 12 three-stroke events (forward order)
three_strokes = [
    [4, 6, 8],  # HMR
    [5, 7, 8],  # KPR
    [1, 2, 8],  # DER
    [1, 7, 8],  # DPR
    [5, 7, 8],  # KPR
    [1, 2, 3],  # DEF
    [2, 7, 8],  # EPR
    [5, 7, 8],  # KPR
    [2, 3, 6],  # EFM
    [1, 2, 3],  # DEF
    [1, 2, 3],  # DEF
    [1, 2, 4],  # DEH
]

print("=== DA VINCI CIPHER DECODE ATTEMPTS ===\n")

# Method 1: Use the ASCII letters directly, then apply cipher
print("1. ASCII letters -> Cipher decode:")
for stroke in three_strokes:
    letters = [formants[f]['ascii'] for f in stroke]
    # Cipher decode: position in alphabet -> key letter
    decoded = []
    for letter in letters:
        pos = ord(letter) - ord('A')
        decoded.append(CIPHER_KEY[pos])
    print(f"  {''.join(letters)} -> {''.join(decoded)}")

# Method 2: Use formant indices as cipher positions
print("\n2. Formant index (1-8) as cipher position (0-7):")
for stroke in three_strokes:
    decoded = []
    for f in stroke:
        pos = f - 1  # 1->0, 2->1, etc.
        decoded.append(CIPHER_KEY[pos])
    print(f"  {stroke} -> {''.join(decoded)}")

# Method 3: Use formant index as cipher position, but reversed
print("\n3. Formant index reversed (8->0, 7->1, etc.):")
for stroke in three_strokes:
    decoded = []
    for f in stroke:
        pos = 8 - f  # 8->0, 7->1, etc.
        decoded.append(CIPHER_KEY[pos])
    print(f"  {stroke} -> {''.join(decoded)}")

# Method 4: Use MIDI note mod 26 as position
print("\n4. MIDI mod 26 -> cipher position:")
for stroke in three_strokes:
    decoded = []
    for f in stroke:
        midi = formants[f]['midi']
        pos = midi % 26
        decoded.append(CIPHER_KEY[pos])
    print(f"  {stroke} -> {''.join(decoded)}")

# Method 5: Read only specific positions from each 3-stroke
print("\n5. Only first formant of each 3-stroke:")
for stroke in three_strokes:
    f = stroke[0]
    print(f"{formants[f]['ascii']}", end="")
print()

print("\n6. Only middle formant of each 3-stroke:")
for stroke in three_strokes:
    f = stroke[1]
    print(f"{formants[f]['ascii']}", end="")
print()

print("\n7. Only last formant of each 3-stroke:")
for stroke in three_strokes:
    f = stroke[2]
    print(f"{formants[f]['ascii']}", end="")
print()

# Method 8: Try all 3-stroke combinations in reversed order
print("\n8. Reversed sequence, first formant only:")
for stroke in reversed(three_strokes):
    f = stroke[0]
    print(f"{formants[f]['ascii']}", end="")
print()

# Method 9: Look at frequency gaps between formants in each 3-stroke
print("\n9. Frequency gaps within each 3-stroke (rounded):")
for stroke in three_strokes:
    freqs = [formants[f]['freq'] for f in stroke]
    gaps = [int(round(freqs[i+1] - freqs[i])) for i in range(len(freqs)-1)]
    print(f"  {stroke}: {freqs} -> gaps {gaps}")

# Method 10: Frequency values as digits
print("\n10. Sum of 3 frequencies, then convert to letter:")
for stroke in three_strokes:
    freq_sum = sum(formants[f]['freq'] for f in stroke)
    midi = 69 + 12 * np.log2(freq_sum/3 / 440.0)
    letter = chr(int(round(midi)) % 26 + ord('A'))
    print(f"  {stroke}: sum={freq_sum:.0f} Hz -> {letter}")

print("\n=== END ===")
