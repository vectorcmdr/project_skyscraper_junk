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
print(f"Image: {width}x{height}")

# Both channels have the same structure
# LEFT channel: rows 0-310, RIGHT channel: rows 311-625
# The formant shelves are in the ~400-1000 Hz range
# From the labels, this is roughly rows 80-180 in LEFT, rows 390-490 in RIGHT

# Let's extract the formant shelf region from BOTH channels and combine them
left_shelf = gray[80:180, :]   # LEFT channel, ~400-1000 Hz
right_shelf = gray[390:490, :]  # RIGHT channel, ~400-1000 Hz

# Average the two channels to get a cleaner signal
combined_shelf = (left_shelf + right_shelf) / 2

print(f"Combined shelf region: {combined_shelf.shape}")

# Save the combined view
plt.figure(figsize=(24, 6))
plt.imshow(combined_shelf, aspect='auto', cmap='magma', vmin=0, vmax=255)
plt.title('Combined Formant Shelf Region (~400-1000 Hz) - Both Channels')
plt.xlabel('Time (pixels)')
plt.ylabel('Frequency (pixels)')
plt.colorbar(label='Brightness')
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\combined_shelf.png', dpi=200)
plt.close()

# Now let's analyze the vertical structure (across frequency) at each time point
# The shelves appear as horizontal bars at specific frequencies
# Let's find the "on" and "off" rows at each time column

# First, let's look at the overall row brightness profile
row_profile = np.mean(combined_shelf, axis=1)
print(f"\nRow brightness profile (averaged across time):")
for i in range(len(row_profile)):
    bar = '#' * int(row_profile[i] / 3)
    print(f"  Row {i:3d}: {row_profile[i]:6.1f} |{bar}")

# Find the shelf rows (peaks in the row profile)
peaks, properties = signal.find_peaks(row_profile, height=100, distance=5, prominence=30)
print(f"\nShelf row positions: {peaks}")
print(f"Shelf brightness: {[f'{row_profile[p]:.1f}' for p in peaks]}")

# Now let's analyze the time-domain pattern at each shelf row
# This will show us the on/off pattern over time

print(f"\n=== Time-domain analysis at shelf rows ===")
for shelf_row in peaks:
    row_data = combined_shelf[shelf_row, :]
    
    # Threshold to binary
    threshold = np.mean(row_data) + 0.5 * np.std(row_data)
    binary = (row_data > threshold).astype(int)
    
    # Find on/off transitions
    transitions = np.diff(binary)
    on_starts = np.where(transitions == 1)[0] + 1
    off_starts = np.where(transitions == -1)[0] + 1
    
    print(f"\nRow {shelf_row} (brightness={row_profile[shelf_row]:.1f}):")
    print(f"  Threshold: {threshold:.1f}")
    print(f"  On transitions: {len(on_starts)}")
    print(f"  Off transitions: {len(off_starts)}")
    
    # Calculate on/off durations
    if len(on_starts) > 0 and len(off_starts) > 0:
        on_durations = np.diff(on_starts) if len(on_starts) > 1 else [0]
        print(f"  On durations: {on_durations[:20]}...")
    
    # Convert to a compact representation
    # Sample at every 10 pixels to reduce data
    sampled = binary[::10]
    bit_string = ''.join(map(str, sampled))
    print(f"  Sampled bit string (every 10px): {bit_string[:100]}...")
    
    # Try to decode as ASCII
    print(f"  Trying 7-bit ASCII decode:")
    chars = []
    for start in range(0, min(len(bit_string), 70) - 6, 7):
        byte = bit_string[start:start+7]
        value = int(byte, 2)
        char = chr(value) if 32 <= value <= 126 else '.'
        chars.append(char)
    print(f"    {''.join(chars)}")
