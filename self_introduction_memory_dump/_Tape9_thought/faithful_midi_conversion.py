import librosa
import numpy as np

audio_path = r'C:\stack\arg\self_introduction_memory_dump.mp3'
print("Loading audio...")
y, sr = librosa.load(audio_path, sr=None, mono=False)
y_mono = (y[0] + y[1]) / 2
print(f"Audio: {len(y_mono)} samples @ {sr} Hz, duration: {len(y_mono)/sr:.3f}s")

# Use pYIN for pitch tracking
print("Running pYIN pitch tracking...")
f0, voiced_flag, voiced_probs = librosa.pyin(y_mono, sr=sr,
                                               fmin=librosa.note_to_hz('C2'),
                                               fmax=librosa.note_to_hz('C7'))

times = librosa.times_like(f0, sr=sr)

# Convert Hz to MIDI notes, only where voiced
midi_notes = []
for freq, voiced in zip(f0, voiced_flag):
    if voiced and not np.isnan(freq) and freq > 0:
        midi = 69 + 12 * np.log2(freq / 440.0)
        midi_notes.append(round(midi))
    else:
        midi_notes.append(None)

# Find contiguous note segments
print("Segmenting notes...")
note_segments = []
in_note = False
seg_start = 0
seg_midi = None

for i in range(len(midi_notes)):
    if midi_notes[i] is not None:
        if not in_note:
            in_note = True
            seg_start = i
            seg_midi = midi_notes[i]
        elif midi_notes[i] != seg_midi:
            # Note changed, end previous and start new
            note_segments.append({
                'start_time': times[seg_start],
                'end_time': times[i-1],
                'duration': times[i-1] - times[seg_start],
                'midi': int(seg_midi),
                'freq': 440.0 * 2**((seg_midi - 69)/12)
            })
            seg_start = i
            seg_midi = midi_notes[i]
    else:
        if in_note:
            in_note = False
            note_segments.append({
                'start_time': times[seg_start],
                'end_time': times[i-1],
                'duration': times[i-1] - times[seg_start],
                'midi': int(seg_midi),
                'freq': 440.0 * 2**((seg_midi - 69)/12)
            })

# Handle last segment
if in_note:
    note_segments.append({
        'start_time': times[seg_start],
        'end_time': times[-1],
        'duration': times[-1] - times[seg_start],
        'midi': int(seg_midi),
        'freq': 440.0 * 2**((seg_midi - 69)/12)
    })

print(f"Total note segments: {len(note_segments)}")

# Filter very short notes (noise/glitches)
min_dur = 0.03  # 30ms
note_segments = [n for n in note_segments if n['duration'] >= min_dur]
print(f"After filtering (min {min_dur}s): {len(note_segments)}")

# Print summary
print("\nNote summary (first 30):")
for i, note in enumerate(note_segments[:30]):
    print(f"  Note {i+1}: MIDI {note['midi']:3d}, {note['freq']:.1f} Hz, "
          f"{note['start_time']:.3f}s - {note['end_time']:.3f}s "
          f"(dur: {note['duration']:.3f}s)")

# Write MIDI file
print("\nWriting MIDI file...")

# MIDI header
header = bytearray()
header.extend(b'MThd')
header.extend((6).to_bytes(4, 'big'))
header.extend((0).to_bytes(2, 'big'))  # Format 0
header.extend((1).to_bytes(2, 'big'))  # 1 track
header.extend((480).to_bytes(2, 'big'))  # Ticks per quarter note

# Track data
track_data = bytearray()

# Tempo meta event (120 BPM = 500000 microseconds per quarter note)
track_data.append(0x00)  # Delta time
track_data.append(0xFF)  # Meta event
track_data.append(0x51)  # Tempo
track_data.append(0x03)  # Length
track_data.extend((500000).to_bytes(3, 'big'))

# Create note events
ticks_per_second = 480 * 2  # 120 BPM = 2 beats per second
last_time = 0

def write_delta_time(delta_seconds):
    delta_ticks = int(delta_seconds * ticks_per_second)
    delta_bytes = []
    value = delta_ticks
    while True:
        byte = value & 0x7F
        value >>= 7
        if delta_bytes:
            byte |= 0x80
        delta_bytes.insert(0, byte)
        if value == 0:
            break
    return bytes(delta_bytes)

for note in note_segments:
    # Note on
    delta = write_delta_time(note['start_time'] - last_time)
    track_data.extend(delta)
    track_data.append(0x90)  # Note on, channel 0
    track_data.append(note['midi'])
    track_data.append(100)  # Velocity
    last_time = note['start_time']
    
    # Note off
    delta = write_delta_time(note['end_time'] - last_time)
    track_data.extend(delta)
    track_data.append(0x80)  # Note off, channel 0
    track_data.append(note['midi'])
    track_data.append(0)  # Velocity
    last_time = note['end_time']

# End of track meta event
track_data.append(0x00)
track_data.append(0xFF)
track_data.append(0x2F)
track_data.append(0x00)

# Write track chunk
track_chunk = bytearray()
track_chunk.extend(b'MTrk')
track_chunk.extend(len(track_data).to_bytes(4, 'big'))
track_chunk.extend(track_data)

# Write file
output_path = r'C:\stack\arg\tapes_man_2\audio_to_midi_faithful.mid'
with open(output_path, 'wb') as f:
    f.write(header)
    f.write(track_chunk)

print(f"\nMIDI file saved to: {output_path}")
print(f"File size: {len(header) + len(track_chunk)} bytes")

# Also save the note data as text for reference
with open(r'C:\stack\arg\tapes_man_2\midi_note_data.txt', 'w') as f:
    f.write("=== Faithful Audio-to-MIDI Conversion ===\n\n")
    f.write(f"Audio: self_introduction_memory_dump.mp3\n")
    f.write(f"Duration: {len(y_mono)/sr:.3f}s\n")
    f.write(f"Total notes: {len(note_segments)}\n\n")
    f.write("Note,MIDI,Freq_Hz,Start_s,End_s,Duration_s\n")
    for note in note_segments:
        f.write(f"{note['midi']},{note['midi']},{note['freq']:.2f},"
                f"{note['start_time']:.4f},{note['end_time']:.4f},"
                f"{note['duration']:.4f}\n")

print("Note data saved to: midi_note_data.txt")
