from dual_deck.deck import Deck, DualDeck
from dual_deck.audio_engine import AudioEngine


def test_initial_state():
    deck = Deck()
    assert deck.is_loaded() is False
    assert deck.is_playing() is False
    assert deck.is_paused() is False
    assert deck.get_position() == 0
    assert deck.get_volume() == 1.0     
    assert deck.get_pitch() == 1.0       

def test_load_file():
    deck = Deck()
    deck.load("song.mp3")
    assert deck.is_loaded() is True

def test_play_changes_state_to_playing(audio_engine_mock):
    deck = Deck(audio_engine=audio_engine_mock)
    deck.load("song.mp3")

    deck.play()

    assert deck.is_playing() is True
    assert deck.is_paused() is False
    audio_engine_mock.play.assert_called_once()

def test_play_without_load_does_nothing():
    deck = Deck()
    deck.play()
    assert deck.is_playing() is False

def test_pause_changes_state_to_paused(audio_engine_mock):
    deck = Deck(audio_engine=audio_engine_mock)
    deck.load("song.mp3")
    deck.play()

    deck.pause()

    assert deck.is_paused() is True
    assert deck.is_playing() is False
    audio_engine_mock.pause.assert_called_once()
   
def test_pause_without_play_does_nothing():
    deck = Deck()
    deck.load("song.mp3")
    deck.pause()
    assert deck.is_paused() is False
    
def test_stop_resets_state_and_position(audio_engine_mock):
    deck = Deck(audio_engine=audio_engine_mock)
    deck.load("song.mp3")
    deck.play()
    deck.seek(45)
    deck.stop()

    assert deck.is_playing() is False
    assert deck.is_paused() is False
    assert deck.get_position() == 0
    audio_engine_mock.stop.assert_called_once()

def test_set_volume(audio_engine_mock):
    deck = Deck(audio_engine=audio_engine_mock)

    deck.set_volume(0.5)

    assert deck.get_volume() == 0.5
    audio_engine_mock.set_volume.assert_called_once_with(0.5)
   
def test_set_pitch(audio_engine_mock):
    deck = Deck(audio_engine=audio_engine_mock)

    deck.set_pitch(0.8)

    assert deck.get_pitch() == 0.8
    audio_engine_mock.set_pitch.assert_called_once_with(0.8)

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

def test_deck_loads_track(audio_engine_mock):
    deck = Deck(audio_engine=audio_engine_mock)

    deck.load("song.mp3")

    assert deck.current_track == "song.mp3"
    audio_engine_mock.load.assert_called_once_with("song.mp3")
    assert deck.is_playing() is False

def test_crossfader():
    dd = DualDeck()
    dd.set_crossfader(0.0)
    assert dd.deck_a.get_volume() == 1.0
    assert dd.deck_b.get_volume() == 0.0

 