# Main script for the channeled music player

import numpy as np
import pyaudio
import argparse

# --- Constants ---
SAMPLE_RATE = 44100
# --- Note Frequencies (in Hz) ---
NOTE_FREQUENCIES = {
    'C': 261.63, 'C#': 277.18, 'D': 293.66, 'D#': 311.13, 'E': 329.63, 'F': 349.23,
    'F#': 369.99, 'G': 392.00, 'G#': 415.30, 'A': 440.00, 'A#': 466.16, 'B': 493.88
}

def generate_wave(frequency, duration):
    """
    Generates a sine wave for a given frequency and duration.
    """
    if frequency == 0:  # Rest
        return np.zeros(int(duration * SAMPLE_RATE))

    t = np.linspace(0, duration, int(duration * SAMPLE_RATE), False)
    wave = 0.5 * np.sin(2 * np.pi * frequency * t)
    return wave.astype(np.float32)

def play_audio(stream, wave):
    """
    Plays a wave on the given audio stream.
    """
    stream.write(wave.tobytes())

def parse_notation(notation):
    """
    Parses the music notation and returns a list of (frequency, duration) tuples.
    """
    notes = []
    parts = notation.split()

    current_octave = 4  # Default octave
    i = 0
    while i < len(parts):
        part = parts[i]

        if part.startswith('^'):
            current_octave += 1
            part = part[1:]
        elif part.startswith("'"):
            current_octave -= 1
            part = part[1:]

        note_name = part.upper()

        if note_name in NOTE_FREQUENCIES:
            frequency = NOTE_FREQUENCIES[note_name] * (2 ** (current_octave - 4))
            duration = 0.25  # Default duration

            # Check for a duration modifier
            if i + 1 < len(parts) and parts[i+1].isdigit():
                duration = 1.0 / int(parts[i+1])
                i += 1

            notes.append((frequency, duration))
        elif note_name == 'R':
            duration = 0.25  # Default duration

            # Check for a duration modifier
            if i + 1 < len(parts) and parts[i+1].isdigit():
                duration = 1.0 / int(parts[i+1])
                i += 1

            notes.append((0, duration))
        else:
            raise ValueError(f"Invalid syntax: '{part}'")

        i += 1

    return notes

def get_output_device_index(p):
    """
    Finds the index of the first available output device.
    """
    for i in range(p.get_device_count()):
        dev_info = p.get_device_info_by_index(i)
        if dev_info['maxOutputChannels'] > 0:
            return i
    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Channeled Music Player")
    parser.add_argument("file", nargs="?", help="A file containing the music notation to play.")
    args = parser.parse_args()

    if args.file:
        with open(args.file, 'r') as f:
            notation = f.read()
    else:
        notation = "C 4 D 4 E 4 F 4 G 4 A 4 B 4"

    try:
        parsed_notes = parse_notation(notation)
    except ValueError as e:
        print(f"Error: {e}")
        exit()

    p = pyaudio.PyAudio()

    output_device_index = get_output_device_index(p)
    if output_device_index is None:
        print("No output device found.")
        p.terminate()
        exit()

    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=SAMPLE_RATE,
                    output=True,
                    output_device_index=output_device_index)

    for frequency, duration in parsed_notes:
        wave = generate_wave(frequency, duration)
        play_audio(stream, wave)

    stream.stop_stream()
    stream.close()
    p.terminate()
