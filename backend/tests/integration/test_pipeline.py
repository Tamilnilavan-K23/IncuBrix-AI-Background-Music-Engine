import json, wave
from app.schemas import MusicRequest
from app.services.pipeline import generate

def test_pipeline_emits_three_exact_duration_stems(tmp_path):
    req=MusicRequest(prompt="warm optimistic instrumental",duration_s=5,tempo_bpm=100)
    result=generate(req,tmp_path,"test-job",lambda _:None)
    assert "mix" in result["files"]
    for name in ("mix.wav","stems/drums.wav","stems/bass.wav","stems/harmony.wav"):
        with wave.open(str(tmp_path/name)) as f:
            assert f.getframerate()==48000
            assert abs(f.getnframes()/f.getframerate()-5)<.05
    report=json.loads((tmp_path/"validation_report.json").read_text())
    assert report["stem_count"]==3
    assert report["core_artifact_checks_passed"] is True
    assert report["quality_status"]=="not_measured"
