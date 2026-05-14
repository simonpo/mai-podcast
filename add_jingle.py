"""Generate intro/outro jingles and wrap a WAV file."""

import struct
import sys
import wave

import numpy as np


def generate_jingle(sample_rate: int = 24000, duration: float = 3.0) -> np.ndarray:
    """Generate a short upbeat jingle using layered sine waves."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

    # A bright chord progression: C major -> G major (approx 1.5s each)
    half = len(t) // 2

    # C major chord: C4(262), E4(330), G4(392)
    chunk1 = (
        0.3 * np.sin(2 * np.pi * 262 * t[:half])
        + 0.25 * np.sin(2 * np.pi * 330 * t[:half])
        + 0.2 * np.sin(2 * np.pi * 392 * t[:half])
    )

    # G major chord: G4(392), B4(494), D5(587)
    chunk2 = (
        0.3 * np.sin(2 * np.pi * 392 * t[:half])
        + 0.25 * np.sin(2 * np.pi * 494 * t[:half])
        + 0.2 * np.sin(2 * np.pi * 587 * t[:half])
    )

    jingle = np.concatenate([chunk1, chunk2])

    # Add a simple melody on top
    melody_notes = [523, 587, 659, 784, 659, 784, 1047]  # C5 D5 E5 G5 E5 G5 C6
    note_dur = duration / len(melody_notes)
    melody = np.array([], dtype=np.float64)
    for note in melody_notes:
        note_t = np.linspace(0, note_dur, int(sample_rate * note_dur), endpoint=False)
        # Envelope: quick attack, gentle decay
        env = np.exp(-1.5 * note_t / note_dur)
        melody = np.append(melody, 0.35 * np.sin(2 * np.pi * note * note_t) * env)

    # Trim/pad melody to match jingle length
    if len(melody) < len(jingle):
        melody = np.pad(melody, (0, len(jingle) - len(melody)))
    else:
        melody = melody[: len(jingle)]

    mixed = jingle + melody

    # Fade in/out
    fade_samples = int(sample_rate * 0.15)
    mixed[:fade_samples] *= np.linspace(0, 1, fade_samples)
    mixed[-fade_samples:] *= np.linspace(1, 0, fade_samples)

    # Add a brief silence gap after the jingle
    gap = np.zeros(int(sample_rate * 0.5))
    mixed = np.concatenate([mixed, gap])

    # Normalize
    mixed = mixed / np.max(np.abs(mixed)) * 0.7

    return (mixed * 32767).astype(np.int16)


def generate_outro(sample_rate: int = 24000, duration: float = 5.0) -> np.ndarray:
    """Generate a doom-laden outro reminiscent of dark Mordor vibes."""
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

    # Dark drone on D3 (147 Hz) and A2 (110 Hz) with audible overtones
    drone = (
        0.25 * np.sin(2 * np.pi * 110 * t)       # A2
        + 0.30 * np.sin(2 * np.pi * 147 * t)      # D3
        + 0.20 * np.sin(2 * np.pi * 220 * t)      # A3 octave
        + 0.12 * np.sin(2 * np.pi * 294 * t)      # D4 octave
        + 0.08 * np.sin(2 * np.pi * 330 * t)      # E4 — adds tension
    )

    # Slow LFO tremolo for unease
    tremolo = 0.65 + 0.35 * np.sin(2 * np.pi * 1.2 * t)
    drone *= tremolo

    # Ominous descending melody in audible range
    # D5 -> C#5 -> Bb4 -> A4 -> F4 -> E4 -> D4
    melody_freqs = [587, 554, 466, 440, 349, 330, 294]
    note_dur = duration / len(melody_freqs)
    melody = np.array([], dtype=np.float64)
    for freq in melody_freqs:
        note_t = np.linspace(0, note_dur, int(sample_rate * note_dur), endpoint=False)
        env = (1 - np.exp(-5 * note_t / note_dur)) * np.exp(-0.4 * note_t / note_dur)
        tone = 0.35 * np.sin(2 * np.pi * freq * note_t)
        # Dissonant minor second for tension
        tone += 0.12 * np.sin(2 * np.pi * freq * 16 / 15 * note_t)
        melody = np.append(melody, tone * env)

    if len(melody) < len(drone):
        melody = np.pad(melody, (0, len(drone) - len(melody)))
    else:
        melody = melody[: len(drone)]

    # War drums — punchy hits with audible thud + click transient
    drums = np.zeros_like(t)
    hit_times = [0.0, 0.7, 1.0, 1.8, 2.5, 3.0, 3.5, 3.8, 4.3]
    for ht in hit_times:
        idx = int(ht * sample_rate)
        if idx < len(drums):
            hit_len = min(int(0.35 * sample_rate), len(drums) - idx)
            hit_t = np.linspace(0, 0.35, hit_len, endpoint=False)
            # Body: 80 Hz thud
            body = 0.7 * np.sin(2 * np.pi * 80 * hit_t) * np.exp(-6 * hit_t)
            # Attack click: short burst at 400 Hz for transient snap
            click = 0.5 * np.sin(2 * np.pi * 400 * hit_t) * np.exp(-40 * hit_t)
            # Sub-boom
            boom = 0.4 * np.sin(2 * np.pi * 55 * hit_t) * np.exp(-4 * hit_t)
            drums[idx : idx + hit_len] += body + click + boom

    mixed = drone + melody + drums

    # Silence gap before outro
    gap_before = np.zeros(int(sample_rate * 0.8))
    # Long fade out (clamped so it never exceeds the array length)
    fade_len = min(int(sample_rate * 1.5), len(mixed))
    mixed[-fade_len:] *= np.linspace(1, 0, fade_len)
    # Fade in (clamped)
    fade_in = min(int(sample_rate * 0.3), len(mixed))
    mixed[:fade_in] *= np.linspace(0, 1, fade_in)

    mixed = np.concatenate([gap_before, mixed])

    # Normalize
    mixed = mixed / np.max(np.abs(mixed)) * 0.85

    return (mixed * 32767).astype(np.int16)


def wrap_with_jingles(speech_wav: str, output_wav: str) -> None:
    """Read a speech WAV, add intro jingle and doom outro."""
    with wave.open(speech_wav, "rb") as wf:
        params = wf.getparams()
        speech_data = wf.readframes(params.nframes)

    sample_rate = params.framerate

    intro = generate_jingle(sample_rate=sample_rate)
    outro = generate_outro(sample_rate=sample_rate)

    intro_bytes = struct.pack(f"<{len(intro)}h", *intro)
    outro_bytes = struct.pack(f"<{len(outro)}h", *outro)

    with wave.open(output_wav, "wb") as wf:
        wf.setparams(params)
        wf.writeframes(intro_bytes)
        wf.writeframes(speech_data)
        wf.writeframes(outro_bytes)

    print(f"Saved with intro + outro: {output_wav}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python add_jingle.py <input.wav> <output.wav>")
        sys.exit(1)
    wrap_with_jingles(sys.argv[1], sys.argv[2])
