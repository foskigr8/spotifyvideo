'use client'

import { ReactNode } from 'react'
import { motion } from 'framer-motion'
import { TYPE_LABELS } from './SceneRenderer'
import type { Scene } from '@/lib/video/types'

interface Props {
  scene: Scene
  progress: number
  children: ReactNode
}

export function Stage({ scene, progress, children }: Props) {
  return (
    <div
      className="relative w-full overflow-hidden rounded-xl"
      style={{
        border: '2px solid #1A1A1A',
        borderRadius: '6px 12px 6px 12px / 12px 6px 12px 6px',
        boxShadow: '5px 5px 0 rgba(26,26,26,0.12)',
        background: '#F5F0E8',
        backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 27px, rgba(26,26,26,0.05) 27px, rgba(26,26,26,0.05) 28px)',
      }}
    >
      {/* 16:9 aspect frame */}
      <div className="relative w-full" style={{ minHeight: 220, aspectRatio: '16/9' }}>
        {/* the actual scene */}
        <div className="absolute inset-0">{children}</div>

        {/* top-left type label */}
        <div className="absolute left-4 top-3 flex items-center gap-2">
          <span className="h-2 w-2 rounded-full animate-pulse" style={{ background: '#E34948' }} />
          <span style={{ fontFamily: 'var(--font-mono), monospace', fontSize: '0.6rem', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(26,26,26,0.45)' }}>
            {TYPE_LABELS[scene.type]}
          </span>
        </div>

        {/* top-right scene id */}
        <div className="absolute right-4 top-3" style={{ fontFamily: 'var(--font-mono), monospace', fontSize: '0.6rem', letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(26,26,26,0.3)' }}>
          SCENE {String(scene.id).padStart(4, '0')}
        </div>

        {/* bottom progress bar */}
        <div className="absolute bottom-0 left-0 right-0" style={{ height: 3, background: 'rgba(26,26,26,0.1)' }}>
          <motion.div
            className="h-full"
            style={{ width: `${progress * 100}%`, background: '#1DB954' }}
          />
        </div>
      </div>
    </div>
  )
}
