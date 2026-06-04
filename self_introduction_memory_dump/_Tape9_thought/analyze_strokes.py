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

# Extract the bottom region of LEFT channel (rows 250-310)
# This is where the strokes appear to be
left_bottom = gray[250:311, :]

print(f"Left bottom region: {left_bottom.shape}")

# The strokes are the DARK vertical streaks
# Let's threshold to find the dark areas (strokes)
# Dark = low brightness = stroke

# Find the threshold that separates dark strokes from bright background
threshold = np.mean(left_bottom) - 0.5 * np.std(left_bottom)
print(f"Threshold for dark strokes: {threshold:.1f}")

# Create binary mask where True = dark (stroke)
dark_mask = left_bottom < threshold
print(f"Dark pixels: {np.sum(dark_mask)} ({100*np.sum(dark_mask)/dark_mask.size:.1f}%)")

# Save the dark mask
plt.figure(figsize=(24, 4))
plt.imshow(dark_mask, aspect='auto', cmap='binary')
plt.title('Dark Strokes (Vertical Lines)')
plt.xlabel('Time (pixels)')
plt.ylabel('Frequency (pixels)')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\dark_strokes.png', dpi=150)
plt.close()

# Now let's look at the column pattern
# Each column represents a time slice
# Dark pixels in a column indicate a stroke at that time

# Sum dark pixels per column to get stroke intensity
col_dark_sum = np.sum(dark_mask, axis=0)

# Find columns with significant dark content (strokes)
mean_dark = np.mean(col_dark_sum)
std_dark = np.std(col_dark_sum)
stroke_threshold = mean_dark + 0.5 * std_dark

print(f"\nColumn dark sum statistics:")
print(f"  Mean: {mean_dark:.1f}")
print(f"  Std: {std_dark:.1f}")
print(f"  Stroke threshold: {stroke_threshold:.1f}")

# Find stroke columns
stroke_cols = col_dark_sum > stroke_threshold
print(f"  Stroke columns: {np.sum(stroke_cols)}")

# Find contiguous stroke groups
stroke_groups = []
in_group = False
group_start = 0
for i in range(len(stroke_cols)):
    if stroke_cols[i] and not in_group:
        in_group = True
        group_start = i
    elif not stroke_cols[i] and in_group:
        in_group = False
        stroke_groups.append((group_start, i-1))
if in_group:
    stroke_groups.append((group_start, len(stroke_cols)-1))

print(f"  Stroke groups: {len(stroke_groups)}")
print(f"  First 30 groups (start, end, width):")
for start, end in stroke_groups[:30]:
    print(f"    {start:4d}-{end:4d}, width={end-start+1:3d}")

# Let's try to convert this to a binary barcode
# Sample at regular intervals
sample_rate = 10  # Sample every 10 pixels
sampled_dark = col_dark_sum[::sample_rate]

# Convert to binary (1 = dark/stroke, 0 = bright/no stroke)
barcode_binary = (sampled_dark > np.mean(sampled_dark)).astype(int)

print(f"\nSampled barcode:")
print(f"  Length: {len(barcode_binary)} bits")
print(f"  Binary: {''.join(map(str, barcode_binary))}")

# Try to decode as ASCII
bit_string = ''.join(map(str, barcode_binary))
print(f"\nTrying to decode as 7-bit ASCII:")
for start in range(0, len(bit_string) - 6, 7):
    byte = bit_string[start:start+7]
    value = int(byte, 2)
    if 32 <= value <= 126:
        print(f"  Byte {start//7:3d}: {byte} = {value:3d} = '{chr(value)}'")
    else:
        print(f"  Byte {start//7:3d}: {byte} = {value:3d} = (non-printable)")

# Also try 8-bit ASCII
print(f"\nTrying to decode as 8-bit ASCII:")
for start in range(0, len(bit_string) - 7, 8):
    byte = bit_string[start:start+8]
    value = int(byte, 2)
    if 32 <= value <= 126:
        print(f"  Byte {start//8:3d}: {byte} = {value:3d} = '{chr(value)}'")
    else:
        print(f"  Byte {start//8:3d}: {byte} = {value:3d} = (non-printable)")
