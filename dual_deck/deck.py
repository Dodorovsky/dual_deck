class Deck:
    def __init__(self):
        self.file_path = None
        self.duration = 0
        self.position = 0
        self.volume = 1.0
        self.pitch = 1.0
        self.state = "stopped"   # "playing", "paused", "stopped"

    # --- Carga ---
    def load(self, file_path: str):
        self.file_path = file_path
        self.position = 0
        self.state = "stopped"
        # Por ahora no calculamos duración real
        self.duration = 180  # valor ficticio para tests
        # En el futuro: usar audio_engine para obtener duración

    def is_loaded(self):
        return self.file_path is not None

        if self.is_loaded():
            self.state = "playing"

    def pause(self):
        if self.is_loaded() and self.state == "playing":
            self.state = "paused"
            
    def play(self):
        if self.is_loaded():
            self.state = "playing"

    def stop(self):
        if self.is_loaded():
            self.state = "stopped"
            self.position = 0

    def is_playing(self):
        return self.state == "playing"

    def is_paused(self):
        return self.state == "paused"

    def seek(self, seconds: float):
        if self.is_loaded():
            self.position = max(0, min(seconds, self.duration))

    def get_position(self):
        return self.position

    def get_duration(self):
        return self.duration

    def set_volume(self, value: float):
        self.volume = max(0.0, min(value, 1.0))

    def get_volume(self):
        return self.volume

    def set_pitch(self, value: float):
        self.pitch = value

    def get_pitch(self):
        return self.pitch
