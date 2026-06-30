'use client'

import { motion } from 'framer-motion'
import type { Scene } from '@/lib/video/types'

interface Props {
  scene: Scene
  progress: number
}

const DEFAULT_ITEMS = [
  { label: 'Spotify cut (30%)',       value: '$3.60', color: '#E34948' },
  { label: 'Major label share',       value: '$4.20', color: '#E34948' },
  { label: 'Distributor fee',         value: '$0.50', color: '#FF8C00' },
  { label: 'Publisher/PRO',           value: '$1.10', color: '#FF8C00' },
  { label: 'Songwriter royalty',      value: '$0.45', color: '#6B6560' },
  { label: 'Artist payout',          value: '$0.15', color: '#1DB954' },
]

export function Receipt({ scene, progress }: Props) {
  const items = (scene.params?.items as typeof DEFAULT_ITEMS) ?? DEFAULT_ITEMS
  const visibleCount = Math.ceil(progress * (items.length + 2))

  return (
    <div className="flex h-full w-full items-center justify-center p-6">
      <div
        className="relative w-full max-w-sm"
        style={{
          fontFamily: 'var(--font-mono), monospace',
          background: '#FFFEF8',
          border: '2px solid #1A1A1A',
          borderRadius: '4px 8px 4px 8px / 8px 4px 8px 4px',
          boxShadow: '4px 4px 0 rgba(26,26,26,0.15)',
          padding: '24px 20px',
        }}
      >
        {/* receipt header */}
        {visibleCount > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-4 text-center"
          >
            <div style={{ fontSize: 'clamp(0.7rem, 1.5vw, 0.9rem)', color: '#6B6560', letterSpacing: '0.2em', textTransform: 'uppercase' }}>
              RECEIPT
            </div>
            <div style={{ fontSize: 'clamp(1rem, 2.5vw, 1.4rem)', fontWeight: 700, color: '#1A1A1A', fontFamily: 'var(--font-display), cursive' }}>
              Where $11.99 goes
            </div>
            <div style={{ borderTop: '2px dashed #1A1A1A', marginTop: 8, paddingTop: 8, fontSize: '0.7rem', color: '#6B6560' }}>
              ─────────────────────
            </div>
          </motion.div>
        )}

        {/* line items */}
        <div className="space-y-2">
          {items.map((item, i) => (
            visibleCount > i + 1 ? (
              <motion.div
                key={item.label}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="flex justify-between items-baseline"
              >
                <span style={{ fontSize: 'clamp(0.65rem,1.2vw,0.8rem)', color: '#1A1A1A' }}>
                  {item.label}
                </span>
                <span style={{ fontSize: 'clamp(0.75rem,1.4vw,0.9rem)', fontWeight: 700, color: item.color }}>
                  {item.value}
                </span>
              </motion.div>
            ) : null
          ))}
        </div>

        {/* total */}
        {visibleCount > items.length + 1 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            style={{ borderTop: '2px solid #1A1A1A', marginTop: 12, paddingTop: 10 }}
          >
            <div className="flex justify-between items-baseline">
              <span style={{ fontSize: 'clamp(0.75rem,1.4vw,0.9rem)', fontWeight: 700, color: '#1A1A1A' }}>TOTAL PAID</span>
              <span style={{ fontSize: 'clamp(0.85rem,1.6vw,1rem)', fontWeight: 700, color: '#1A1A1A' }}>$11.99</span>
            </div>
            <div className="flex justify-between items-baseline mt-1">
              <span style={{ fontSize: 'clamp(0.75rem,1.4vw,0.9rem)', fontWeight: 700, color: '#1DB954' }}>ARTIST GETS</span>
              <span style={{ fontSize: 'clamp(0.85rem,1.6vw,1rem)', fontWeight: 700, color: '#1DB954' }}>$0.15</span>
            </div>
          </motion.div>
        )}

        {/* tape mark top */}
        <div style={{
          position: 'absolute', top: -10, left: '50%', transform: 'translateX(-50%)',
          width: 60, height: 20, background: 'rgba(29,185,84,0.25)',
          border: '1px solid rgba(29,185,84,0.4)',
          borderRadius: 2,
        }} />
      </div>
    </div>
  )
}
