import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import signal

# Read the brightened image
img_pil = Image.open(r'C:\stack\arg\self_intro_spec_cont_brightened.png')
img = np.array(img_pil)
img_rgb = img[:, :, :3]
gray = np.mean(img_rgb, axis=2)

height, width = gray.shape

# Extract formant shelf region from LEFT channel (~400-1000 Hz)
# This is rows 80-180 based on the frequency labels
shelf_region = gray[80:180, :]

print(f"Shelf region shape: {shelf_region.shape}")

# Find vertical dark gaps (columns with low brightness)
# These gaps separate the "characters"
col_means = np.mean(shelf_region, axis=0)

# Smooth the column means to reduce noise
from scipy.ndimage import uniform_filter1d
col_smooth = uniform_filter1d(col_means, size=5)

# Find the threshold for dark gaps
median_val = np.median(col_smooth)
std_val = np.std(col_smooth)
gap_threshold = median_val - 0.5 * std_val

print(f"Column brightness stats:")
print(f"  Median: {median_val:.1f}")
print(f"  Std: {std_val:.1f}")
print(f"  Gap threshold: {gap_threshold:.1f}")

# Find dark gap regions
is_dark = col_smooth < gap_threshold

# Find contiguous dark regions
dark_regions = []
in_dark = False
dark_start = 0
for i in range(len(is_dark)):
    if is_dark[i] and not in_dark:
        in_dark = True
        dark_start = i
    elif not is_dark[i] and in_dark:
        in_dark = False
        if i - dark_start > 3:  # Minimum gap width
            dark_regions.append((dark_start, i-1))
if in_dark and len(is_dark) - dark_start > 3:
    dark_regions.append((dark_start, len(is_dark)-1))

print(f"\nDark gap regions found: {len(dark_regions)}")
print("Gap positions (start, end, width):")
for start, end in dark_regions:
    print(f"  {start:4d}-{end:4d} (width={end-start+1:3d})")

# Now the "characters" are the bright regions between dark gaps
char_regions = []
prev_end = 0
for start, end in dark_regions:
    if start - prev_end > 5:  # Minimum character width
        char_regions.append((prev_end, start-1))
    prev_end = end + 1

# Add the last character if it exists
if len(shelf_region[0]) - prev_end > 5:
    char_regions.append((prev_end, len(shelf_region[0])-1))

print(f"\nCharacter regions found: {len(char_regions)}")
print("Character positions (start, end, width):")
for i, (start, end) in enumerate(char_regions):
    print(f"  Char {i:2d}: {start:4d}-{end:4d} (width={end-start+1:3d})")

# Now let's analyze each character region
# For each character, we'll look at the vertical pattern (which rows are bright)

print(f"\n=== Character Analysis ===")
for i, (start, end) in enumerate(char_regions[:20]):  # First 20 characters
    char_slice = shelf_region[:, start:end+1]
    
    # Find which rows are bright in this character
    row_brightness = np.mean(char_slice, axis=1)
    threshold = np.mean(row_brightness) + 0.3 * np.std(row_brightness)
    bright_rows = np.where(row_brightness > threshold)[0]
    
    # Find contiguous bright row groups
    if len(bright_rows) > 0:
        groups = []
        group_start = bright_rows[0]
        prev = bright_rows[0]
        for row in bright_rows[1:]:
            if row == prev + 1:
                prev = row
            else:
                groups.append((group_start, prev))
                group_start = row
                prev = row
        groups.append((group_start, prev))
        
        # Convert to a compact representation
        # Each group of bright rows represents a horizontal bar
        bars = [(g[0], g[1]) for g in groups]
        
        print(f"\nChar {i:2d} (cols {start:4d}-{end:4d}):")
        print(f"  Bright row groups: {bars[:10]}")
        
        # Create a binary pattern
        pattern = np.zeros(len(row_brightness), dtype=int)
        for g_start, g_end in groups:
            pattern[g_start:g_end+1] = 1
        pattern_str = ''.join(map(str, pattern))
        print(f"  Binary pattern: {pattern_str}")
    else:
        print(f"\nChar {i:2d} (cols {start:4d}-{end:4d}): No bright rows found")

# Let's also visualize the character regions
plt.figure(figsize=(24, 8))
plt.imshow(shelf_region, aspect='auto', cmap='magma', vmin=0, vmax=255)

# Mark character regions
for i, (start, end) in enumerate(char_regions):
    plt.axvline(x=start, color='cyan', linewidth=0.5, alpha=0.7)
    plt.axvline(x=end, color='cyan', linewidth=0.5, alpha=0.7)
    if i < 30:
        plt.text((start+end)/2, -5, str(i), ha='center', va='bottom', fontsize=8, color='cyan')

plt.title('Formant Shelf Region with Character Boundaries')
plt.xlabel('Time (pixels)')
plt.ylabel('Frequency (pixels)')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\shelf_characters.png', dpi=200)
plt.close()
