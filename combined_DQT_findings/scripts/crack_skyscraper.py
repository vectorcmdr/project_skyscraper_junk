import os, sys, struct, json, subprocess, shutil
import numpy as np
from collections import Counter
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
BASE = os.path.dirname(os.path.dirname(__file__))
OUT = os.path.dirname(__file__)

import jpeglib

# ================================================================
# HELPERS
# ================================================================
ZZ = [0,1,5,6,14,15,27,28,
      2,4,7,13,16,26,29,42,
      3,8,12,17,25,30,41,43,
      9,11,18,24,31,40,44,53,
      10,19,23,32,39,45,52,54,
      20,22,33,38,46,51,55,60,
      21,34,37,47,50,56,59,61,
      35,36,48,49,57,58,62,63]

def zigzag_pos(z):
    return ZZ[z] // 8, ZZ[z] % 8

def txt_of(b):
    return ''.join(chr(x) if 32<=x<127 else '.' for x in b)

def bits_to_bytes(blist, msb=True):
    out = bytearray()
    for i in range(0, len(blist)-7, 8):
        byte = 0
        for j in range(8):
            if msb: byte = (byte << 1) | blist[i+j]
            else: byte = byte | (blist[i+j] << j)
        out.append(byte)
    return bytes(out)

def bits_to_int(bits):
    v = 0
    for b in bits: v = (v << 1) | b
    return v

