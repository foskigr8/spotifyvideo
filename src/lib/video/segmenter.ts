import type { Cue, Scene, SceneType, Word } from './types'

// ---------------------------------------------------------------------------
// Segmentation engine
//
// Goal (per the brief):
//   - scenes change every ~3s, max 10s if a single idea needs more room
//   - every scene matches the script (we have word-level timestamps)
//   - maximise retention via constant visual mutation + type variety
//
// Strategy:
//   - SRT cues already average ~3.5s, so they are natural scene boundaries.
//   - We walk the cues, decide a type for each via keyword detection, then
//     optionally merge a run of same-type short cues (<=10s total) into one
//     scene so a stat/quote/chart can breathe. This satisfies the 3s rule
//     (most scenes stay ~3-4s) and the 10s ceiling simultaneously.
//   - The first ~20 scenes are hand-curated overrides for the hook, because
//     the opening 90s is where retention is won or lost.
// ---------------------------------------------------------------------------

const MIN_SCENE = 2.6 // don't let a scene go shorter than this if it can merge
const MAX_SCENE = 10.0 // hard ceiling from the brief

// ---- keyword -> scene type assignment -------------------------------------

interface TypeRule {
  type: SceneType
  test: (text: string) => boolean
  build?: (text: string, cues: Cue[]) => Record<string, unknown>
}

const has = (t: string, ...words: string[]) =>
  words.some((w) => t.includes(w))

// Extract a headline number/$/%/year for stat scenes
function extractStat(text: string): { value?: string; label?: string } {
  const dollar = text.match(/\$\s?[\d.,]+[KMB]?/i)
  const percent = text.match(/\d+(\.\d+)?\s?%/)
  const streams = text.match(/[\d,]+\s?streams?/i)
  const billion = text.match(/\$?\s?[\d.]+\s?(billion|million|trillion)/i)
  const year = text.match(/\b(20\d{2})\b/)
  const value = dollar?.[0] || percent?.[0] || streams?.[0] || billion?.[0]
  return { value: value?.replace(/\s+/g, ' '), label: undefined }
}

const TYPE_RULES: TypeRule[] = [
  {
    type: 'moneyflow',
    test: (t) =>
      has(
        t,
        "you pay",
        'you paid',
        'spotify keeps',
        'keeps the difference',
        'where the money',
        'payout',
        'per stream',
        'per-stream',
        'royalt',
        'they get less',
        'artists get',
      ),
  },
  {
    type: 'stat',
    test: (t) =>
      !!extractStat(t).value &&
      !has(t, 'every year', 'year since', 'since 2023'),
    build: (t) => extractStat(t),
  },
  {
    type: 'quote',
    test: (t) =>
      has(
        t,
        'they said',
        'spotify said',
        'spotify framed',
        'framed this',
        'claimed',
        'according to',
        'democratizing',
        'democratize',
        'press release',
        'blog post',
      ),
  },
  {
    type: 'chart',
    test: (t) =>
      (has(t, 'every year', 'year since', 'since 2023', 'price hike', 'raised') &&
        /\b20\d{2}\b/.test(t)) ||
      has(t, 'stock', 'revenue', 'market cap', 'shares'),
  },
  {
    type: 'timeline',
    test: (t) =>
      /\b(20\d{2})\b.*\b(20\d{2})\b/.test(t) ||
      has(t, 'in 2023', 'in 2024', 'in 2025', 'in 2026', 'in november', 'then again'),
  },
  {
    type: 'receipt',
    test: (t) => has(t, 'receipt', 'read the receipt', 'line item', 'the math'),
  },
  {
    type: 'split',
    test: (t) => has(t, 'you pay more', 'they get less', 'you, the listener'),
  },
]

function assignType(text: string): { type: SceneType; params: Record<string, unknown> } {
  const lower = text.toLowerCase()
  for (const rule of TYPE_RULES) {
    if (rule.test(lower)) {
      return { type: rule.type, params: rule.build ? rule.build(lower, []) : {} }
    }
  }
  return { type: 'kinetic', params: {} }
}

// ---- hand-curated overrides for the hook (first ~90s) ---------------------
// The opening is retention-critical, so we author it beat by beat.
// Times are in seconds. type matches the curated intent.
interface Override {
  until: number // scene covers cues with start < until
  type: SceneType
  params?: Record<string, unknown>
}

