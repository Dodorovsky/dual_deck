class AudioEngine:
    def __init__(self):
        self.duration = 0
        self.position = 0
        self.state = "stopped"   # "playing", "paused", "stopped"

    def load(self, file_path: str) -> float:
        # Fictitious duration for now
        self.duration = 180.0
        self.position = 0
        self.state = "stopped"
        return self.duration

    def play(self):
        if self.duration > 0:
            self.state = "playing"

    def pause(self):
        if self.state == "playing":
            self.state = "paused"

    def stop(self):
        if self.duration > 0:
            self.state = "stopped"
            self.position = 0

    def update(self, delta: float):
        if self.state == "playing":
            self.position += delta
            if self.position > self.duration:
                self.position = self.duration
                self.state = "stopped"

    def get_position(self) -> float:
        return self.position
