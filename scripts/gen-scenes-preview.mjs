// scripts/gen-scenes-preview.mjs
// Generates public/data/scenes_preview.json — draw commands for the first 10
// 3-second windows (0–30s) of the Spotify transcript.
// Follows GLM_BRIEF.md: 640x360 canvas, paper doodle style, 5 command types,
// ≤3000ms per window, dual-zone interleaving, drawn illustrations (not text-only),
// correct Spotify logo (filled green circle + 3 white arcs).

import { writeFileSync } from 'fs'

// ---- geometry helpers (renderer adds ±1.5px jitter; we emit clean points) ----

function line(x1, y1, x2, y2, steps = 8) {
  const pts = []
  for (let i = 0; i <= steps; i++) {
    const t = i / steps
    pts.push({ x: x1 + (x2 - x1) * t, y: y1 + (y2 - y1) * t })
  }
  return pts
}

function arrow(x1, y1, x2, y2) {
  const pts = line(x1, y1, x2, y2, 12)
  const ang = Math.atan2(y2 - y1, x2 - x1)
  const len = 11
  pts.push({ x: x2 - len * Math.cos(ang - 0.5), y: y2 - len * Math.sin(ang - 0.5) })
  pts.push({ x: x2, y: y2 })
  pts.push({ x: x2 - len * Math.cos(ang + 0.5), y: y2 - len * Math.sin(ang + 0.5) })
  return pts
}

function rect(x, y, w, h) {
  return [{ x, y }, { x: x + w, y }, { x: x + w, y: y + h }, { x, y: y + h }, { x, y }]
}

// quadratic bezier arc through a peak (for logo sound waves + headbands)
function quadArc(x1, y1, yPeak, x3, y3, n = 20) {
  const pts = []
  for (let i = 0; i <= n; i++) {
    const t = i / n
    const x = x1 + (x3 - x1) * t
    const y = (1 - t) * (1 - t) * y1 + 2 * t * (1 - t) * yPeak + t * t * y3
    pts.push({ x, y })
  }
  return pts
}

// ---- composite doodle builders (return arrays of commands) ----

function stickFigure(cx, cy, label, labelColor, pose = 'normal') {
  const cmds = [
    { type: 'circle', cx, cy: cy - 50, r: 16, color: '#222', fill: false, duration: 240 },
    { type: 'stroke', points: line(cx, cy - 34, cx, cy + 20, 4), color: '#222', width: 2.5, duration: 180 },
    { type: 'stroke', points: line(cx - 28, cy - 8, cx + 28, cy - 8, 6), color: '#222', width: 2.5, duration: 180 },
    { type: 'stroke', points: line(cx, cy + 20, cx - 18, cy + 50, 4), color: '#222', width: 2.5, duration: 150 },
    { type: 'stroke', points: line(cx, cy + 20, cx + 18, cy + 50, 4), color: '#222', width: 2.5, duration: 150 },
  ]
  if (label) cmds.push({ type: 'text', text: label, x: cx - 18, y: cy + 68, size: 18, color: labelColor || '#888', duration: 130 })
  return cmds
}

// CORRECT Spotify logo: filled green circle + 3 white curved arcs (sound waves)
function spotifyLogo(cx, cy, r) {
  const cmds = [{ type: 'circle', cx, cy, r, color: '#1DB954', fill: true, duration: 320 }]
  const arcs = [
    { x1: cx - r * 0.70, x3: cx + r * 0.70, y: cy - r * 0.18, peak: cy - r * 0.36 },
    { x1: cx - r * 0.56, x3: cx + r * 0.56, y: cy + r * 0.02, peak: cy - r * 0.10 },
    { x1: cx - r * 0.42, x3: cx + r * 0.42, y: cy + r * 0.22, peak: cy + r * 0.12 },
  ]
  for (const a of arcs) {
    cmds.push({ type: 'stroke', points: quadArc(a.x1, a.y, a.peak, a.x3, a.y), color: '#fff', width: 4, duration: 170 })
  }
  return cmds
}

function coin(cx, cy, r = 14) {
  return [
    { type: 'circle', cx, cy, r, color: '#BA7517', fill: true, duration: 140 },
    { type: 'text', text: '$', x: cx - 5, y: cy + 6, size: 16, color: '#fff', duration: 90 },
  ]
}

