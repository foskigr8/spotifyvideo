'use client'

import { useEffect, useMemo, useRef, useState, useCallback } from 'react'
import { AnimatePresence } from 'framer-motion'
import type { Cue, Scene, Word } from '@/lib/video/types'
import { segmentTranscript, findSceneAt, activeWordIndex } from '@/lib/video/segmenter'
import { SceneRenderer, TYPE_LABELS } from '@/components/video/SceneRenderer'
import { Stage } from '@/components/video/Stage'
import { Transport } from '@/components/video/Transport'
import { SceneTimeline } from '@/components/video/SceneTimeline'
import { SubtitleBar } from '@/components/video/SubtitleBar'

export default function Home() {
  const [cues, setCues] = useState<Cue[]>([])
  const [words, setWords] = useState<Word[]>([])
  const [scenes, setScenes] = useState<Scene[]>([])
  const [loading, setLoading] = useState(true)

  const [t, setT] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState(1)
  const rafRef = useRef<number | null>(null)
  const lastTickRef = useRef<number>(0)

  useEffect(() => {
    let cancelled = false
    Promise.all([
      fetch('/data/transcript.json').then((r) => r.json()),
      fetch('/data/words.json').then((r) => r.json()),
    ]).then(([c, w]: [Cue[], Word[]]) => {
      if (cancelled) return
      setCues(c)
      setWords(w)
      setScenes(segmentTranscript(c))
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [])

  const duration = useMemo(() => (cues.length ? cues[cues.length - 1].end : 0), [cues])

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
        if (next >= duration) { setPlaying(false); return duration }
        return next
      })
      rafRef.current = requestAnimationFrame(tick)
    }
    rafRef.current = requestAnimationFrame(tick)
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current) }
  }, [playing, speed, duration])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement) return
      if (e.code === 'Space') { e.preventDefault(); setPlaying((p) => !p) }
      else if (e.code === 'ArrowLeft') setT((p) => Math.max(0, p - (e.shiftKey ? 10 : 3)))
      else if (e.code === 'ArrowRight') setT((p) => Math.min(duration, p + (e.shiftKey ? 10 : 3)))
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [duration])

  const activeScene = useMemo(() => findSceneAt(scenes, t), [scenes, t])
  const activeCue = useMemo(() => {
    if (!cues.length) return null
    for (const c of cues) { if (t >= c.start - 0.05 && t < c.end) return c }
    if (t >= cues[cues.length - 1].end) return cues[cues.length - 1]
    return cues[0]
  }, [cues, t])
  const nextCue = useMemo(() => {
    if (!activeCue) return null
    return cues.find((c) => c.idx === activeCue.idx + 1) ?? null
  }, [cues, activeCue])

  const globalProgress = duration ? t / duration : 0
  const wordIdx = useMemo(() => activeWordIndex(words, t), [words, t])
  const onStep = useCallback((delta: number) => setT((p) => Math.max(0, Math.min(duration, p + delta))), [duration])

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center" style={{ background: '#F5F0E8' }}>
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full" style={{ border: '3px solid rgba(26,26,26,0.1)', borderTop: '3px solid #1DB954' }} />
          <p style={{ fontFamily: 'var(--font-mono), monospace', fontSize: '0.75rem', letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(26,26,26,0.5)' }}>
            Loading transcript…
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen" style={{ background: '#F5F0E8', color: '#1A1A1A' }}>
      <div className="relative mx-auto flex min-h-screen max-w-7xl flex-col gap-5 px-4 py-6 md:px-8">
        {/* header */}
        <header className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 style={{ fontFamily: 'var(--font-display), cursive', fontSize: 'clamp(1.4rem, 3vw, 2rem)', fontWeight: 700, color: '#1A1A1A' }}>
              Spotify <span style={{ color: '#1DB954' }}>Video Previewer</span>
            </h1>
            <p style={{ fontFamily: 'var(--font-mono), monospace', fontSize: '0.62rem', letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(26,26,26,0.45)' }}>
              {Math.round(duration / 60)} min · {scenes.length} scenes · {words.length.toLocaleString()} words
            </p>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5" style={{ border: '1.5px solid rgba(26,26,26,0.15)', borderRadius: '999px', background: 'rgba(26,26,26,0.04)' }}>
            <span className="h-2 w-2 rounded-full" style={{ background: '#1DB954' }} />
            <span style={{ fontFamily: 'var(--font-mono), monospace', fontSize: '0.62rem', letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(26,26,26,0.5)' }}>
              audio pending
            </span>
          </div>
        </header>

        {/* main grid */}
        <div className="grid gap-5 lg:grid-cols-[1fr_280px]">
          <div className="flex flex-col gap-4">
            {activeScene && (
              <Stage scene={activeScene} progress={globalProgress}>
                <AnimatePresence mode="wait">
                  <SceneRenderer key={activeScene.id} scene={activeScene} words={words} t={t} />
                </AnimatePresence>
              </Stage>
            )}
            <Transport t={t} duration={duration} playing={playing} speed={speed} onSeek={setT} onTogglePlay={() => setPlaying((p) => !p)} onSpeed={setSpeed} onStep={onStep} />
            <SubtitleBar cue={activeCue} nextCue={nextCue} />
          </div>

          {/* inspector */}
          <aside className="flex flex-col gap-4">
            <div className="rounded-xl p-4" style={{ border: '1.5px solid rgba(26,26,26,0.12)', background: 'rgba(26,26,26,0.03)' }}>
              <h2 style={{ fontFamily: 'var(--font-mono)', fontSize: '0.62rem', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(26,26,26,0.4)', marginBottom: 12 }}>
                Active scene
              </h2>
              {activeScene && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="rounded-md px-2 py-1" style={{ background: 'rgba(29,185,84,0.12)', fontFamily: 'var(--font-mono)', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#1DB954' }}>
                      {TYPE_LABELS[activeScene.type]}
                    </span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'rgba(26,26,26,0.4)' }}>
                      #{activeScene.id}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.85rem', lineHeight: 1.5, color: 'rgba(26,26,26,0.7)' }}>{activeScene.text}</p>
                  <div className="flex justify-between pt-2" style={{ borderTop: '1px solid rgba(26,26,26,0.1)', fontFamily: 'var(--font-mono)', fontSize: '0.62rem', color: 'rgba(26,26,26,0.4)' }}>
                    <span>{activeScene.start.toFixed(2)}s</span>
                    <span>{(activeScene.end - activeScene.start).toFixed(2)}s</span>
                    <span>{activeScene.end.toFixed(2)}s</span>
                  </div>
                </div>
              )}
            </div>

            <div className="rounded-xl p-4" style={{ border: '1.5px solid rgba(26,26,26,0.12)', background: 'rgba(26,26,26,0.03)' }}>
              <h2 style={{ fontFamily: 'var(--font-mono)', fontSize: '0.62rem', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(26,26,26,0.4)', marginBottom: 8 }}>
                Now speaking
              </h2>
              <p style={{ fontFamily: 'var(--font-display), cursive', fontSize: 'clamp(1.2rem, 2.5vw, 1.5rem)', fontWeight: 600, color: '#1DB954' }}>
                {words[wordIdx]?.text ?? '—'}
              </p>
              <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.62rem', color: 'rgba(26,26,26,0.35)', marginTop: 4 }}>
                word {wordIdx.toLocaleString()} / {words.length.toLocaleString()}
              </p>
            </div>

            <div className="rounded-xl p-4" style={{ border: '1.5px solid rgba(26,26,26,0.12)', background: 'rgba(26,26,26,0.03)' }}>
              <h2 style={{ fontFamily: 'var(--font-mono)', fontSize: '0.62rem', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(26,26,26,0.4)', marginBottom: 8 }}>
                Shortcuts
              </h2>
              <ul className="space-y-1.5" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'rgba(26,26,26,0.5)' }}>
                <li className="flex justify-between"><span>Play / pause</span><kbd className="rounded px-1.5" style={{ background: 'rgba(26,26,26,0.08)' }}>Space</kbd></li>
                <li className="flex justify-between"><span>±3s</span><kbd className="rounded px-1.5" style={{ background: 'rgba(26,26,26,0.08)' }}>← →</kbd></li>
                <li className="flex justify-between"><span>±10s</span><kbd className="rounded px-1.5" style={{ background: 'rgba(26,26,26,0.08)' }}>Shift+← →</kbd></li>
              </ul>
            </div>
          </aside>
        </div>

        <SceneTimeline scenes={scenes} t={t} duration={duration} onSeek={setT} activeId={activeScene?.id ?? 0} />

        <footer className="mt-auto pt-2 text-center" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.6rem', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(26,26,26,0.25)' }}>
          Prototype · {scenes.length} scenes auto-segmented from transcript
        </footer>
      </div>
    </div>
  )
}
