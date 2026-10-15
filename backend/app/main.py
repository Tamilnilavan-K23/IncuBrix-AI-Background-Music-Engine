from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse

from app.schemas import MusicRequest
from app.services.pipeline import generate

DATA = Path(os.getenv("MUSIC_DATA_DIR", "./data")).resolve()
OUTPUTS = DATA / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.INFO, format='{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s"}')
log = logging.getLogger("incubrix")
pool = ThreadPoolExecutor(max_workers=int(os.getenv("MUSIC_WORKERS", "2")))
jobs: dict[str, dict] = {}
idem: dict[str, tuple[str, str]] = {}
lock = threading.Lock()
app = FastAPI(title="IncuBrix Background Music Engine", version="1.0.0", openapi_version="3.1.0")


def _run(job_id: str, req: MusicRequest) -> None:
    with lock:
        jobs[job_id].update(status="running", progress=5)
    try:
        result = generate(req, OUTPUTS / job_id, job_id, lambda p: jobs[job_id].update(progress=p))
        with lock:
            jobs[job_id].update(status="succeeded", progress=100, result=result, error=None)
    except Exception as exc:
        log.exception("job failed job_id=%s", job_id)
        with lock:
            jobs[job_id].update(status="failed", progress=100, error={"code":"GENERATION_FAILED","message":str(exc),"retryable":False,"details":{}})


@app.get("/health")
def health():
    return {"status":"alive"}


@app.get("/ready")
def ready():
    return {"status":"ready","backend":os.getenv("MUSIC_BACKEND","symbolic")}


@app.post("/api/v1/music/jobs", status_code=202)
def create_job(req: MusicRequest, idempotency_key: str = Header(..., alias="Idempotency-Key")):
    digest = hashlib.sha256(req.model_dump_json().encode()).hexdigest()
    with lock:
        if idempotency_key in idem:
            old_digest, old_id = idem[idempotency_key]
            if old_digest != digest:
                raise HTTPException(409, detail={"code":"IDEMPOTENCY_CONFLICT","message":"Key was used with a different request","retryable":False,"details":{}})
            return {"job_id":old_id,"status":jobs[old_id]["status"],"progress":jobs[old_id]["progress"]}
        job_id = str(uuid.uuid4())
        jobs[job_id] = {"job_id":job_id,"status":"queued","progress":0,"error":None,"result":None}
        idem[idempotency_key] = (digest, job_id)
    log.info("job queued job_id=%s correlation_id=%s", job_id, idempotency_key)
    pool.submit(_run, job_id, req)
    return {"job_id":job_id,"status":"queued","progress":0}


@app.get("/api/v1/jobs/{job_id}")
def get_job(job_id: str):
    with lock:
        job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, detail={"code":"JOB_NOT_FOUND","message":"Job not found","retryable":False,"details":{}})
    response = {k:v for k,v in job.items() if k != "result"}
    if job["result"]:
        response["result"] = {"manifest_url":f"/api/v1/music/jobs/{job_id}/manifest", "files":job["result"]["files"]}
    return response


@app.get("/api/v1/music/jobs/{job_id}/manifest")
def manifest(job_id: str):
    path = OUTPUTS / job_id / "music_manifest.json"
    if not path.exists():
        raise HTTPException(404, detail={"code":"MANIFEST_NOT_FOUND","message":"Manifest unavailable","retryable":False,"details":{}})
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/v1/music/jobs/{job_id}/files/{file_name}")
def download(job_id: str, file_name: str):
    base = (OUTPUTS / job_id).resolve()
    path = (base / file_name).resolve()
    if base not in path.parents or not path.is_file():
        raise HTTPException(404, detail={"code":"FILE_NOT_FOUND","message":"File not found","retryable":False,"details":{}})
    return FileResponse(path)
