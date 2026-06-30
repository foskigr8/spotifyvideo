'use client'

import { useEffect, useMemo, useRef, useState, useCallback } from 'react'
import { DoodleCanvas, type SceneWindow } from '@/components/video/DoodleCanvas'
import { Transport } from '@/components/video/Transport'

interface Cue {
  idx: number
  start: number
  end: number
  text: string
}

interface ScenesFile {
  scenes: SceneWindow[]
}

export default function Home() {
  const [cues, setCues] = useState<Cue[]>([])
  const [scenes, setScenes] = useState<SceneWindow[]>([])
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)

  const [t, setT] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState(1)
  const [replayKey, setReplayKey] = useState(0)
  const rafRef = useRef<number | null>(null)
  const lastTickRef = useRef<number>(0)

  useEffect(() => {
    let cancelled = false
    Promise.all([
      fetch('/data/transcript.json').then((r) => r.json()),
      fetch('/data/scenes_preview.json').then((r) => {
        if (!r.ok) throw new Error('no scenes_preview.json yet')
        return r.json()
      }),
    ])
      .then(([c, s]: [Cue[], ScenesFile]) => {
        if (cancelled) return
        setCues(c)
        setScenes(s.scenes.sort((a, b) => a.time_start - b.time_start))
        setLoading(false)
      })
      .catch(() => {
        if (cancelled) return
        setNotFound(true)
        setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  // Only as long as the hand-authored / GLM-generated windows cover — this
  // previewer plays exactly what's in scenes_preview.json, nothing further.
  const duration = useMemo(() => (scenes.length ? scenes[scenes.length - 1].time_end : 0), [scenes])

  useEffect(() => {
    if (!playing) {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
      return
    }
    lastTickRef.current = performance.now()
    const tick = (now: number) => {
      const dt = (now - lastTickRef.current) / 1000
      lastTickRef.current = now
      setT((prev) => {
        const next = prev + dt * speed
        if (next >= duration) {
          setPlaying(false)
          return duration
        }
        return next
      })
      rafRef.current = requestAnimationFrame(tick)
    }
    rafRef.current = requestAnimationFrame(tick)
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, [playing, speed, duration])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement) return
      if (e.code === 'Space') {
        e.preventDefault()
        setPlaying((p) => !p)
      } else if (e.code === 'ArrowLeft') {
        setT((p) => Math.max(0, p - (e.shiftKey ? 9 : 3)))
        setReplayKey((k) => k + 1)
      } else if (e.code === 'ArrowRight') {
        setT((p) => Math.min(duration, p + (e.shiftKey ? 9 : 3)))
        setReplayKey((k) => k + 1)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [duration])

  const activeScene = useMemo(
    () => scenes.find((s) => t >= s.time_start && t < s.time_end) ?? scenes[scenes.length - 1] ?? null,
    [scenes, t]
  )

  const activeCue = useMemo(() => {
    if (!cues.length) return null
    for (const c of cues) {
      if (t >= c.start - 0.05 && t < c.end) return c
    }
    return cues[cues.length - 1]
  }, [cues, t])

  const onSeek = useCallback((newT: number) => {
    setT(newT)
    setReplayKey((k) => k + 1)
  }, [])

  const onStep = useCallback(
    (delta: number) => {
      setT((p) => Math.max(0, Math.min(duration, p + delta)))
      setReplayKey((k) => k + 1)
    },
    [duration]
  )

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center" style={{ background: '#F5F0E8' }}>
        <div className="text-center">
          <div
            className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full"
            style={{ border: '3px solid rgba(26,26,26,0.1)', borderTop: '3px solid #1DB954' }}
          />
          <p
            style={{
              fontFamily: 'var(--font-mono), monospace',
              fontSize: '0.75rem',
              letterSpacing: '0.2em',
              textTransform: 'uppercase',
              color: 'rgba(26,26,26,0.5)',
            }}
          >
            Loading scenes…
          </p>
        </div>
      </div>
    )
  }

  if (notFound || !scenes.length) {
    return (
      <div className="flex min-h-screen items-center justify-center px-6" style={{ background: '#F5F0E8' }}>
        <div className="max-w-md text-center">
          <p style={{ fontFamily: 'var(--font-display), cursive', fontSize: '1.8rem', color: '#1A1A1A', marginBottom: 12 }}>
            No scenes yet
          </p>
          <p style={{ fontFamily: 'var(--font-mono), monospace', fontSize: '0.8rem', color: 'rgba(26,26,26,0.55)', lineHeight: 1.6 }}>
            public/data/scenes_preview.json is missing or empty. Generate it (hand-authored
            or via the GLM pipeline) and reload.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen" style={{ background: '#F5F0E8', color: '#1A1A1A' }}>
      <div className="relative mx-auto flex min-h-screen max-w-4xl flex-col gap-5 px-4 py-6 md:px-8">
        {/* header */}
        <header className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1
              style={{
                fontFamily: 'var(--font-display), cursive',
                fontSize: 'clamp(1.4rem, 3vw, 2rem)',
                fontWeight: 700,
                color: '#1A1A1A',
              }}
            >
              Spotify <span style={{ color: '#1DB954' }}>Doodle Previewer</span>
            </h1>
            <p
              style={{
                fontFamily: 'var(--font-mono), monospace',
                fontSize: '0.62rem',
                letterSpacing: '0.2em',
                textTransform: 'uppercase',
                color: 'rgba(26,26,26,0.45)',
              }}
            >
              {scenes.length} windows · {Math.round(duration)}s previewed
            </p>
          </div>
        </header>

        {/* canvas stage */}
        <div
          className="relative w-full overflow-hidden rounded-xl"
          style={{
            border: '2px solid rgba(26,26,26,0.12)',
            boxShadow: '0 20px 60px -20px rgba(0,0,0,0.25)',
            aspectRatio: '16 / 9',
          }}
        >
          <DoodleCanvas scene={activeScene} replayKey={replayKey} playing={playing} speed={speed} />
          <div
            className="absolute left-3 top-3 rounded-full px-2.5 py-1"
            style={{
              background: 'rgba(255,255,255,0.85)',
              fontFamily: 'var(--font-mono), monospace',
              fontSize: '0.6rem',
              letterSpacing: '0.15em',
              textTransform: 'uppercase',
              color: 'rgba(26,26,26,0.55)',
            }}
          >
            window {activeScene?.window_index ?? '–'}
          </div>
        </div>

        <Transport
          t={t}
          duration={duration}
          playing={playing}
          speed={speed}
          onSeek={onSeek}
          onTogglePlay={() => setPlaying((p) => !p)}
          onSpeed={setSpeed}
          onStep={onStep}
        />

        {/* current phrase + cue */}
        <div
          className="rounded-xl px-6 py-4 text-center"
          style={{ border: '1.5px solid rgba(26,26,26,0.12)', background: 'rgba(26,26,26,0.03)' }}
        >
          <p
            style={{
              fontFamily: 'var(--font-display), cursive',
              fontSize: 'clamp(1.1rem, 2vw, 1.6rem)',
              fontWeight: 600,
              color: '#1A1A1A',
              minHeight: '2rem',
            }}
          >
            {activeCue?.text ?? '—'}
          </p>
        </div>

        {/* scene strip */}
        <div className="rounded-xl p-3" style={{ border: '1.5px solid rgba(26,26,26,0.12)', background: 'rgba(26,26,26,0.03)' }}>
          <div className="mb-2 flex items-center justify-between px-1">
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.6rem',
                letterSpacing: '0.2em',
                textTransform: 'uppercase',
                color: 'rgba(26,26,26,0.4)',
              }}
            >
              Windows
            </span>
          </div>
          <div className="flex h-10 gap-[2px] overflow-hidden rounded-md">
            {scenes.map((s) => {
              const w = ((s.time_end - s.time_start) / duration) * 100
              const active = s === activeScene
              return (
                <button
                  key={s.window_index}
                  onClick={() => onSeek(s.time_start + 0.01)}
                  title={s.phrase}
                  style={{
                    width: `${w}%`,
                    background: active ? '#1DB954' : 'rgba(29,185,84,0.25)',
                  }}
                />
              )
            })}
          </div>
        </div>

        <footer
          className="mt-auto pt-2 text-center"
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.6rem',
            letterSpacing: '0.25em',
            textTransform: 'uppercase',
            color: 'rgba(26,26,26,0.25)',
          }}
        >
          Pure-canvas doodle renderer · driven by scenes_preview.json
        </footer>
      </div>
    </div>
  )
}
