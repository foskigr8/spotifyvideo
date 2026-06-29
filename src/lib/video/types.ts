// Core data types for the video previewer pipeline

export interface Word {
  start: number // seconds
  end: number // seconds
  text: string
}

export interface Cue {
  idx: number
  start: number
  end: number
  text: string
}

// The set of code-driven scene templates. Each maps to a React component.
export type SceneType =
  | 'kinetic' // word-by-word text reveal (default / glue / emphasis)
  | 'stat' // big number counts up / slams in
  | 'moneyflow' // listener -> spotify -> artist money animation
  | 'quote' // pulled corporate quote on solid card
  | 'chart' // animated bar/line chart (price hikes, payout decline)
  | 'receipt' // receipt printing with line items
  | 'timeline' // events on a horizontal timeline
  | 'split' // side-by-side comparison (you pay / they get)
  | 'chapter' // full-screen chapter title card

export interface Scene {
  id: number
  start: number
  end: number
  type: SceneType
  cueIdx: number // index into cues[] for the primary cue
  cues: Cue[] // all cues covered by this scene
  text: string // assembled text
  params: Record<string, unknown> // type-specific params
}
