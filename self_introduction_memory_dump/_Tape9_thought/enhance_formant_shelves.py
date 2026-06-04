import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import uniform_filter1d

# Read the brightened spectrogram image
img = Image.open(r'C:\stack\arg\self_intro_spec_cont_brightened.png')
img_array = np.array(img)

print(f"Image shape: {img_array.shape}")

# Convert to grayscale
if len(img_array.shape) == 3 and img_array.shape[2] in [3, 4]:
    gray = np.mean(img_array[:,:,:3], axis=2)
else:
    gray = img_array

# The image is 2381x626
# LEFT channel: top half (rows 0-310)
# RIGHT channel: bottom half (rows 311-625)

# The red box in the structures image highlights a region in the LEFT channel
# This appears to be the ~400-1000 Hz range
# Looking at the frequency labels: 400 is near row ~200, 700 near row ~170, 1000 near row ~150

# Let's extract the formant shelf region more precisely
# From visual inspection, the shelves are around rows 150-200 in LEFT channel
left_shelf = gray[140:210, :]
right_shelf = gray[450:520, :]  # Same region in RIGHT channel

print(f"LEFT shelf region: {left_shelf.shape}")
print(f"RIGHT shelf region: {right_shelf.shape}")

# Enhance contrast
from PIL import ImageEnhance

# Convert to PIL for enhancement
left_pil = Image.fromarray(left_shelf.astype(np.uint8))
right_pil = Image.fromarray(right_shelf.astype(np.uint8))

# Enhance contrast
enhancer = ImageEnhance.Contrast(left_pil)
left_enhanced = enhancer.enhance(3.0)
enhancer = ImageEnhance.Contrast(right_pil)
right_enhanced = enhancer.enhance(3.0)

# Save enhanced regions
plt.figure(figsize=(24, 4))
plt.imshow(left_enhanced, aspect='auto', cmap='gray', vmin=0, vmax=255)
plt.title('LEFT Channel - Formant Shelf Region (Enhanced 3x)')
plt.xlabel('Time (pixels)')
plt.ylabel('Frequency')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\left_shelf_enhanced.png', dpi=200)
plt.close()

plt.figure(figsize=(24, 4))
plt.imshow(right_enhanced, aspect='auto', cmap='gray', vmin=0, vmax=255)
plt.title('RIGHT Channel - Formant Shelf Region (Enhanced 3x)')
plt.xlabel('Time (pixels)')
plt.ylabel('Frequency')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\right_shelf_enhanced.png', dpi=200)
plt.close()

# Try thresholding to make the shelves more visible
left_thresh = np.array(left_enhanced)
right_thresh = np.array(right_enhanced)

# Adaptive thresholding
left_binary = left_thresh > np.mean(left_thresh) + 0.5 * np.std(left_thresh)
right_binary = right_thresh > np.mean(right_thresh) + 0.5 * np.std(right_thresh)

plt.figure(figsize=(24, 4))
plt.imshow(left_binary, aspect='auto', cmap='binary')
plt.title('LEFT Channel - Binary Threshold')
plt.xlabel('Time (pixels)')
plt.ylabel('Frequency')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\left_shelf_binary.png', dpi=200)
plt.close()

plt.figure(figsize=(24, 4))
plt.imshow(right_binary, aspect='auto', cmap='binary')
plt.title('RIGHT Channel - Binary Threshold')
plt.xlabel('Time (pixels)')
plt.ylabel('Frequency')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\right_shelf_binary.png', dpi=200)
plt.close()

# Try extreme contrast enhancement
enhancer = ImageEnhance.Contrast(left_pil)
left_extreme = enhancer.enhance(10.0)
enhancer = ImageEnhance.Contrast(right_pil)
right_extreme = enhancer.enhance(10.0)

plt.figure(figsize=(24, 4))
plt.imshow(left_extreme, aspect='auto', cmap='gray', vmin=0, vmax=255)
plt.title('LEFT Channel - Extreme Contrast (10x)')
plt.xlabel('Time (pixels)')
plt.ylabel('Frequency')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\left_shelf_extreme.png', dpi=200)
plt.close()

plt.figure(figsize=(24, 4))
plt.imshow(right_extreme, aspect='auto', cmap='gray', vmin=0, vmax=255)
plt.title('RIGHT Channel - Extreme Contrast (10x)')
plt.xlabel('Time (pixels)')
plt.ylabel('Frequency')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\right_shelf_extreme.png', dpi=200)
plt.close()

print("\nEnhanced images saved:")
print("  left_shelf_enhanced.png")
print("  right_shelf_enhanced.png")
print("  left_shelf_binary.png")
print("  right_shelf_binary.png")
print("  left_shelf_extreme.png")
print("  right_shelf_extreme.png")
