from PIL import Image
import numpy as np

img = Image.open(r'C:\stack\arg\self_intro_spec_cont_brightened.png')
arr = np.array(img)
print('Image shape:', arr.shape)

h, w = arr.shape[:2]
mid = h // 2

# crop bottom of top half (approx 50 rows)
top_crop = arr[mid-55:mid, :]
# crop bottom of bottom half
bot_crop = arr[h-55:h, :]

# stretch vertically
factor = 4
top_stretch = np.repeat(top_crop, factor, axis=0)
bot_stretch = np.repeat(bot_crop, factor, axis=0)

from PIL import Image
Image.fromarray(top_stretch).save(r'C:\stack\arg\tapes_man_2\top_bottom_stretched.png')
Image.fromarray(bot_stretch).save(r'C:\stack\arg\tapes_man_2\bot_bottom_stretched.png')
print('Saved stretched crops.')
