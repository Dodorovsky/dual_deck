import soundfile as sf
import numpy as np
import dearpygui.dearpygui as dpg
from pydub import AudioSegment

def load_waveform(path, samples=2000):
    # Load audio with pydub (supports MP3)
    audio = AudioSegment.from_file(path)

    # Convertir a numpy
    data = np.array(audio.get_array_of_samples()).astype(np.float32)

    # If stereo, mix to mono
    if audio.channels == 2:
        data = data.reshape((-1, 2))
        data = data.mean(axis=1)

    # Normalize to [-1, 1]
    data /= np.iinfo(audio.array_type).max

    # Reduce number of samples
    factor = max(1, len(data) // samples)
    waveform = data[::factor]

    return waveform, audio.frame_rate

def draw_local_waveform(waveform, position, window_size, tag, width=400, height=60):
    dpg.delete_item(tag, children_only=True)
    dpg.draw_rectangle(
    (0, 0),
    (width, height),
    fill=(0, 0, 0),
    color=(40, 40, 40),   # dark gray border
    thickness=1,
    parent=tag
)

    if waveform is None or len(waveform) < 2:
        return

    # Mixxx style window: starts in position
    start = max(0, min(position, len(waveform) - window_size))
    end = start + window_size
    segment = waveform[start:end]

    if len(segment) < 2:
        return

    mid = height // 2
    step = width / len(segment)

    for i in range(len(segment) - 1):
        x1 = i * step
        y1 = mid - segment[i] * mid
        x2 = (i + 1) * step
        y2 = mid - segment[i + 1] * mid

        dpg.draw_line((x1, y1), (x2, y2),
                      color=(255, 200, 0),
                      thickness=2,
                      parent=tag)

    # Playhead at startup
    dpg.draw_line((0, 0), (0, height),
                  color=(255, 0, 0),
                  thickness=2,
                  parent=tag)

