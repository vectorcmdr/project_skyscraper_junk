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

# The user says the strokes are in the 150-1000 Hz range
# In the spectrogram, low frequency is at the bottom (high row number)
# The 1000 Hz label appears to be near the bottom

# Let's look at the bottom portion of each channel
# LEFT channel is top half, RIGHT channel is bottom half
# The separator is around row 311

left_channel = gray[:311, :]
right_channel = gray[311:, :]

print(f"LEFT channel: {left_channel.shape}")
print(f"RIGHT channel: {right_channel.shape}")

# Let's look at the very bottom of each channel (lowest frequencies)
# Bottom 20% of each channel would be rows 250-311 for LEFT, rows 250-315 for RIGHT

left_bottom = left_channel[250:, :]  # Bottom ~20% of LEFT
right_bottom = right_channel[250:, :]  # Bottom ~20% of RIGHT

print(f"LEFT bottom: {left_bottom.shape}")
print(f"RIGHT bottom: {right_bottom.shape}")

# Let's visualize these bottom regions
plt.figure(figsize=(24, 4))
plt.imshow(left_bottom, aspect='auto', cmap='magma', vmin=0, vmax=255)
plt.title('LEFT Channel - Bottom 20% (Low Frequencies ~150-1000 Hz)')
plt.xlabel('Time (pixels)')
plt.ylabel('Frequency (pixels)')
plt.colorbar(label='Brightness')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\left_bottom_freq.png', dpi=150)
plt.close()

plt.figure(figsize=(24, 4))
plt.imshow(right_bottom, aspect='auto', cmap='magma', vmin=0, vmax=255)
plt.title('RIGHT Channel - Bottom 20% (Low Frequencies ~150-1000 Hz)')
plt.xlabel('Time (pixels)')
plt.ylabel('Frequency (pixels)')
plt.colorbar(label='Brightness')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\right_bottom_freq.png', dpi=150)
plt.close()

# Now let's try to enhance and threshold these regions
# to see the strokes more clearly

# For LEFT channel bottom
left_bottom_gray = left_bottom
left_threshold = np.mean(left_bottom_gray) + 1.5 * np.std(left_bottom_gray)
left_binary = left_bottom_gray > left_threshold

plt.figure(figsize=(24, 4))
plt.imshow(left_binary, aspect='auto', cmap='binary')
plt.title('LEFT Channel Bottom - Binary (Threshold = Mean + 1.5*Std)')
plt.xlabel('Time (pixels)')
plt.ylabel('Frequency (pixels)')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\left_bottom_binary.png', dpi=150)
plt.close()

# For RIGHT channel bottom
right_bottom_gray = right_bottom
right_threshold = np.mean(right_bottom_gray) + 1.5 * np.std(right_bottom_gray)
right_binary = right_bottom_gray > right_threshold

plt.figure(figsize=(24, 4))
plt.imshow(right_binary, aspect='auto', cmap='binary')
plt.title('RIGHT Channel Bottom - Binary (Threshold = Mean + 1.5*Std)')
plt.xlabel('Time (pixels)')
plt.ylabel('Frequency (pixels)')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\right_bottom_binary.png', dpi=150)
plt.close()

# Let's also try to look for vertical bars (potential barcode)
# in the bottom region

print("\nAnalyzing vertical patterns in bottom region:")
for name, region in [("LEFT", left_bottom), ("RIGHT", right_bottom)]:
    # Convert to binary
    threshold = np.mean(region) + 1.5 * np.std(region)
    binary = region > threshold
    
    # Find columns with many bright pixels (potential bar strokes)
    col_sums = np.sum(binary, axis=0)
    mean_col = np.mean(col_sums)
    std_col = np.std(col_sums)
    
    # Find columns that are significantly brighter
    bright_cols = col_sums > mean_col + 2 * std_col
    
    print(f"\n{name} channel:")
    print(f"  Mean column brightness: {mean_col:.1f}")
    print(f"  Std: {std_col:.1f}")
    print(f"  Bright columns: {np.sum(bright_cols)}")
    
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
            bright_groups.append((group_start, i - 1))
    if in_group:
        bright_groups.append((group_start, len(bright_cols) - 1))
    
    print(f"  Bright groups: {bright_groups[:20]}")
