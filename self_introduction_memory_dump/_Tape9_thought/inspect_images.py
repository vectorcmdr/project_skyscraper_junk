from PIL import Image
import numpy as np

for name in ['self_intro_spec_cont_brightened.png', 'self_intro_spec.png']:
    img = Image.open(rf'C:\stack\arg\{name}')
    print(name, 'size', img.size, 'mode', img.mode)
    gray = np.array(img.convert('L'))
    print('  min/max', gray.min(), gray.max())
    bright = gray > 200
    row_counts = bright.sum(axis=1)
    top_rows = np.argsort(row_counts)[-20:]
    print('  top bright rows:', sorted(top_rows.tolist()))
    print('  counts:', row_counts[top_rows])
