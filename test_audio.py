

from dual_deck.audio_engine import AudioEngine
import time

engine = AudioEngine()
engine.load(r"C:\Users\dodor\Planet.mp3")
engine.play()

print("Playing...")

# Mantener el programa vivo mientras el stream está activo
while engine.state == "playing":
    time.sleep(0.1)

print("Finished")