function headphones(cx, cy) {
  // headband = top semicircle arc
  const band = []
  for (let i = 0; i <= 16; i++) {
    const t = i / 16
    const ang = Math.PI + t * Math.PI // PI..2PI = top semicircle
    band.push({ x: cx + 40 * Math.cos(ang), y: cy + 40 * Math.sin(ang) })
  }
  return [
    { type: 'stroke', points: band, color: '#222', width: 2.5, duration: 240 },
    { type: 'circle', cx: cx - 40, cy: cy + 20, r: 11, color: '#222', fill: true, duration: 180 },
    { type: 'circle', cx: cx + 40, cy: cy + 20, r: 11, color: '#222', fill: true, duration: 180 },
  ]
}

function musicNote(cx, cy, color = '#1D9E75') {
  return [
    { type: 'stroke', points: line(cx, cy, cx, cy - 26, 4), color, width: 2.5, duration: 130 },
    { type: 'circle', cx: cx - 5, cy, r: 6, color, fill: true, duration: 110 },
  ]
}

// ---- budget tracker (enforces ≤3000ms per window) ----
function budget(cmds) {
  let ms = 0
  for (const c of cmds) ms += c.ms || c.duration || 0
  return ms
}

// =========================================================================
// WINDOWS 0–9
// =========================================================================

const windows = []

// ---- Window 0 [0–3]: "You've paid Spotify more money every single year" ----
// Hook opener: YOU (stick figure) hands a coin → Spotify logo. "MORE" in red.
{
  const cmds = []
  cmds.push({ type: 'text', text: 'YOU', x: 36, y: 64, size: 26, color: '#222', duration: 280 })
  cmds.push(...spotifyLogo(500, 140, 42))                       // zone B starts (logo)
  cmds.push({ type: 'circle', cx: 90, cy: 150, r: 16, color: '#222', fill: false, duration: 200 })
  cmds.push({ type: 'stroke', points: line(90, 166, 90, 210, 4), color: '#222', width: 2.5, duration: 150 })
  cmds.push({ type: 'stroke', points: line(62, 188, 118, 188, 6), color: '#222', width: 2.5, duration: 150 })
  cmds.push({ type: 'stroke', points: line(90, 210, 72, 238, 4), color: '#222', width: 2.5, duration: 130 })
  cmds.push({ type: 'stroke', points: line(90, 210, 108, 238, 4), color: '#222', width: 2.5, duration: 130 })
  cmds.push({ type: 'text', text: 'you', x: 76, y: 258, size: 16, color: '#888', duration: 110 })
  cmds.push(...coin(170, 182, 14))                               // coin in hand
  cmds.push({ type: 'stroke', points: arrow(186, 182, 440, 160), color: '#BA7517', width: 2.5, duration: 360 })
  cmds.push({ type: 'text', text: 'MORE', x: 540, y: 72, size: 32, color: '#E34948', duration: 290 })
  cmds.push({ type: 'wait', ms: 90 })
  windows.push({ window_index: 0, time_start: 0, time_end: 3, phrase: "You've paid Spotify more money every single year", cmds })
}

// ---- Window 1 [3–6]: "year since 2023. And artists" ----
// Emphasize "2023" (bad year), introduce artist figure on the right.
{
  const cmds = []
  cmds.push({ type: 'text', text: 'since', x: 80, y: 196, size: 18, color: '#888', duration: 150 })
  cmds.push({ type: 'text', text: '2023', x: 126, y: 220, size: 46, color: '#E34948', duration: 400 })
  cmds.push({ type: 'wait', ms: 90 })
  cmds.push({ type: 'stroke', points: arrow(180, 200, 470, 150), color: '#888', width: 2, duration: 330 })
  cmds.push({ type: 'circle', cx: 520, cy: 150, r: 16, color: '#1D9E75', fill: false, duration: 200 })
  cmds.push({ type: 'stroke', points: line(520, 166, 520, 210, 4), color: '#1D9E75', width: 2.5, duration: 150 })
  cmds.push({ type: 'stroke', points: line(492, 188, 548, 188, 6), color: '#1D9E75', width: 2.5, duration: 150 })
  cmds.push({ type: 'stroke', points: line(520, 210, 502, 238, 4), color: '#1D9E75', width: 2.5, duration: 130 })
  cmds.push({ type: 'stroke', points: line(520, 210, 538, 238, 4), color: '#1D9E75', width: 2.5, duration: 130 })
  cmds.push({ type: 'text', text: 'ARTISTS', x: 478, y: 258, size: 22, color: '#1D9E75', duration: 200 })
  cmds.push(...musicNote(560, 120, '#1D9E75'))
  cmds.push({ type: 'wait', ms: 80 })
  windows.push({ window_index: 1, time_start: 3, time_end: 6, phrase: 'year since 2023. And artists', cmds })
}