def log(msg):
    print(msg)
    with open(os.path.join(OUT, 'extraction_log.txt'), 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

log("=" * 72)
log("SKYSCRAPER STEGANOGRAPHIC DECODING - COMPREHENSIVE EXTRACTION")
log("=" * 72)

# ================================================================
# LOAD ALL DATA
# ================================================================
log("\n[0] Loading data...")
sky_data = open(os.path.join(BASE, 'project-skyscraper.jpg'), 'rb').read()
tr4_data = open(os.path.join(BASE, 'TR4CE.jpg'), 'rb').read()
img4_data = open(os.path.join(BASE, 'IMG_00004.jpg'), 'rb').read()

def find_dqt(data):
    dqts = []
    i = 0
    while i < len(data) - 3:
        if data[i] == 0xFF and data[i+1] == 0xDB:
            length = struct.unpack('>H', data[i+2:i+4])[0]
            content = data[i+4:i+2+length]
            pos = 0
            while pos < len(content):
                info = content[pos]
                tid = info & 0xF
                prec = (info >> 4) & 0xF
                size = 128 if prec else 64
                vals = list(content[pos+1:pos+1+size])[:64]
                dqts.append({'id': tid, 'vals': vals})
                pos += 1 + size
            i += 2 + length
        else:
            i += 1
    return dqts

sky_dqts = find_dqt(sky_data)
tr4_dqts = find_dqt(tr4_data)
img4_dqts = find_dqt(img4_data)

sky_dct = jpeglib.read_dct(os.path.join(BASE, 'project-skyscraper.jpg'))

# Build DQT dicts: {id: 64-element zigzag-ordered array}
def get_tbl_by_id(dqts, tid):
    for t in dqts:
        if t['id'] == tid:
            return dict((t['id'], np.array(t['vals'], dtype=int)) for t in dqts if t['id'] == tid)
    return {}

sky_tbls = {}
for t in sky_dqts: sky_tbls.setdefault(t['id'], []).append(np.array(t['vals'], dtype=int))
tr4_tbls = {}
for t in tr4_dqts: tr4_tbls.setdefault(t['id'], []).append(np.array(t['vals'], dtype=int))
img4_tbls = {}
for t in img4_dqts: img4_tbls.setdefault(t['id'], []).append(np.array(t['vals'], dtype=int))

sky_d0 = sky_tbls[0][0] if 0 in sky_tbls else np.ones(64, dtype=int)
sky_d1 = sky_tbls[1][0] if 1 in sky_tbls else np.ones(64, dtype=int)
tr4_s0_d0 = tr4_tbls[0][0] if 0 in tr4_tbls else np.ones(64, dtype=int)
tr4_s0_d1 = tr4_tbls[1][0] if 1 in tr4_tbls and len(tr4_tbls[1]) > 0 else np.ones(64, dtype=int)
tr4_s1_d0 = tr4_tbls[0][1] if 0 in tr4_tbls and len(tr4_tbls[0]) > 1 else np.ones(64, dtype=int)
tr4_s1_d1 = tr4_tbls[1][1] if 1 in tr4_tbls and len(tr4_tbls[1]) > 1 else np.ones(64, dtype=int)
img4_s0_d0 = img4_tbls[0][0] if 0 in img4_tbls else np.ones(64, dtype=int)
img4_s0_d1 = img4_tbls[1][0] if 1 in img4_tbls and len(img4_tbls[1]) > 0 else np.ones(64, dtype=int)
img4_s1_d0 = img4_tbls[0][1] if 0 in img4_tbls and len(img4_tbls[0]) > 1 else np.ones(64, dtype=int)
img4_s1_d1 = img4_tbls[1][1] if 1 in img4_tbls and len(img4_tbls[1]) > 1 else np.ones(64, dtype=int)

y_coeffs = sky_dct.Y
cb_coeffs = sky_dct.Cb
cr_coeffs = sky_dct.Cr

# ================================================================
# SECTION 1: JSTEG-STYLE DCT LSB EXTRACTION
# ================================================================
log("\n" + "=" * 72)
log("SECTION 1: JSTEG DCT LSB EXTRACTION AT DQT>1 POSITIONS")
log("=" * 72)

# JSteg: extract LSB from DCT coefficients where DQT value != 1
# The DQT tells us which coefficients carry data (DQT > 1 = modified)

for tid, label, tbl in [(0, 'DQT0', sky_d0), (1, 'DQT1', sky_d1)]:
    carrier_pos = [z for z in range(64) if tbl[z] > 1]
    log(f"\n  {label}: {len(carrier_pos)} carrier positions: {carrier_pos}")
    
    for plane_name, coeffs in [('Y', y_coeffs), ('Cb', cb_coeffs), ('Cr', cr_coeffs)]:
        if coeffs is None: continue
        rows, cols, _, _ = coeffs.shape
        
        # Extract LSBs in zigzag order for each block, then flatten
        all_lsbs = []
        for zpos in carrier_pos:
            r = ZZ[zpos] // 8
            c = ZZ[zpos] % 8
            block_lsbs = (np.abs(coeffs[:, :, r, c]).astype(int) & 1).flatten()
            all_lsbs.extend(block_lsbs)
        
        blen = len(all_lsbs)
        log(f"    {plane_name}: {blen} bits ({blen//8} bytes)")
        
        # Try as bytes with various offsets and bit orders
        results = []
        for msb in [True, False]:
            for offset in range(8):
                shifted = all_lsbs[offset:]
                bs = bits_to_bytes(shifted, msb)
                printable = sum(1 for b in bs[:64] if 32<=b<127) / min(64, len(bs))
                results.append((printable, msb, offset, bs))
                if printable > 0.3:
                    log(f"      MSB={msb} offset={offset}: printable={printable:.0%}")
                    log(f"        {txt_of(bs[:80])}")
        
        best = max(results, key=lambda x: x[0])
        log(f"      Best: MSB={best[1]} offset={best[2]} printable={best[0]:.0%}")
        
        # Try XOR with common keys (repeating key for long payloads)
        for key_name, key_bytes in [
            ("0x7FFF", b'\x7f\xff'), ("0x3FF", b'\x03\xff'), ("0x1FF", b'\x01\xff'),
            ("0x23", b'\x23'), ("0x0F", b'\x0f'),
            ("7FFF", b'7FFF'), ("1023", b'1023'), ("TR4CE", b'TR4CE'),
        ]:
            if len(all_lsbs) < len(key_bytes)*8: continue
            kbl = len(key_bytes)
            xored = [all_lsbs[i] ^ ((key_bytes[(i//8)%kbl] >> (7-i%8)) & 1) for i in range(min(len(all_lsbs), 80000))]
            bs = bits_to_bytes(xored)
            printable = sum(1 for b in bs[:64] if 32<=b<127) / min(64, len(bs))
            if printable > 0.35:
                log(f"      XOR key={key_name}: printable={printable:.0%}")
                log(f"        {txt_of(bs[:80])}")

# ================================================================
# SECTION 2: COMPANION SET 1 DQT AS DECODER MASK
# ================================================================
log("\n" + "=" * 72)
log("SECTION 2: COMPANION SET 1 DQT AS DECODER MASK")
log("=" * 72)

# The correct indexing: DQT tables are in zigzag order, indexed by z
# sky_d0[z] = DQT value at zigzag position z
# tr4_s1_d0[z] = companion Set 1 DQT0 at zigzag position z

# CORRECTED: positions where SKY has > 1 but companion has == 1
d0_extra = [z for z in range(64) if sky_d0[z] > 1 and tr4_s1_d0[z] == 1]
d1_extra = [z for z in range(64) if sky_d1[z] > 1 and tr4_s1_d1[z] == 1]
log(f"\n  DQT0 extra (SKY>1, Set1=1): {d0_extra} ({len(d0_extra)} positions)")
log(f"  DQT1 extra (SKY>1, Set1=1): {d1_extra} ({len(d1_extra)} positions)")

for tid_label, extra in [("DQT0", d0_extra), ("DQT1", d1_extra)]:
    if not extra: continue
    log(f"\n  === {tid_label} ({len(extra)} bits per block, {len(extra)*90000} bits total) ===")
    
    for plane_name, coeffs in [('Y', y_coeffs), ('Cb', cb_coeffs), ('Cr', cr_coeffs)]:
        if coeffs is None: continue
        
        # Extract multi-bit per block
        block_vals = np.zeros(90000, dtype=np.uint32)
        for bi, zpos in enumerate(extra):
            r = ZZ[zpos] // 8; c = ZZ[zpos] % 8
            lsbs = (np.abs(coeffs[:, :, r, c]).astype(np.uint32) & 1)
            block_vals |= (lsbs.reshape(-1) << bi)
        
        # Convert to bitstream
        bit_depth = len(extra)
        bits_flat = np.unpackbits(block_vals.astype(f'>u{max(4, (bit_depth+7)//8)}').view(np.uint8))
        # Actually unpackbits only works on uint8. Let's do it manually:
        bits_flat = []
        for v in block_vals:
            for bi in range(bit_depth):
                bits_flat.append((v >> bi) & 1)
        
        log(f"\n    {plane_name}:")
        
        for msb in [True, False]:
            out = bits_to_bytes(bits_flat, msb)
            printable = sum(1 for b in out[:128] if 32<=b<127) / min(128, len(out))
            log(f"      MSB={msb}: printable={printable:.0%}")
            if printable > 0.2:
                log(f"        {txt_of(out[:96])}")
        
        # Try XOR with keys
        for key_name, key_int in [("0x7FFF", 0x7FFF), ("0x3FF", 0x3FF), ("0x1FF", 0x1FF),
                                    ("1023", 1023), ("32767", 32767)]:
            key_bits = [(key_int >> i) & 1 for i in range(min(bit_depth, 16))]
            if len(key_bits) < bit_depth:
                key_bits = key_bits * (bit_depth // len(key_bits) + 1)
            key_bits = key_bits[:bit_depth]
            
            xored = block_vals.copy()
            for bi in range(bit_depth):
                xored = xored ^ (key_bits[bi] << bi)
            
            bits_xor = []
            for v in xored:
                for bi in range(bit_depth):
                    bits_xor.append((v >> bi) & 1)
            
            out = bits_to_bytes(bits_xor)
            printable = sum(1 for b in out[:128] if 32<=b<127) / min(128, len(out))
            if printable > 0.25:
                log(f"      XOR key={key_name}: printable={printable:.0%}")
                log(f"        {txt_of(out[:96])}")
        
        # Try reading as a 2D image (reshape to 300x300)
        for decode_as in ['text']:
            # Convert to 8-byte groups for printable text
            out = bits_to_bytes(bits_flat)
            # Save raw bits
            out_path_txt = os.path.join(OUT, f'section2_{tid_label}_{plane_name}_msb.bin')
            with open(out_path_txt, 'wb') as f:
                f.write(bits_to_bytes(bits_flat))
            log(f"      Saved: section2_{tid_label}_{plane_name}_msb.bin ({len(bits_flat)//8} bytes)")
            
            # Save as 2D image
            img_data = np.array(block_vals, dtype=np.uint32).reshape(300, 300)
            # Normalize for visualization
            if bit_depth <= 8:
                vis = (img_data * (255 // max(1, int(np.max(img_data))))).astype(np.uint8)
            else:
                vis = (img_data >> 16).astype(np.uint8)  # Take top 8 bits
                if np.max(vis) == 0:
                    vis = (img_data >> 8).astype(np.uint8)
                    if np.max(vis) == 0:
                        vis = img_data.astype(np.uint8)
            Image.fromarray(vis).save(os.path.join(OUT, f'section2_{tid_label}_{plane_name}_vis.png'))

# ================================================================
# SECTION 3: DEEP DECODE OF THE 9 DQT0 CARRIER POSITIONS  
# ================================================================
log("\n" + "=" * 72)
log("SECTION 3: 9-BIT DEEP DECODE FROM DQT0 CARRIER POSITIONS")
log("=" * 72)

# At each of the 9 DQT0 carrier positions, extract LSB for each block
# Also try combining with TR4CE Set 0 DQT values as quantizer
# The "data" is at positions where SKY DQT > 1 AND companion DQT is "normal" (Set 0 has standard values)

d0_positions = d0_extra  # 9 positions
if d0_positions:
    log(f"\n  Carrier zigzag positions: {d0_positions}")
    log(f"  Corresponding DCT indices (r,c):")
    for z in d0_positions:
        r, c = ZZ[z] // 8, ZZ[z] % 8
        log(f"    z={z:02d}: DCT({r},{c})  SKY_D0={sky_d0[z]}  TR4_Set1_D0={tr4_s1_d0[z]}  TR4_Set0_D0={tr4_s0_d0[z]}")
    
    # For each plane, extract 9-bit value per block
    for plane_name, coeffs in [('Y', y_coeffs), ('Cb', cb_coeffs), ('Cr', cr_coeffs)]:
        if coeffs is None: continue
        
        block_vals = np.zeros(90000, dtype=np.uint16)
        for bi, zpos in enumerate(d0_positions):
            r = ZZ[zpos] // 8; c = ZZ[zpos] % 8
            lsbs = (np.abs(coeffs[:, :, r, c]).astype(np.uint16) & 1)
            block_vals |= (lsbs.reshape(-1) << bi)
        
        log(f"\n  === {plane_name} plane ===")
        
        # Value distribution (top values)
        vc = Counter(block_vals)
        log(f"  Top 20 values:")
        for val, cnt in vc.most_common(20):
            c = chr(val) if 32 <= val < 127 else '.'
            log(f"    0x{val:03x} ({val:3d}): {cnt:5d} blocks  '{c}'")
        
        # Most common value = likely "null"
        most_common_val = vc.most_common(1)[0][0]
        log(f"  Most common value: {most_common_val} (likely null/background)")
        
        # Filter out null values to find the message
        filtered = [v for v in block_vals if v != most_common_val]
        log(f"  Non-null values: {len(filtered)}/{len(block_vals)}")
        
        if len(filtered) > 0:
            # Decode as bitstream with null filtering
            bits_filtered = []
            for v in filtered:
                for bi in range(9):
                    bits_filtered.append((v >> bi) & 1)
            
            for msb in [True, False]:
                out = bits_to_bytes(bits_filtered, msb)
                printable = sum(1 for b in out[:128] if 32<=b<127) / min(128, len(out))
                log(f"    Filtered MSB={msb}: printable={printable:.0%}")
                if printable > 0.15:
                    log(f"      {txt_of(out[:96])}")
            
            # Save raw data
            out_path = os.path.join(OUT, f'section3_{plane_name}_filtered.bin')
            # Save as 16-bit values (since values can be > 255)
            np.array(filtered, dtype=np.uint16).tofile(out_path)
            log(f"    Saved: section3_{plane_name}_filtered.bin ({len(filtered)} 16-bit values)")
        
        # Also try all values without filtering
        bits_all = []
        for v in block_vals:
            for bi in range(9):
                bits_all.append((v >> bi) & 1)
        
        for msb in [True, False]:
            out = bits_to_bytes(bits_all, msb)
            printable = sum(1 for b in out[:128] if 32<=b<127) / min(128, len(out))
            log(f"    All MSB={msb}: printable={printable:.0%}")
        
        # Visualize as 300x300 image
        vis = (block_vals * (255 // max(1, int(np.max(block_vals))))).astype(np.uint8)
        Image.fromarray(vis).save(os.path.join(OUT, f'section3_{plane_name}_vis.png'))
        
        # Try reading each bit-plane separately
        log(f"\n  Individual bit-planes:")
        for bi in range(9):
            bp = (block_vals >> bi) & 1
            ones = np.sum(bp)
            zpos = d0_positions[bi]
            r, c = ZZ[zpos] // 8, ZZ[zpos] % 8
            log(f"    Bit {bi} (z={zpos:02d} DCT({r},{c})): {ones}/{90000} = {100*ones/90000:.1f}% ones")

# ================================================================
# SECTION 4: COMBINED PAYLOAD WITH KEY XOR
# ================================================================
log("\n" + "=" * 72)
log("SECTION 4: COMBINED DQT PAYLOAD WITH KEY XOR")
log("=" * 72)

def dqt_bits(vals):
    return [0 if v == 2 else 1 for v in vals if v > 1]

# Build all payloads
sky_d0_bits = dqt_bits(sky_d0)
sky_d1_bits = dqt_bits(sky_d1)
t4s1_d0_bits = dqt_bits(tr4_s1_d0)
t4s1_d1_bits = dqt_bits(tr4_s1_d1)
i4s1_d0_bits = dqt_bits(img4_s1_d0)
i4s1_d1_bits = dqt_bits(img4_s1_d1)

log(f"\n  SKY DQT0: {len(sky_d0_bits)} bits = {bits_to_int(sky_d0_bits):06X}")
log(f"  SKY DQT1: {len(sky_d1_bits)} bits")
log(f"  TR4 Set1 DQT0: {len(t4s1_d0_bits)} bits = {bits_to_int(t4s1_d0_bits):06X}")
log(f"  TR4 Set1 DQT1: {len(t4s1_d1_bits)} bits")
log(f"  IMG4 Set1 DQT0: {len(i4s1_d0_bits)} bits = {bits_to_int(i4s1_d0_bits):06X}")
log(f"  IMG4 Set1 DQT1: {len(i4s1_d1_bits)} bits")

# XOR combinations
combos = {
    "XOR_SKY-TR4S1_D0": zip(sky_d0_bits, t4s1_d0_bits),
    "XOR_SKY-TR4S1_D1": zip(sky_d1_bits, t4s1_d1_bits),
    "XOR_TR4S1-IMG4S1_D0": zip(t4s1_d0_bits, i4s1_d0_bits),
    "XOR_TR4S1-IMG4S1_D1": zip(t4s1_d1_bits, i4s1_d1_bits),
}

for name, pairs in combos.items():
    xor_bits = [a ^ b for a, b in pairs]
    if any(xor_bits):
        val = bits_to_int(xor_bits)
        bs = bits_to_bytes(xor_bits)
        log(f"\n  {name}: {val:0{max(4,(len(xor_bits)+3)//4)}X}")
        log(f"    ASCII: {txt_of(bs[:32])}")
        
        # Try XOR with keys
        for key_name, key_val in [("0x7FFF", 0x7FFF), ("1023", 1023), ("511", 511),
                                    ("32767", 32767), ("0x1FF", 0x1FF)]:
            xk = val ^ key_val
            log(f"    XOR {key_name}: {xk:0{max(4,(len(xor_bits)+3)//4)}X}")

# Combined payloads
log(f"\n  Combined payloads:")
combined = {
    "SKY_D0+D1": sky_d0_bits + sky_d1_bits,
    "TR4S1_D0+D1": t4s1_d0_bits + t4s1_d1_bits,
    "SKY+TR4S1": sky_d0_bits + sky_d1_bits + t4s1_d0_bits + t4s1_d1_bits,
    "D0_SKY+TR4S1": sky_d0_bits + t4s1_d0_bits,
    "D1_SKY+TR4S1": sky_d1_bits + t4s1_d1_bits,
}

for name, bits in combined.items():
    val = bits_to_int(bits)
    bs = bits_to_bytes(bits)
    printable = sum(1 for b in bs[:64] if 32<=b<127) / min(64, len(bs))
    log(f"    {name} ({len(bits)} bits):")
    log(f"      Hex: {bs[:16].hex()}")
    log(f"      ASCII: {txt_of(bs[:32])} printable={printable:.0%}")
    
    # Save each
    with open(os.path.join(OUT, f'section4_{name.replace("+","_").replace(" ","")}.bin'), 'wb') as f:
        f.write(bs)

# ================================================================
# SECTION 5: ROW 7 ANOMALY DEEP EXTRACTION
# ================================================================
log("\n" + "=" * 72)
log("SECTION 5: ROW 7 GLITCH/ANOMALY EXTRACTION")
log("=" * 72)

row = 7
# Extract message from row 7 using ALL DQT>1 position LSBs
log(f"\n  Row {row} (pixel rows {row*8}-{row*8+7}):")
row_vals = []

for col in range(300):
    bits = []
    for zpos in range(64):
        if sky_d0[zpos] > 1:
            r = ZZ[zpos] // 8; c = ZZ[zpos] % 8
            bits.append(np.abs(y_coeffs[row, col, r, c]).astype(int) & 1)
    row_vals.append(bits_to_int(bits))

# Find distinct patterns
vc = Counter(row_vals)
log(f"  Distinct row patterns: {len(vc)}")
most_common_val = vc.most_common(1)[0][0] if vc else 0
log(f"  Most common pattern: 0x{most_common_val:08x} ({most_common_val}) = {vc[most_common_val]}/{300} blocks")

# Filter out dominant pattern
filtered = [(col, v) for col, v in enumerate(row_vals) if v != most_common_val]
log(f"  Non-dominant blocks: {len(filtered)} columns")

if filtered:
    # Extract as bitstream
    bit_depth = len([z for z in range(64) if sky_d0[z] > 1])
    bits_flat = []
    for _, v in filtered:
        for bi in range(bit_depth):
            bits_flat.append((v >> bi) & 1)
    
    for msb in [True, False]:
        out = bits_to_bytes(bits_flat, msb)
        printable = sum(1 for b in out[:64] if 32<=b<127) / min(64, len(out))
        log(f"    Filtered MSB={msb}: printable={printable:.0%}")
        if printable > 0.1:
            log(f"      {txt_of(out[:64])}")
    
    # Show pattern at the period boundaries (col 0, 25, 50, ...)
    log(f"\n  Period boundary blocks (cols 0,25,50...275):")
    for col in range(0, 300, 25):
        log(f"    col {col:3d}: 0x{row_vals[col]:08x} ({row_vals[col]})")
    
    # Col 0 is usually special
    log(f"\n  Block at col 0: 0x{row_vals[0]:08x}")
    log(f"  Block at col 1: 0x{row_vals[1]:08x}")

# ================================================================
# SECTION 6: IMAGE XOR / PIXEL ANALYSIS
# ================================================================
log("\n" + "=" * 72)
log("SECTION 6: IMAGE XOR / PIXEL / VISUAL ANALYSIS")
log("=" * 72)

# Open all images
sky_img = Image.open(os.path.join(BASE, 'project-skyscraper.jpg'))
tr4_img = Image.open(os.path.join(BASE, 'TR4CE.jpg'))
img4_img = Image.open(os.path.join(BASE, 'IMG_00004.jpg'))

# Pixel LSB extraction from skyscraper
log(f"\n  Pixel LSB extraction from project-skyscraper.jpg:")
sky_pixels = list(sky_img.getdata())
all_lsbs = []
for p in sky_pixels[:100000]:
    if isinstance(p, tuple):
        for ch in p[:3]:
            all_lsbs.append(ch & 1)
    else:
        all_lsbs.append(p & 1)

for offset in range(8):
    shifted = all_lsbs[offset:]
    out = bits_to_bytes(shifted)
    printable = sum(1 for b in out[:64] if 32<=b<127) / min(64, len(out))
    if printable > 0.1:
        log(f"    offset={offset}: printable={printable:.0%}: {txt_of(out[:48])}")

# Also save full pixel LSB data
with open(os.path.join(OUT, 'skyscraper_pixel_lsbs.bin'), 'wb') as f:
    f.write(bits_to_bytes(all_lsbs))

# XOR the two companion images (resized to match)
log(f"\n  Resizing and XOR of images:")
try:
    tr4_r = tr4_img.resize((1212, 742))
    xor_tr4_img4 = Image.fromarray(
        (np.array(tr4_r, dtype=np.int16) - np.array(img4_img, dtype=np.int16)).clip(0, 255).astype(np.uint8)
    )
    xor_tr4_img4.save(os.path.join(OUT, 'xor_tr4ce_img4.png'))
    log(f"    Saved: xor_tr4ce_img4.png")
    
    # Check if XOR reveals anything
    xor_data = np.array(xor_tr4_img4)
    log(f"    XOR mean: {xor_data.mean():.1f} std: {xor_data.std():.1f}")
    unique_vals = len(np.unique(xor_data))
    log(f"    Unique pixel values: {unique_vals}")
    if unique_vals < 50:
        log(f"    *** Almost identical images! ***")
except Exception as e:
    log(f"    Error: {e}")

# Histogram of pixel LSB distribution
sky_arr = np.array(sky_img)
r_lsb = sky_arr[:,:,0] & 1
g_lsb = sky_arr[:,:,1] & 1
b_lsb = sky_arr[:,:,2] & 1
log(f"\n  Pixel LSB bias:")
for name, lsb in [("R", r_lsb), ("G", g_lsb), ("B", b_lsb)]:
    ones = np.sum(lsb)
    log(f"    {name}: {ones}/{lsb.size} = {100*ones/lsb.size:.1f}% ones")

# Check 8x8 block LSB statistics
blocks_r = []
for by in range(300):
    for bx in range(300):
        block = r_lsb[by*8:(by+1)*8, bx*8:(bx+1)*8]
        blocks_r.append(np.mean(block))
blocks_r = np.array(blocks_r)
log(f"\n  Block-level LSB mean stats (R channel):")
log(f"    min={blocks_r.min():.3f} max={blocks_r.max():.3f} mean={blocks_r.mean():.3f} std={blocks_r.std():.3f}")

# ================================================================
# SECTION 7: ALTERNATIVE DCT DECODING APPROACHES
# ================================================================
log("\n" + "=" * 72)
log("SECTION 7: ALTERNATIVE DCT DECODING APPROACHES")
log("=" * 72)

# 7a: Use companion Set 0 DQT values as quantizers for skyscraper DCT
log(f"\n  7a: Companion Set 0 DQT as quantizer:")
log(f"    TR4CE Set 0 DQT0 has values 5-61, SKY has 1-3")
log(f"    The RATIO of companion_DQT / SKY_DQT at each position")
log(f"    tells us how many bits of data are embedded")

for z in range(64):
    if sky_d0[z] > 1 and tr4_s0_d0[z] > 1:
        ratio = tr4_s0_d0[z] / sky_d0[z]
        # Number of bits = floor(log2(ratio))
        n_bits = int(np.floor(np.log2(ratio)))
        if n_bits > 0:
            r = ZZ[z] // 8; c = ZZ[z] % 8
            coeffs = np.abs(y_coeffs[:, :, r, c]).flatten().astype(int)
            # Extract n_bits from each coefficient (divided by DQT value)
            bits_extracted = []
            for val in coeffs[:1000]:
                quantized = val // int(tr4_s0_d0[z])
                for bi in range(n_bits):
                    bits_extracted.append((quantized >> bi) & 1)
            if len(bits_extracted) >= 8:
                out = bits_to_bytes(bits_extracted)
                printable = sum(1 for b in out[:16] if 32<=b<127) / 16
                if printable > 0.3:
                    log(f"    z={z:02d} (r={r},c={c}): ratio={ratio:.1f} n_bits={n_bits} printable={printable:.0%}")
                    log(f"      {txt_of(out[:32])}")

# 7b: Use EXIF padding as one-time pad
log(f"\n  7b: EXIF padding OTP decode:")
def get_padding(data):
    i = data.find(b'\x1c\xea')  # Look for 0xEA1C tag
    if i < 0: return None
    # Read the IFD entry value/offset
    return data[i:i+256]

tr4_pad = get_padding(tr4_data)
if tr4_pad:
    log(f"    TR4CE padding: {tr4_pad[:32].hex()}")
    # XOR with first 256 bytes of skyscraper DCT LSB stream
    bits_all = []
    for zpos in range(64):
        if sky_d0[zpos] > 1:
            r = ZZ[zpos] // 8; c = ZZ[zpos] % 8
            bits_all.extend((np.abs(y_coeffs[:, :, r, c]).astype(int) & 1).flatten())
    
    for offset in range(8):
        shifted = bits_all[offset:]
        dct_bytes = bits_to_bytes(shifted)
        xored = bytes(a ^ b for a, b in zip(dct_bytes[:len(tr4_pad)], tr4_pad))
        printable = sum(1 for b in xored[:64] if 32<=b<127) / 64
        if printable > 0.3:
            log(f"    offset={offset}: printable={printable:.0%}")
            log(f"      {txt_of(xored[:96])}")

# 7c: Try the DQT XOR between TR4CE Set 0 and IMG4 Set 0
log(f"\n  7c: TR4CE Set 0 DQT0 as direct LSB quantizer:")
# The companion Set 0 DQT0 values are large (5-61)
# If we use them as direct LSB quantizer per coefficient:
for plane_name, coeffs in [('Y', y_coeffs)]:
    if coeffs is None: continue
    all_vals = []
    for zpos in d0_positions:
        if tr4_s0_d0[zpos] > 0:
            r = ZZ[zpos] // 8; c = ZZ[zpos] % 8
            vals = np.abs(coeffs[:, :, r, c]).flatten().astype(int)
            # Mod by companion DQT to extract embedded message
            embedded = vals % tr4_s0_d0[zpos]
            all_vals.extend(embedded[:1000])
    
    if all_vals:
        hist = Counter(all_vals)
        log(f"    Mod values distribution: {hist.most_common(10)}")

# ================================================================
# SECTION 8: EXTRACT ALL DCT COEFFICIENTS - FULL BINARY DUMP
# ================================================================
log("\n" + "=" * 72)
log("SECTION 8: FULL DCT BINARY DUMP AT CARRIER POSITIONS")
log("=" * 72)

# Dump ALL DCT coefficients at carrier positions as raw bytes
carrier_sets = {
    'DQT0_carriers_30': [z for z in range(64) if sky_d0[z] > 1],
    'DQT1_carriers_56': [z for z in range(64) if sky_d1[z] > 1],
    'DQT0_extra_9': d0_positions,
}

for name, positions in carrier_sets.items():
    if not positions: continue
    log(f"\n  {name} ({len(positions)} positions):")
    for plane_name, coeffs in [('Y', y_coeffs)]:
        if coeffs is None: continue
        
        # Extract coefficient values (not just LSBs) as raw data
        raw_coeffs = []
        for zpos in positions:
            r = ZZ[zpos] // 8; c = ZZ[zpos] % 8
            raw_coeffs.extend(np.abs(coeffs[:, :, r, c]).flatten().astype(np.int16).tolist())
        
        arr = np.array(raw_coeffs, dtype=np.int16)
        # Save raw 16-bit
        arr.tofile(os.path.join(OUT, f'section8_{name}_{plane_name}_raw.bin'))
        
        # Also save LSB-only version
        lsbs = (np.abs(arr) & 1).tolist()
        with open(os.path.join(OUT, f'section8_{name}_{plane_name}_lsb.bin'), 'wb') as f:
            f.write(bits_to_bytes(lsbs))
        
        log(f"    {plane_name}: {len(arr)} values, {len(arr)*2} bytes raw, {len(lsbs)//8} bytes LSB")
        
        # Check coefficient value distribution
        vc = Counter(arr[:10000])
        log(f"    Top 10 raw values: {vc.most_common(10)}")

# ================================================================
# SECTION 9: FREQUENCY-BASED PATTERN ANALYSIS
# ================================================================
log("\n" + "=" * 72)
log("SECTION 9: FREQUENCY-BASED PATTERN ANALYSIS")
log("=" * 72)

# Check the 25-block period boundary
log(f"\n  25-block period analysis:")
for zpos in d0_positions:
    r = ZZ[zpos] // 8; c = ZZ[zpos] % 8
    coeffs = np.abs(y_coeffs[:, :, r, c]).astype(int)
    
    # Check values at columns 0, 25, 50, 75, 100, 125, 150, 175, 200, 225, 250, 275
    period_vals = []
    for by in range(300):
        period_vals.extend([coeffs[by, col] for col in range(0, 300, 25)])
    period_vals = np.array(period_vals)
    non_zero = np.sum(period_vals > 0)
    even_pct = np.sum(period_vals % 2 == 0) / len(period_vals) * 100
    
    # Compare with non-period columns
    other_vals = []
    for by in range(300):
        cols = [c for c in range(1, 300) if c % 25 != 0]
        other_vals.extend([coeffs[by, col] for col in cols])
    other_vals = np.array(other_vals)
    other_even = np.sum(other_vals % 2 == 0) / len(other_vals) * 100
    
    diff_even = even_pct - other_even
    if abs(diff_even) > 1.0:
        log(f"    z={zpos:02d} (DCT({r},{c})): period even={even_pct:.1f}% non-period even={other_even:.1f}% diff={diff_even:+.1f}%")

# ================================================================
# SECTION 10: TARGETED DECODE - MOST PROMISING APPROACHES
# ================================================================
log("\n" + "=" * 72)
log("SECTION 10: TARGETED DECODE - BEST APPROACHES COMBINED")
log("=" * 72)

# 10a: Only the 3 active bits from DQT0 extra (bits 1, 6, 8)
log(f"\n  10a: 3 active bits from DQT0 extra (z=35, z=40, z=42):")
active_bits = [1, 6, 8]  # bit indices in the 9-bit value
active_positions = [d0_positions[i] for i in [1, 6, 8]]

for plane_name, coeffs in [('Y', y_coeffs), ('Cb', cb_coeffs), ('Cr', cr_coeffs)]:
    if coeffs is None: continue
    block_vals = np.zeros(90000, dtype=np.uint8)
    for bi, zpos in enumerate(active_positions):
        r = ZZ[zpos] // 8; c = ZZ[zpos] % 8
        lsbs = (np.abs(coeffs[:, :, r, c]).astype(np.uint8) & 1)
        block_vals |= (lsbs.reshape(-1) << bi)
    
    bits_flat = []
    for v in block_vals:
        for bi in range(3):
            bits_flat.append((v >> bi) & 1)
    
    for msb in [True, False]:
        out = bits_to_bytes(bits_flat, msb)
        printable = sum(1 for b in out[:128] if 32<=b<127) / min(128, len(out))
        log(f"    {plane_name} MSB={msb}: {printable:.0%} printable")
        if printable > 0.25:
            log(f"      {txt_of(out[:96])}")
    
    # Try reading as hex (nibble extraction)
    hex_chars = '0123456789ABCDEF'
    hex_out = ''
    for v in block_vals:
        if v < 8:
            hex_out += hex_chars[v]
    log(f"    As hex string (first 64 chars): {hex_out[:64]}")
    
    # Save
    out_path = os.path.join(OUT, f'section10a_{plane_name}_3bit.bin')
    with open(out_path, 'wb') as f:
        f.write(bits_to_bytes(bits_flat))

# 10b: Only DQT1 extra 3 positions (z=6, 9, 12)  
log(f"\n  10b: DQT1 extra 3 positions (z=6, 9, 12):")
for plane_name, coeffs in [('Y', y_coeffs)]:
    if coeffs is None: continue
    block_vals = np.zeros(90000, dtype=np.uint8)
    for bi, zpos in enumerate(d1_extra):
        r = ZZ[zpos] // 8; c = ZZ[zpos] % 8
        lsbs = (np.abs(coeffs[:, :, r, c]).astype(np.uint8) & 1)
        block_vals |= (lsbs.reshape(-1) << bi)
    
    bits_flat = []
    for v in block_vals:
        for bi in range(3):
            bits_flat.append((v >> bi) & 1)
    
    for msb in [True, False]:
        out = bits_to_bytes(bits_flat, msb)
        printable = sum(1 for b in out[:128] if 32<=b<127) / min(128, len(out))
        log(f"    {plane_name} MSB={msb}: {printable:.0%} printable")
        if printable > 0.25:
            log(f"      {txt_of(out[:96])}")

# 10c: All 12 carrier positions (9 DQT0 + 3 DQT1) combined
log(f"\n  10c: All 12 carrier positions combined:")
all_extra = d0_positions + d1_extra  # z=28,35-42 + z=6,9,12
for plane_name, coeffs in [('Y', y_coeffs)]:
    if coeffs is None: continue
    block_vals = np.zeros(90000, dtype=np.uint16)
    for bi, zpos in enumerate(all_extra):
        r = ZZ[zpos] // 8; c = ZZ[zpos] % 8
        lsbs = (np.abs(coeffs[:, :, r, c]).astype(np.uint16) & 1)
        block_vals |= (lsbs.reshape(-1) << bi)
    
    bits_flat = []
    for v in block_vals:
        for bi in range(len(all_extra)):
            bits_flat.append((v >> bi) & 1)
    
    for msb in [True, False]:
        out = bits_to_bytes(bits_flat, msb)
        printable = sum(1 for b in out[:128] if 32<=b<127) / min(128, len(out))
        log(f"    {plane_name} MSB={msb}: {printable:.0%} printable")
        if printable > 0.2:
            log(f"      {txt_of(out[:96])}")
    
    # Save
    out_path = os.path.join(OUT, f'section10c_{plane_name}_12bit.bin')
    with open(out_path, 'wb') as f:
        f.write(bits_to_bytes(bits_flat))

# 10d: Try DQT payload as coordinates (0x7FFF = 32767, 0x3FF = 1023)
log(f"\n  10d: DQT payload as image coordinates:")
sky_d0_val = bits_to_int(sky_d0_bits)
tr4s1_d0_val = bits_to_int(t4s1_d0_bits)
log(f"    SKY DQT0 = {sky_d0_val}")
log(f"    TR4 Set1 DQT0 = {tr4s1_d0_val}")
log(f"    As pixel coordinates:")
log(f"      (x={sky_d0_val % 2400}, y={sky_d0_val // 2400})")
log(f"      (x={tr4s1_d0_val % 2400}, y={tr4s1_d0_val // 2400})")
log(f"      (x={sky_d0_val % 624}, y={sky_d0_val // 624}) for TR4CE")
log(f"      (x={tr4s1_d0_val % 624}, y={tr4s1_d0_val // 624}) for TR4CE")

# 10e: Check pixel values at these coordinates
sky_arr = np.array(sky_img)
for name, val in [("SKY_DQT0", sky_d0_val), ("TR4S1_DQT0", tr4s1_d0_val)]:
    x = val % 2400
    y = val // 2400
    if y < 2400:
        px = sky_arr[y, x]
        log(f"    Pixel at ({x},{y}) in SKY: RGB({px[0]},{px[1]},{px[2]})")

# 10f: Try XOR or ADD of the two values as a third coordinate
combined = sky_d0_val ^ tr4s1_d0_val
log(f"\n  10e: XOR as offset: {combined}")
x = combined % 2400
y = combined // 2400
if y < 2400:
    px = sky_arr[y, x]
    log(f"    Pixel at ({x},{y}) in SKY: RGB({px[0]},{px[1]},{px[2]})")

# Also check in IMG4
img4_arr = np.array(img4_img)
img4_w, img4_h = img4_img.size
for name, val in [("SKY_DQT0", sky_d0_val), ("TR4S1_DQT0", tr4s1_d0_val)]:
    x = val % img4_w
    y = val // img4_w
    if y < img4_h:
        px = img4_arr[y, x]
        log(f"    Pixel at ({x},{y}) in IMG4: RGB({px[0]},{px[1]},{px[2]})")


# ================================================================
log("\n" + "=" * 72)
log("SECTION 11: KEY FINDINGS & BEST CANDIDATES")
log("=" * 72)

log(f"\n  KEY PAYLOADS:")
log(f"    SKY DQT0: 30 bits = 0x{bits_to_int(sky_d0_bits):06X} = {bits_to_int(sky_d0_bits)}")
log(f"    SKY DQT1: 56 bits (first 24: {''.join(str(b) for b in sky_d1_bits[:24])})")
log(f"    TR4 Set1 DQT0: 21 bits = 0x{bits_to_int(t4s1_d0_bits):06X} = {bits_to_int(t4s1_d0_bits)}")
log(f"    TR4 Set1 DQT1: 53 bits (first 24: {''.join(str(b) for b in t4s1_d1_bits[:24])})")
log(f"    XOR D0: 0x{bits_to_int([a^b for a,b in zip(sky_d0_bits, t4s1_d0_bits)]):06X}")
log(f"    Combined: {len(sky_d0_bits+sky_d1_bits+t4s1_d0_bits+t4s1_d1_bits)} bits total\n")

log(f"  9 CARRIER POSITIONS (DQT0 extra):")
for i, z in enumerate(d0_positions):
    r, c = ZZ[z] // 8, ZZ[z] % 8
    log(f"    z={z:02d} DCT({r},{c}) bits=1/{i}")

log(f"\n  TOP BIT-PLANES (DQT0 extra):")
log(f"    Bit 1 (z=35): 47.0% ones (most active, likely data)")
log(f"    Bit 8 (z=42): 45.1% ones (most active)")
log(f"    Bit 6 (z=40): 42.3% ones (most active)")
log(f"    Bits 0,2,3,4,5,7: 2-12% ones (mostly null, could be control)")

log(f"\n  BEST TEXT CANDIDATES:")
# Read the saved files and summarize
for fname in sorted(os.listdir(OUT)):
    if fname.endswith('_msb.bin'):
        fpath = os.path.join(OUT, fname)
        data = open(fpath, 'rb').read()
        printable = sum(1 for b in data[:128] if 32<=b<127) / min(128, len(data))
        if printable > 0.2:
            log(f"    {fname:<50} {printable:.0%} printable: {txt_of(data[:48])}")

log(f"\n  Output files summary:")
for fname in sorted(os.listdir(OUT)):
    fpath = os.path.join(OUT, fname)
    if os.path.isfile(fpath) and fname != os.path.basename(__file__):
        size = os.path.getsize(fpath)
        log(f"    {fname:<50} {size:>8} bytes")

log("\n" + "=" * 72)
log("EXTRACTION COMPLETE")
log("=" * 72)
