import pyaudio
from pydub import AudioSegment
import audioop

class AudioEngine:
    def __init__(self):
        self.duration = 0
        self.position = 0.0
        self.state = "stopped"   # "playing", "paused", "stopped"

        self._audio = None
        self._raw_data = None
        self._frame_rate = 44100
        self._channels = 2
        self._sample_width = 2
        self._volume = 1.0


        self._stream = None
        self._byte_position = 0

        self._pyaudio = pyaudio.PyAudio()

    def load(self, file_path: str) -> float:
        print("AudioEngine.load:", file_path)
        # Reset
        self._byte_position = 0
        self.position = 0
        self.state = "stopped"

        # Load audio
        self._audio = AudioSegment.from_file(file_path)
        self._audio = self._audio.set_frame_rate(self._frame_rate)\
                                 .set_channels(self._channels)\
                                 .set_sample_width(self._sample_width)

        self._raw_data = self._audio.raw_data
        self.duration = len(self._audio) / 1000.0  # ms → seconds

        return self.duration

    def _callback(self, in_data, frame_count, time_info, status):
        bytes_per_frame = self._channels * self._sample_width
        bytes_requested = frame_count * bytes_per_frame

        if self.state != "playing":
            # Silence while paused
            return (b'\x00' * bytes_requested, pyaudio.paContinue)

        start = self._byte_position
        end = start + bytes_requested

        chunk = self._audio.raw_data[self._byte_position:end]

        # Aplicar volumen real
        if self._volume != 1.0:
            chunk = audioop.mul(chunk, self._sample_width, self._volume)


        # Update byte position
        self._byte_position = end

        # Update position in seconds
        self.position = self._byte_position / (self._frame_rate * bytes_per_frame)

        # End of track
        if len(chunk) < bytes_requested:
            self.state = "stopped"
            return (chunk, pyaudio.paComplete)

        return (chunk, pyaudio.paContinue)

    def play(self):
        if self._audio is None:
            return

        # If stopped, restart from beginning
        if self.state == "stopped":
            self._byte_position = 0

        self.state = "playing"

        # Create stream only once
        if self._stream is None:
            self._stream = self._pyaudio.open(
                format=self._pyaudio.get_format_from_width(self._sample_width),
                channels=self._channels,
                rate=self._frame_rate,
                output=True,
                stream_callback=self._callback
            )

        self._stream.start_stream()

    def pause(self):
        if self.state == "playing":
            self.state = "paused"

    def stop(self):
        if self._audio is None:
            return

        self.state = "stopped"
        self.position = 0
        self._byte_position = 0

        if self._stream is not None:
            self._stream.stop_stream()

    def seek(self, position):
        # Clamp
        position = max(0, min(position, self.duration))

        bytes_per_frame = self._channels * self._sample_width
        self._byte_position = int(position * self._frame_rate) * bytes_per_frame
        self.position = position

    def set_volume(self, volume: float):
        # Clamp por seguridad
        self._volume = max(0.0, min(1.0, volume))

    def set_pitch(self, pitch):
        pass  # siguiente fase
