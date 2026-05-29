## Project Skyscraper ARG Community Reference Files

<img src="https://github.com/vectorcmdr/project_skyscraper_junk/blob/main/cropped-project-skyscraper.jpg" width="160">

Shared findings and other junk for the No Man's Sky 'Project Skyscraper' ARG.

Contains static site mirror for file and source reference, original images, image forensics (and outputs) and various other reports.

### Layout:

- Static site mirror + scripts live here: [/_site_mirror](https://github.com/vectorcmdr/project_skyscraper_junk/tree/main/_site_mirror)

- Root files are scripts, general reports and base images for analysis - by file name or purpose.
- Folders matching file names are analysis output folders -> img / bin / audio / report / etc.
- Folders not matching are specific to purpose.

I'll clean it up properly later (...probably).

**⚠️ Warning for the audio files:** <br />
- Some are like beautiful whale songs... others are like having your teeth jackhammered - make sure your headphones are not too loud.

### Current known message cipher "Highschool Code":
This was part of the "/code" puzzle "When_we_were_17" image.

### Explainer:

It is a monoalphabetic position based cipher flavoured after da vinci's writing style as a left-hander in the time of ink (da Vinci often wrote letters in a (non-cipher) mirror writing style to avoid smudging ink).

1. For each ciphertext letter, use its A=0...Z=25 value as an index into the
   key text. The key letter at that position is the plaintext.

3. The ciphertext `BNCBO HD DKFCWHL` decodes to `ICNIV ED DRANOEL` (read right
   to left in French: LÉONARD DE VINCI).

```
Position:  0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25
Key text:  M  I  N  D  F  A  G  E  B  J  R  L  H  C  V  P  Q  S  K  Y  U  W  O  X  T  Z
Plain:     A  B  C  D  E  F  G  H  I  J  K  L  M  N  O  P  Q  R  S  T  U  V  W  X  Y  Z
```

### Walkthrough

```
Cipher:   L  H  W  C  F  K  D     D  H     O  B  C  N  B
Value:   11  7 22  2  5 10  3     3  7    14  1  2 13  1
          ↓  ↓  ↓  ↓  ↓  ↓  ↓     ↓  ↓     ↓  ↓  ↓  ↓  ↓
Key[pos]: L  E  O  N  A  R  D     D  E     V  I  N  C  I
Plain:    L  E  O  N  A  R  D     D  E     V  I  N  C  I

       =  LÉONARD DE VINCI
```

### Things of note for the image forensics:
- Try to reference files here first before exploring the site endpoints, source, image forensics etc. to help reduce doubling up of work and flooding of cycling queries.

- There are possible DQT/DCT steganography indications within the image files `TR4CE.jpg`, `IMG_00004.jp`, `IMG_00004_1.jp` and `project-skyscraper.jpg` and some other file anomalies too. Read the reports for more info on how to help.

- `connection-detected-access-denied-v0-8c7atk6y141h1.png` could use some extra eyes. Seems to have some kind of data in blocks, 10x10 / 50(49) segments due to anomalous offsets and channel manipulation. Spectrogram is assumed because of the visuals (and some filter/XOR spectrogram outputs) - but all discernable outputs either have a speech like cadence, or a burst-like thrum. Could be scales, morse, positionals or even frames. Could also just be encoded bin segments and not human facing.

- Given puzzle one: There is a strong possibility this might just be a participation phase and the files (while anomalous) may contain no worthwhile output. `the_architect` has been queried via two routes (one known, one currently hidden) to confirm.
