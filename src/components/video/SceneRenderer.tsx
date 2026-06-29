'use client'

import type { Scene, Word } from '@/lib/video/types'
import { KineticText } from './scenes/KineticText'
import { StatReveal } from './scenes/StatReveal'
import { MoneyFlow } from './scenes/MoneyFlow'
import { QuoteCard } from './scenes/QuoteCard'
import { Split } from './scenes/Split'
import { Timeline } from './scenes/Timeline'
import { Chapter } from './scenes/Chapter'

interface Props {
  scene: Scene
  words: Word[]
  t: number
}

export function SceneRenderer({ scene, words, t }: Props) {
  const progress = Math.min(1, Math.max(0, (t - scene.start) / (scene.end - scene.start || 1)))

  switch (scene.type) {
    case 'kinetic':
      return <KineticText scene={scene} words={words} t={t} />
    case 'stat':
      return <StatReveal scene={scene} t={t} progress={progress} />
    case 'moneyflow':
      return <MoneyFlow scene={scene} progress={progress} />
    case 'quote':
      return <QuoteCard scene={scene} progress={progress} />
    case 'split':
      return <Split scene={scene} progress={progress} />
    case 'timeline':
      return <Timeline scene={scene} progress={progress} />
    case 'chapter':
      return <Chapter scene={scene} progress={progress} />
    default:
      return <KineticText scene={scene} words={words} t={t} />
  }
}

// Color per scene type, used by the timeline strip + badges
export const TYPE_COLORS: Record<Scene['type'], string> = {
  kinetic: '#3A3A3A',
  stat: '#1DB954',
  moneyflow: '#1DB954',
  quote: '#F4EFE6',
  chart: '#1DB954',
  receipt: '#F4EFE6',
  timeline: '#1DB954',
  split: '#FF3B3B',
  chapter: '#F5F5F5',
}

export const TYPE_LABELS: Record<Scene['type'], string> = {
  kinetic: 'KINETIC',
  stat: 'STAT',
  moneyflow: 'MONEY FLOW',
  quote: 'QUOTE',
  chart: 'CHART',
  receipt: 'RECEIPT',
  timeline: 'TIMELINE',
  split: 'SPLIT',
  chapter: 'CHAPTER',
}
