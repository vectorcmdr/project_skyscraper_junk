# Project Skyscraper ARG Community Reference Files

<img src="https://github.com/vectorcmdr/project_skyscraper_junk/blob/main/archived/cropped-project-skyscraper.jpg" width="160">

Shared findings and other junk for the No Man's Sky 'Project Skyscraper' ARG.

Contains static site mirror for file and source reference, original images, image forensics (and outputs) and various other reports.

## Layout:

- Static site mirror + scripts live here: [/_site_mirror](https://github.com/vectorcmdr/project_skyscraper_junk/tree/main/_site_mirror)

- Root files are scripts, general reports and base images for analysis - by file name or purpose.
- Folders matching file names are analysis output folders -> img / bin / audio / report / etc.
- Folders not matching are specific to purpose.

I'll clean it up properly later (...probably) and do my best to keep it relatively up to date.

**⚠️ Warning for the audio files:** <br />
- Some are like beautiful whale songs... others are like having your teeth jackhammered - make sure your headphones are not too loud.

## Current known message cipher "Highschool Code":
This was part of the "/code" puzzle "When_we_were_17" image.

### Explainer:

It is a monoalphabetic position based cipher using the key `MINDFAGEBJRLHCVPQSKYUWOXTZ`:

1. For each ciphertext letter, use its A=0...Z=25 value as an index into the
   key text. The key letter at that position is the plaintext.

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

## 20x20 "Pixel" 8x5 bit block puzzles (like the Fragment[C3q5NYF]):

The ERROR carrier of layer 0/1 was confirmed early on.
The hint that as given regarding offsets (though partial solved + WT knowledge beat it before the hint) was the pin for this one.

Solve was to offset +2/-6 at the anomalous block position (QSRSV):
```
B1[7] -> BK=1:
Row 0: cols 58-65: 0 1 0 0 0 1 0 1 = 45h = E
Row 1: cols 58-65: 0 1 0 0 1 1 0 1 = 4Dh = M
Row 2: cols 58-65: 0 1 0 0 1 0 0 1 = 49h = I
Row 3: cols 58-65: 0 1 0 0 1 1 0 0 = 4Ch = L
Row 4: cols 58-65: 0 1 0 1 1 0 0 1 = 59h = Y
```
This puzzle concept may get later re-use.

- `connection-detected-access-denied-v0-8c7atk6y141h1.png` has been connected to the new `C3q5NYF.png`. `connection-fragment-solve-compressed.gif` offers visual insight. This was likely a (subtle?) clue about the offsets needing to be considered.

## Things of note for the image forensics:
- Try to reference files here first before exploring the site endpoints, source, image forensics etc. to help reduce doubling up of work and flooding of cycling queries.
