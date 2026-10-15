from pydantic import BaseModel, Field, field_validator


class Section(BaseModel):
    start_s: float = Field(ge=0)
    mood: str = Field(min_length=1, max_length=120)


class Output(BaseModel):
    sample_rate: int = Field(default=48000, ge=48000, le=48000)
    target_lufs: float = Field(default=-16, ge=-30, le=-8)
    formats: list[str] = ["wav"]


class MusicRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=1000)
    duration_s: float = Field(ge=5, le=300)
    tempo_bpm: int = Field(default=100, ge=40, le=200)
    key: str = "C major"
    sections: list[Section] = []
    loopable: bool = False
    seed: int = 42
    output: Output = Output()
    narration_path: str | None = None

    @field_validator("prompt")
    @classmethod
    def prompt_not_blank(cls, v):
        if not v.strip():
            raise ValueError("prompt must not be blank")
        return v.strip()

    @field_validator("sections")
    @classmethod
    def sections_in_range(cls, v):
        if any(s.start_s >= 300 for s in v):
            raise ValueError("section start must be before track end")
        if any(b.start_s - a.start_s < 1.5 for a,b in zip(v, v[1:])):
            raise ValueError("sections must be at least 1.5 seconds apart")
        return sorted(v, key=lambda s:s.start_s)

    @field_validator("sections")
    @classmethod
    def section_starts_before_track_end(cls, v, info):
        duration = info.data.get("duration_s")
        if duration is not None and any(s.start_s >= duration for s in v):
            raise ValueError("section start must be before track end")
        return v
