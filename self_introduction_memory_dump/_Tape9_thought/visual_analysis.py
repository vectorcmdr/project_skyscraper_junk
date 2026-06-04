import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

# Read the brightened image
img = mpimg.imread(r'C:\stack\arg\self_intro_spec_cont_brightened.png')
print(f"Image shape: {img.shape}")
print(f"Image dtype: {img.dtype}")

# Let's understand the image layout
# It's a stacked spectrogram with LEFT on top, RIGHT on bottom
# We need to figure out where the frequency labels are

# First, let's see what the pixel values look like
# The image should be 128x710x3 or similar based on the read output
# Let me check the actual dimensions

# The image appears to be quite wide (710 pixels) and relatively short
# Let's check if we can identify the frequency regions

# From the visual inspection:
# - The image has two channels stacked (LEFT top, RIGHT bottom)
# - The frequency axis appears to be on the left side
# - The bright patterns are in the middle section

# Let's try to extract a horizontal strip from the image to see the pattern
height, width = img.shape[:2]
print(f"Height: {height}, Width: {width}")

# Let's look at a few horizontal strips to understand the layout
for y_pos in [10, 20, 30, 40, 50]:
    if y_pos < height:
        strip = img[y_pos, :, :]
        avg_brightness = np.mean(strip)
        print(f"Row {y_pos}: avg brightness = {avg_brightness:.3f}")

# Let's try to identify the frequency regions
# In spectrograms, the bottom is usually low frequency, top is high frequency
# But this is a stacked view, so we need to find the separator

# Looking at the image, the patterns seem to form vertical bars
# Let's try to extract a region that looks like it might contain text

# The brightened image has strong magenta/white patterns
# Let's threshold to find bright regions
if img.dtype == np.float32 or img.max() <= 1.0:
    img_uint8 = (img * 255).astype(np.uint8)
else:
    img_uint8 = img.astype(np.uint8)

# Convert to grayscale
if len(img_uint8.shape) == 3:
    # Take the maximum across channels for bright regions
    gray = np.max(img_uint8, axis=2)
else:
    gray = img_uint8

print(f"Gray shape: {gray.shape}")
print(f"Gray min: {gray.min()}, max: {gray.max()}")

# Threshold to find bright pixels
threshold = 200
bright_mask = gray > threshold
print(f"Bright pixels: {np.sum(bright_mask)} out of {gray.size} ({100*np.sum(bright_mask)/gray.size:.1f}%)")

# Let's look at the distribution of bright pixels
# Focus on the 1000-4000 Hz range
# First, we need to find where the frequency labels are

# From the original images, I can see labels on the left side
# Let's try to find the region that corresponds to 1000-4000 Hz

# The image has a black border on the left with frequency labels
# Let's crop out the actual spectrogram part (excluding labels)

# Looking at the image, the labels are on the very left
# The actual spectrogram starts after the labels
# Let's assume the labels take about 10-20 pixels on the left

# Crop to just the spectrogram data
spectrogram_left = 15  # Skip the frequency labels
spec_img = img[:, spectrogram_left:, :]
spec_gray = gray[:, spectrogram_left:]

print(f"Spectrogram image shape: {spec_img.shape}")

# Now let's find the vertical separator between LEFT and RIGHT channels
# Looking at the brightened image, there's a black horizontal line in the middle
# Let's find it by looking for the darkest row in the middle region
mid_height = spec_gray.shape[0] // 2
search_range = 20
mid_region = spec_gray[mid_height-search_range:mid_height+search_range, :]
row_means = np.mean(mid_region, axis=1)
separator_row = mid_height - search_range + np.argmin(row_means)
print(f"Separator row (relative to spec_img): {separator_row}")

# Split into LEFT and RIGHT
left_img = spec_img[:separator_row, :, :]
right_img = spec_img[separator_row:, :, :]

print(f"LEFT shape: {left_img.shape}")
print(f"RIGHT shape: {right_img.shape}")

# Now let's focus on the 1000-4000 Hz region
# We need to figure out which rows correspond to which frequency
# The frequency labels show: 1000, 1500, 2000, 2500, 3000, 4000, 5000, 6000, 7000, 8000, 10000, 12000, 15000, 19000

# From the image, the patterns are strongest in the 1000-4000 Hz range
# Let's try to find this region by looking at the bright patterns

# The brightest patterns seem to be in the middle-to-lower part of each channel
# Let's take the middle 60% of each channel
left_start = left_img.shape[0] // 5
left_end = left_img.shape[0] * 4 // 5
right_start = right_img.shape[0] // 5
right_end = right_img.shape[0] * 4 // 5

left_region = left_img[left_start:left_end, :, :]
right_region = right_img[right_start:right_end, :, :]

print(f"LEFT region shape: {left_region.shape}")
print(f"RIGHT region shape: {right_region.shape}")

# Let's threshold and look for vertical bars
for name, region in [("LEFT", left_region), ("RIGHT", right_region)]:
    if len(region.shape) == 3:
        region_gray = np.max(region, axis=2)
    else:
        region_gray = region
    
    threshold = 200
    bright = region_gray > threshold
    
    # Look for vertical bars - columns with many bright pixels
    col_sums = np.sum(bright, axis=0)
    mean_col_sum = np.mean(col_sums)
    std_col_sum = np.std(col_sums)
    
    # Find columns that are significantly brighter than average
    bright_cols = col_sums > mean_col_sum + 2 * std_col_sum
    
    print(f"\n{name} channel:")
    print(f"  Bright columns: {np.sum(bright_cols)} out of {len(bright_cols)}")
    
    # Find contiguous groups of bright columns
    bright_groups = []
    in_group = False
    group_start = 0
    for i in range(len(bright_cols)):
        if bright_cols[i] and not in_group:
            in_group = True
            group_start = i
        elif not bright_cols[i] and in_group:
            in_group = False
            bright_groups.append((group_start, i))
    if in_group:
        bright_groups.append((group_start, len(bright_cols)))
    
    print(f"  Bright groups (start, end): {bright_groups[:20]}")
    
    # Let's visualize the region
    plt.figure(figsize=(20, 5))
    plt.imshow(bright, aspect='auto', cmap='binary')
    plt.title(f'{name} Channel - Bright Regions')
    plt.xlabel('Time (pixels)')
    plt.ylabel('Frequency (pixels)')
    plt.savefig(f'C:\\stack\\arg\\tapes_man_2\\spec_bright_{name.lower()}.png')
    plt.close()
