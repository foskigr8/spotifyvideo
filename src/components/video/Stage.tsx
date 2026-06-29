'use client'

import { ReactNode } from 'react'
import { motion } from 'framer-motion'
import { TYPE_LABELS } from './SceneRenderer'
import type { Scene } from '@/lib/video/types'

interface Props {
  scene: Scene
  progress: number // global 0..1 across whole video
  children: ReactNode
}

// The 16:9 stage. Adds the documentary "UI dressing":
// corner ticks, chapter/type label, bottom progress bar, subtle vignette + grain.
export function Stage({ scene, progress, children }: Props) {
  return (
    <div className="relative w-full overflow-hidden rounded-xl border border-white/10 bg-[#0A0A0A] shadow-[0_40px_120px_-30px_rgba(0,0,0,0.9)]">
      {/* 16:9 aspect frame */}
      <div className="relative aspect-video w-full">
        {/* the actual scene */}
        <div className="absolute inset-0">{children}</div>

        {/* vignette */}
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              'radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,0.55) 100%)',
          }}
        />
        {/* film grain */}
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.05] mix-blend-overlay"
          style={{
            backgroundImage:
              "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")",
          }}
        />

        {/* corner ticks */}
        <Corner className="left-3 top-3" />
        <Corner className="right-3 top-3 rotate-90" />
        <Corner className="bottom-3 left-3 -rotate-90" />
        <Corner className="bottom-3 right-3 rotate-180" />

        {/* top-left type label */}
        <div className="absolute left-5 top-4 flex items-center gap-2">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[#FF3B3B]" />
          <span className="font-mono text-[0.65rem] uppercase tracking-[0.25em] text-white/50">
            REC · {TYPE_LABELS[scene.type]}
          </span>
        </div>

        {/* top-right scene id */}
        <div className="absolute right-5 top-4 font-mono text-[0.65rem] uppercase tracking-[0.25em] text-white/35">
          SCENE {String(scene.id).padStart(4, '0')}
        </div>

        {/* bottom global progress bar */}
        <div className="absolute bottom-0 left-0 right-0 h-[3px] bg-white/10">
          <motion.div
            className="h-full bg-[#1DB954]"
            style={{ width: `${progress * 100}%` }}
          />
        </div>
      </div>
    </div>
  )
}

function Corner({ className }: { className: string }) {
  return (
    <div className={`pointer-events-none absolute h-4 w-4 ${className}`}>
      <div className="absolute left-0 top-0 h-full w-px bg-white/30" />
      <div className="absolute left-0 top-0 h-px w-full bg-white/30" />
    </div>
  )
}
