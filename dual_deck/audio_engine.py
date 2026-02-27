import threading
import audioop
import pyaudio
import librosa
import soundfile as sf
from pydub import AudioSegment
import numpy as np


class AudioEngine:
    def __init__(self):
        self._audio = None
        self._raw_data = None
        self._frame_rate = 44100
        self._channels = 2
        self._sample_width = 2

        self._volume = 1.0
        self._pitch = 1.0
        self.pitch_range = 0.08   # ±8% by default

        self._byte_position = 0
        self.state = "stopped"

        self._pyaudio = pyaudio.PyAudio()
        self._stream = None
        self._thread = None
        self._stop_flag = False
        self.keylock = False
        self._playhead = 0.0  # position in frames, not bytes
        self._vu = 0.0


    def load(self, file_path):

        # If there is a previous stream, close it
        if self._stream is not None:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except:
                pass
            self._stream = None

        # Upload audio
        self._audio = AudioSegment.from_file(file_path)

        self._frame_rate = self._audio.frame_rate
        self._channels = self._audio.channels
        self._sample_width = self._audio.sample_width
        self._raw_data = self._audio.raw_data

        # Reset position
        self._byte_position = 0
        self._playhead = 0.0
        self.state = "stopped"

    def play(self):
        if self._audio is None:
            return
        if self.state == "playing":
            return

        self.state = "playing"
        self._stop_flag = False

        self._stream = self._pyaudio.open(
            format=self._pyaudio.get_format_from_width(self._sample_width),
            channels=self._channels,
            rate=self._frame_rate,
            output=True
        )

        self._thread = threading.Thread(target=self._play_loop, daemon=True, name="AudioEngineThread")
        self._thread.start()
            
        def pause(self):
            if self.state != "playing":
                return

            self._stop_flag = True
            self.state = "paused"

            t = self._thread
            if t is not None and t.is_alive() and t is not threading.current_thread():
                t.join()
            self._thread = None

            if self._stream is not None:
                try:
                    self._stream.stop_stream()
                    self._stream.close()
                except Exception:
                    pass
                self._stream = None
      
    def pause(self):
        if self.state != "playing":
            return

        self._stop_flag = True
        self.state = "paused"

        t = self._thread
        if t is not None and t.is_alive() and t is not threading.current_thread():
            t.join()
        self._thread = None

        if self._stream is not None:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        
    def resume(self):
        if self.state != "paused":
            return

        self._stop_flag = False
        self.state = "playing"

        # reopen stream
        self._stream = self._pyaudio.open(
            format=self._pyaudio.get_format_from_width(self._sample_width),
            channels=self._channels,
            rate=self._frame_rate,
            output=True
        )

        #  launch play thread
        self._thread = threading.Thread(target=self._play_loop)
        self._thread.start()

    def stop(self):
        if self.state not in ("playing", "paused"):
            return

        self._stop_flag = True
        self.state = "stopped"

        t = self._thread
        if t is not None and t.is_alive() and t is not threading.current_thread():
            t.join()
        self._thread = None

        if self._stream is not None:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

        self._byte_position = 0
        self._playhead = 0.0

    def set_pitch(self, pitch):
        self._pitch = max(0.5, min(2.0, pitch))
        
    def set_pitch_range(self, r):
        # r it must be 0.08, 0.16 or 0.50
        self.pitch_range = r
        
    def set_pitch_slider(self, slider_value):
        # slider_value ∈ [-1.0, +1.0]
        self._pitch = 1.0 + (slider_value * self.pitch_range)

    def set_volume(self, vol):
        self._volume = max(0.0, min(1.0, vol))

    def get_position_frames(self):
        return self._playhead

    def _play_loop(self):
        chunk_frames = 1024
        bytes_per_frame = self._sample_width * self._channels

        while not self._stop_flag and self._byte_position < len(self._raw_data):
            start = self._byte_position
            end = start + chunk_frames * bytes_per_frame

            original_chunk = self._raw_data[start:end]
            chunk = original_chunk

            if len(chunk) == 0:
                break

            if self._volume != 1.0:
                chunk = audioop.mul(chunk, self._sample_width, self._volume)

            if self._pitch != 1.0:
                new_rate = int(self._frame_rate / self._pitch)
                chunk, _ = audioop.ratecv(
                    chunk,
                    self._sample_width,
                    self._channels,
                    self._frame_rate,
                    new_rate,
                    None
                )

            samples = np.frombuffer(chunk, dtype=np.int16).astype(np.float32)
            rms = np.sqrt(np.mean(samples**2))
            self._vu = min(rms / 32768.0, 1.0)

            # If stop/pause closes the stream, write can throw exception.
            # In that case, we leave the clean loop.
            try:
                self._stream.write(chunk)
            except Exception as e:
                print("[audio] stream.write error:", e)
                break

            frames_played = len(original_chunk) // bytes_per_frame
            self._playhead += frames_played
            self._byte_position += len(original_chunk)

        self._stop_flag = True

    def set_keylock(self, enabled: bool):
        self.keylock = enabled