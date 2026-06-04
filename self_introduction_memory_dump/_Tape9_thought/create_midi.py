import librosa
import numpy as np
from scipy import signal as sig

# Try importing pretty_midi, if not available use a simple MIDI writer
try:
    import pretty_midi
    USE_PRETTY_MIDI = True
    print("Using pretty_midi library")
except ImportError:
    USE_PRETTY_MIDI = False
    print("pretty_midi not available, will use simple MIDI writer")

audio_path = r'C:\stack\arg\self_introduction_memory_dump.mp3'
y, sr = librosa.load(audio_path, sr=None, mono=False)
y_mono = (y[0] + y[1]) / 2

n_fft = 32768
hop = 64
D = librosa.stft(y_mono, n_fft=n_fft, hop_length=hop)
S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)
freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
times = librosa.frames_to_time(np.arange(S_db.shape[1]), sr=sr, hop_length=hop)

# The 8 formant frequencies
formant_freqs = [409.1, 442.8, 453.5, 528.9, 613.7, 702.5, 819.6, 912.5]
formant_bins = [np.argmin(np.abs(freqs - f)) for f in formant_freqs]

# Extract energy at each formant
formant_energies = np.array([S_db[b, :] for b in formant_bins])

# Calculate thresholds
thresholds = []
for i in range(len(formant_bins)):
    median = np.median(formant_energies[i, :])
    std = np.std(formant_energies[i, :])
    thresholds.append(median + 0.8 * std)

# Binary on/off matrix
binary_matrix = np.zeros((len(formant_bins), S_db.shape[1]), dtype=int)
for i in range(len(formant_bins)):
    binary_matrix[i, :] = (formant_energies[i, :] > thresholds[i]).astype(int)

# Convert frequencies to MIDI notes
formant_midis = []
for f in formant_freqs:
    midi = 69 + 12 * np.log2(f / 440.0)
    formant_midis.append(round(midi))

print("Formant frequencies and MIDI notes:")
for i, (f, m) in enumerate(zip(formant_freqs, formant_midis)):
    print(f"  Formant {i+1}: {f:.1f} Hz -> MIDI {m}")

if USE_PRETTY_MIDI:
    # Create MIDI file using pretty_midi
    midi_file = pretty_midi.PrettyMIDI()
    
    # Create an instrument track
    instrument = pretty_midi.Instrument(program=0)  # Acoustic Grand Piano
    
    # Find note on/off events for each formant
    for formant_idx in range(len(formant_freqs)):
        midi_note = int(formant_midis[formant_idx])
        
        # Find segments where this formant is active
        in_note = False
        note_start = 0
        
        for t in range(binary_matrix.shape[1]):
            is_active = binary_matrix[formant_idx, t] == 1
            
            if is_active and not in_note:
                # Note on
                in_note = True
                note_start = times[t]
            elif not is_active and in_note:
                # Note off
                in_note = False
                note_end = times[t - 1] if t > 0 else times[t]
                duration = note_end - note_start
                
                # Only add notes with meaningful duration (>50ms)
                if duration >= 0.05:
                    note = pretty_midi.Note(
                        velocity=100,
                        pitch=midi_note,
                        start=note_start,
                        end=note_end
                    )
                    instrument.notes.append(note)
        
        # Handle note that extends to end
        if in_note:
            note_end = times[-1]
            duration = note_end - note_start
            if duration >= 0.05:
                note = pretty_midi.Note(
                    velocity=100,
                    pitch=midi_note,
                    start=note_start,
                    end=note_end
                )
                instrument.notes.append(note)
    
    # Add instrument to MIDI file
    midi_file.instruments.append(instrument)
    
    # Save
    output_path = r'C:\stack\arg\tapes_man_2\formant_notes.mid'
    midi_file.write(output_path)
    print(f"\nMIDI file saved to: {output_path}")
    print(f"Total notes: {len(instrument.notes)}")
    
    # Print note summary
    print("\nNote summary:")
    for note in sorted(instrument.notes, key=lambda x: x.start)[:30]:
        print(f"  Pitch {note.pitch} ({pretty_midi.note_number_to_name(note.pitch)}): "
              f"{note.start:.3f}s - {note.end:.3f}s (dur: {note.end-note.start:.3f}s)")
    
