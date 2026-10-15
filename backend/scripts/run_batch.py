"""Submit a JSON array of requests to a running local API and save job responses."""
import argparse, json, time
from pathlib import Path
import urllib.request

def main():
    p=argparse.ArgumentParser(); p.add_argument('requests',type=Path); p.add_argument('--url',default='http://127.0.0.1:8000'); p.add_argument('--out',type=Path,default=Path('reports/batch.json')); a=p.parse_args()
    rows=json.loads(a.requests.read_text(encoding='utf-8')); out=[]
    for i,body in enumerate(rows):
        req=urllib.request.Request(a.url+'/api/v1/music/jobs',data=json.dumps(body).encode(),headers={'Content-Type':'application/json','Idempotency-Key':f'batch-{i}'},method='POST')
        try:
            with urllib.request.urlopen(req) as r: out.append(json.loads(r.read()))
        except Exception as e: out.append({'error':str(e),'request':body})
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(out,indent=2),encoding='utf-8')
if __name__=='__main__': main()
