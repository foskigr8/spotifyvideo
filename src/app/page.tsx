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

  // ---- load data ----
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
    return () => {
      cancelled = true
    }
  }, [])

  const duration = useMemo(() => (cues.length ? cues[cues.length - 1].end : 0), [cues])

  // ---- playback clock ----
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

  // ---- keyboard shortcuts ----
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement) return
      if (e.code === 'Space') {
        e.preventDefault()
        setPlaying((p) => !p)
      } else if (e.code === 'ArrowLeft') {
        setT((p) => Math.max(0, p - (e.shiftKey ? 10 : 3)))
      } else if (e.code === 'ArrowRight') {
        setT((p) => Math.min(duration, p + (e.shiftKey ? 10 : 3)))
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [duration])

  const activeScene = useMemo(() => findSceneAt(scenes, t), [scenes, t])
  const activeCue = useMemo(() => {
    if (!cues.length) return null
    for (const c of cues) {
      if (t >= c.start - 0.05 && t < c.end) return c
    }
    // if past last
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
      <div className="flex min-h-screen items-center justify-center bg-[#0A0A0A] text-white/50">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-2 border-white/20 border-t-[#1DB954]" />
          <p className="font-mono text-sm uppercase tracking-widest">Loading transcript…</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#0A0A0A] text-white">
      {/* ambient glow */}
      <div className="pointer-events-none fixed inset-0 opacity-60">
        <div className="absolute left-1/2 top-0 h-[400px] w-[800px] -translate-x-1/2 rounded-full bg-[#1DB954]/10 blur-[120px]" />
      </div>

      <div className="relative mx-auto flex min-h-screen max-w-7xl flex-col gap-5 px-4 py-6 md:px-8">
        {/* header */}
        <header className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="font-display text-xl font-bold tracking-tight md:text-2xl">
              Spotify Video <span className="text-[#1DB954]">Previewer</span>
            </h1>
            <p className="font-mono text-[0.65rem] uppercase tracking-[0.2em] text-white/40">
              {Math.round(duration / 60)} min · {scenes.length} scenes · {words.length.toLocaleString()} words · word-synced
            </p>
          </div>
          <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5">
            <span className="h-2 w-2 rounded-full bg-[#1DB954]" />
            <span className="font-mono text-[0.65rem] uppercase tracking-widest text-white/50">
              audio pending
            </span>
          </div>
        </header>

        {/* main grid */}
        <div className="grid gap-5 lg:grid-cols-[1fr_280px]">
          {/* stage + transport */}
          <div className="flex flex-col gap-4">
            {activeScene && (
              <Stage scene={activeScene} progress={globalProgress}>
                <AnimatePresence mode="wait">
                  <SceneRenderer key={activeScene.id} scene={activeScene} words={words} t={t} />
                </AnimatePresence>
              </Stage>
            )}
            <Transport
              t={t}
              duration={duration}
              playing={playing}
              speed={speed}
              onSeek={setT}
              onTogglePlay={() => setPlaying((p) => !p)}
              onSpeed={setSpeed}
              onStep={onStep}
            />
            <SubtitleBar cue={activeCue} nextCue={nextCue} />
          </div>

          {/* inspector */}
          <aside className="flex flex-col gap-4">
            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
              <h2 className="mb-3 font-mono text-[0.65rem] uppercase tracking-[0.25em] text-white/40">
                Active scene
              </h2>
              {activeScene && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="rounded-md bg-[#1DB954]/15 px-2 py-1 font-mono text-[0.7rem] font-bold uppercase tracking-wider text-[#1DB954]">
                      {TYPE_LABELS[activeScene.type]}
                    </span>
                    <span className="font-mono text-xs text-white/40">
                      #{activeScene.id}
                    </span>
                  </div>
                  <p className="text-sm leading-relaxed text-white/70">{activeScene.text}</p>
                  <div className="flex justify-between border-t border-white/10 pt-2 font-mono text-[0.65rem] text-white/40">
                    <span>{activeScene.start.toFixed(2)}s</span>
                    <span>{(activeScene.end - activeScene.start).toFixed(2)}s</span>
                    <span>{activeScene.end.toFixed(2)}s</span>
                  </div>
                </div>
              )}
            </div>

            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
              <h2 className="mb-3 font-mono text-[0.65rem] uppercase tracking-[0.25em] text-white/40">
                Now speaking
              </h2>
              <p className="font-display text-lg font-semibold text-[#1DB954]">
                {words[wordIdx]?.text ?? '—'}
              </p>
              <p className="mt-1 font-mono text-[0.65rem] text-white/35">
                word {wordIdx.toLocaleString()} / {words.length.toLocaleString()}
              </p>
            </div>

            <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
              <h2 className="mb-3 font-mono text-[0.65rem] uppercase tracking-[0.25em] text-white/40">
                Shortcuts
              </h2>
              <ul className="space-y-1.5 font-mono text-[0.7rem] text-white/50">
                <li className="flex justify-between"><span>Play / pause</span><kbd className="rounded bg-white/10 px-1.5">Space</kbd></li>
                <li className="flex justify-between"><span>±3s</span><kbd className="rounded bg-white/10 px-1.5">← →</kbd></li>
                <li className="flex justify-between"><span>±10s</span><kbd className="rounded bg-white/10 px-1.5">Shift+← →</kbd></li>
              </ul>
            </div>
          </aside>
        </div>

        {/* full-width timeline */}
        <SceneTimeline scenes={scenes} t={t} duration={duration} onSeek={setT} activeId={activeScene?.id ?? 0} />

        {/* footer note */}
        <footer className="mt-auto pt-2 text-center font-mono text-[0.6rem] uppercase tracking-[0.25em] text-white/25">
          Prototype · motion-graphics pipeline · {scenes.length} scenes auto-segmented from transcript
        </footer>
      </div>
    </div>
  )
}
