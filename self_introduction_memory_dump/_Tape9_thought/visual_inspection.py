import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Read the brightened image
img_pil = Image.open(r'C:\stack\arg\self_intro_spec_cont_brightened.png')
img = np.array(img_pil)
print(f"Image shape: {img.shape}")

# This is RGBA, convert to RGB
if img.shape[2] == 4:
    img_rgb = img[:, :, :3]
else:
    img_rgb = img

# Convert to grayscale for analysis
gray = np.mean(img_rgb, axis=2)

# The image is 2381x626 pixels
# Let's try to understand the layout better
# The frequency labels are on the left side (columns 0-30 roughly)
# The spectrogram data starts around column 30

# Let's look at the left side to find where the labels are
left_strip = gray[:, :30]
print(f"Left strip mean: {np.mean(left_strip):.1f}")

# Now let's try to find the 1000-4000 Hz region
# From the original image, the frequency labels go from 1000 at bottom to 19000 at top
# But in the image, low frequency is at the bottom (row 625) and high frequency at top (row 0)

# Let's try to map the frequency labels to pixel positions
# Looking at the original image, I saw labels like 1000, 1500, 2000, 2500, 3000, 4000, 5000, 6000, 7000, 8000, 10000, 12000, 15000, 19000

# For now, let's assume the bottom 1/3 is the 1000-4000 Hz region
# Let's crop a region and see what we can see

height, width = gray.shape
print(f"Height: {height}, Width: {width}")

# Let's try to view different parts of the image
# First, let's see what the whole image looks like when enhanced
plt.figure(figsize=(24, 8))
plt.imshow(gray, aspect='auto', cmap='magma', vmin=0, vmax=255)
plt.colorbar(label='Brightness')
plt.xlabel('Time (pixels)')
plt.ylabel('Frequency (pixels)')
plt.title('Full Spectrogram (Brightened)')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\full_spectrogram_view.png', dpi=150)
plt.close()

# Now let's try to extract the 1000-4000 Hz region
# Assuming the bottom 30% of the image is 1000-4000 Hz
# This is a rough estimate - we'll refine later

bottom_region = gray[int(height*0.7):, :]  # Bottom 30%
top_region = gray[:int(height*0.3), :]      # Top 30%

plt.figure(figsize=(24, 4))
plt.imshow(bottom_region, aspect='auto', cmap='magma', vmin=0, vmax=255)
plt.title('Bottom Region (Assumed 1000-4000 Hz)')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\bottom_region.png', dpi=150)
plt.close()

plt.figure(figsize=(24, 4))
plt.imshow(top_region, aspect='auto', cmap='magma', vmin=0, vmax=255)
plt.title('Top Region (Assumed 8000-19000 Hz)')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\top_region.png', dpi=150)
plt.close()

# Let's also try to threshold the image to see the patterns more clearly
# The brightened image has strong magenta (255,0,255) and blue (0,0,255) colors
# Let's look for magenta pixels which seem to form the text patterns

# Magenta is R=255, G=0, B=255
# Blue is R=0, G=0, B=255
# White is R=255, G=255, B=255

# Let's create masks for different colors
r, g, b = img_rgb[:,:,0], img_rgb[:,:,1], img_rgb[:,:,2]

# Magenta mask: R high, G low, B high
magenta_mask = (r > 200) & (g < 50) & (b > 200)

# Blue mask: R low, G low, B high
blue_mask = (r < 50) & (g < 50) & (b > 200)

# White mask: R high, G high, B high
white_mask = (r > 200) & (g > 200) & (b > 200)

# Black mask: all channels low
black_mask = (r < 30) & (g < 30) & (b < 30)

print(f"\nColor distribution:")
print(f"  Magenta pixels: {np.sum(magenta_mask)} ({100*np.sum(magenta_mask)/magenta_mask.size:.1f}%)")
print(f"  Blue pixels: {np.sum(blue_mask)} ({100*np.sum(blue_mask)/blue_mask.size:.1f}%)")
print(f"  White pixels: {np.sum(white_mask)} ({100*np.sum(white_mask)/white_mask.size:.1f}%)")
print(f"  Black pixels: {np.sum(black_mask)} ({100*np.sum(black_mask)/black_mask.size:.1f}%)")

# Let's visualize the magenta and white patterns which seem to form the text
plt.figure(figsize=(24, 8))
plt.imshow(magenta_mask | white_mask, aspect='auto', cmap='binary')
plt.title('Magenta + White Patterns (Text Areas)')
plt.xlabel('Time (pixels)')
plt.ylabel('Frequency (pixels)')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\text_patterns.png', dpi=150)
plt.close()

# Let's also try to enhance the contrast of the original image
# and save different frequency regions

# For now, let's save the bottom region with better contrast
bottom_enhanced = np.clip(bottom_region * 1.5, 0, 255).astype(np.uint8)
plt.figure(figsize=(24, 4))
plt.imshow(bottom_enhanced, aspect='auto', cmap='magma', vmin=0, vmax=255)
plt.title('Bottom Region Enhanced')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\bottom_region_enhanced.png', dpi=150)
plt.close()
