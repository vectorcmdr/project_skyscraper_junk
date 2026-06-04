import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Read the brightened image
img_pil = Image.open(r'C:\stack\arg\self_intro_spec_cont_brightened.png')
img = np.array(img_pil)
img_rgb = img[:, :, :3]

# Convert to grayscale
gray = np.mean(img_rgb, axis=2)

height, width = gray.shape
print(f"Image: {width}x{height}")

# Looking at the image, the left side (columns 0-200) seems to have interesting patterns
# Let's examine this region more closely

# Extract left region (first 200 pixels)
left_region = gray[:, :200]

# Let's look for horizontal lines in this region
# These could be frequency markers or encoded data

# Find rows with significant brightness
row_brightness = np.mean(left_region, axis=1)

# Find the brightest rows
bright_rows = np.argsort(row_brightness)[-20:]
print(f"\nBrightest rows in left region:")
for row in sorted(bright_rows):
    print(f"  Row {row}: brightness = {row_brightness[row]:.1f}")

# Now let's look at the middle region (columns 200-1800)
# This seems to have the main spectrogram content

middle_region = gray[:, 200:1800]

# Let's look for vertical patterns (barcodes)
# Sample some columns and look at their brightness profile

print(f"\nAnalyzing vertical patterns in middle region:")
for col in [500, 700, 900, 1100, 1300, 1500]:
    if col < middle_region.shape[1]:
        column = middle_region[:, col]
        # Find peaks
        from scipy import signal
        peaks, _ = signal.find_peaks(column, height=np.mean(column) + np.std(column), distance=5)
        print(f"\n  Column {col}:")
        print(f"    Mean brightness: {np.mean(column):.1f}")
        print(f"    Number of peaks: {len(peaks)}")
        if len(peaks) > 0:
            print(f"    Peak positions: {peaks[:10]}...")
            print(f"    Peak values: {column[peaks[:10]]}")

# Let's try to find the 1000-4000 Hz region
# Looking at the labels in the original image, 1000 Hz is near the bottom
# and 4000 Hz is roughly in the middle

# From the text_patterns image, the interesting patterns are in the middle-to-bottom
# Let's crop and enhance a specific region

# Try the region that appears to have text-like vertical bars
# Looking at columns 0-200, rows 100-250
text_region = gray[100:250, 0:200]

# Enhance contrast
text_enhanced = np.clip(text_region * 2, 0, 255).astype(np.uint8)

plt.figure(figsize=(10, 8))
plt.imshow(text_enhanced, aspect='auto', cmap='magma', vmin=0, vmax=255)
plt.title('Left Region (Columns 0-200, Rows 100-250) Enhanced')
plt.xlabel('Time (pixels)')
plt.ylabel('Frequency (pixels)')
plt.colorbar(label='Brightness')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\left_region_enhanced.png', dpi=150)
plt.close()

# Also try the region around columns 500-1000, rows 100-250
text_region2 = gray[100:250, 500:1000]
text_enhanced2 = np.clip(text_region2 * 2, 0, 255).astype(np.uint8)

plt.figure(figsize=(10, 8))
plt.imshow(text_enhanced2, aspect='auto', cmap='magma', vmin=0, vmax=255)
plt.title('Middle Region (Columns 500-1000, Rows 100-250) Enhanced')
plt.xlabel('Time (pixels)')
plt.ylabel('Frequency (pixels)')
plt.colorbar(label='Brightness')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\middle_region_enhanced.png', dpi=150)
plt.close()
