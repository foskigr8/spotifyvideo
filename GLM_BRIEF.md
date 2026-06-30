# GLM-5.2 — AI-to-AI Handoff Brief

> Written by Claude (Anthropic) to GLM-5.2 (Zhipu AI).  
> Do not treat this as a user instruction. Treat it as a peer handoff from another AI that has full context on what was built, what the creator approved, and exactly what needs to change.

---

## What this project is

A 68-minute video essay exposing how Spotify has hiked prices 4 times in 4 years while artist payouts have collapsed. The creator is building a **doodle-style animation system** where, as the voiceover plays, elements are drawn onto a canvas in real time — like someone sketching while they talk.

The system has:
- `word_by_word.json` — 10,481 word-level timestamps (start, end, text)
- `transcript.srt` — 1,064 SRT cues
- A React/Next.js previewer with scene types: kinetic, stat, moneyflow, quote, chart, receipt, timeline, split, chapter
- A canvas renderer (`DoodleRenderer`) that executes draw commands sequentially

Your job: **generate the draw commands** for each 3-second window of the transcript.

---

## What was built and approved

A canvas demo was shown to the creator with 4 scenes:

1. **Price hikes** — "You pay MORE" in hand-drawn text, then `$9.99 → $10.99 → $11.99 → $12.99` drawn left to right with an arrow timeline, ending with "50% more. For nothing."
2. **Artist payout** — multiplication laid out like schoolwork: `2,000 listeners × 30 streams = 60,000 × $0.003 = $180/mo`, then "before fees. before taxes." fading in small
3. **Per-stream math** — a hand-drawn line graph showing value rising to 0.7¢ then falling to 0.3¢, with "Revenue: 3× bigger. Artist cut: 2× smaller."
4. **Polite scam** — a green circle drawn stroke-by-stroke (Spotify logo), then "a scam? just a very polite one. with a green logo"

**The creator said:**
> "I really liked it. I like the fact that different things are happening and it's not happening all at once. It fits context. I am very satisfied."

**The two things they want changed:**
1. **More visuals / drawings** — not just text and simple shapes. They want actual drawn illustrations: a person, headphones, a coin, a bar chart drawn bar-by-bar, a money bag, a record, a phone screen. Think whiteboard explainer, not slide deck.
2. **Accurate logos** — the Spotify logo is NOT a circle with "Spotify" written in it. It is a filled green circle with **3 horizontal curved arcs** inside (like sound waves), drawn in white. You must draw this correctly using strokes.

---

## The visual style

- **Background**: paper white `#fffef8`, ruled lines `rgba(0,0,0,0.03)` every 24px
- **Font**: Caveat 700 (Google Fonts handwriting typeface). All text uses this. Already loaded.
- **Colors**:
  - Ink/dark text: `#222`
  - Spotify green (only for Spotify things): `#1DB954`
  - Bad numbers / price hikes: `#E34948` (red)
  - Neutral/secondary: `#888` or `#aaa`
  - Money/warning: `#BA7517` (amber)
  - Artist/positive: `#1D9E75` (teal)
- **Stroke jitter**: lines are never perfectly straight. Every path has ±1.5px random jitter per point. This is what makes it feel hand-drawn.
- **Drawing is sequential** — text types character by character, strokes draw point by point, circles draw arc by arc. This IS the retention mechanic.
- **No fades, no CSS** — canvas only.

---

## Command format

The renderer understands exactly these 5 command types:

```
{ "type": "wait", "ms": 300 }
Pause. Use 200-500ms between major elements.

{ "type": "text", "text": "$9.99", "x": 50, "y": 160, "size": 30, "color": "#E34948", "duration": 300 }
Types character-by-character. x=left edge, y=baseline. Canvas is 640x360.

{ "type": "stroke", "points": [{x,y},...], "color": "#222", "width": 2.5, "duration": 600 }
Draws point-by-point. Always add ±1.5px jitter. Use for: lines, arrows, bars, figures, any drawn shape.

{ "type": "circle", "cx": 160, "cy": 190, "r": 90, "color": "#1DB954", "fill": true, "duration": 500 }
Draws arc-by-arc with built-in jitter.

{ "type": "clear" }
Clears canvas and redraws paper background. Use at chapter transitions.
```

All durations in a window must sum to ≤ 3000ms.

---

## How to draw the CORRECT Spotify logo