// ---- Window 2 [6–9]: "artists are getting paid less per stream than ever. Let me say that again" ----
// Artist paid LESS: red down-arrow, shrinking coin, "$0.003 per stream". Loop "again".
{
  const cmds = []
  cmds.push({ type: 'stroke', points: arrow(520, 90, 520, 130), color: '#E34948', width: 3, duration: 320 })
  cmds.push({ type: 'text', text: 'LESS', x: 446, y: 86, size: 38, color: '#E34948', duration: 360 })
  cmds.push({ type: 'stroke', points: line(442, 96, 540, 96, 6), color: '#E34948', width: 2.5, duration: 170 })
  cmds.push({ type: 'wait', ms: 80 })
  cmds.push(...coin(520, 168, 9))                                // smaller coin
  cmds.push({ type: 'text', text: '$0.003', x: 478, y: 196, size: 17, color: '#E34948', duration: 190 })
  cmds.push({ type: 'text', text: 'per stream', x: 472, y: 216, size: 13, color: '#888', duration: 150 })
  cmds.push({ type: 'wait', ms: 90 })
  cmds.push({ type: 'text', text: '(again)', x: 96, y: 282, size: 24, color: '#222', duration: 220 })
  cmds.push({ type: 'stroke', points: quadArc(150, 280, 246, 240, 280, 16), color: '#222', width: 2, duration: 320 })
  windows.push({ window_index: 2, time_start: 6, time_end: 9, phrase: 'artists are getting paid less per stream than ever. Let me say that again', cmds })
}

// ---- Window 3 [9–12]: "say that again, because it should be the most insane sentence in" ----
// "INSANE" slam + a dizzy/crazy head with X eyes.
{
  const cmds = []
  cmds.push({ type: 'text', text: 'INSANE', x: 200, y: 130, size: 56, color: '#E34948', duration: 460 })
  cmds.push({ type: 'wait', ms: 80 })
  cmds.push({ type: 'stroke', points: line(196, 142, 430, 142, 8), color: '#E34948', width: 3, duration: 200 })
  cmds.push({ type: 'text', text: '!', x: 442, y: 110, size: 52, color: '#E34948', duration: 200 })
  cmds.push({ type: 'wait', ms: 80 })
  cmds.push({ type: 'text', text: 'in the music industry', x: 170, y: 178, size: 20, color: '#888', duration: 240 })
  cmds.push({ type: 'circle', cx: 90, cy: 140, r: 20, color: '#222', fill: false, duration: 240 })
  cmds.push({ type: 'stroke', points: line(80, 132, 100, 148, 4), color: '#222', width: 2.5, duration: 140 })
  cmds.push({ type: 'stroke', points: line(100, 132, 80, 148, 4), color: '#222', width: 2.5, duration: 140 })
  cmds.push({ type: 'stroke', points: line(80, 158, 100, 158, 4), color: '#222', width: 2.5, duration: 110 })
  cmds.push(...musicNote(560, 200, '#888'))
  cmds.push({ type: 'wait', ms: 90 })
  windows.push({ window_index: 3, time_start: 9, time_end: 12, phrase: 'say that again, because it should be the most insane sentence in', cmds })
}

