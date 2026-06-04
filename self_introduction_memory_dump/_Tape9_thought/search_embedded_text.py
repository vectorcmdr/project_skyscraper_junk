import librosa
import numpy as np
import struct

audio_path = r'C:\stack\arg\self_introduction_memory_dump.mp3'

# Read the raw MP3 bytes
with open(audio_path, 'rb') as f:
    raw_bytes = f.read()

print(f"File size: {len(raw_bytes)} bytes")

# Search for printable ASCII strings
print("\n=== Printable ASCII strings in raw file ===")
strings_found = []
current_string = []
for b in raw_bytes:
    if 32 <= b <= 126:
        current_string.append(chr(b))
    else:
        if len(current_string) >= 4:
            strings_found.append(''.join(current_string))
        current_string = []

for s in strings_found[:50]:
    print(f"  {s}")

# Check for ID3 tags
print("\n=== ID3 Tags ===")
if raw_bytes[:3] == b'ID3':
    print("  ID3 tag found")
    # Parse ID3 header
    version = raw_bytes[3:5]
    flags = raw_bytes[5]
    size = struct.unpack('>I', raw_bytes[6:10])[0]
    print(f"  Version: {version}")
    print(f"  Flags: {flags}")
    print(f"  Size: {size}")
else:
    print("  No ID3 tag at start")

# Check for other common markers
markers = [b'TIT2', b'TPE1', b'TALB', b'COMM', b'TXXX', b'APIC']
for marker in markers:
    pos = raw_bytes.find(marker)
    if pos != -1:
        print(f"  Found {marker.decode()} at offset {pos}")

# Load audio and check PCM samples for hidden text
y, sr = librosa.load(audio_path, sr=None, mono=False)
print(f"\n=== PCM Sample Analysis ===")
print(f"Shape: {y.shape}, SR: {sr}")

# Check for 8-bit text encoding in samples
# Samples are float32 in range [-1, 1]
# Convert to 8-bit integers
y_int8 = ((y + 1) * 127.5).astype(np.uint8)

for ch in range(y_int8.shape[0]):
    print(f"\nChannel {ch} - searching for printable strings:")
    strings = []
    current = []
    for b in y_int8[ch]:
        if 32 <= b <= 126:
            current.append(chr(b))
        else:
            if len(current) >= 4:
                strings.append(''.join(current))
            current = []
    
    for s in strings[:20]:
        print(f"  {s}")

# Check for 16-bit text encoding
# Convert float [-1,1] to int16
y_int16 = (y * 32767).astype(np.int16)
for ch in range(y_int16.shape[0]):
    print(f"\nChannel {ch} - 16-bit sample strings:")
    strings = []
    current = []
    for i in range(0, len(y_int16[ch]) - 1, 2):
        val = struct.unpack('<h', struct.pack('<hh', y_int16[ch][i], 0)[:2])[0]
        if 32 <= val <= 126:
            current.append(chr(val))
        else:
            if len(current) >= 4:
                strings.append(''.join(current))
            current = []
    
    for s in strings[:20]:
        print(f"  {s}")

# Check LSB steganography
print("\n=== LSB Analysis ===")
for ch in range(y.shape[0]):
    # Extract LSBs and group into bytes
    lsb_bits = []
    for sample in y[ch]:
        # Convert float to 16-bit integer
        int_val = int(sample * 32767)
        lsb_bits.append(int_val & 1)
    
    # Convert bits to bytes
    bytes_data = []
    for i in range(0, len(lsb_bits) - 7, 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | lsb_bits[i + j]
        bytes_data.append(byte)
    
    # Search for printable strings
    strings = []
    current = []
    for b in bytes_data:
        if 32 <= b <= 126:
            current.append(chr(b))
        else:
            if len(current) >= 4:
                strings.append(''.join(current))
            current = []
    
    print(f"\nChannel {ch} - LSB strings:")
    for s in strings[:20]:
        print(f"  {s}")
