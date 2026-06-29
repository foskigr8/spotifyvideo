'use client'

import { motion } from 'framer-motion'
import type { Scene } from '@/lib/video/types'

interface Props {
  scene: Scene
  progress: number
}

// Side-by-side comparison: "You pay more" vs "They get less".
// A vertical divider slams down, two panels reveal.
export function Split({ scene }: Props) {
  const left = (scene.params?.left as string) ?? 'You pay more'
  const right = (scene.params?.right as string) ?? 'They get less'

  return (
    <div className="flex h-full w-full items-stretch justify-center">
      <div className="flex w-full">
        <Panel text={left} color="#1DB954" align="right" delay={0} />
        <motion.div
          className="w-[3px] bg-white/80"
          initial={{ scaleY: 0 }}
          animate={{ scaleY: 1 }}
          transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
          style={{ originY: 0.5 }}
        />
        <Panel text={right} color="#FF3B3B" align="left" delay={0.12} />
      </div>
    </div>
  )
}

function Panel({
  text,
  color,
  align,
  delay,
}: {
  text: string
  color: string
  align: 'left' | 'right'
  delay: number
}) {
  return (
    <div className="flex flex-1 items-center justify-center px-[5%]">
      <motion.div
        initial={{ opacity: 0, x: align === 'right' ? -30 : 30 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.4, delay, ease: [0.16, 1, 0.3, 1] }}
        className={`max-w-md text-center ${align === 'right' ? 'text-right' : 'text-left'}`}
      >
        <div
          className="font-display text-[clamp(1.6rem,4.2vw,3.6rem)] font-bold leading-[1.05] tracking-tight"
          style={{ color }}
        >
          {text}
        </div>
        <motion.div
          className={`mt-4 h-[2px] w-16 rounded-full ${align === 'right' ? 'ml-auto' : ''}`}
          style={{ background: color }}
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ duration: 0.4, delay: delay + 0.2, originX: align === 'right' ? 1 : 0 }}
        />
      </motion.div>
    </div>
  )
}