// ---- Window 4 [12–15]: "the music industry, and somehow nobody talks about" ----
// "NOBODY talks about it" — figure shushing, empty crossed-out speech bubble.
{
  const cmds = []
  cmds.push({ type: 'text', text: 'NOBODY', x: 200, y: 96, size: 42, color: '#222', duration: 400 })
  cmds.push({ type: 'wait', ms: 80 })
  cmds.push({ type: 'text', text: 'talks about it', x: 188, y: 138, size: 22, color: '#888', duration: 250 })
  cmds.push({ type: 'wait', ms: 100 })
  // shushing figure
  cmds.push({ type: 'circle', cx: 110, cy: 220, r: 16, color: '#222', fill: false, duration: 240 })
  cmds.push({ type: 'stroke', points: line(110, 236, 110, 280, 4), color: '#222', width: 2.5, duration: 150 })
  cmds.push({ type: 'stroke', points: line(110, 252, 104, 224, 4), color: '#222', width: 2.5, duration: 160 }) // arm to mouth
  cmds.push({ type: 'text', text: 'shh', x: 134, y: 218, size: 26, color: '#888', duration: 180 })
  // empty speech bubble, crossed out
  cmds.push({ type: 'circle', cx: 470, cy: 210, r: 34, color: '#222', fill: false, duration: 250 })
  cmds.push({ type: 'stroke', points: line(438, 178, 502, 242, 8), color: '#E34948', width: 2.5, duration: 200 })
  cmds.push({ type: 'wait', ms: 80 })
  windows.push({ window_index: 4, time_start: 12, time_end: 15, phrase: 'the music industry, and somehow nobody talks about', cmds })
}

// ---- Window 5 [15–18]: "about it. You, the listener, are paying more for Spotify" ----
// Listener (with headphones!) pays an even bigger coin to Spotify. "MORE" again.
{
  const cmds = []
  cmds.push(...headphones(90, 150))                              // headphones on YOU
  cmds.push({ type: 'text', text: 'listener', x: 52, y: 256, size: 18, color: '#222', duration: 180 })
  cmds.push({ type: 'wait', ms: 70 })
  cmds.push(...coin(176, 188, 18))                               // bigger coin
  cmds.push({ type: 'stroke', points: arrow(196, 188, 446, 158), color: '#BA7517', width: 3, duration: 360 })
  cmds.push({ type: 'text', text: 'MORE', x: 540, y: 72, size: 34, color: '#E34948', duration: 290 })
  cmds.push({ type: 'stroke', points: line(538, 84, 624, 84, 6), color: '#E34948', width: 2.5, duration: 170 })
  cmds.push(...coin(248, 188, 15))                               // second coin stacking
  cmds.push({ type: 'wait', ms: 80 })
  windows.push({ window_index: 5, time_start: 15, time_end: 18, phrase: 'about it. You, the listener, are paying more for Spotify', cmds })
}

// ---- Window 6 [18–21]: "Spotify today than you have ever paid in the company's 18-year" ----
// "18-YEAR HISTORY" big, with a timeline 2008→2026.
{
  const cmds = []
  cmds.push({ type: 'text', text: '18-YEAR', x: 150, y: 96, size: 44, color: '#222', duration: 420 })
  cmds.push({ type: 'wait', ms: 80 })
  cmds.push({ type: 'text', text: 'HISTORY', x: 170, y: 146, size: 36, color: '#1DB954', duration: 350 })
  cmds.push({ type: 'wait', ms: 80 })
  cmds.push({ type: 'stroke', points: line(110, 250, 540, 250, 12), color: '#222', width: 2.5, duration: 300 })
  cmds.push({ type: 'stroke', points: line(130, 244, 130, 256, 2), color: '#888', width: 2, duration: 90 })
  cmds.push({ type: 'stroke', points: line(260, 244, 260, 256, 2), color: '#888', width: 2, duration: 90 })
  cmds.push({ type: 'stroke', points: line(390, 244, 390, 256, 2), color: '#888', width: 2, duration: 90 })
  cmds.push({ type: 'stroke', points: line(520, 244, 520, 256, 2), color: '#888', width: 2, duration: 90 })
  cmds.push({ type: 'text', text: '2008', x: 116, y: 276, size: 15, color: '#888', duration: 140 })
  cmds.push({ type: 'text', text: '2026', x: 506, y: 276, size: 15, color: '#888', duration: 140 })
  cmds.push({ type: 'wait', ms: 80 })
  windows.push({ window_index: 6, time_start: 18, time_end: 21, phrase: "Spotify today than you have ever paid in the company's 18-year", cmds })
}

