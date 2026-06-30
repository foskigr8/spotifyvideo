'use client'

import { motion } from 'framer-motion'
import type { Scene } from '@/lib/video/types'

interface Props {
  scene: Scene
  progress: number
}

// Animated bar chart for price hikes and payout decline data
export function Chart({ scene, progress }: Props) {
  const chartType = (scene.params?.chartType as string) ?? inferChartType(scene.text)

  if (chartType === 'payout') return <PayoutChart progress={progress} scene={scene} />
  return <PriceHikeChart progress={progress} scene={scene} />
}

function PriceHikeChart({ progress, scene }: { progress: number; scene: Scene }) {
  const bars = [
    { year: '2014–22', price: 9.99, color: '#4A4A4A' },
    { year: '2023', price: 10.99, color: '#1DB954' },
    { year: '2024', price: 11.99, color: '#e6a817' },
    { year: '2025', price: 12.99, color: '#FF8C00' },
    { year: '2026', price: 14.99, color: '#FF3B3B' },
  ]
  const max = 16

  return (
    <div className="flex h-full w-full flex-col items-center justify-center px-[6%] py-[5%]">
      <motion.p
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6 font-mono text-[clamp(0.65rem,1vw,0.85rem)] uppercase tracking-[0.25em] text-white/40"
      >
        Spotify Premium — individual price (USD)
      </motion.p>
      <div className="flex w-full max-w-3xl items-end justify-around gap-3" style={{ height: '55%' }}>
        {bars.map((bar, i) => {
          const heightPct = (bar.price / max) * 100
          const delay = i * 0.08
          const revealed = progress > delay / 0.5
          return (
            <div key={bar.year} className="flex flex-1 flex-col items-center gap-2">
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: revealed ? 1 : 0 }}
                transition={{ delay }}
                className="font-mono text-[clamp(0.7rem,1.2vw,1rem)] font-bold"
                style={{ color: bar.color }}
              >
                ${bar.price}
              </motion.div>
              <motion.div
                className="w-full rounded-t-md"
                style={{ background: bar.color, maxHeight: '100%' }}
                initial={{ height: '0%' }}
                animate={{ height: revealed ? `${heightPct}%` : '0%' }}
                transition={{ duration: 0.5, delay, ease: [0.16, 1, 0.3, 1] }}
              />
              <div className="font-mono text-[clamp(0.6rem,0.9vw,0.75rem)] text-white/45">{bar.year}</div>
            </div>
          )
        })}
      </div>
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: progress > 0.7 ? 1 : 0 }}
        transition={{ duration: 0.4 }}
        className="mt-6 font-display text-[clamp(1rem,2vw,1.6rem)] font-bold text-[#FF3B3B]"
      >
        +50% in 3 years
      </motion.p>
    </div>
  )
}

function PayoutChart({ progress, scene }: { progress: number; scene: Scene }) {
  const points = [
    { year: '2014', value: 0.7 },
    { year: '2016', value: 0.6 },
    { year: '2018', value: 0.5 },
    { year: '2020', value: 0.45 },
    { year: '2022', value: 0.38 },
    { year: '2024', value: 0.3 },
  ]
  const w = 480
  const h = 160
  const pad = 20
  const maxVal = 0.8
  const xStep = (w - pad * 2) / (points.length - 1)

  const toX = (i: number) => pad + i * xStep
  const toY = (v: number) => h - pad - ((v / maxVal) * (h - pad * 2))

  const pathD = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${toX(i)} ${toY(p.value)}`)
    .join(' ')

  const revealedPoints = Math.ceil(progress * points.length * 1.2)

  return (
    <div className="flex h-full w-full flex-col items-center justify-center px-[8%]">
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="mb-4 font-mono text-[clamp(0.65rem,1vw,0.85rem)] uppercase tracking-[0.25em] text-white/40"
      >
        Per-stream payout (¢)
      </motion.p>
      <svg viewBox="0 0 520 200" className="w-full max-w-2xl">
        {/* grid lines */}
        {[0.2, 0.4, 0.6, 0.8].map((v) => (
          <line key={v} x1={pad} y1={toY(v)} x2={w - pad} y2={toY(v)}
            stroke="rgba(255,255,255,0.08)" strokeWidth="1" />
        ))}
        {/* axis labels */}
        {[0.7, 0.5, 0.3].map((v) => (
          <text key={v} x={pad - 4} y={toY(v) + 4} textAnchor="end"
            className="fill-white/40 font-mono" style={{ fontSize: 10 }}>
            {v}¢
          </text>
        ))}
        {/* year labels */}
        {points.map((p, i) => (
          <text key={p.year} x={toX(i)} y={h + 14} textAnchor="middle"
            className="fill-white/40 font-mono" style={{ fontSize: 10 }}>
            {p.year}
          </text>
        ))}
        {/* line path — clipped to progress */}
        <motion.path
          d={pathD}
          fill="none"
          stroke="#FF3B3B"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: Math.min(1, progress * 1.4) }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        />
        {/* dots */}
        {points.slice(0, revealedPoints).map((p, i) => (
          <motion.circle key={i} cx={toX(i)} cy={toY(p.value)} r="5"
            fill="#FF3B3B" stroke="#0A0A0A" strokeWidth="2"
            initial={{ scale: 0 }} animate={{ scale: 1 }}
            transition={{ delay: i * 0.08 }} />
        ))}
        {/* start/end callouts */}
        <text x={toX(0)} y={toY(0.7) - 10} textAnchor="middle"
          className="fill-white/60 font-mono" style={{ fontSize: 11 }}>0.7¢</text>
        {progress > 0.8 && (
          <text x={toX(5)} y={toY(0.3) - 10} textAnchor="middle"
            style={{ fontSize: 11, fill: '#FF3B3B', fontFamily: 'monospace' }}>0.3¢</text>
        )}
      </svg>
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: progress > 0.75 ? 1 : 0 }}
        className="mt-4 font-display text-[clamp(1rem,1.8vw,1.5rem)] font-bold text-[#FF3B3B]"
      >
        Value of a stream: down 57% in a decade
      </motion.p>
    </div>
  )
}

function inferChartType(text: string): string {
  const t = text.toLowerCase()
  if (t.includes('per stream') || t.includes('payout') || t.includes('royalt')) return 'payout'
  return 'price'
}
