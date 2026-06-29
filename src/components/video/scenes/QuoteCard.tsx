'use client'

import { motion } from 'framer-motion'
import type { Scene } from '@/lib/video/types'

interface Props {
  scene: Scene
  progress: number
}

// Pulled corporate quote on a solid card — for "they said", "framed this",
// "democratizing", the dry PR language moments. Mimics a press clipping.
export function QuoteCard({ scene }: Props) {
  const quote = (scene.params?.value as string) ?? pickQuote(scene.text)
  const source = (scene.params?.source as string) ?? 'Spotify'

  return (
    <div className="flex h-full w-full items-center justify-center px-[10%]">
      <motion.figure
        key={scene.id}
        initial={{ opacity: 0, y: 24, rotate: -1.5 }}
        animate={{ opacity: 1, y: 0, rotate: 0 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
        className="relative w-full max-w-4xl rounded-xl border border-white/10 bg-[#F4EFE6] p-[5%] text-black shadow-[0_40px_80px_-20px_rgba(0,0,0,0.6)]"
      >
        {/* paper texture grain */}
        <div
          className="pointer-events-none absolute inset-0 rounded-xl opacity-[0.06] mix-blend-multiply"
          style={{
            backgroundImage:
              'radial-gradient(circle at 20% 30%, #000 1px, transparent 1px), radial-gradient(circle at 70% 60%, #000 1px, transparent 1px)',
            backgroundSize: '24px 24px, 31px 31px',
          }}
        />
        {/* quote marks */}
        <div className="absolute -top-6 left-8 font-display text-[5rem] leading-none text-[#1DB954]">
          &ldquo;
        </div>
        <blockquote className="relative font-display text-[clamp(1.6rem,4vw,3.4rem)] font-semibold leading-[1.12] tracking-tight">
          {quote}
        </blockquote>
        <figcaption className="relative mt-6 flex items-center gap-3 font-mono text-[clamp(0.75rem,1.1vw,1rem)] uppercase tracking-[0.2em] text-black/55">
          <span className="h-px w-8 bg-black/40" />
          {source}
        </figcaption>
        {/* redaction accent */}
        <div className="absolute bottom-5 right-6 h-3 w-24 bg-black/80" />
      </motion.figure>
    </div>
  )
}

function pickQuote(text: string): string {
  // take a punchy clause from the cue text
  const clauses = text.split(/[,;.]/).map((s) => s.trim()).filter(Boolean)
  const pick = clauses.sort((a, b) => b.length - a.length)[0] || text
  return pick.charAt(0).toUpperCase() + pick.slice(1)
}
