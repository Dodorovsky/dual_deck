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
        self._fade_samples_remaining = 0
        self._fade_total_samples = 0
        self._fade_mode = None  # "out" | "in"
        self._pending_jump_frame = None
        self._pending_jump_frame = None

        self._fade_mode = None              # None | "out" | "in"
        self._fade_frames_total = 0
        self._fade_frames_remaining = 0


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
                
            # --- CLICKLESS JUMP FADE (int16) ---
            if self._fade_mode is not None and len(chunk) > 0:
                frames_in_chunk = len(chunk) // bytes_per_frame
                if frames_in_chunk > 0:
                    # reshape to (frames, channels)
                    audio = np.frombuffer(chunk, dtype=np.int16).reshape(-1, self._channels).astype(np.float32)

                    if self._fade_mode == "out":
                        # ramp from current level to 0 over remaining frames
                        n = min(frames_in_chunk, self._fade_frames_remaining)
                        if n > 0:
                            ramp = np.linspace(1.0, 0.0, num=n, endpoint=True, dtype=np.float32)[:, None]
                            audio[:n] *= ramp
                            self._fade_frames_remaining -= n

                        # When fade-out finished, execute jump and start fade-in
                        if self._fade_frames_remaining <= 0:
                            if self._pending_jump_frame is not None:
                                target = float(self._pending_jump_frame)
                                self._pending_jump_frame = None

                                # Execute jump (frames -> byte position)
                                new_byte_pos = int(target * bytes_per_frame)
                                new_byte_pos = max(0, min(new_byte_pos, len(self._raw_data)))
                                self._byte_position = new_byte_pos
                                self._playhead = float(target)

                            self._fade_mode = "in"
                            self._fade_frames_remaining = self._fade_frames_total

                    elif self._fade_mode == "in":
                        n = min(frames_in_chunk, self._fade_frames_remaining)
                        if n > 0:
                            ramp = np.linspace(0.0, 1.0, num=n, endpoint=True, dtype=np.float32)[:, None]
                            audio[:n] *= ramp
                            self._fade_frames_remaining -= n

                        if self._fade_frames_remaining <= 0:
                            self._fade_mode = None

                    # back to int16 bytes
                    audio = np.clip(audio, -32768, 32767).astype(np.int16)
                    chunk = audio.tobytes()
                
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
        
    def jump_with_fade(self, target_frame: float, fade_ms: int = 10):
        if self._raw_data is None:
            return

        # number of frames for fade
        fade_frames = int((fade_ms / 1000.0) * self._frame_rate)
        fade_frames = max(1, fade_frames)

        # we save “pending jump”
        self._pending_jump_frame = float(target_frame)

        # we activate fade out
        self._fade_mode = "out"
        self._fade_total_samples = fade_frames
        self._fade_samples_remaining = fade_frames        
        
    def jump_with_fade(self, target_frame: float, fade_ms: int = 10):
        """
        Schedule a playback jump with a short fade-out/fade-in to avoid clicks.
        target_frame is in FRAMES (same unit as _playhead).
        """
        if self._raw_data is None:
            return

        fade_frames = int((fade_ms / 1000.0) * self._frame_rate)
        fade_frames = max(1, fade_frames)

        self._pending_jump_frame = float(target_frame)

        # Start fade out
        self._fade_mode = "out"
        self._fade_frames_total = fade_frames
        self._fade_frames_remaining = fade_frames
    
    
    
    