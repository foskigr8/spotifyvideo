'use client'

import { motion } from 'framer-motion'
import type { Scene } from '@/lib/video/types'

interface Props {
  scene: Scene
  progress: number // 0..1 within scene
}

// The thesis visual: money flows Listener -> Spotify -> Artist,
// but the artist slice shrinks. Three nodes with animated coin particles.
export function MoneyFlow({ progress }: Props) {
  return (
    <div className="flex h-full w-full items-center justify-center px-[6%]">
      <div className="flex w-full max-w-6xl items-center justify-between gap-[3%]">
        <Node label="YOU" sub="pay more" color="#F5F5F5" delay={0} />
        <Flow color="#1DB954" count={6} delay={0.2} duration={1.6} progress={progress} />
        <Node label="SPOTIFY" sub="keeps the difference" color="#1DB954" delay={0.15} highlight />
        <Flow color="#FF3B3B" count={6} delay={0.5} duration={2.2} progress={progress} shrink />
        <Node label="ARTISTS" sub="get less" color="#FF3B3B" delay={0.3} shrink />
      </div>
    </div>
  )
}

function Node({
  label,
  sub,
  color,
  delay,
  highlight,
  shrink,
}: {
  label: string
  sub: string
  color: string
  delay: number
  highlight?: boolean
  shrink?: boolean
}) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8, y: 14 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.4, delay, ease: [0.16, 1, 0.3, 1] }}
      className={`relative flex flex-col items-center justify-center rounded-2xl border px-6 py-7 text-center ${
        highlight ? 'bg-[#1DB954]/10' : 'bg-white/[0.03]'
      }`}
      style={{
        borderColor: highlight ? color : 'rgba(255,255,255,0.12)',
        boxShadow: highlight ? `0 0 60px -20px ${color}` : 'none',
        width: 'clamp(140px, 18vw, 240px)',
      }}
    >
      {shrink && (
        <motion.div
          className="absolute -top-3 right-3 rounded-full bg-[#FF3B3B] px-2 py-0.5 font-mono text-[0.7rem] font-bold text-black"
          initial={{ opacity: 0, scale: 0.6 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: delay + 0.4 }}
        >
          ▼
        </motion.div>
      )}
      <div className="font-display text-[clamp(1.3rem,2.6vw,2.4rem)] font-bold tracking-tight" style={{ color }}>
        {label}
      </div>
      <div className="mt-1 font-body text-[clamp(0.7rem,1.1vw,0.95rem)] uppercase tracking-[0.14em] text-white/45">
        {sub}
      </div>
    </motion.div>
  )
}

function Flow({
  color,
  count,
  delay,
  duration,
  shrink,
}: {
  color: string
  count: number
  delay: number
  duration: number
  progress: number
  shrink?: boolean
}) {
  return (
    <div className="relative h-12 flex-1">
      {/* track line */}
      <motion.div
        className="absolute left-0 right-0 top-1/2 h-[2px] -translate-y-1/2 rounded-full"
        style={{ background: `linear-gradient(90deg, ${color}33, ${color}, ${color}33)` }}
        initial={{ scaleX: 0, originX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 0.4, delay }}
      />
      {/* arrow head */}
      <motion.div
        className="absolute right-0 top-1/2 -translate-y-1/2"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: delay + 0.35 }}
        style={{ color }}
      >
        ▶
      </motion.div>
      {/* particles */}
      {Array.from({ length: count }).map((_, i) => (
        <motion.div
          key={i}
          className="absolute top-1/2 h-2.5 w-2.5 -translate-y-1/2 rounded-full"
          style={{ background: color, boxShadow: `0 0 10px ${color}` }}
          initial={{ left: '0%', opacity: 0 }}
          animate={{ left: '92%', opacity: [0, 1, 1, 0.4] }}
          transition={{
            duration,
            delay: delay + 0.3 + (i * duration) / count,
            repeat: Infinity,
            ease: 'linear',
          }}
          // shrink the artist-bound particles over time
          data-shrink={shrink ? '1' : '0'}
        />
      ))}
    </div>
  )
}
