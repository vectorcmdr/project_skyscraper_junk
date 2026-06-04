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

# The image is a stacked spectrogram:
# - LEFT channel: top half (rows 0-310)
# - RIGHT channel: bottom half (rows 311-625)
# Frequency labels on the left side show:
# 100, 400, 700, 1000, 1500, 2000, 2500, 3000, 4000, 5000, 6000, 7000, 8000, 10000, 12000, 15000, 19000

# From the structures image:
# - Red box is in LEFT channel, approximately rows 100-200 (based on frequency labels ~400-1000 Hz)
# - Green circle is in RIGHT channel, approximately rows 400-500 (also ~400-1000 Hz range)

# Let's identify the pixel positions more precisely
# Looking at the labels: "400" appears around row 150 in LEFT, "1000" around row 100
# So the red box region is roughly rows 80-180 in LEFT channel

# Extract the red box region (LEFT channel, ~400-1000 Hz)
left_redbox = gray[80:180, :]

# Extract the green circle region (RIGHT channel, ~400-1000 Hz)
# The green circle is near the middle horizontally (around columns 700-900?)
# and in the RIGHT channel (rows 400-500)
right_greencircle = gray[420:480, 650:850]

print(f"LEFT redbox region: {left_redbox.shape}")
print(f"RIGHT greencircle region: {right_greencircle.shape}")

# Save the regions
plt.figure(figsize=(24, 4))
plt.imshow(left_redbox, aspect='auto', cmap='magma', vmin=0, vmax=255)
plt.title('LEFT Channel - Red Box Region (~400-1000 Hz) - Formant Shelves')
plt.xlabel('Time (pixels)')
plt.ylabel('Frequency (pixels)')
plt.colorbar(label='Brightness')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\left_formant_shelves.png', dpi=200)
plt.close()

plt.figure(figsize=(10, 6))
plt.imshow(right_greencircle, aspect='auto', cmap='magma', vmin=0, vmax=255)
plt.title('RIGHT Channel - Green Circle Region (~400-1000 Hz) - 3 Strokes')
plt.xlabel('Time (pixels)')
plt.ylabel('Frequency (pixels)')
plt.colorbar(label='Brightness')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\right_3strokes.png', dpi=200)
plt.close()

# Now let's analyze the formant shelves structure
# The shelves appear as horizontal bright bars with varying lengths

# Let's find the horizontal bars by looking at rows with high brightness
row_means = np.mean(left_redbox, axis=1)
print(f"\nLEFT formant shelves - Row brightness profile:")
for i in range(0, len(row_means), 5):
    bar = '#' * int(row_means[i] / 5)
    print(f"  Row {i:3d}: {row_means[i]:6.1f} |{bar}")

# Find peaks (bright shelves)
from scipy import signal
peaks, properties = signal.find_peaks(row_means, height=150, distance=3, prominence=20)
print(f"\nBright shelf rows: {peaks}")
print(f"Shelf brightness: {[f'{row_means[p]:.1f}' for p in peaks]}")

# Now let's look at the 3-stroke structure in detail
print(f"\nRIGHT 3-stroke region analysis:")
print(f"Shape: {right_greencircle.shape}")

# Find the columns with bright strokes
col_means = np.mean(right_greencircle, axis=0)
print(f"\nColumn brightness:")
for i in range(len(col_means)):
    bar = '#' * int(col_means[i] / 5)
    print(f"  Col {i:3d}: {col_means[i]:6.1f} |{bar}")

# Find the stroke columns
stroke_peaks, _ = signal.find_peaks(col_means, height=150, distance=3, prominence=20)
print(f"\nStroke column positions: {stroke_peaks}")
print(f"Stroke brightness: {[f'{col_means[p]:.1f}' for p in stroke_peaks]}")

# Calculate spacing between strokes
if len(stroke_peaks) >= 2:
    spacings = np.diff(stroke_peaks)
    print(f"Spacing between strokes: {spacings}")
