import numpy as np

# The 8 formant frequencies identified from the audio analysis
formants = [409.1, 442.8, 453.5, 528.9, 613.7, 702.5, 819.6, 912.5]

print("=== Formant Frequencies to MIDI/ASCII Conversion ===\n")

# Convert to MIDI
midis = [69 + 12 * np.log2(f/440.0) for f in formants]
print("Frequencies -> MIDI notes:")
for f, m in zip(formants, midis):
    print(f"  {f:6.1f} Hz -> MIDI {m:5.1f}")

# Try direct ASCII mapping (MIDI as character code)
print("\n=== Direct ASCII (MIDI as char code) ===")
for f, m in zip(formants, midis):
    midi_int = int(round(m))
    if 32 <= midi_int <= 126:
        print(f"  {f:6.1f} Hz -> MIDI {midi_int:3d} -> '{chr(midi_int)}'")
    else:
        print(f"  {f:6.1f} Hz -> MIDI {midi_int:3d} -> (non-printable)")

# Try modulo 26 -> alphabet (A=0)
print("\n=== Modulo 26 (A=0) mapping ===")
for f, m in zip(formants, midis):
    letter_idx = int(round(m)) % 26
    letter = chr(ord('A') + letter_idx)
    print(f"  {f:6.1f} Hz -> MIDI {int(round(m)):3d} % 26 = {letter_idx:2d} -> '{letter}'")

# Try (MIDI % 26 + 16) % 26 - the previous ARG method mentioned
print("\n=== Previous ARG method: (MIDI % 26 + 16) % 26 ===")
for f, m in zip(formants, midis):
    letter_idx = (int(round(m)) % 26 + 16) % 26
    letter = chr(ord('A') + letter_idx)
    print(f"  {f:6.1f} Hz -> (MIDI {int(round(m)):3d} % 26 + 16) % 26 = {letter_idx:2d} -> '{letter}'")

# Try hex conversion
print("\n=== Hexadecimal conversion ===")
for f, m in zip(formants, midis):
    midi_int = int(round(m))
    hex_val = hex(midi_int)
    if 32 <= midi_int <= 126:
        print(f"  {f:6.1f} Hz -> MIDI {midi_int:3d} -> hex {hex_val} -> '{chr(midi_int)}'")
    else:
        print(f"  {f:6.1f} Hz -> MIDI {midi_int:3d} -> hex {hex_val}")

# The formant frequencies themselves might be significant
print("\n=== Formant frequency ratios ===")
base = formants[0]
for f in formants:
    ratio = f / base
    print(f"  {f:6.1f} Hz / {base:.1f} Hz = {ratio:.3f}")

# Check if they're harmonic multiples
print("\n=== Are these harmonics? ===")
for f in formants:
    fundamental = f
    for n in range(1, 10):
        if abs(f - n * 100) < 20:
            print(f"  {f:.1f} Hz ≈ {n} x 100 Hz")
            break

# Compare with musical notes
note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
print("\n=== Musical note names ===")
for f, m in zip(formants, midis):
    midi_int = int(round(m))
    note_idx = midi_int % 12
    octave = midi_int // 12 - 1
    note_name = note_names[note_idx]
    print(f"  {f:6.1f} Hz -> {note_name}{octave} (MIDI {midi_int})")

# Try mapping to the ARG cipher
CIPHER_KEY = "MINDFAGEBJRLHCVPQSKYUWOXTZ"
print("\n=== ARG Cipher decode (A=0 index into key) ===")
for f, m in zip(formants, midis):
    idx = int(round(m))
    if idx < 26:
        letter = CIPHER_KEY[idx]
        print(f"  {f:6.1f} Hz -> index {idx:2d} -> key letter '{letter}'")
    else:
        print(f"  {f:6.1f} Hz -> index {idx:2d} -> (out of range)")

# The frequencies themselves might spell something when rounded
print("\n=== Rounded frequencies as digits ===")
rounded = [int(round(f)) for f in formants]
print(f"  Frequencies: {rounded}")
# Try pairing into ASCII codes
for i in range(0, len(rounded) - 1, 2):
    code = rounded[i] * 100 + rounded[i+1]
    if 32 <= code <= 126:
        print(f"  {rounded[i]},{rounded[i+1]} -> code {code} -> '{chr(code)}'")
