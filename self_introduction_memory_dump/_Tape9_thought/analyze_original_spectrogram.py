import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Read the original spectrogram (not the brightened one)
img_pil = Image.open(r'C:\stack\arg\self_intro_spec.png')
img = np.array(img_pil)
print(f"Original image shape: {img.shape}")

# Convert to grayscale
if len(img.shape) == 3:
    gray = np.mean(img[:, :, :3], axis=2)
else:
    gray = img

print(f"Gray shape: {gray.shape}")

# The image is a stacked spectrogram with frequency labels on the left
# We need to crop out the labels and separate LEFT and RIGHT channels

# Looking at the image:
# - Left edge has frequency labels (black text on white?)
# - The spectrogram data starts after the labels
# - There's a horizontal separator between LEFT and RIGHT channels

# Let's find the vertical separator
# Look for a row that's mostly black (the separator line)
mid_y = gray.shape[0] // 2
search_range = 30
region = gray[mid_y-search_range:mid_y+search_range, :]
row_means = np.mean(region, axis=1)
separator_rel = np.argmin(row_means)
separator_abs = mid_y - search_range + separator_rel

print(f"Separator at row: {separator_abs}")

# Find the left edge (where spectrogram data starts)
# Look for columns with high variance (data) vs low variance (labels)
col_vars = np.var(gray, axis=0)
threshold_var = np.mean(col_vars) * 2
data_start = np.argmax(col_vars > threshold_var)

print(f"Data starts at column: {data_start}")

# Crop the image
left_channel = gray[:separator_abs, data_start:]
right_channel = gray[separator_abs:, data_start:]

print(f"LEFT channel shape: {left_channel.shape}")
print(f"RIGHT channel shape: {right_channel.shape}")

# Now let's look at the 1000-4000 Hz region
# The frequency axis is logarithmic from 0 to 22050 Hz
# Let's estimate where 1000-4000 Hz is in the image

# From the labels: 1000, 1500, 2000, 2500, 3000, 4000, 5000, 6000, 7000, 8000, 10000, 12000, 15000, 19000
# The frequency labels appear to be at specific pixel positions

# Let's try to identify the region by looking for horizontal bright lines
# In spectrograms, constant frequencies appear as horizontal lines

# Look at the LEFT channel
for name, channel in [("LEFT", left_channel), ("RIGHT", right_channel)]:
    # Find rows with high brightness
    row_means = np.mean(channel, axis=1)
    
    # Find peaks in brightness
    from scipy import signal
    peaks, _ = signal.find_peaks(row_means, height=np.mean(row_means) + 2*np.std(row_means), distance=10)
    
    print(f"\n{name} channel - brightest rows (peaks):")
    for peak in peaks[:20]:
        brightness = row_means[peak]
        print(f"  Row {peak}: brightness = {brightness:.1f}")
    
    # Look for rows that have consistent brightness across time (harmonic lines)
    # These would be the note frequencies
    row_consistency = np.std(channel, axis=1) / (np.mean(channel, axis=1) + 0.001)
    
    # Low std/mean means consistent brightness = harmonic
    harmonic_rows = np.argsort(row_consistency)[:20]
    
    print(f"\n{name} channel - most consistent rows (potential harmonics):")
    for row in sorted(harmonic_rows):
        mean_val = row_means[row]
        std_val = np.std(channel[row, :])
        print(f"  Row {row}: mean={mean_val:.1f}, std={std_val:.1f}, consistency={row_consistency[row]:.3f}")
