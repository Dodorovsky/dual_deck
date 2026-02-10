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

    # --- Initial state ---
    def is_loaded(self):
        return self._track_path is not None

    def is_playing(self):
        return self._is_playing

    def is_paused(self):
        return self._is_paused

    def pause(self):
        if not self._is_playing:
            print("Cannot pause: not playing")
            return  

        self._is_playing = False
        self._is_paused = True

        if self._audio_engine:
            self._audio_engine.pause()

        print(f"[{self._track_path}] Paused")


    def get_position(self):
        return self._position

    def get_volume(self):
        return self._volume

    def get_pitch(self):
        return self._pitch

    def stop(self):
        if not self.is_loaded():
            print("Cannot stop: no track loaded")
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
            print(" Cannot play: no track loaded")
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

class DualDeck:
    def __init__(self, audio_engine_cls=None):
        self.deck_a = Deck(audio_engine_cls() if audio_engine_cls else None)
        self.deck_b = Deck(audio_engine_cls() if audio_engine_cls else None)
        self.crossfader = 0.5  # 0 = A, 1 = B

    def set_crossfader(self, value):
        self.crossfader = value
        # Adjust relative volumes
        self.deck_a.set_volume(1 - value)
        self.deck_b.set_volume(value)


