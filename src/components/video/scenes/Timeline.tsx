'use client'

import { motion } from 'framer-motion'
import type { Scene } from '@/lib/video/types'

interface Props {
  scene: Scene
  progress: number
}

// Horizontal timeline of years/events. Used for "2023... 2024... 2025... 2026"
// the price-hike sequence and other temporal beats.
export function Timeline({ scene, progress }: Props) {
  const years = (scene.params?.years as string[]) ?? extractYears(scene.text)
  const events = (scene.params?.events as { year: string; label: string }[]) ?? undefined

  return (
    <div className="flex h-full w-full items-center justify-center px-[8%]">
      <div className="w-full max-w-6xl">
        <motion.h2
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="mb-10 text-center font-body text-[clamp(0.8rem,1.3vw,1.1rem)] font-semibold uppercase tracking-[0.3em] text-white/40"
        >
          Price hikes
        </motion.h2>
        <div className="relative">
          {/* base line */}
          <div className="absolute left-0 right-0 top-1/2 h-[2px] -translate-y-1/2 bg-white/12" />
          {/* progress fill */}
          <motion.div
            className="absolute left-0 top-1/2 h-[2px] -translate-y-1/2 bg-[#1DB954]"
            initial={{ width: '0%' }}
            animate={{ width: `${Math.min(100, progress * 100)}%` }}
            transition={{ ease: 'linear', duration: 0.1 }}
          />
          <div className="relative flex justify-between">
            {years.map((y, i) => (
              <motion.div
                key={y + i}
                initial={{ opacity: 0, y: 20, scale: 0.7 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.35, delay: 0.15 + i * 0.12, ease: [0.16, 1, 0.3, 1] }}
                className="flex flex-col items-center"
              >
                <div className="mb-3 font-mono text-[clamp(0.7rem,1vw,0.9rem)] uppercase tracking-widest text-white/40">
                  hike {i + 1}
                </div>
                <div className="h-4 w-4 rounded-full bg-[#1DB954] shadow-[0_0_20px_#1DB954]" />
                <div className="mt-3 font-display text-[clamp(1.4rem,2.6vw,2.2rem)] font-bold text-white">
                  {y}
                </div>
                <div className="mt-1 font-mono text-[clamp(0.65rem,0.9vw,0.8rem)] text-[#FF3B3B]">
                  +$ ↑
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function extractYears(text: string): string[] {
  const matches = text.match(/\b20\d{2}\b/g)
  if (matches && matches.length) return [...new Set(matches)]
  return ['—']
}
