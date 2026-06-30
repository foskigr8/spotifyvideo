'use client'

import type { Scene, Word } from '@/lib/video/types'
import { KineticText } from './scenes/KineticText'
import { StatReveal } from './scenes/StatReveal'
import { MoneyFlow } from './scenes/MoneyFlow'
import { QuoteCard } from './scenes/QuoteCard'
import { Split } from './scenes/Split'
import { Timeline } from './scenes/Timeline'
import { Chapter } from './scenes/Chapter'
import { Chart } from './scenes/Chart'
import { Receipt } from './scenes/Receipt'

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
    case 'chart':
      return <Chart scene={scene} progress={progress} />
    case 'receipt':
      return <Receipt scene={scene} progress={progress} />
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

export const TYPE_COLORS: Record<Scene['type'], string> = {
  kinetic: '#D4CCBA',
  stat: '#1DB954',
  moneyflow: '#1DB954',
  quote: '#E8D5B0',
  chart: '#FF8C00',
  receipt: '#E8D5B0',
  timeline: '#7BC8A4',
  split: '#E34948',
  chapter: '#1A1A1A',
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
