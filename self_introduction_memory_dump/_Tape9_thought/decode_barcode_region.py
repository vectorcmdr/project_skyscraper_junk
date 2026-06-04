import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Read the brightened image
img_pil = Image.open(r'C:\stack\arg\self_intro_spec_cont_brightened.png')
img = np.array(img_pil)
img_rgb = img[:, :, :3]
gray = np.mean(img_rgb, axis=2)

print(f"Image: {gray.shape[1]}x{gray.shape[0]}")

# From the previous analysis, the interesting region is:
# Columns 0-50, Rows 100-150
# This area has vertical bars that could be a barcode or text

# Let's extract and enhance this region
barcode_region = gray[100:150, 0:50]
print(f"Barcode region shape: {barcode_region.shape}")

# Enhance contrast
barcode_enhanced = np.clip(barcode_region * 2, 0, 255).astype(np.uint8)

# Save the enhanced region
plt.figure(figsize=(10, 8))
plt.imshow(barcode_enhanced, aspect='auto', cmap='magma', vmin=0, vmax=255)
plt.title('Barcode Region (Rows 100-150, Columns 0-50)')
plt.xlabel('Time (pixels)')
plt.ylabel('Frequency (pixels)')
plt.colorbar(label='Brightness')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\barcode_region.png', dpi=150)
plt.close()

# Let's also look at the label text on the left side
# The frequency labels might be readable

# Extract the leftmost columns (0-30) to see the labels
label_region = gray[:, :30]
print(f"\nLabel region shape: {label_region.shape}")

# Let's try to enhance and read the labels
label_enhanced = np.clip(label_region * 2, 0, 255).astype(np.uint8)

plt.figure(figsize=(10, 12))
plt.imshow(label_enhanced, aspect='auto', cmap='magma', vmin=0, vmax=255)
plt.title('Frequency Labels (Columns 0-30)')
plt.xlabel('Time (pixels)')
plt.ylabel('Frequency (pixels)')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\frequency_labels.png', dpi=150)
plt.close()

# Now let's look for text in the main spectrogram area
# From the left_region_enhanced image, there was interesting structure
# Let's extract the region that looked like it had text

# Looking at the previous image, there was a pattern that looked like it could be
# the frequency labels or encoded text around rows 100-150

# Let's try to decode this as a barcode
# First, let's convert the region to binary
threshold = 180
binary_barcode = barcode_enhanced > threshold

print(f"\nBarcode analysis:")
print(f"  Binary shape: {binary_barcode.shape}")
print(f"  White pixels (1s): {np.sum(binary_barcode)} ({100*np.sum(binary_barcode)/binary_barcode.size:.1f}%)")

# Let's look at the column sums to find the barcode pattern
col_sums = np.sum(binary_barcode, axis=0)
print(f"  Column sums: {col_sums}")

# Try to decode as a barcode
# This looks like it could be a simple 1D barcode
# Let's threshold each column as 0 or 1 based on majority of pixels
barcode_bits = (col_sums > barcode_enhanced.shape[0] / 2).astype(int)
print(f"  Barcode bits: {''.join(map(str, barcode_bits))}")

# Let's try to decode as ASCII
# Group bits into bytes (8 bits each)
bit_string = ''.join(map(str, barcode_bits))
print(f"\n  Bit string: {bit_string}")
print(f"  Length: {len(bit_string)} bits")

# Try decoding as 7-bit ASCII
for start in range(0, len(bit_string) - 7, 7):
    byte = bit_string[start:start+7]
    value = int(byte, 2)
    if 32 <= value <= 126:
        print(f"  Byte {start//7}: {byte} = {value} = '{chr(value)}'")
    else:
        print(f"  Byte {start//7}: {byte} = {value} = (non-printable)")
