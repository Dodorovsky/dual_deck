import threading
import audioop
import pyaudio
import librosa
import soundfile as sf
from pydub import AudioSegment
import numpy as np
import math

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
        self.keylock = False

        self._byte_position = 0
        self.state = "stopped"
        self._pyaudio = pyaudio.PyAudio()
        self._stream = None
        self._thread = None
        self._stop_flag = False
        self._playhead = 0.0  # position in frames, not bytes
        
        self._vu = 0.0
        
        self._loop_in = None
        self._loop_out = None
        self._loop_enabled = False
        
        # clickless jump state
        self._pending_jump_frame = None
        self._fade_mode = None              # None | "out" | "in"
        self._fade_frames_total = 0
        self._fade_frames_remaining = 0
        
        # --- DJ Filter (one-knob) ---
        self._filter_value = 0.0
        self._filter_mode = None            # None | "lp" | "hp"
        self._filter_cutoff_hz = 0.0

        # biquad state per channel: x1,x2,y1,y2
        self._bx1 = np.zeros(self._channels, dtype=np.float32)
        self._bx2 = np.zeros(self._channels, dtype=np.float32)
        self._by1 = np.zeros(self._channels, dtype=np.float32)
        self._by2 = np.zeros(self._channels, dtype=np.float32)
        
        self._transport_lock = threading.Lock()
        self._seek_request = None  # tuple(frame:int, fade_ms:int)
        
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
        
        self.reset_filter_state()
        self._thread = threading.Thread(target=self._play_loop, daemon=True, name="AudioEngineThread")
        self._thread.start()
            
    def pause(self):
        if self.state != "playing":
            return

        self._stop_flag = True
        
        with self._transport_lock:
            self._seek_request = None
            self._pending_jump_frame = None
            self._fade_mode = None
            self._fade_frames_remaining = 0
            self._fade_frames_total = 0
                
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
        
        with self._transport_lock:
            self._seek_request = None
            self._pending_jump_frame = None
            self._fade_mode = None
            self._fade_frames_remaining = 0
            self._fade_frames_total = 0
                
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
    
    def jump_with_fade(self, target_frame: float, fade_ms: int = 12):
        if self._raw_data is None:
            return

        fade_frames = int((fade_ms / 1000.0) * self._frame_rate)
        fade_frames = max(1, fade_frames)

        bytes_per_frame = self._sample_width * self._channels
        total_frames = len(self._raw_data) // bytes_per_frame
        if total_frames <= 0:
            return

        # ✅ cuantiza a frame entero y clamp
        target_frame = int(round(float(target_frame)))
        target_frame = max(0, min(target_frame, total_frames - 1))

        self._pending_jump_frame = target_frame  # ✅ guarda int

        self._fade_mode = "out"
        self._fade_frames_total = fade_frames
        self._fade_frames_remaining = fade_frames

    def _int16_bytes_to_audio(self, chunk: bytes):
        """bytes -> np.float32 shaped (frames, channels) and frames count."""
        samples_total = len(chunk) // 2  # int16 samples
        samples_total -= (samples_total % self._channels)
        if samples_total <= 0:
            return None
        audio = np.frombuffer(chunk[:samples_total * 2], dtype=np.int16) \
                .reshape(-1, self._channels).astype(np.float32)
        return audio

    def _audio_to_int16_bytes(self, audio: np.ndarray) -> bytes:
        """np.float32 (frames, channels) -> int16 bytes"""
        audio = np.clip(audio, -32768, 32767).astype(np.int16)
        return audio.tobytes()

    def _apply_volume(self, chunk: bytes) -> bytes:
        if self._volume != 1.0:
            return audioop.mul(chunk, self._sample_width, self._volume)
        return chunk
    
    def _apply_pitch(self, chunk: bytes) -> bytes:
        if self._pitch == 1.0:
            return chunk

        new_rate = int(self._frame_rate / self._pitch)
        pitched, _ = audioop.ratecv(
            chunk,
            self._sample_width,
            self._channels,
            self._frame_rate,
            new_rate,
            None
        )
        return pitched
    
    def _update_vu(self, chunk: bytes) -> None:
        # chunk es int16 interleaved
        samples = np.frombuffer(chunk, dtype=np.int16).astype(np.float32)
        if samples.size == 0:
            self._vu = 0.0
            return
        rms = np.sqrt(np.mean(samples ** 2))
        self._vu = min(rms / 32768.0, 1.0)
        
    def _apply_filter(self, chunk: bytes) -> bytes:
        if self._filter_mode is None or self._filter_cutoff_hz <= 0:
            return chunk

        coeffs = self._biquad_coeffs(self._filter_mode, self._filter_cutoff_hz, q=0.707)
        if coeffs is None:
            return chunk

        audio = self._int16_bytes_to_audio(chunk)
        if audio is None:
            return chunk

        b0, b1, b2, a1, a2 = coeffs

        for ch in range(self._channels):
            x1 = self._bx1[ch]; x2 = self._bx2[ch]
            y1 = self._by1[ch]; y2 = self._by2[ch]

            for i in range(audio.shape[0]):
                x0 = audio[i, ch]
                y0 = b0*x0 + b1*x1 + b2*x2 - a1*y1 - a2*y2
                audio[i, ch] = y0
                x2, x1 = x1, x0
                y2, y1 = y1, y0

            self._bx1[ch], self._bx2[ch] = x1, x2
            self._by1[ch], self._by2[ch] = y1, y2

        return self._audio_to_int16_bytes(audio)
        
    def _apply_fade_and_jump(self, chunk: bytes):
        if self._fade_mode is None or len(chunk) == 0:
            return chunk, False

        audio = self._int16_bytes_to_audio(chunk)
        if audio is None:
            return chunk, False

        frames_in_chunk = audio.shape[0]
        bytes_per_frame = self._sample_width * self._channels
        jumped = False

        if self._fade_mode == "out":
            n = min(frames_in_chunk, self._fade_frames_remaining)
            if n > 0:
                ramp = np.linspace(1.0, 0.0, num=n, endpoint=True, dtype=np.float32)[:, None]
                audio[:n] *= ramp
                self._fade_frames_remaining -= n

            if self._fade_frames_remaining <= 0:
                if self._pending_jump_frame is not None:
                    target = self._pending_jump_frame
                    self._pending_jump_frame = None

                    new_byte_pos = int(target) * bytes_per_frame
                    new_byte_pos = max(0, min(new_byte_pos, len(self._raw_data)))

                    with self._transport_lock:
                        self._byte_position = new_byte_pos
                        self._playhead = float(target)

                    jumped = True

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

        chunk = self._audio_to_int16_bytes(audio)
        return chunk, jumped
        
    def _maybe_schedule_loop_wrap(self, original_chunk_len_bytes: int, bytes_per_frame: int, loop_fade_ms: int):
        frames_in_original = original_chunk_len_bytes // bytes_per_frame
        if self._loop_enabled and self._loop_in is not None and self._loop_out is not None:
            if self._loop_out > self._loop_in and self._fade_mode is None:
                if (self._playhead + frames_in_original) >= self._loop_out:
                    self.jump_with_fade(self._loop_in, fade_ms=loop_fade_ms)
    
    def _write_chunk(self, chunk: bytes) -> bool:
        try:
            self._stream.write(chunk)
            return True
        except Exception as e:
            print("[audio] stream.write error:", e)
            return False

    def _advance_positions(self, original_chunk_len_bytes: int, bytes_per_frame: int):
        frames_played = original_chunk_len_bytes // bytes_per_frame
        with self._transport_lock:
            self._playhead += frames_played
            self._byte_position += original_chunk_len_bytes

    def _play_loop(self):
        chunk_frames = 1024
        bytes_per_frame = self._sample_width * self._channels
        loop_fade_ms = 20

        while True:
            with self._transport_lock:
                if self._stop_flag or self._raw_data is None or self._byte_position >= len(self._raw_data):
                    break
                start = self._byte_position
                end = start + chunk_frames * bytes_per_frame

            original_chunk = self._raw_data[start:end]
            if len(original_chunk) == 0:
                break
        
            # --- Apply pending seek request (thread-safe) ---
            with self._transport_lock:
                req = self._seek_request
                self._seek_request = None

            if req is not None:
                target, fade_ms = req
                if fade_ms <= 0:
                    # immediate reposition
                    with self._transport_lock:
                        self._pending_jump_frame = None
                        self._fade_mode = None
                        self._fade_frames_remaining = 0
                        self._fade_frames_total = 0
                        self._playhead = float(target)
                        self._byte_position = int(target * bytes_per_frame)
                    continue
                else:
                    # clickless reposition
                    self.jump_with_fade(target, fade_ms=fade_ms)
                    # let fade logic run this cycle
            
            chunk = original_chunk

            chunk = self._apply_volume(chunk)
            chunk = self._apply_pitch(chunk)

            self._update_vu(chunk)

            chunk = self._apply_filter(chunk)
            chunk, jumped = self._apply_fade_and_jump(chunk)

            self._maybe_schedule_loop_wrap(len(original_chunk), bytes_per_frame, loop_fade_ms)

            with self._transport_lock:
                if self._stop_flag or self._stream is None:
                    break

            if not self._write_chunk(chunk):
                break

            with self._transport_lock:
                if self._stop_flag:
                    break

            # ✅ si hubo jump en este ciclo, NO avances (ya fijaste byte_position/playhead)
            if not jumped:
                self._advance_positions(len(original_chunk), bytes_per_frame)
        
        with self._transport_lock:
            self._stop_flag = True
            if self.state == "playing":
                self.state = "stopped"

    def set_keylock(self, enabled: bool):
        self.keylock = enabled
        
    def set_loop(self, loop_in, loop_out, enabled: bool):
        self._loop_in = None if loop_in is None else float(loop_in)
        self._loop_out = None if loop_out is None else float(loop_out)
        self._loop_enabled = bool(enabled)
        
    def seek_ratio(self, ratio: float, fade_ms: int = 12):
        if self._raw_data is None:
            return

        ratio = max(0.0, min(1.0, float(ratio)))

        bytes_per_frame = self._sample_width * self._channels
        total_frames = len(self._raw_data) // bytes_per_frame
        if total_frames <= 0:
            return

        target = ratio * (total_frames - 1)
        self.seek_frame(target, fade_ms=fade_ms)
        
    def set_filter_knob(self, value: float):
        
        """
        DJ-style filter knob:
        -1..0 = HP (more negative = stronger HP)
        0..1 = LP (more positive = stronger LP)
        """
        v = float(value)
        v = max(-1.0, min(1.0, v))
        self._filter_value = v

        deadzone = 0.02
        if abs(v) < deadzone:
            self._filter_mode = None
            self._filter_cutoff_hz = 0.0
            return

        if v > 0:
            self._filter_mode = "lp"
            # v in (0..1): map to cutoff 18k -> 200 Hz (more v = lower cutoff)
            t = v
            self._filter_cutoff_hz = 18000.0 * ((200.0 / 18000.0) ** t)
        else:
            self._filter_mode = "hp"
            # |v| in (0..1): map to cutoff 20 -> 5000 Hz (more |v| = higher cutoff)
            t = abs(v)
            self._filter_cutoff_hz = 20.0 * ((2000.0 / 20.0) ** t)      
            
    def reset_filter_state(self):
        self._bx1[:] = 0
        self._bx2[:] = 0
        self._by1[:] = 0
        self._by2[:] = 0
        
    def _biquad_coeffs(self, mode: str, fc: float, q: float = 0.707):
        fs = float(self._frame_rate)
        fc = max(20.0, min(fc, fs * 0.45))  # clamp seguro

        w0 = 2.0 * math.pi * (fc / fs)
        cosw0 = math.cos(w0)
        sinw0 = math.sin(w0)
        alpha = sinw0 / (2.0 * q)

        if mode == "lp":
            b0 = (1 - cosw0) / 2
            b1 = 1 - cosw0
            b2 = (1 - cosw0) / 2
            a0 = 1 + alpha
            a1 = -2 * cosw0
            a2 = 1 - alpha

        elif mode == "hp":
            b0 = (1 + cosw0) / 2
            b1 = -(1 + cosw0)
            b2 = (1 + cosw0) / 2
            a0 = 1 + alpha
            a1 = -2 * cosw0
            a2 = 1 - alpha

        else:
            return None

        # normalize (muy importante)
        b0 /= a0; b1 /= a0; b2 /= a0
        a1 /= a0; a2 /= a0

        return (b0, b1, b2, a1, a2)  
    
    def seek_frame(self, target_frame: float, fade_ms: int = 12):
        if self._raw_data is None:
            return

        bytes_per_frame = self._sample_width * self._channels
        total_frames = len(self._raw_data) // bytes_per_frame
        if total_frames <= 0:
            return

        target = int(round(float(target_frame)))
        target = max(0, min(target, total_frames - 1))
        
        if fade_ms <= 0:
            with self._transport_lock:
                self._seek_request = None
                self._pending_jump_frame = None
                self._fade_mode = None
                self._fade_frames_remaining = 0
                self._fade_frames_total = 0
                self._playhead = float(target)
                self._byte_position = int(target * bytes_per_frame)
            return

        with self._transport_lock:
            thread_alive = self._thread is not None and self._thread.is_alive()

            # If there's an active audio thread, enqueue request (thread applies it safely)
            if thread_alive:
                self._seek_request = (target, int(fade_ms))
                return

            # No thread: apply immediately
            self._pending_jump_frame = None
            self._fade_mode = None
            self._fade_frames_remaining = 0
            self._fade_frames_total = 0

            self._playhead = float(target)
            self._byte_position = int(target * bytes_per_frame)
            
    def is_actually_playing(self) -> bool:
        t = self._thread
        return (
            self._raw_data is not None
            and self._stream is not None
            and not self._stop_flag
            and t is not None
            and t.is_alive()
        )        
            
            
            