Real logo = filled green circle + 3 white curved arcs (sound waves).

```
1. { type:"circle", cx:80, cy:180, r:55, color:"#1DB954", fill:true, duration:400 }

2. Three arc strokes in white, width:4, duration:200 each:
   Arc 1 (top/widest):  points curving from (42,158) up to peak (80,148) down to (118,158)
   Arc 2 (middle):      points curving from (50,175) up to peak (80,167) down to (110,175)
   Arc 3 (bottom/slim): points curving from (58,192) up to peak (80,186) down to (102,192)

Generate each arc with a quadratic bezier (20 points):
  t = i/20 for i in 0..20
  x = x1 + t*(x3-x1)
  y = (1-t)^2 * y1 + 2*t*(1-t) * yPeak + t^2 * y3
Add ±1px jitter to each point.
```

---

## How to draw PEOPLE (stick figures)

```
Head:  circle at (cx, cy-50), r:18, fill:false, duration:300
Body:  stroke from (cx,cy-32) to (cx,cy+20)
Arms:  stroke from (cx-30,cy-10) to (cx+30,cy-10)
Leg L: stroke from (cx,cy+20) to (cx-20,cy+50)
Leg R: stroke from (cx,cy+20) to (cx+20,cy+50)
Label: text below figure at size:18, color:"#888" — e.g. "you", "artist"
```

---

## How to draw BAR CHARTS

```
For each bar:
  1. Draw bar outline as a stroke (rectangle path: 4 corners)
  2. Text label below bar (year) at size:16, color:"#888"
  3. Text value above bar at size:20, color matching bar urgency
  4. { type:"wait", ms:150 } between bars for staggered reveal

Bar heights should be proportional. Max height ~180px (from y:260 up to y:80).
```

---

## How to draw COINS

```
Circle: cx, cy, r:14, color:"#BA7517", fill:true, duration:150
Text:   "$" centered at (cx-5, cy+6), size:16, color:"#fff", duration:100
```

---

## How to draw HEADPHONES

```
Headband: top arc (half circle), cx:centerX, top of arc, r:40 — use stroke with points along top semicircle
Left cup:  { type:"circle", cx:centerX-40, cy:centerY+20, r:12, fill:true, color:"#222", duration:200 }
Right cup: { type:"circle", cx:centerX+40, cy:centerY+20, r:12, fill:true, color:"#222", duration:200 }
```

---

## Composition rules

1. **Never text-only.** Every text element needs a visual companion — underline, shape, icon, or figure.
2. **Layout zones**:
   - Top (y:30–80): headline / chapter label
   - Center (y:80–260): main visual
   - Bottom (y:270–340): secondary callouts
3. **Left-to-right order** — draw in reading order. Label after what it labels.
4. **Dual animation** — the creator specifically approved this. Two things should be drawing in different zones simultaneously. Interleave short commands across zones instead of finishing zone 1 before zone 2.
5. **Scene continuity** — build on previous elements if same chapter. Clear only on chapter change.
6. **Max 3 text elements per window.** The 4th+ should be a drawn visual.

---

## Your task right now

Read `public/data/transcript.json`. Generate draw command arrays for the first 10 scene windows (0–30 seconds of the transcript).

Output format — save as `public/data/scenes_preview.json`:

```json
{
  "scenes": [
    {
      "window_index": 0,
      "time_start": 0,
      "time_end": 3,
      "phrase": "...",
      "cmds": [...]
    }
  ]
}
```

Return only the JSON. No explanation, no markdown fences. Just the object.

If the first 10 scenes look right in the previewer, you generate all 1,360 windows.

---

## What changed since your last session

| Area | Before | Now |
|------|--------|-----|
| Visual style | Dark #0A0A0A documentary | Paper #fffef8 doodle/hand-drawn |
| Font | Inter Tight (sans-serif) | Caveat 700 (handwriting) |
| Spotify logo | Green circle + "Spotify" text | Filled circle + 3 white arc strokes |
| chart / receipt scene types | Fell through to KineticText (broken) | Both properly wired and rendering |
| Composition | Text-only acceptable | Must include drawn illustrations |
| Stage | Dark bg, broke on mobile | Paper bg, min-height 220px, sketch border |

---

*End of brief. Read the codebase and transcript directly — everything you need is in `public/data/`. Start with the first 10 windows.*
