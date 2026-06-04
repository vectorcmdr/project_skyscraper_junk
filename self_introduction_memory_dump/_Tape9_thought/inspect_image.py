from PIL import Image
import numpy as np, os

img_path = r'C:\stack\arg\self_intro_spec.png'
img = Image.open(img_path)
print('Image size:', img.size, 'mode:', img.mode)
# convert to grayscale
gray = np.array(img.convert('L'))
print('Gray shape:', gray.shape)
print('Min/max pixel:', gray.min(), gray.max())
# show some stats about bright pixels
bright = gray > 200
print('Bright pixels (>200):', bright.sum())
# find rows with many bright pixels
row_counts = bright.sum(axis=1)
print('Top 10 bright rows:', np.argsort(row_counts)[-10:])
print('Counts at those rows:', row_counts[np.argsort(row_counts)[-10:]])
# show top-left crop
print('Top-left 20x20:')
print(gray[:20, :20])
