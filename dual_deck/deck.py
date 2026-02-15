from dual_deck.audio_engine import AudioEngine
import dearpygui.dearpygui as dpg
from dual_deck.waveform import load_waveform
import numpy as np
from .analysis import analyze_track
from .library import get_all_tracks



class Deck:
    def __init__(self, prefix, audio_engine=None):
        self.prefix = prefix
        self._audio_engine = audio_engine
        self._track_path = None
        self._is_playing = False
        self._is_paused = False
        self._position = 0
        self._volume = 1.0
        self._pitch = 1.0
        self.cue_position = 0
        self.original_bpm = None
        self.current_bpm = None
        self.pitch_range = 0.08   
        self.waveform = None

    # --- Initial state ---
    def is_loaded(self):
        return self._track_path is not None

    def is_playing(self):
        return self._is_playing

    def is_paused(self):
        return self._is_paused

    def pause(self):
        if not self._is_playing:
            return  

        self._is_playing = False
        self._is_paused = True

        if self._audio_engine:
            self._audio_engine.pause()
            
    def resume(self):
        if self._audio_engine:
            self._audio_engine.resume()

    def get_position(self):
        return self._position

    def get_volume(self):
        return self._volume

    def get_pitch(self):
        return self._pitch

    def stop(self):
        if not self.is_loaded():
            return
        self._is_playing = False
        self._is_paused = False
        self._position = 0

        if self._audio_engine:
            self._audio_engine.stop()

    def seek(self, position):
        self._position = position
        if self._audio_engine:
            self._audio_engine.seek(position)

    def set_volume(self, volume):
        self._volume = volume
        if self._audio_engine:
            self._audio_engine.set_volume(volume)

    # --- From the previous test ---
    @property
    def current_track(self):
        return self._track_path
    
    def load(self, path):
        self.load_track(path)

    def load_track(self, path):
        self._track_path = path
        # 1. Search the library
        tracks = get_all_tracks()
        track_data = next((t for t in tracks if t[4] == path), None)

        if track_data is None:
            print("[deck] Track not in library. Analyzing...")
            analysis = analyze_track(path)
            self.bpm = analysis["bpm"]
            print("[DEBUG] analysis =", analysis)

            self.bpm = analysis["bpm"]
            self.original_bpm = self.bpm
            self.current_bpm = self.bpm
            try:
                dpg.set_value(f"{self.prefix}_bpm_label", f"{self.current_bpm:.2f} BPM")
            except:
                pass
            
            self.duration = analysis["duration"]
            self.waveform_path = analysis["waveform_path"]

            # waveform from analysis
            self.waveform = analysis["waveform"]

        else:
            print("[deck] Track found in library.")
            _, title, bpm, duration, waveform_path = track_data

            self.bpm = bpm
            self.duration = duration
            self.waveform_path = waveform_path
            
            self.original_bpm = self.bpm
            self.current_bpm = self.bpm


            # load waveform from disk
            self.waveform = np.load(waveform_path)

        # 2. Load audio into the engine
        self._audio_engine.load(path)

        print("[deck] Track loaded successfully.")
    
    def _update_ui(self):
        # update internal position
        self._position = self.position

        # update local wave
        try:
            dpg.set_value(f"{self.prefix}_local_wave", self._position)
        except:
            pass


    @property
    def position(self):
        eng = self._audio_engine
        if eng is None or self.waveform is None or eng._raw_data is None:
            return 0

        bytes_per_frame = eng._sample_width * eng._channels
        total_frames = len(eng._raw_data) // bytes_per_frame
        if total_frames == 0:
            return 0

        wf_index = int(len(self.waveform) * eng._playhead / total_frames)
        return max(0, min(wf_index, len(self.waveform) - 1))

    def play(self):
        if not self.is_loaded():
            return  

        self._is_playing = True
        self._is_paused = False

        if self._audio_engine:
            self._audio_engine.play()
            print("Playing")
            
        dpg.set_frame_callback(self._update_ui)

            
    def set_pitch(self, pitch):
        self._pitch = pitch

        if self._audio_engine:
            self._audio_engine.set_pitch(pitch)

        if self.original_bpm:
            self.current_bpm = self.original_bpm * pitch
            dpg.set_value(f"{self.prefix}_bpm_label", f"{self.current_bpm:.2f} BPM")
          
    def set_pitch_range(self, r):
        self.pitch_range = r
        if self._audio_engine:
            self._audio_engine.set_pitch_range(r)
        
    def set_pitch_slider(self, slider_value):
        self._pitch_slider_value = slider_value
        self._audio_engine.set_pitch_slider(slider_value)

        if self.original_bpm:
            self.current_bpm = self.original_bpm * self._audio_engine._pitch
            dpg.set_value(f"{self.prefix}_bpm_label", f"{self.current_bpm:.2f} BPM")

    def set_cue(self):
        self.cue_position = self._audio_engine._byte_position
        
    def goto_cue(self):
        self._audio_engine._byte_position = self.cue_position

    def cue_play(self):
        self.goto_cue()
        self.play()

    def cue_stop(self):
        self.stop()
        self.goto_cue()

    def sync_to(self, other_deck):
        if not self.original_bpm or not other_deck.current_bpm:
            return

        target_bpm = other_deck.current_bpm
        ratio = target_bpm / self.original_bpm

        # aplicar pitch REAL al motor
        self.set_pitch(ratio)




class DualDeck:
    def __init__(self, audio_engine_cls=None):
        self.deck_a = Deck("A", audio_engine_cls() if audio_engine_cls else None)
        self.deck_b = Deck("B", audio_engine_cls() if audio_engine_cls else None)

        self.crossfader = 0.5  # 0 = A, 1 = B
        self.active_deck = "A"
        self.master_volume = 1.0   # 100%
        
    def set_crossfader(self, value):
        self.crossfader = value
        # Adjust relative volumes
        self.deck_a.set_volume(1 - value)
        self.deck_b.set_volume(value)

    def set_active_deck(self, deck_id):
        self.active_deck = deck_id  # "A" o "B"

    def set_pitch_slider(self, value):
        if self.active_deck == "A":
            self.deck_a.set_pitch_slider(value)
        else:
            self.deck_b.set_pitch_slider(value)

    def set_pitch_range(self, r):
        if self.active_deck == "A":
            self.deck_a.set_pitch_range(r)
        else:
            self.deck_b.set_pitch_range(r)

    def _active_deck(self):
        return self.deck_a if self.crossfader < 0.5 else self.deck_b

    def get_pitch(self):
        return self._active_deck()._pitch

    def update(self):
        self.deck_a._position = self.deck_a.position
        self.deck_b._position = self.deck_b.position


