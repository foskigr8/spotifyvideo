'use client'

import { motion } from 'framer-motion'
import type { Scene, Word } from '@/lib/video/types'

interface Props {
  scene: Scene
  words: Word[]
  t: number // current time in seconds
}

// KineticText: word-by-word reveal locked to the narration timestamps.
// This is the "glue" scene — used between bigger visual moments and for
// emphasis lines. Constant mutation = retention.
export function KineticText({ scene, words, t }: Props) {
  const sceneWords = words.filter((w) => w.end > scene.start && w.start < scene.end)
  const emphasis = scene.params?.emphasis === true

  // current spoken word index inside this scene
  let activeIdx = -1
  for (let i = 0; i < sceneWords.length; i++) {
    if (t >= sceneWords[i].start - 0.04 && t < sceneWords[i].end + 0.12) {
      activeIdx = i
    }
  }
  // if we're past the last word but still in scene, keep last lit
  if (activeIdx === -1 && sceneWords.length && t >= sceneWords[sceneWords.length - 1].end) {
    activeIdx = sceneWords.length - 1
  }

  return (
    <div className="flex h-full w-full items-center justify-center px-[8%]">
      <motion.div
        key={scene.id}
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 1.02 }}
        transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
        className="text-center"
      >
        <p
          className={`font-display font-semibold leading-[1.05] tracking-tight ${
            emphasis
              ? 'text-[clamp(2.2rem,6vw,5.5rem)]'
              : 'text-[clamp(1.6rem,4.4vw,4rem)]'
          }`}
        >
          {sceneWords.map((w, i) => {
            const isActive = i === activeIdx
            const isPast = activeIdx !== -1 && i < activeIdx
            return (
              <span
                key={i}
                className="inline-block transition-all duration-150"
                style={{
                  color: isActive ? '#1DB954' : isPast ? '#F5F5F5' : '#3A3A3A',
                  transform: isActive ? 'translateY(-2px) scale(1.06)' : 'none',
                  textShadow: isActive ? '0 0 28px rgba(29,185,84,0.35)' : 'none',
                  marginRight: '0.28em',
                }}
              >
                {w.text}
              </span>
            )
          })}
        </p>
        {emphasis && (
          <motion.div
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ duration: 0.5, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
            className="mx-auto mt-6 h-[3px] w-24 origin-left rounded-full bg-[#1DB954]"
          />
        )}
      </motion.div>
    </div>
  )
}
