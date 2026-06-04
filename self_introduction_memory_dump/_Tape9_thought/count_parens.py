line = "            midi_note = int(round(librosa.hz_to_midi(librosa.note_to_hz('A2') * (2 ** (np.median(peak_bin[start:j]) / 12.0))))"
print('open:', line.count('('))
print('close:', line.count(')'))
