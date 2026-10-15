from fastapi.testclient import TestClient
from app.main import app

def test_job_lifecycle_without_external_credentials():
    c=TestClient(app)
    response=c.post('/api/v1/music/jobs',headers={'Idempotency-Key':'e2e-test'},json={'prompt':'gentle instrumental test','duration_s':5})
    assert response.status_code==202
    job=response.json()['job_id']
    import time
    for _ in range(1200):
        state=c.get(f'/api/v1/jobs/{job}').json()
        if state['status'] in ('succeeded','failed'): break
        time.sleep(.05)
    assert state['status']=='succeeded'
    assert c.get(f'/api/v1/music/jobs/{job}/manifest').status_code==200

def test_idempotency_replay_returns_same_job_and_conflict_is_clear():
    c=TestClient(app)
    h={'Idempotency-Key':'e2e-duplicate'}
    body={'prompt':'soft music','duration_s':5}
    first=c.post('/api/v1/music/jobs',headers=h,json=body)
    second=c.post('/api/v1/music/jobs',headers=h,json=body)
    changed=c.post('/api/v1/music/jobs',headers=h,json={**body,'tempo_bpm':120})
    assert first.status_code==second.status_code==202
    assert first.json()['job_id']==second.json()['job_id']
    assert changed.status_code==409
