import pytest
from unittest.mock import MagicMock

@pytest.fixture
def audio_engine_mock():
    mock = MagicMock()
    mock.load = MagicMock()
    mock.play = MagicMock()
    mock.pause = MagicMock()
    mock.stop = MagicMock()
    mock.is_playing = MagicMock(return_value=False)
    return mock
 