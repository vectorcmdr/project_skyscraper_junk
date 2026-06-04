from PIL import Image
import numpy as np

img = Image.open(r'C:\stack\arg\self_intro_spec_cont_brightened.png').convert('L')
arr = np.array(img)

# define bands (approx) from image analysis
# top channel band: rows 185-215 (relative to top half)
# bottom channel band: rows 495-525 (absolute)
left_margin = 80

for ch_name, band_rows in [('TOP', slice(185, 215)), ('BOTTOM', slice(495, 525))]:
    region = arr[band_rows, left_margin:]
    # average brightness per column
    col_avg = np.mean(region, axis=0)
    # threshold: median of col_avg
    median = np.median(col_avg)
    binary = (col_avg > median).astype(int)
    # group runs
    symbols = []
    if len(binary) > 0:
        current = binary[0]
        start = 0
        for i in range(1, len(binary)):
            if binary[i] != current:
                dur = i - start
                if dur >= 3:
                    symbols.append((start, dur, int(current)))
                current = binary[i]
                start = i
        dur = len(binary) - start
        if dur >= 3:
            symbols.append((start, dur, int(current)))
    print(f'=== {ch_name} 1D barcode (band avg threshold) ===')
    print('Run lengths (first 100):', [s[1] for s in symbols[:100]])
    # Convert run lengths to bits: treat each run as a bit? No, binary is already bit.
    # Maybe group bits into bytes (8 runs per byte)
    bits = [s[2] for s in symbols]
    print('Bit sequence length:', len(bits))
    # Try grouping into 8-bit chunks
    for n_bits in [8, 7, 6, 5]:
        print(f'--- {n_bits}-bit groups ---')
        chars = []
        for i in range(0, len(bits) - len(bits)%n_bits, n_bits):
            byte = sum(bits[i+j] << (n_bits - 1 - j) for j in range(n_bits))
            chars.append(chr(byte) if 32 <= byte <= 126 else f'0x{byte:02x}')
        print(''.join(chars[:80]))
        # Also try reversed bit order
        chars_rev = []
        for i in range(0, len(bits) - len(bits)%n_bits, n_bits):
            byte = sum(bits[i+j] << j for j in range(n_bits))
            chars_rev.append(chr(byte) if 32 <= byte <= 126 else f'0x{byte:02x}')
        print('Rev:', ''.join(chars_rev[:80]))
    # Also try run-length encoding as symbols
    # map short run=0, long run=1? Not sure.
    print()
