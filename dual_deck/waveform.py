import soundfile as sf
import numpy as np

def load_waveform(path, samples=2000):
    # Leer audio completo
    data, sr = sf.read(path, dtype="float32")

    # Convertir a mono
    if data.ndim > 1:
        data = data.mean(axis=1)

    # Reducir número de muestras
    factor = max(1, len(data) // samples)
    waveform = data[::factor]

    return waveform, sr


