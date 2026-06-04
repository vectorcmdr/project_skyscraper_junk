import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# The character binary patterns from the previous analysis
# Let me analyze them more carefully

# From the output, each character has a binary pattern of 100 bits (rows 0-99)
# The patterns show where bright rows are in the formant shelf region

# Let me create a simpler representation - just the "shape" of each character
# by noting which row groups are bright

characters = {
    0: [(4,10), (12,18), (28,35), (44,51), (61,73), (83,99)],
    1: [(66,68), (70,99)],
    2: [(58,60), (63,63), (65,67), (69,99)],
    3: [(58,58), (66,99)],
    4: [(49,53), (56,56), (58,58), (61,62), (64,99)],
    5: [(48,48), (59,60), (62,99)],
    6: [(53,53), (55,99)],
    7: [(58,59), (68,99)],
    8: [(52,52), (54,56), (58,63), (66,67), (69,99)],
    9: [(54,56), (58,67), (69,99)],
    10: [(55,55), (58,63), (65,66), (68,99)],
    11: [(10,10), (12,12), (70,99)],
    12: [(71,99)],
    13: [(55,55), (71,99)],
    14: [(58,58), (67,67), (71,99)],
    15: [(70,70), (72,99)],
    16: [(55,55), (68,99)],
    17: [(59,59), (63,99)],
    18: [(50,55), (61,64), (69,99)],
    19: [(66,66), (69,69), (71,99)],
}

print("=== Character Pattern Analysis ===\n")

# Analyze each character's "shape"
for char_idx, groups in sorted(characters.items()):
    # Count the number of distinct bright regions
    num_regions = len(groups)
    
    # Calculate the total "bright" rows
    total_bright = sum(end - start + 1 for start, end in groups)
    
    # Find the lowest bright row (closest to 1000 Hz)
    lowest_row = max(end for start, end in groups)
    
    # Find the highest bright row (closest to 400 Hz)
    highest_row = min(start for start, end in groups)
    
    # Calculate the "span" of the character
    span = lowest_row - highest_row
    
    print(f"Char {char_idx:2d}: {num_regions} regions, {total_bright} bright rows, "
          f"span={span}, rows {highest_row}-{lowest_row}")
    print(f"        Groups: {groups}")

# Now let's try to match these patterns to potential characters
# The formant shelf pattern might encode:
# 1. Vowel sounds (based on formant frequencies)
# 2. Letters (based on pattern shape)
# 3. Numbers (based on region count or other features)

print("\n=== Potential Decoding Approaches ===")

# Approach 1: Count of regions
print("\n1. By region count:")
region_counts = {}
for char_idx, groups in characters.items():
    count = len(groups)
    if count not in region_counts:
        region_counts[count] = []
    region_counts[count].append(char_idx)

for count, chars in sorted(region_counts.items()):
    print(f"   {count} regions: Characters {chars}")

# Approach 2: By lowest bright row (frequency)
print("\n2. By lowest bright row (frequency indicator):")
lowest_rows = {}
for char_idx, groups in characters.items():
    lowest = max(end for start, end in groups)
    if lowest not in lowest_rows:
        lowest_rows[lowest] = []
    lowest_rows[lowest].append(char_idx)

for row, chars in sorted(lowest_rows.items()):
    print(f"   Row {row}: Characters {chars}")

# Approach 3: By total bright rows
print("\n3. By total bright rows:")
bright_counts = {}
for char_idx, groups in characters.items():
    total = sum(end - start + 1 for start, end in groups)
    if total not in bright_counts:
        bright_counts[total] = []
    bright_counts[total].append(char_idx)

for count, chars in sorted(bright_counts.items()):
    print(f"   {count} rows: Characters {chars}")

# Let's also visualize the characters as a grid
fig, axes = plt.subplots(5, 4, figsize=(12, 15))
axes = axes.flatten()

for i, (char_idx, groups) in enumerate(sorted(characters.items())):
    if i >= 20:
        break
    
    # Create a 100-row binary image
    pattern = np.zeros((100, 20), dtype=int)
    for start, end in groups:
        pattern[start:end+1, :] = 1
    
    axes[i].imshow(pattern, aspect='auto', cmap='binary', vmin=0, vmax=1)
    axes[i].set_title(f'Char {char_idx}', fontsize=10)
    axes[i].set_xlabel('Time')
    axes[i].set_ylabel('Freq')

plt.suptitle('Formant Shelf Character Patterns', fontsize=14)
plt.tight_layout()
plt.savefig(r'C:\stack\arg\tapes_man_2\character_grid.png', dpi=150)
plt.close()
