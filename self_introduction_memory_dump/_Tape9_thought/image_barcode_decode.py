from PIL import Image
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

img_path = r'C:\stack\arg\self_intro_spec_cont_brightened.png'
img = Image.open(img_path).convert('L')
arr = np.array(img)
print('Image shape:', arr.shape)

# Split into top and bottom channels (approx)
h = arr.shape[0]
mid = h // 2
# Exclude a margin from left for axis
left_margin = 80

# --- TOP CHANNEL ---
top = arr[:mid, left_margin:]
# compute bright pixel count per row
row_sums = np.sum(top > 200, axis=1)
# smooth a bit
from scipy.ndimage import gaussian_filter1d
smoothed = gaussian_filter1d(row_sums.astype(float), sigma=1)
# find peaks
from scipy.signal import find_peaks
peaks, props = find_peaks(smoothed, distance=5, prominence=20)
print('Top channel row peaks (relative):', peaks)
print('Prominences:', props['prominences'])
# map to absolute row indices
abs_peaks_top = peaks
print('Top channel absolute rows:', abs_peaks_top)

# --- BOTTOM CHANNEL ---
bottom = arr[mid:, left_margin:]
row_sums_b = np.sum(bottom > 200, axis=1)
smoothed_b = gaussian_filter1d(row_sums_b.astype(float), sigma=1)
peaks_b, props_b = find_peaks(smoothed_b, distance=5, prominence=20)
print('Bottom channel row peaks (relative):', peaks_b)
print('Prominences:', props_b['prominences'])
abs_peaks_bottom = peaks_b + mid
print('Bottom channel absolute rows:', abs_peaks_bottom)

# Save a plot showing row sums and peaks
fig, axes = plt.subplots(2, 1, figsize=(10, 6))
axes[0].plot(smoothed)
axes[0].plot(peaks, smoothed[peaks], 'ro')
axes[0].set_title('Top channel row sums')
axes[1].plot(smoothed_b)
axes[1].plot(peaks_b, smoothed_b[peaks_b], 'ro')
axes[1].set_title('Bottom channel row sums')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\image_row_peaks.png')
print('Saved row peak plot.')

# For each channel, extract the barcode
# Use the top N peaks (e.g., 8)
N = min(8, len(abs_peaks_top))
for ch_name, abs_peaks, region in [('TOP', abs_peaks_top, top), ('BOTTOM', abs_peaks_bottom, bottom)]:
    print(f'\n=== {ch_name} BARCODE ===')
    # sort peaks by row (lowest frequency first)
    idx = np.argsort(abs_peaks)
    rows = abs_peaks[idx][:N]
    # For each column, compute average intensity in a small band around each peak
    barcode = []
    bandwidth = 3  # pixels above and below
    for col in range(region.shape[1]):
        bits = []
        for r in rows:
            # r is relative to region start
            r_rel = r if ch_name == 'TOP' else r - mid
            low = max(0, r_rel - bandwidth)
            high = min(region.shape[0], r_rel + bandwidth + 1)
            val = np.mean(region[low:high, col])
            bits.append(1 if val > 128 else 0)
        barcode.append(bits)
    barcode = np.array(barcode)
    print('Barcode shape:', barcode.shape)
    # Group identical consecutive patterns
    symbols = []
    if len(barcode) > 0:
        current = barcode[0].copy()
        start = 0
        for i in range(1, len(barcode)):
            if not np.array_equal(barcode[i], current):
                dur = i - start
                if dur >= 3:
                    byte_val = sum(b << (N - 1 - j) for j, b in enumerate(current))
                    char = chr(byte_val) if 32 <= byte_val <= 126 else f'0x{byte_val:02x}'
                    symbols.append((start, dur, current.copy(), byte_val, char))
                current = barcode[i].copy()
                start = i
        dur = len(barcode) - start
        if dur >= 3:
            byte_val = sum(b << (N - 1 - j) for j, b in enumerate(current))
            char = chr(byte_val) if 32 <= byte_val <= 126 else f'0x{byte_val:02x}'
            symbols.append((start, dur, current.copy(), byte_val, char))
    print('Symbols (first 40):')
    for start, dur, bits, val, char in symbols[:40]:
        bits_str = ''.join(str(b) for b in bits)
        print(f'  col={start:4d} dur={dur:3d} {bits_str} = 0x{val:02x} {char}')
    # Also try interpreting as 7-bit ASCII
    ascii_chars = []
    for _, _, _, val, _ in symbols:
        if 32 <= val <= 126:
            ascii_chars.append(chr(val))
        else:
            ascii_chars.append('.')
    print('ASCII from symbols:', ''.join(ascii_chars))
    # Try with different bit orders
    for label, bit_order in [('MSB-first', None), ('LSB-first', 'rev')]:
        vals = []
        for _, _, bits, _, _ in symbols:
            b = bits[::-1] if bit_order == 'rev' else bits
            v = sum(b << (N - 1 - j) for j, b in enumerate(b))
            vals.append(v)
        s = ''.join(chr(v) if 32 <= v <= 126 else '.' for v in vals)
        print(f'{label}:', s)
    # Try offset shifts on the values
    for offset in [0, 32, 64, -32]:
        s = ''.join(chr(v + offset) if 32 <= v + offset <= 126 else '.' for _, _, _, v, _ in symbols)
        print(f'offset={offset}:', s)
