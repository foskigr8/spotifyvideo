'use client'

import { motion } from 'framer-motion'
import type { Scene } from '@/lib/video/types'

interface Props {
  scene: Scene
  progress: number
}

// Full-screen chapter title card. Used for major section breaks / the hook's
// thesis line. Big, slow, weighted.
export function Chapter({ scene }: Props) {
  const title = (scene.params?.title as string) ?? scene.text
  const subtitle = (scene.params?.subtitle as string) ?? null

  return (
    <div className="flex h-full w-full items-center justify-center px-[10%]">
      <motion.div
        key={scene.id}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.5 }}
        className="text-center"
      >
        <motion.div
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="mx-auto mb-8 h-[3px] w-16 origin-center rounded-full bg-[#1DB954]"
        />
        <motion.h1
          initial={{ opacity: 0, y: 30, filter: 'blur(12px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          transition={{ duration: 0.6, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
          className="font-display text-[clamp(2.2rem,6vw,6rem)] font-bold leading-[1.02] tracking-tight text-white"
        >
          {title}
        </motion.h1>
        {subtitle && (
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            className="mt-6 font-body text-[clamp(1rem,2vw,1.8rem)] font-light text-white/55"
          >
            {subtitle}
          </motion.p>
        )}
      </motion.div>
    </div>
  )
}
