import { useEffect, useRef, useState } from 'react'

const defaults = { prompt: '', duration_s: 30, tempo_bpm: 100, key: 'C major', seed: 42, loopable: false }
const stems = [{ name: 'drums', label: 'Drums', color: 'rose' }, { name: 'bass', label: 'Bass', color: 'amber' }, { name: 'harmony', label: 'Harmony', color: 'sage' }]

export default function App() {
  const [form, setForm] = useState(defaults)
  const [sections, setSections] = useState([])
  const [job, setJob] = useState(null)
  const [manifest, setManifest] = useState(null)
  const [activeAudio, setActiveAudio] = useState('mix')
  const [api, setApi] = useState('checking')
  const [error, setError] = useState('')
  const timer = useRef()

  useEffect(() => { fetch('/ready').then(r => setApi(r.ok ? 'online' : 'offline')).catch(() => setApi('offline')) }, [])
  useEffect(() => {
    if (!job || !['queued', 'running'].includes(job.status)) return
    let cancelled = false
    async function poll() {
      try {
        const r = await fetch(`/api/v1/jobs/${job.job_id}`)
        const data = await r.json()
        if (!r.ok) throw new Error(data?.detail?.message || 'Could not read job status')
        if (cancelled) return
        setJob(data)
        if (data.status === 'succeeded') {
          const mr = await fetch(`/api/v1/music/jobs/${data.job_id}/manifest`)
          if (mr.ok) setManifest(await mr.json())
        } else if (data.status === 'failed') setError(data.error?.message || 'Generation failed')
        else timer.current = setTimeout(poll, 900)
      } catch (e) { if (!cancelled) setError(e.message || 'API request failed') }
    }
    timer.current = setTimeout(poll, 400)
    return () => { cancelled = true; clearTimeout(timer.current) }
  }, [job?.job_id, job?.status])

  const set = (name, value) => setForm(v => ({ ...v, [name]: value }))
  const working = job && ['queued', 'running'].includes(job.status)
  const fileBase = job ? `/api/v1/music/jobs/${job.job_id}/files/` : ''
  const audioSrc = activeAudio === 'mix' ? `${fileBase}mix.wav` : `${fileBase}stems/${activeAudio}.wav`

  async function submit(e) {
    e.preventDefault(); setError(''); setManifest(null); setActiveAudio('mix')
    const body = { ...form, sections, output: { sample_rate: 48000, target_lufs: -16, formats: ['wav'] } }
    try {
      const r = await fetch('/api/v1/music/jobs', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Idempotency-Key': crypto.randomUUID() }, body: JSON.stringify(body) })
      const data = await r.json()
      if (!r.ok) throw new Error(data?.detail?.message || JSON.stringify(data?.detail) || 'Could not create job')
      setJob(data)
    } catch (err) { setError(err.message || 'Could not connect to the API') }
  }

  return <div className="shell">
    <header className="topbar">
      <a className="brand" href="#home"><span className="brand-mark">≈</span><b>incubrix<span>audio</span></b><i /> <small>STUDIO</small></a>
      <div className="nav-right"><span className={`api-state ${api}`}><i />{api === 'online' ? 'API connected' : api === 'checking' ? 'Connecting' : 'API offline'}</span><span className="engine-state">LOCAL SYMBOLIC ENGINE</span><a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">API docs ↗</a></div>
    </header>

    <main id="home" className="main">
      <section className="hero"><div className="overline"><i /> BACKGROUND MUSIC GENERATOR</div><h1>Set the scene.<br/><em>Find your sound.</em></h1><p>Describe the atmosphere. Shape the details. Create a layered instrumental track.</p></section>
      <div className="columns">
        <form className="panel composer" onSubmit={submit}>
          <div className="panel-title"><div><span className="step">01</span><h2>Compose a track</h2></div><span className="local-chip">● LOCAL</span></div>
          <label className="label" htmlFor="prompt">Describe your music</label>
          <div className="prompt-box"><textarea id="prompt" required maxLength="1000" rows="4" value={form.prompt} onChange={e => set('prompt', e.target.value)} placeholder="Warm, optimistic acoustic music for a technology product launch…"/><div className="prompt-meta"><span>✦ Be descriptive about mood and energy</span><span>{form.prompt.length}/1000</span></div></div>
          <div className="label settings-label">Track settings</div>
          <div className="settings">
            <label><span>◷ &nbsp;Duration</span><div><input type="number" min="5" max="300" value={form.duration_s} onChange={e => set('duration_s', Number(e.target.value))}/><small>sec</small></div></label>
            <label><span>⌁ &nbsp;Tempo</span><div><input type="number" min="40" max="200" value={form.tempo_bpm} onChange={e => set('tempo_bpm', Number(e.target.value))}/><small>BPM</small></div></label>
            <label><span>♫ &nbsp;Key</span><div><select value={form.key} onChange={e => set('key', e.target.value)}>{['C major','D major','E major','F major','G major','A major','A minor','D minor'].map(k => <option key={k}>{k}</option>)}</select><small>⌄</small></div></label>
            <label><span>◉ &nbsp;Seed</span><div><input type="number" value={form.seed} onChange={e => set('seed', Number(e.target.value))}/></div></label>
          </div>
          <div className="section-head"><div className="label">Mood sections <small>OPTIONAL</small></div><button type="button" onClick={() => setSections(s => [...s, { start_s: s.length ? Number(s.at(-1).start_s) + 5 : 10, mood: '' }])}>＋ Add section</button></div>
          {sections.map((section, i) => <div className="section-row" key={i}><input aria-label="Section start time" type="number" min="0" max={form.duration_s - 1} value={section.start_s} onChange={e => setSections(s => s.map((x,j) => i === j ? {...x,start_s:Number(e.target.value)} : x))}/><span>sec</span><input aria-label="Section mood" placeholder="Describe the mood" value={section.mood} onChange={e => setSections(s => s.map((x,j) => i === j ? {...x,mood:e.target.value} : x))}/><button type="button" title="Remove section" onClick={() => setSections(s => s.filter((_,j) => i !== j))}>×</button></div>)}
          <div className="options"><label className="loop-toggle"><input type="checkbox" checked={form.loopable} onChange={e => set('loopable', e.target.checked)}/><i/><span><b>Loopable</b><small>Check loop boundary</small></span></label><span className="format">〰 &nbsp;WAV&nbsp; · &nbsp;48 kHz</span></div>
          {error && <div className="error"><b>!</b><span>{error}</span><button type="button" onClick={() => setError('')}>×</button></div>}
          <button className="submit" disabled={working || api !== 'online'}>{working ? <><span className="spinner"/> Composing your track…</> : <>✦ &nbsp; Generate music <span>↗</span></>}</button>
          <div className="under-submit">Generated locally · No external model or API calls</div>
        </form>

        <aside className="right-col">
          <section className="panel result"><div className="panel-title"><div><span className="step">02</span><h2>Your track</h2></div>{job && <span className={`badge ${job.status}`}>{job.status}</span>}</div>
            {!job && <div className="empty"><div className="vinyl"><div>≈</div></div><h3>Your next soundtrack<br/>starts with an idea.</h3><p>Describe a mood to create your first track.</p><div className="visualizer">{Array.from({length:36},(_,i)=><i key={i} style={{height:`${8+(i*17%28)}px`}}/>)}</div></div>}
            {working && <div className="progress-view"><div className="pulse-mark">≈</div><h3>{job.status === 'queued' ? 'In the queue' : 'Composing your track'}</h3><p>The engine is arranging your instrumental layers.</p><div className="progress"><i style={{width:`${Math.max(job.progress || 4,4)}%`}}/></div><small>{job.status}<span>{job.progress || 0}%</span></small></div>}
            {job?.status === 'failed' && <div className="failed"><div>×</div><h3>Track generation failed</h3><p>{job.error?.message || error || 'Something went wrong.'}</p><button onClick={() => {setJob(null);setError('')}}>↻ &nbsp;Try another prompt</button></div>}
            {job?.status === 'succeeded' && <div className="track-result">
              <div className="track-meta"><div className="cover">≈</div><div className="track-name"><small>GENERATED INSTRUMENTAL</small><b>{form.prompt}</b><span>{form.duration_s}s &nbsp;·&nbsp; {form.tempo_bpm} BPM &nbsp;·&nbsp; {form.key}</span></div><a className="download" href={`${fileBase}mix.wav`} download title="Download mix">↓</a></div>
              <audio controls key={audioSrc} src={audioSrc}/>
              <div className="visualizer result-wave">{Array.from({length:48},(_,i)=><i key={i} className={i<15?'lit':''} style={{height:`${8+(i*13%27)}px`}}/>)}</div>
              <div className="stem-head"><span>INSTRUMENT STEMS</span><span>3 TRACKS</span></div>
              <div className="stem-list">{stems.map(stem=><div className={`stem ${stem.color} ${activeAudio===stem.name?'selected':''}`} key={stem.name}><button onClick={()=>setActiveAudio(stem.name)}><i>♫</i><b>{stem.label}</b><small>{manifest?.stems?.find(s=>s.name===stem.name)?.gain ?? '—'} gain</small></button><a href={`${fileBase}stems/${stem.name}.wav`} download title={`Download ${stem.label}`}>↓</a></div>)}</div>
              <div className="quality-note">ⓘ &nbsp;Local symbolic composition. Loudness and true-peak measurements are not available in this prototype.</div>
              <a className="manifest" href={`/api/v1/music/jobs/${job.job_id}/manifest`} target="_blank" rel="noreferrer">View music manifest <span>↗</span></a>
            </div>}
          </section>
          <div className="engine-note"><span>◖</span><p><b>Powered by the local symbolic engine</b><br/>Procedurally composed instrument parts. Not a neural text-to-music model.</p></div>
        </aside>
      </div>
      <footer><span>INCUBRIX · AUDIO ENGINE</span><span>LOCAL DEVELOPMENT BUILD · 48 kHz WAV</span></footer>
    </main>
  </div>
}
