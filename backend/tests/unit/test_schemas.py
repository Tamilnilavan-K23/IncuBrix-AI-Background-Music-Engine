import pytest
from pydantic import ValidationError
from app.schemas import MusicRequest

def test_short_duration_allowed():
    assert MusicRequest(prompt="gentle", duration_s=5).duration_s == 5

def test_empty_prompt_rejected():
    with pytest.raises(ValidationError):
        MusicRequest(prompt="  ", duration_s=5)

def test_duration_bounds():
    with pytest.raises(ValidationError):
        MusicRequest(prompt="music", duration_s=301)

def test_close_sections_rejected():
    with pytest.raises(ValidationError):
        MusicRequest(prompt="music", duration_s=10, sections=[{"start_s":1,"mood":"calm"},{"start_s":2,"mood":"bright"}])
