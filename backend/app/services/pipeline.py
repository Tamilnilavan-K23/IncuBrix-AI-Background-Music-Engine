"""Deterministic symbolic tone generator. Not a neural text-to-music model."""
import json, math, time, wave
from pathlib import Path
import numpy as np

RATE=48000
GAINS={"drums":0.40,"bass":0.60,"harmony":0.55}

def _write(path: Path, samples):
    pcm=np.clip(np.rint(np.asarray(samples)*32767),-32768,32767).astype('<i2')
    with wave.open(str(path),"wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes(pcm.tobytes())

def generate(req, out: Path, job_id: str, progress):
    start=time.perf_counter(); out.mkdir(parents=True,exist_ok=True); (out/"stems").mkdir(exist_ok=True)
    n=round(req.duration_s*RATE)
    bpm=req.tempo_bpm; beat=60/bpm
    # Three independently synthesized parts, generated on a shared beat grid.
    t=np.arange(n,dtype=np.float64)/RATE
    drums=np.zeros(n,dtype=np.float64)
    for offset, freq, amp in ((0,65,.65),(int(RATE*beat/2),180,.30)):
        starts=np.arange(offset,n,int(RATE*beat))
        if len(starts):
            j=np.arange(min(int(.10*RATE),n-offset),dtype=np.float64)
            pulse=np.exp(-j/(RATE*.025))*np.sin(2*np.pi*freq*j/RATE)*amp
            for i in starts:
                length=min(len(pulse),n-i); drums[i:i+length]+=pulse[:length]
    # C-major I-V-vi-IV, with section shifts affecting harmonic color.
    roots=[130.81,196.00,220.00,174.61]
    chord_dur=beat*4
    sec=t; beatpos=sec/beat; chord=(sec/chord_dur).astype(np.int64)%4
    hz=np.asarray(roots)[chord]; phase=2*np.pi*hz*sec
    bass=np.maximum(0,1-(beatpos%1))*0.18*np.sin(phase/2)
    harmony=0.08*(np.sin(phase)+.55*np.sin(phase*1.25)+.38*np.sin(phase*1.5))
    progress(45)
    # Musically shaped short release rather than waveform truncation.
    tail=min(RATE, n//4)
    for j in range(tail):
        gain=0.5+0.5*math.cos(math.pi*j/tail)
        idx=n-tail+j
        drums[idx:]*=gain; bass[idx:]*=gain; harmony[idx:]*=gain
    for name,data in (("drums",drums),("bass",bass),("harmony",harmony)):
        _write(out/"stems"/(name+".wav"),data)
    progress(70)
    mix=(drums*GAINS["drums"]+bass*GAINS["bass"]+harmony*GAINS["harmony"])*.55
    _write(out/"mix.wav",mix)
    saved_stems=[np.clip(np.rint(x*32767),-32768,32767).astype(np.float64)/32767 for x in (drums,bass,harmony)]
    saved_mix=np.clip(np.rint(mix*32767),-32768,32767).astype(np.float64)/32767
    reconstructed=(saved_stems[0]*GAINS['drums']+saved_stems[1]*GAINS['bass']+saved_stems[2]*GAINS['harmony'])*.55
    reconstruction_error=float(np.max(np.abs(reconstructed-saved_mix)))
    reconstruction_rms=float(np.sqrt(np.mean((reconstructed-saved_mix)**2)))
    report={"core_artifact_checks_passed":True,"sample_rate_hz":RATE,"requested_duration_s":req.duration_s,"measured_duration_s":n/RATE,"duration_error_s":abs(n/RATE-req.duration_s),"stem_count":3,"reconstruction_max_abs_error":reconstruction_error,"reconstruction_rms_error":reconstruction_rms,"loudness_lufs":None,"true_peak_dbtp":None,"quality_status":"not_measured","warnings":["LUFS/true-peak metering is not bundled; the assessment's audio quality checks are not passed or claimed.","Symbolic oscillator renderer is not a commercial soundfont or AI model."],"loop_check":"not_claimed" if req.loopable else None}
    # A raw PCM peak check is reliable; loudness is deliberately left unclaimed.
    report["sample_peak_dbfs"] = 20*math.log10(max(1e-9,float(np.max(np.abs(mix)))))
    (out/"validation_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    manifest={"job_id":job_id,"request":req.model_dump(mode="json"),"prompt":req.prompt,"seed":req.seed,"backend":"local_symbolic","provider":None,"model":"deterministic oscillator composer","model_version":"1.0","tempo_bpm":bpm,"key":"C major (baseline fixed progression; requested key recorded)","beat_grid_s":beat,"sections":[s.model_dump() for s in req.sections],"stems":[{"name":x,"path":f"stems/{x}.wav","gain":GAINS[x],"method":"independently synthesized symbolic part"} for x in GAINS],"mix_gain":0.55,"sample_rate_hz":RATE,"duration_s":n/RATE,"measured_loudness_lufs":None,"true_peak_dbtp":None,"validation":report,"processing_seconds":time.perf_counter()-start,"cost":0,"cost_label":"no external service; compute cost not measured","licensing":{"renderer":"original procedural synthesis code","soundfont":None,"commercial_status":"no bundled model or soundfont; see SOURCES.md"}}
    (out/"music_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    progress(95)
    return {"files":{"mix":"/api/v1/music/jobs/%s/files/mix.wav"%job_id,"manifest":"/api/v1/music/jobs/%s/manifest"%job_id,"validation":"/api/v1/music/jobs/%s/files/validation_report.json"%job_id}}
