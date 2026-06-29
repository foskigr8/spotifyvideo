import { readFileSync, writeFileSync, copyFileSync, mkdirSync } from 'fs'

const srt = readFileSync('upload/transcript.srt', 'utf8')
const blocks = srt.trim().split(/\r?\n\r?\n/)
const cues = []
for (const block of blocks) {
  const lines = block.split(/\r?\n/)
  if (lines.length < 3) continue
  const idx = parseInt(lines[0], 10)
  const timeMatch = lines[1].match(/(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})/)
  if (!timeMatch) continue
  const [, h1,m1,s1,ms1,h2,m2,s2,ms2] = timeMatch
  const start = (+h1*3600 + +m1*60 + +s1) + (+ms1/1000)
  const end = (+h2*3600 + +m2*60 + +s2) + (+ms2/1000)
  const text = lines.slice(2).join(' ').replace(/\s+/g,' ').trim()
  cues.push({ idx, start, end, text })
}
console.log(`Parsed ${cues.length} cues. First start=${cues[0].start}, last end=${cues[cues.length-1].end}s (${(cues[cues.length-1].end/60).toFixed(1)} min)`)
mkdirSync('public/data', { recursive: true })
writeFileSync('public/data/transcript.json', JSON.stringify(cues))
copyFileSync('upload/word by word.json', 'public/data/words.json')
console.log('Wrote public/data/transcript.json and public/data/words.json')
// quick stats on cue durations
const durs = cues.map(c => c.end - c.start)
const avg = durs.reduce((a,b)=>a+b,0)/durs.length
console.log(`Cue duration: min=${Math.min(...durs).toFixed(2)}s avg=${avg.toFixed(2)}s max=${Math.max(...durs).toFixed(2)}s`)
