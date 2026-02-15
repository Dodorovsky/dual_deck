import numpy as np
import uuid
import os

def save_waveform(waveform_array):
    """Save waveform to disk and return the path."""
    if not os.path.exists("waveforms"):
        os.makedirs("waveforms")

    filename = f"wf_{uuid.uuid4().hex}.npy"
    path = os.path.join("waveforms", filename)

    np.save(path, waveform_array)
    return path