import librosa
import os
import numpy as np

from .waveform import generate_waveform

from .save_waveform import save_waveform
from .library import add_track




def analyze_track(path):
    """
    Analyze a track:
    - Load audio
    - Calculate BPM
    - Generate waveform
    - Save waveform to disk
    - Save track info to library
    - Return analysis data
    """

    if not os.path.exists(path):
        raise FileNotFoundError(f"Track not found: {path}")

    # Load audio with librosa
    print(f"[analysis] Loading {path}...")
    samples, sr = librosa.load(path, sr=None, mono=True)

    # Duration in seconds
    duration = librosa.get_duration(y=samples, sr=sr)

    # BPM detection
    print("[analysis] Calculating BPM...")
    tempo, _ = librosa.beat.beat_track(y=samples, sr=sr)
    bpm = float(tempo)

    # Generate waveform (global)
    print("[analysis] Generating waveform...")
    waveform_array = generate_waveform(samples)

    # Save waveform to disk
    waveform_path = save_waveform(waveform_array)

    # Extract title from filename
    title = os.path.basename(path)

    # Save to library
    print("[analysis] Saving to library...")
    add_track(
        path=path,
        title=title,
        bpm=bpm,
        duration=duration,
        waveform_path=waveform_path
    )

    # Return analysis data for deck loading
    return {
        "path": path,
        "title": title,
        "bpm": bpm,
        "duration": duration,
        "waveform_path": waveform_path,
        "sample_rate": sr,
        "samples": samples,
        "waveform": waveform_array
    }

