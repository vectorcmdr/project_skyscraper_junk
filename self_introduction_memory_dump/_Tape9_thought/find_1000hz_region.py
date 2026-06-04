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

height, width = gray.shape
print(f"Image: {width}x{height}")

# From the original image, I saw frequency labels:
# 1000, 1500, 2000, 2500, 3000, 4000, 5000, 6000, 7000, 8000, 10000, 12000, 15000, 19000
# The 1000 Hz label appears to be near the bottom of each channel

# Let's try to find where the 1000 Hz label is by looking for text patterns
# The labels are likely in the leftmost columns (0-30)

# First, let's look at the very bottom of the image
bottom_rows = gray[height-50:, :]
print(f"\nBottom 50 rows shape: {bottom_rows.shape}")
print(f"Mean brightness: {np.mean(bottom_rows):.1f}")

# Let's also look at rows around 500-626 (bottom 20% of full image)
# This should include the 1000 Hz region for both channels

# The separator between LEFT and RIGHT is around row 311
# So LEFT channel rows 0-310, RIGHT channel rows 311-625

# For LEFT channel (rows 0-310):
# Bottom of LEFT channel (rows 250-310) would be the lowest frequencies in LEFT
# For RIGHT channel (rows 311-625):
# Bottom of RIGHT channel (rows 560-625) would be the lowest frequencies in RIGHT

left_bottom = gray[250:311, :]  # Bottom of LEFT channel
right_bottom = gray[560:626, :]  # Bottom of RIGHT channel

print(f"\nLEFT bottom (rows 250-310): {left_bottom.shape}")
print(f"RIGHT bottom (rows 560-625): {right_bottom.shape}")

# Let's enhance and save these
plt.figure(figsize=(24, 4))
plt.imshow(left_bottom, aspect='auto', cmap='magma', vmin=0, vmax=255)
plt.title('LEFT Channel - Bottom (Rows 250-310) - Should be ~1000 Hz region')
plt.xlabel('Time (pixels)')
plt.ylabel('Frequency (pixels)')
plt.colorbar(label='Brightness')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\left_bottom_actual.png', dpi=150)
plt.close()

plt.figure(figsize=(24, 4))
plt.imshow(right_bottom, aspect='auto', cmap='magma', vmin=0, vmax=255)
plt.title('RIGHT Channel - Bottom (Rows 560-625) - Should be ~1000 Hz region')
plt.xlabel('Time (pixels)')
plt.ylabel('Frequency (pixels)')
plt.colorbar(label='Brightness')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\right_bottom_actual.png', dpi=150)
plt.close()

# Let's also look for the actual strokes by finding dark vertical bands
# In a spectrorogram, the strokes would be areas of higher energy (brighter)
# but the user says "bright strokes" which means they ARE the bright areas

# Let's threshold to find the brightest areas
for name, region in [("LEFT", left_bottom), ("RIGHT", right_bottom)]:
    threshold = np.mean(region) + 2 * np.std(region)
    bright_mask = region > threshold
    
    print(f"\n{name} channel - Bright regions (strokes):")
    print(f"  Threshold: {threshold:.1f}")
    print(f"  Bright pixels: {np.sum(bright_mask)} ({100*np.sum(bright_mask)/bright_mask.size:.1f}%)")
    
    # Find vertical bars (columns with many bright pixels)
    col_sums = np.sum(bright_mask, axis=0)
    mean_col = np.mean(col_sums)
    std_col = np.std(col_sums)
    
    # Find columns significantly brighter than average
    bright_cols = col_sums > mean_col + 2 * std_col
    print(f"  Bright columns: {np.sum(bright_cols)}")
    
    # Find groups of bright columns
    bright_groups = []
    in_group = False
    group_start = 0
    for i in range(len(bright_cols)):
        if bright_cols[i] and not in_group:
            in_group = True
            group_start = i
        elif not bright_cols[i] and in_group:
            in_group = False
            bright_groups.append((group_start, i-1))
    if in_group:
        bright_groups.append((group_start, len(bright_cols)-1))
    
    print(f"  Bright groups: {bright_groups[:30]}")
