'use client'

import type { Cue } from '@/lib/video/types'

interface Props {
  cue: Cue | null
  nextCue: Cue | null
}

// Large subtitle bar below the stage. Shows current + previews next cue.
export function SubtitleBar({ cue, nextCue }: Props) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.03] px-6 py-4 text-center">
      <p className="min-h-[3.5rem] font-display text-[clamp(1.1rem,2vw,1.6rem)] font-medium leading-snug text-white">
        {cue?.text ?? '—'}
      </p>
      {nextCue && (
        <p className="mt-2 font-body text-sm italic text-white/30">{nextCue.text}</p>
      )}
    </div>
  )
}
