from dual_deck.audio_engine import AudioEngine





class Deck:
    def __init__(self, audio_engine=None):
        self._audio_engine = audio_engine
        self._track_path = None
        self._is_playing = False
        self._is_paused = False
        self._position = 0
        self._volume = 1.0
        self._pitch = 1.0
        self.cue_position = 0
        


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

    def load(self, track_path):
        self._track_path = track_path
        self._is_playing = False
        self._is_paused = False
        self._position = 0
        if self._audio_engine:
            self._audio_engine.load(track_path)

    def play(self):
        if not self.is_loaded():
            return  

        self._is_playing = True
        self._is_paused = False

        if self._audio_engine:
            self._audio_engine.play()
            print("Playing")
            
    def set_pitch(self, pitch):
        self._pitch = pitch
        if self._audio_engine:
            self._audio_engine.set_pitch(pitch)
            
    def set_pitch_range(self, r):
        if self._audio_engine:
            self._audio_engine.set_pitch_range(r)
        
    def set_pitch_slider(self, value):
        if self._audio_engine:
            self._audio_engine.set_pitch_slider(value)

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
        if hasattr(other_deck, "original_bpm") and hasattr(self, "original_bpm"):
            ratio = other_deck.original_bpm / self.original_bpm
            self.set_pitch_slider((ratio - 1.0) / self.pitch_range)



class DualDeck:
    def __init__(self, audio_engine_cls=None):
        self.deck_a = Deck(audio_engine_cls() if audio_engine_cls else None)
        self.deck_b = Deck(audio_engine_cls() if audio_engine_cls else None)
        self.crossfader = 0.5  # 0 = A, 1 = B
        self.active_deck = "A"


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