// ---- Window 7 [21–24]: "18-year history. Spotify raised its prices in" ----
// "RAISED PRICES" + big UP arrow + "$↑" + small Spotify logo + "2023".
{
  const cmds = []
  cmds.push({ type: 'text', text: 'RAISED PRICES', x: 150, y: 80, size: 32, color: '#E34948', duration: 420 })
  cmds.push({ type: 'wait', ms: 80 })
  cmds.push({ type: 'stroke', points: arrow(320, 200, 320, 110), color: '#E34948', width: 3, duration: 360 })
  cmds.push({ type: 'text', text: '$', x: 296, y: 140, size: 40, color: '#E34948', duration: 280 })
  cmds.push({ type: 'text', text: '2023', x: 440, y: 150, size: 30, color: '#222', duration: 250 })
  cmds.push(...spotifyLogo(80, 220, 28))
  cmds.push({ type: 'wait', ms: 80 })
  windows.push({ window_index: 7, time_start: 21, time_end: 24, phrase: '18-year history. Spotify raised its prices in', cmds })
}

// ---- Window 8 [24–27]: "in 2023. Then again in 2024." ----
// Bar chart: 2023 ($10.99) → 2024 ($11.99), taller. Arrow up between tops.
{
  const cmds = []
  // bar 2023
  cmds.push({ type: 'stroke', points: rect(140, 200, 56, 60), color: '#222', width: 2.5, duration: 300 })
  cmds.push({ type: 'text', text: '2023', x: 146, y: 280, size: 16, color: '#888', duration: 150 })
  cmds.push({ type: 'text', text: '$10.99', x: 138, y: 192, size: 18, color: '#222', duration: 200 })
  cmds.push({ type: 'wait', ms: 150 })
  // bar 2024 (taller)
  cmds.push({ type: 'stroke', points: rect(240, 160, 56, 100), color: '#E34948', width: 2.5, duration: 300 })
  cmds.push({ type: 'text', text: '2024', x: 246, y: 280, size: 16, color: '#888', duration: 150 })
  cmds.push({ type: 'text', text: '$11.99', x: 238, y: 152, size: 18, color: '#E34948', duration: 200 })
  cmds.push({ type: 'wait', ms: 100 })
  cmds.push({ type: 'stroke', points: arrow(198, 205, 238, 165), color: '#E34948', width: 2.5, duration: 250 })
  cmds.push({ type: 'text', text: 'hike 2', x: 360, y: 120, size: 22, color: '#E34948', duration: 200 })
  cmds.push({ type: 'wait', ms: 80 })
  windows.push({ window_index: 8, time_start: 24, time_end: 27, phrase: 'in 2023. Then again in 2024.', cmds })
}

// ---- Window 9 [27–30]: "2024. Then again in 2025. And they just" ----
// Third bar 2025 ($12.99) taller still + "AND AGAIN" + faint 4th ghost bar.
{
  const cmds = []
  cmds.push({ type: 'stroke', points: rect(340, 120, 56, 140), color: '#E34948', width: 2.5, duration: 300 })
  cmds.push({ type: 'text', text: '2025', x: 346, y: 280, size: 16, color: '#888', duration: 150 })
  cmds.push({ type: 'text', text: '$12.99', x: 338, y: 112, size: 18, color: '#E34948', duration: 200 })
  cmds.push({ type: 'wait', ms: 130 })
  cmds.push({ type: 'stroke', points: arrow(298, 165, 338, 125), color: '#E34948', width: 2.5, duration: 240 })
  cmds.push({ type: 'text', text: 'AND AGAIN', x: 420, y: 80, size: 28, color: '#E34948', duration: 280 })
  cmds.push({ type: 'wait', ms: 80 })
  // faint ghost 4th bar (2026 hint)
  cmds.push({ type: 'stroke', points: rect(440, 80, 56, 180), color: '#aaa', width: 1.5, duration: 220 })
  cmds.push({ type: 'text', text: '2026?', x: 444, y: 280, size: 15, color: '#aaa', duration: 150 })
  cmds.push({ type: 'wait', ms: 90 })
  windows.push({ window_index: 9, time_start: 27, time_end: 30, phrase: '2024. Then again in 2025. And they just', cmds })
}

// ---- verify budgets & write ----
const out = { scenes: windows }
let ok = true
for (const w of windows) {
  const ms = budget(w.cmds)
  const flag = ms <= 3000 ? 'OK ' : 'OVER'
  if (ms > 3000) ok = false
  console.log(`${flag} window ${w.window_index}: ${ms}ms, ${w.cmds.length} cmds`)
}
writeFileSync('public/data/scenes_preview.json', JSON.stringify(out, null, 2))
console.log(`\nWrote public/data/scenes_preview.json — ${windows.length} windows, budget ${ok ? 'all ≤3000ms' : 'VIOLATED'}`)
