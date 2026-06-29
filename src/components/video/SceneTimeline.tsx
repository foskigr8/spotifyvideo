'use client'

import { useEffect, useRef } from 'react'
import type { Scene } from '@/lib/video/types'
import { TYPE_COLORS, TYPE_LABELS } from './SceneRenderer'

interface Props {
  scenes: Scene[]
  t: number
  duration: number
  onSeek: (t: number) => void
  activeId: number
}

// A horizontal strip of all scenes (colored by type, sized by duration).
// Click to seek. Auto-scrolls to follow the playhead.
export function SceneTimeline({ scenes, t, duration, onSeek, activeId }: Props) {
  const trackRef = useRef<HTMLDivElement>(null)
  const playheadRef = useRef<HTMLDivElement>(null)

  // auto-scroll to keep playhead visible
  useEffect(() => {
    const track = trackRef.current
    const playhead = playheadRef.current
    if (!track || !playhead) return
    const trackRect = track.getBoundingClientRect()
    const phRect = playhead.getBoundingClientRect()
    const playheadLeft = phRect.left - trackRect.left
    const target = playheadLeft - trackRect.width / 2
    track.scrollTo({ left: track.scrollLeft + target, behavior: 'smooth' })
  }, [activeId])

  const playheadPct = (t / duration) * 100

  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3">
      <div className="mb-2 flex items-center justify-between px-1">
        <span className="font-mono text-[0.65rem] uppercase tracking-[0.25em] text-white/40">
          Scene timeline · {scenes.length} scenes
        </span>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          {Object.entries(TYPE_LABELS).map(([type, label]) => (
            <span key={type} className="flex items-center gap-1 font-mono text-[0.6rem] uppercase tracking-wider text-white/40">
              <span className="h-2 w-2 rounded-sm" style={{ background: TYPE_COLORS[type as Scene['type']] }} />
              {label}
            </span>
          ))}
        </div>
      </div>
      <div ref={trackRef} className="relative h-14 overflow-x-auto overflow-y-hidden rounded-md bg-black/30">
        <div className="relative flex h-full min-w-full items-stretch" style={{ width: 'max-content', minWidth: '100%' }}>
          {scenes.map((s) => {
            const w = Math.max(2, ((s.end - s.start) / duration) * 10000)
            const active = s.id === activeId
            return (
              <button
                key={s.id}
                onClick={() => onSeek(s.start + 0.01)}
                title={`#${s.id} ${TYPE_LABELS[s.type]} · ${s.text.slice(0, 60)}`}
                className="group relative shrink-0 border-r border-black/40 transition-all"
                style={{
                  width: `${w}px`,
                  background: active ? TYPE_COLORS[s.type] : `${TYPE_COLORS[s.type]}55`,
                  opacity: active ? 1 : 0.75,
                }}
              >
                {active && (
                  <span className="absolute -top-5 left-1/2 -translate-x-1/2 whitespace-nowrap font-mono text-[0.55rem] text-white/70">
                    #{s.id}
                  </span>
                )}
              </button>
            )
          })}
          {/* playhead */}
          <div
            ref={playheadRef}
            className="pointer-events-none absolute top-0 bottom-0 z-10 w-0.5 bg-white shadow-[0_0_8px_white]"
            style={{ left: `${playheadPct}%` }}
          />
        </div>
      </div>
    </div>
  )
}
