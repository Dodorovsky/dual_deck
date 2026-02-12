import threading
import audioop
import pyaudio
import librosa
import soundfile as sf
from pydub import AudioSegment


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


    def load(self, file_path):
        # Load full audio for playback (pydub)
        self._audio = AudioSegment.from_file(file_path)

        self._frame_rate = self._audio.frame_rate
        self._channels = self._audio.channels
        self._sample_width = self._audio.sample_width
        self._raw_data = self._audio.raw_data

        self._byte_position = 0
        self.state = "stopped"

        # --- FAST LOADING FOR BPM ANALYSIS ---
        # Read only 60 seconds
        with sf.SoundFile(file_path) as f:
            sr = f.samplerate
            frames = sr * 60
            y = f.read(frames, dtype='float32')

        # Convert to mono if stereo
        if y.ndim > 1:
            y = y.mean(axis=1)

        # Detect BPM
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        self.original_bpm = float(tempo)
        self.bpm = float(tempo)  



    def play(self):
        if self._audio is None:
            return

        if self.state == "playing":
            return

        self.state = "playing"
        self._stop_flag = False

        #  open stream
        self._stream = self._pyaudio.open(
            format=self._pyaudio.get_format_from_width(self._sample_width),
            channels=self._channels,
            rate=self._frame_rate,
            output=True
        )

        # throw thread
        self._thread = threading.Thread(target=self._play_loop)
        self._thread.start()
        
    def pause(self):
        if self.state != "playing":
            return

        self._stop_flag = True
        self.state = "paused"
        
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
        self._stop_flag = True
        self.state = "stopped"

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

    def _play_loop(self):
        chunk_frames = 1024
        bytes_per_frame = self._sample_width * self._channels

        while not self._stop_flag and self._byte_position < len(self._raw_data):
            start = self._byte_position
            end = start + chunk_frames * bytes_per_frame
            chunk = self._raw_data[start:end]

            if len(chunk) == 0:
                break

            # volumen
            if self._volume != 1.0:
                chunk = audioop.mul(chunk, self._sample_width, self._volume)

            # classic pitch
            if self._pitch != 1.0:
                new_rate = int(self._frame_rate * self._pitch)
                chunk, _ = audioop.ratecv(
                    chunk,
                    self._sample_width,
                    self._channels,
                    self._frame_rate,
                    new_rate,
                    None
                )

            try:
                self._stream.write(chunk)
            except Exception:
                break

            self._byte_position += chunk_frames * bytes_per_frame

        self._stream.stop_stream()
        self._stream.close()
        self.state = "stopped"


    def set_keylock(self, enabled: bool):
        self.keylock = enabled