else:
    # Simple MIDI writer fallback
    print("\nWriting simple MIDI file...")
    
    # MIDI file format
    # Header chunk
    header = bytearray()
    header.extend(b'MThd')
    header.extend((6).to_bytes(4, 'big'))  # Chunk length
    header.extend((0).to_bytes(2, 'big'))  # Format 0 (single track)
    header.extend((1).to_bytes(2, 'big'))  # 1 track
    header.extend((480).to_bytes(2, 'big'))  # Ticks per quarter note
    
    # Track chunk
    track_data = bytearray()
    
    # Tempo meta event (120 BPM = 500000 microseconds per quarter note)
    track_data.append(0x00)  # Delta time
    track_data.append(0xFF)  # Meta event
    track_data.append(0x51)  # Tempo
    track_data.append(0x03)  # Length
    track_data.extend((500000).to_bytes(3, 'big'))
    
    # Collect all note events with their times
    events = []
    for formant_idx in range(len(formant_freqs)):
        midi_note = int(formant_midis[formant_idx])
        
        in_note = False
        note_start_time = 0
        
        for t in range(binary_matrix.shape[1]):
            is_active = binary_matrix[formant_idx, t] == 1
            
            if is_active and not in_note:
                in_note = True
                note_start_time = times[t]
            elif not is_active and in_note:
                in_note = False
                note_end_time = times[t - 1] if t > 0 else times[t]
                duration = note_end_time - note_start_time
                
                if duration >= 0.05:
                    events.append({
                        'time': note_start_time,
                        'type': 'on',
                        'note': midi_note,
                        'velocity': 100
                    })
                    events.append({
                        'time': note_end_time,
                        'type': 'off',
                        'note': midi_note,
                        'velocity': 0
                    })
        
        if in_note:
            note_end_time = times[-1]
            duration = note_end_time - note_start_time
            if duration >= 0.05:
                events.append({
                    'time': note_start_time,
                    'type': 'on',
                    'note': midi_note,
                    'velocity': 100
                })
                events.append({
                    'time': note_end_time,
                    'type': 'off',
                    'note': midi_note,
                    'velocity': 0
                })
    
    # Sort events by time
    events.sort(key=lambda x: x['time'])
    
    # Convert to MIDI events with delta times
    ticks_per_second = 480 * 2  # 120 BPM = 2 beats per second
    last_time = 0
    
    for event in events:
        delta_ticks = int((event['time'] - last_time) * ticks_per_second)
        last_time = event['time']
        
        # Variable-length quantity for delta time
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
        
        track_data.extend(delta_bytes)
        
        if event['type'] == 'on':
            track_data.append(0x90)  # Note on, channel 0
        else:
            track_data.append(0x80)  # Note off, channel 0
        
        track_data.append(event['note'])
        track_data.append(event['velocity'])
    
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
    output_path = r'C:\stack\arg\tapes_man_2\formant_notes.mid'
    with open(output_path, 'wb') as f:
        f.write(header)
        f.write(track_chunk)
    
    print(f"MIDI file saved to: {output_path}")
    print(f"Total events: {len(events)}")
    print(f"Total notes: {len(events)//2}")

# Also create a version with sustained tones only (low freq)
print("\n=== Creating sustained tones MIDI ===")

# Detect sustained tones in low frequency range
f_min, f_max = 100, 1000
mask = (freqs >= f_min) & (freqs <= f_max)
S_db_low = S_db[mask, :]
freqs_low = freqs[mask]

# Find sustained tones by looking at peaks
peaks_all = []
for t in range(0, S_db_low.shape[1], 100):  # Sample every 100 frames
    spectrum = S_db_low[:, t]
    peaks, props = sig.find_peaks(spectrum, height=np.max(spectrum)-15, distance=10, prominence=5)
    for p in peaks:
        freq = freqs_low[p]
        midi = 69 + 12 * np.log2(freq / 440.0)
        peaks_all.append({'time': times[t], 'freq': freq, 'midi': round(midi)})

# Group close MIDI notes
note_groups = {}
for peak in peaks_all:
    midi = int(peak['midi'])
    if midi not in note_groups:
        note_groups[midi] = []
    note_groups[midi].append(peak['time'])

print("Detected sustained MIDI notes:")
for midi, times_list in sorted(note_groups.items()):
    if len(times_list) >= 3:  # At least 3 detections
        print(f"  MIDI {midi} ({librosa.midi_to_note(midi)}): {len(times_list)} detections")

print("\nDone!")
