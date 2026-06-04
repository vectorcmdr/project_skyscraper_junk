import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Read the brightened image with PIL
img_pil = Image.open(r'C:\stack\arg\self_intro_spec_cont_brightened.png')
print(f"PIL image mode: {img_pil.mode}")
print(f"PIL image size: {img_pil.size}")
print(f"PIL image dtype: {img_pil.getbands()}")

# Convert to numpy array
img = np.array(img_pil)
print(f"Numpy shape: {img.shape}")
print(f"Numpy dtype: {img.dtype}")
print(f"Min: {img.min()}, Max: {img.max()}")

# If it's RGBA, convert to RGB
if img.shape[2] == 4:
    img = img[:, :, :3]
    print(f"Converted to RGB: {img.shape}")

# Let's look at the actual pixel values
# Check a few specific positions
height, width = img.shape[:2]
print(f"\nImage dimensions: {width}x{height}")

# Look at the middle of the image
mid_x, mid_y = width // 2, height // 2
print(f"Center pixel: {img[mid_y, mid_x]}")

# Look at some random pixels
for y in [50, 100, 150, 200, 250, 300]:
    for x in [100, 500, 1000, 1500, 2000]:
        if y < height and x < width:
            pixel = img[y, x]
            print(f"Pixel at ({x},{y}): {pixel}")

# Let's check if the image is truly the spectrogram or if it has been altered
# Try to find the frequency labels by looking for white text on the left side
left_strip = img[:, :50, :]  # First 50 pixels
print(f"\nLeft strip average brightness: {np.mean(left_strip):.3f}")

# The brightened image might have different characteristics
# Let me try to threshold it differently
gray = np.mean(img, axis=2)
print(f"\nGray statistics:")
print(f"  Mean: {np.mean(gray):.3f}")
print(f"  Std: {np.std(gray):.3f}")
print(f"  Min: {np.min(gray):.3f}")
print(f"  Max: {np.max(gray):.3f}")

# Histogram of gray values
hist, bins = np.histogram(gray.flatten(), bins=50)
print("\nHistogram of gray values:")
for i in range(len(hist)):
    if hist[i] > 0:
        print(f"  {bins[i]:.3f}-{bins[i+1]:.3f}: {hist[i]} pixels ({100*hist[i]/gray.size:.1f}%)")
