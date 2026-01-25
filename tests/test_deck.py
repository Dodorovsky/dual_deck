from dual_deck.deck import Deck
from dual_deck.audio_engine import AudioEngine


def test_initial_state():
    deck = Deck()
    assert deck.is_loaded() is False
    assert deck.is_playing() is False
    assert deck.is_paused() is False
    assert deck.get_position() == 0
    assert deck.get_volume() == 1.0      # default volume
    assert deck.get_pitch() == 1.0       # normal pitch (100%)

def test_load_file():
    deck = Deck()
    deck.load("song.mp3")
    assert deck.is_loaded() is True

def test_play_changes_state_to_playing():
    deck = Deck()
    deck.load("song.mp3")
    deck.play()
    assert deck.is_playing() is True
    
def test_play_without_load_does_nothing():
    deck = Deck()
    deck.play()
    assert deck.is_playing() is False

def test_pause_changes_state_to_paused():
    deck = Deck()
    deck.load("song.mp3")
    deck.play()
    deck.pause()
    assert deck.is_paused() is True
    
def test_pause_without_play_does_nothing():
    deck = Deck()
    deck.load("song.mp3")
    deck.pause()
    assert deck.is_paused() is False
    
def test_stop_resets_state_and_position():
    deck = Deck()
    deck.load("song.mp3")
    deck.play()
    deck.seek(45)  # we pretend that it advanced
    deck.stop()
    assert deck.is_playing() is False
    assert deck.is_paused() is False
    assert deck.get_position() == 0

def test_set_volume():
    deck = Deck()
    deck.set_volume(0.7)
    assert deck.get_volume() == 0.7
    
def test_set_pitch():
    deck = Deck() 
    deck.set_pitch(1.2) 
    assert deck.get_pitch() == 1.2

def test_seek_changes_position():
    deck = Deck()
    deck.load("song.mp3")
    deck.seek(30)
    assert deck.get_position() == 30

def test_audio_engine_load_returns_duration():
    engine = AudioEngine()
    duration = engine.load("song.mp3")
    assert duration > 0

def test_audio_engine_update_advances_position():
    engine = AudioEngine()
    engine.load("song.mp3")
    engine.play()
    engine.update(1.0)
    assert engine.get_position() > 0
    
def test_load_returns_duration():
    engine = AudioEngine()
    duration = engine.load("song.mp3")
    assert duration > 0

def test_update_advances_position():
    engine = AudioEngine()
    engine.load("song.mp3")
    engine.play()
    engine.update(1.0)
    assert engine.get_position() > 0

def test_pause_stops_position_advancing():
    engine = AudioEngine()
    engine.load("song.mp3")
    engine.play()
    engine.update(1.0)
    pos_before = engine.get_position()
    engine.pause()
    engine.update(1.0)
    assert engine.get_position() == pos_before

def test_stop_resets_position():
    engine = AudioEngine()
    engine.load("song.mp3")
    engine.play()
    engine.update(1.0)
    engine.stop()
    assert engine.get_position() == 0