const HOOK_OVERRIDES: Override[] = [
  { until: 3.84, type: 'kinetic', params: { emphasis: true } }, // "You've paid Spotify more money every single year since"
  { until: 7.26, type: 'stat', params: { value: '2023', label: 'since' } },
  { until: 10.76, type: 'kinetic', params: { emphasis: true } }, // "artists getting paid less per stream than ever"
  { until: 17.53, type: 'stat', params: { value: 'LESS', label: 'per stream, every year' } }, // "let me say that again..."
  { until: 21.61, type: 'stat', params: { value: '18 yrs', label: 'most you have ever paid' } },
  { until: 25.01, type: 'timeline', params: { years: ['2023'] } },
  { until: 32.39, type: 'timeline', params: { years: ['2023', '2024', '2025', '2026'] } },
  { until: 39.67, type: 'split', params: { left: 'Same app. Same songs.', right: '4 hikes in 4 years' } },
  { until: 50.72, type: 'moneyflow' }, // "the people who made the music... watching their per-stream payout collapse"
  { until: 59.30, type: 'split', params: { left: 'You pay more', right: 'They get less' } },
  { until: 63.37, type: 'quote', params: { value: 'It is a scam.', source: '— a polite one, with a green logo' } },
  { until: 70.0, type: 'chapter', params: { title: 'We are going to read the receipt.', subtitle: 'All of it.' } },
]

function overrideFor(start: number): Override | undefined {
  return HOOK_OVERRIDES.find((o) => start < o.until)
}

// ---- main segmentation -----------------------------------------------------

export function segmentTranscript(cues: Cue[]): Scene[] {
  const scenes: Scene[] = []
  let i = 0
  let id = 0

  while (i < cues.length) {
    const cue = cues[i]
    const start = cue.start

    // 1. Hook overrides take precedence for the opening
    const ov = overrideFor(start)
    if (ov) {
      // gather cues until we reach `ov.until`
      const group: Cue[] = []
      let j = i
      while (j < cues.length && cues[j].start < ov.until) {
        group.push(cues[j])
        j++
      }
      const end = group[group.length - 1].end
      const text = group.map((c) => c.text).join(' ')
      scenes.push({
        id: id++,
        start,
        end,
        type: ov.type,
        cueIdx: group[0].idx,
        cues: group,
        text,
        params: ov.params ?? {},
      })
      i = j
      continue
    }

    // 2. Default: one cue = one scene, but merge a run of same-type short cues
    const { type, params } = assignType(cue.text)
    const group: Cue[] = [cue]
    let j = i + 1
    while (j < cues.length) {
      const next = cues[j]
      const nextType = assignType(next.text).type
      const wouldEnd = next.end
      const totalDur = wouldEnd - start
      if (nextType === type && totalDur <= MAX_SCENE && group[group.length - 1].end - start < MIN_SCENE) {
        group.push(next)
        j++
      } else {
        break
      }
    }
    const end = group[group.length - 1].end
    const text = group.map((c) => c.text).join(' ')
    const mergedParams = type === 'stat' && params.value ? params : assignType(text).params
    scenes.push({
      id: id++,
      start,
      end,
      type,
      cueIdx: group[0].idx,
      cues: group,
      text,
      params: mergedParams,
    })
    i = j
  }

  return scenes
}

// Helper: find the active scene at a given time (binary search)
export function findSceneAt(scenes: Scene[], t: number): Scene | null {
  if (scenes.length === 0) return null
  let lo = 0
  let hi = scenes.length - 1
  while (lo <= hi) {
    const mid = (lo + hi) >> 1
    const s = scenes[mid]
    if (t < s.start) hi = mid - 1
    else if (t >= s.end) lo = mid + 1
    else return s
  }
  // before first scene
  if (t < scenes[0].start) return scenes[0]
  return scenes[scenes.length - 1]
}

// Helper: find words active at time t, and words within a scene
export function wordsInRange(words: Word[], start: number, end: number): Word[] {
  return words.filter((w) => w.end > start && w.start < end)
}

export function activeWordIndex(words: Word[], t: number): number {
  let lo = 0
  let hi = words.length - 1
  while (lo <= hi) {
    const mid = (lo + hi) >> 1
    const w = words[mid]
    if (t < w.start) hi = mid - 1
    else if (t > w.end) lo = mid + 1
    else return mid
  }
  return Math.max(0, hi)
}
