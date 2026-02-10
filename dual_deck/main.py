from dual_deck.ui import start_ui
from dual_deck.audio_engine import AudioEngine
from dual_deck.deck import DualDeck

dual = DualDeck(audio_engine_cls=AudioEngine)


if __name__ == "__main__":
    start_ui()
