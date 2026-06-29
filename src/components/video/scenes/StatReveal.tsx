'use client'

import { motion } from 'framer-motion'
import type { Scene } from '@/lib/video/types'

interface Props {
  scene: Scene
  t: number
  progress: number // 0..1 within scene
}

// A big number / short phrase that slams in and counts/holds.
// Used for: "$11.99", "1,000 streams", "$0.003", "2023", "LESS", etc.
export function StatReveal({ scene, progress }: Props) {
  const value = (scene.params?.value as string) ?? '—'
  const label = (scene.params?.label as string) ?? scene.text

  // count-up effect for numeric values
  const isNumeric = /^[\d.,$]+/.test(value)
  const display = isNumeric ? animateNumber(value, progress) : value

  return (
    <div className="flex h-full w-full flex-col items-center justify-center px-[8%]">
      <motion.div
        key={scene.id}
        initial={{ opacity: 0, y: 28, scale: 0.9 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, scale: 1.04 }}
        transition={{ duration: 0.32, ease: [0.16, 1, 0.3, 1] }}
        className="flex flex-col items-center text-center"
      >
        <motion.div
          className="font-display font-bold leading-none tracking-tighter text-[#1DB954]"
          style={{ fontSize: 'clamp(3.5rem, 13vw, 11rem)' }}
          initial={{ filter: 'blur(14px)' }}
          animate={{ filter: 'blur(0px)' }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
        >
          {display}
        </motion.div>
        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.18 }}
          className="mt-6 max-w-2xl font-body text-[clamp(0.95rem,1.8vw,1.5rem)] font-medium uppercase tracking-[0.18em] text-white/55"
        >
          {label}
        </motion.p>
      </motion.div>
      {/* under-line accent that draws with progress */}
      <motion.div
        className="mt-10 h-[2px] rounded-full bg-gradient-to-r from-transparent via-[#1DB954] to-transparent"
        initial={{ width: '0%' }}
        animate={{ width: `${Math.min(100, progress * 140)}%` }}
        transition={{ ease: 'linear', duration: 0.1 }}
      />
    </div>
  )
}

// crude count-up: for "$11.99" reveal digits left-to-right with progress
function animateNumber(value: string, progress: number): string {
  const m = value.match(/^(\$?\s?)([\d.,]+)(.*)$/)
  if (!m) return value
  const [, prefix, digits, suffix] = m
  const chars = digits.split('')
  const revealCount = Math.max(1, Math.ceil(chars.length * Math.min(1, progress * 1.6)))
  const shown = chars.slice(0, revealCount).join('')
  const hidden = chars.slice(revealCount).map(() => ' ').join('')
  return `${prefix}${shown}${hidden}${suffix}`
}
