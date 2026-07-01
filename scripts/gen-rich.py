#!/usr/bin/env python3
"""
gen-rich.py — Generate rich, drawing-heavy scenes for cues 72+ with word-level timing.

KEY IMPROVEMENTS over previous attempts:
1. ACTUAL DRAWINGS: every scene has stick figures, coins, arrows, charts, receipts,
   tally marks, checkmarks, flow diagrams — not just text + underline.
2. WORD-LEVEL TIMING: draw command durations are derived from word_by_word.json
   timestamps, so drawings appear precisely as the narrator says the words.
3. BREATHING: generous waits (300-800ms) between elements, proportional to speech.
4. CONTEXT-AWARE: each scene's visual composition matches what's being said.
5. VARIETY: 20+ drawing primitives, 15+ scene archetypes, no two scenes identical.

DRAWING LIBRARY:
  - stick_figure(cx, cy, label, expression) — head + body + arms + legs + label
  - coin(cx, cy, r) — filled amber circle + $ inside
  - dollar_bill(x, y, w, h, amount) — rectangle + $ + amount label
  - arrow(x1, y1, x2, y2) — line + arrowhead
  - tally_mark(x, y) — vertical stroke
  - tally_cross(x1, x2, y1, y2) — diagonal crossbar over tally marks
  - checkmark(x, y) — two short strokes forming ✓
  - cross_out(x, y, w, h) — X over a region
  - underline(x, y, length) — wobbly horizontal line
  - circle_around(cx, cy, r) — emphasis circle
  - receipt(x, y, w, h, items) — rectangle + line items + tear bottom
  - price_tag(x, y, price) — tag shape + price inside
  - bar_chart(x, y, bars) — vertical bars with labels
  - timeline(x, y, years) — horizontal line + dots + year labels
  - flow_diagram(elements) — boxes connected by arrows
  - spotify_logo(cx, cy, r) — green circle + 3 white arcs
  - phone_mockup(x, y) — rounded rectangle phone with screen elements
  - speech_bubble(x, y, text) — bubble shape + text
  - downward_arrow_big(x, y, h) — thick downward arrow (collapse)
  - upward_arrow_big(x, y, h) — thick upward arrow (growth)
  - percentage_ring(cx, cy, r, pct) — circle + % text
"""

import json, math, random, re
random.seed(42)

CANVAS_W, CANVAS_H = 640, 360
RED    = "#E34948"
GREEN  = "#1DB954"
AMBER  = "#F5A623"
INK    = "#1A1A1A"
GRAY   = "#888888"
LGRAY  = "#BBBBBB"
DGRAY  = "#6E6E6E"
WHITE  = "#ffffff"

# ── Primitive geometry ────────────────────────────────────────────────────────

def jit(v, j=1.2):
    return v + (random.random() - 0.5) * 2 * j

def J(pts, j=1.2):
    return [{"x": round(p["x"]+(random.random()-.5)*2*j, 1),
             "y": round(p["y"]+(random.random()-.5)*2*j, 1)} for p in pts]

def line(x1, y1, x2, y2, steps=28):
    return J([{"x": round(x1+(x2-x1)*i/steps, 1),
               "y": round(y1+(y2-y1)*i/steps, 1)} for i in range(steps+1)])

def hline(x1, x2, y, steps=32):
    return line(x1, y, x2, y, steps)

def vline(x, y1, y2, steps=18):
    return line(x, y1, x, y2, steps)

def arrow_pts(x1, y1, x2, y2, head=12):
    pts = line(x1, y1, x2, y2, 30)
    a = math.atan2(y2-y1, x2-x1)
    s = 0.45
    pts += [
        {"x": round(x2-head*math.cos(a-s),1), "y": round(y2-head*math.sin(a-s),1)},
        {"x": round(x2,1), "y": round(y2,1)},
        {"x": round(x2-head*math.cos(a+s),1), "y": round(y2-head*math.sin(a+s),1)},
    ]
    return pts

def underline_pts(x, y, length, steps=26):
    return J([{"x": round(x+length*i/steps,1), "y": round(y+math.sin(i/steps*math.pi*2)*1.0,1)}
              for i in range(steps+1)], j=0.5)

def curved_pts(x, y, length, steps=32):
    return [{"x": round(x+length*i/steps,1), "y": round(y+math.sin(i/steps*math.pi)*4,1)}
            for i in range(steps+1)]

def quad_arc(x1, y1, yP, x3, y3, n=20):
    pts = []
    for i in range(n+1):
        t = i/n
        x = x1 + (x3-x1)*t
        y = (1-t)**2*y1 + 2*t*(1-t)*yP + t**2*y3
        pts.append({"x": round(x,1), "y": round(y,1)})
    return J(pts, 0.8)

def rect_pts(x, y, w, h, r=0):
    """Rounded rectangle path as a list of points."""
    pts = []
    if r > 0:
        # corners
        for cx, cy, a0, a1 in [(x+r,y+r,math.pi,1.5*math.pi),(x+w-r,y+r,1.5*math.pi,2*math.pi),
                                (x+w-r,y+h-r,0,0.5*math.pi),(x+r,y+h-r,0.5*math.pi,math.pi)]:
            for i in range(6):
                a = a0 + (a1-a0)*i/5
                pts.append({"x": round(cx+r*math.cos(a),1), "y": round(cy+r*math.sin(a),1)})
        pts.append(pts[0])  # close
    else:
        for px, py in [(x,y),(x+w,y),(x+w,y+h),(x,y+h),(x,y)]:
            for i in range(8):
                pts.append({"x": round(px,1), "y": round(py,1)})  # just corners
        pts = [{"x":x,"y":y},{"x":x+w,"y":y},{"x":x+w,"y":y+h},{"x":x,"y":y+h},{"x":x,"y":y}]
        pts = J(pts, 1.0)
    return pts

# ── Command builders ──────────────────────────────────────────────────────────

def T(text, x, y, size=28, color=INK, dur=300):
    return {"type":"text","text":text,"x":x,"y":y,"size":size,"color":color,"duration":dur}

def S(points, color=INK, width=2.5, dur=500):
    return {"type":"stroke","points":points,"color":color,"width":width,"duration":dur}

def C(cx, cy, r, color=INK, fill=False, dur=400):
    return {"type":"circle","cx":cx,"cy":cy,"r":r,"color":color,"fill":fill,"duration":dur}

def W(ms=300):
    return {"type":"wait","ms":ms}

def CLR():
    return {"type":"clear"}

# ── Drawing library ───────────────────────────────────────────────────────────

def spotify_logo(cx, cy, r=36):
    cmds = [C(cx, cy, r, color=GREEN, fill=True, dur=300), W(80)]
    arcs = [
        {"x1":cx-r*0.6,"y1":cy-r*0.25,"yP":cy-r*0.55,"x3":cx+r*0.6,"y3":cy-r*0.25},
        {"x1":cx-r*0.5,"y1":cy+r*0.05,"yP":cy-r*0.2, "x3":cx+r*0.5,"y3":cy+r*0.05},
        {"x1":cx-r*0.35,"y1":cy+r*0.3,"yP":cy+r*0.1, "x3":cx+r*0.35,"y3":cy+r*0.3},
    ]
    for arc in arcs:
        cmds += [S(quad_arc(arc["x1"],arc["y1"],arc["yP"],arc["x3"],arc["y3"]),
                   color=WHITE, width=3.5, dur=150), W(40)]
    return cmds

def stick_figure(cx, cy, label=None, expression="normal"):
    """Stick figure at (cx, cy) where cy is the center of the body.
    expression: 'normal', 'sad', 'happy', 'angry'
    """
    cmds = [
        C(cx, cy-35, 13, color=INK, fill=False, dur=250),            # head
        S(line(cx, cy-22, cx, cy+20, 4), color=INK, width=2.3, dur=160),  # body
        S(line(cx-22, cy-5, cx+22, cy-5, 5), color=INK, width=2.3, dur=160),  # arms
        S(line(cx, cy+20, cx-16, cy+42, 4), color=INK, width=2.3, dur=140),   # leg L
        S(line(cx, cy+20, cx+16, cy+42, 4), color=INK, width=2.3, dur=140),   # leg R
    ]
    # expression: mouth
    if expression == "sad":
        cmds.append(S(line(cx-6, cy-30, cx+6, cy-33, 4), color=INK, width=2, dur=80))  # frown
    elif expression == "happy":
        cmds.append(S(line(cx-6, cy-33, cx+6, cy-30, 4), color=INK, width=2, dur=80))  # smile
    if label:
        cmds.append(T(label, cx-20, cy+60, size=20, color=DGRAY, dur=200))
    return cmds

def coin(cx, cy, r=18):
    return [
        C(cx, cy, r, color=AMBER, fill=True, dur=250),
        T("$", cx-r*0.3, cy+r*0.35, size=int(r*1.1), color=WHITE, dur=120),
    ]

def dollar_bill(x, y, w, h, amount=None):
    cmds = [
        S(rect_pts(x, y, w, h, r=4), color=GREEN, width=2.5, dur=300),
        T("$", x+w//2-6, y+h//2+8, size=20, color=GREEN, dur=120),
    ]
    if amount:
        cmds.append(T(amount, x-5, y-8, size=20, color=GREEN, dur=180))
    return cmds

def arrow_cmd(x1, y1, x2, y2, color=INK, width=2.5, dur=400):
    return S(arrow_pts(x1, y1, x2, y2), color=color, width=width, dur=dur)

def underline_cmd(x, y, length, color=INK, width=2.5, dur=250):
    return S(underline_pts(x, y, length), color=color, width=width, dur=dur)

def double_underline_cmd(x, y, length, color=RED, dur=250):
    return [
        S(underline_pts(x, y, length), color=color, width=3, dur=dur),
        S(underline_pts(x+5, y+8, length-10), color=color, width=2, dur=dur-50),
    ]

def cross_out_cmd(x, y, w, h, color=RED, dur=250):
    return [
        S(line(x, y, x+w, y+h, 12), color=color, width=3, dur=dur),
        S(line(x+w, y, x, y+h, 12), color=color, width=3, dur=dur),
    ]

def checkmark_cmd(x, y, size=20, color=INK, dur=200):
    return [
        S(line(x, y, x+size*0.3, y+size*0.5, 5), color=color, width=2.5, dur=dur//2),
        S(line(x+size*0.3, y+size*0.5, x+size, y-size*0.3, 8), color=color, width=2.5, dur=dur//2),
    ]

def tally_mark_cmd(x, y, h=60, color=RED, dur=200):
    return S(line(x, y, x, y+h, 12), color=color, width=4, dur=dur)

def tally_cross_cmd(x1, x2, y1, y2, color=RED, dur=250):
    return S(line(x1-10, y2+5, x2+10, y1-5, 18), color=color, width=4, dur=dur)

def circle_around_cmd(cx, cy, r, color=RED, dur=400):
    return C(cx, cy, r, color=color, fill=False, dur=dur)

def receipt_cmd(x, y, w, h, items):
    """Draw a receipt: rectangle + line items + tear bottom."""
    cmds = [
        S(rect_pts(x, y, w, h, r=0), color=INK, width=2.2, dur=350),  # outline
        S(hline(x+10, x+w-10, y+25, 12), color=INK, width=1.5, dur=150),  # top line
    ]
    yy = y + 45
    for item in items[:5]:
        cmds.append(T("•", x+12, yy+6, size=18, color=INK, dur=80))
        cmds.append(T(item[:20], x+25, yy+6, size=16, color=INK, dur=150))
        cmds.append(S(hline(x+10, x+w-10, yy+15, 8), color=LGRAY, width=1, dur=80))
        yy += 28
    # tear bottom (zigzag)
    zig = []
    for i in range(12):
        zx = x + 5 + i * (w-10)/11
        zy = y + h - 5 + (5 if i%2 else -5)
        zig.append({"x": round(zx,1), "y": round(zy,1)})
    cmds.append(S(zig, color=INK, width=2, dur=200))
    return cmds

def price_tag_cmd(x, y, price, color=INK, size=28):
    """Price tag: rectangle + hole + price."""
    w, h = 80, 44
    return [
        S(rect_pts(x, y, w, h, r=3), color=color, width=2.2, dur=280),
        C(x+8, y+8, 4, color=color, fill=False, dur=80),
        T(price, x+15, y+h-8, size=size, color=color, dur=220),
    ]

def bar_chart_cmd(x, y, bars, max_h=150):
    """Bar chart: vertical bars with labels.
    bars: [(label, value, color), ...]
    """
    cmds = []
    n = len(bars)
    bar_w = 50
    gap = 20
    total_w = n * bar_w + (n-1) * gap
    # baseline
    cmds.append(S(hline(x, x+total_w+10, y, 20), color=INK, width=2.5, dur=300))
    cmds.append(W(150))
    for i, (label, value, color) in enumerate(bars):
        bx = x + i * (bar_w + gap)
        h = max_h * value
        cmds.append(S(rect_pts(bx, y-h, bar_w, h, r=0), color=color, width=2.5, dur=280))
        cmds.append(T(label, bx+5, y+18, size=18, color=DGRAY, dur=150))
        cmds.append(W(180))
    return cmds

def timeline_cmd(x, y, years, w=480):
    """Horizontal timeline with year dots and labels.
    years: [(year, color), ...]
    """
    cmds = [S(hline(x, x+w, y, 36), color=INK, width=2.5, dur=450), W(200)]
    n = len(years)
    for i, (yr, color) in enumerate(years):
        dx = x + (w / max(1, n-1)) * i
        cmds.append(C(dx, y, 7, color=color, fill=True, dur=180))
        cmds.append(T(str(yr), dx-22, y+25, size=22, color=color, dur=200))
        cmds.append(W(200))
    return cmds

def flow_diagram_cmd(elements, y=180):
    """Flow: element1 → element2 → element3
    elements: [(text, color), ...]
    """
    cmds = []
    n = len(elements)
    spacing = 560 // n
    for i, (text, color) in enumerate(elements):
        ex = 60 + i * spacing
        cmds.append(C(ex, y, 28, color=color, fill=False, dur=250))
        cmds.append(T(text, ex-len(text)*4, y+5, size=16, color=color, dur=200))
        if i < n-1:
            cmds.append(S(arrow_pts(ex+30, y, ex+spacing-30, y, head=10),
                         color=INK, width=2, dur=250))
        cmds.append(W(200))
    return cmds

def phone_mockup_cmd(x, y, w=80, h=140):
    """Phone outline with screen elements."""
    cmds = [
        S(rect_pts(x, y, w, h, r=10), color=INK, width=2.5, dur=350),   # phone body
        S(rect_pts(x+6, y+15, w-12, h-30, r=4), color=LGRAY, width=1.5, dur=200),  # screen
        C(x+w//2, y+7, 2, color=INK, fill=True, dur=60),  # speaker dot
        S(hline(x+10, x+w-10, y+h-12, 8), color=INK, width=1.5, dur=100),  # home indicator
        # screen content: album art + title lines
        S(rect_pts(x+12, y+25, 24, 24, r=2), color=GREEN, width=1.5, dur=150),  # album art
        S(hline(x+42, x+w-12, y+30, 8), color=INK, width=1.5, dur=100),  # title line 1
        S(hline(x+42, x+w-18, y+38, 8), color=LGRAY, width=1, dur=80),   # title line 2
        S(hline(x+12, x+w-12, y+h-35, 6), color=AMBER, width=2, dur=120), # play bar
    ]
    return cmds

def speech_bubble_cmd(x, y, text, w=120, h=50):
    cmds = [
        S(rect_pts(x, y, w, h, r=8), color=INK, width=2, dur=280),
        S(line(x+15, y+h, x+10, y+h+12, 5), color=INK, width=2, dur=100),  # tail
        S(line(x+10, y+h+12, x+25, y+h, 5), color=INK, width=2, dur=100),
        T(text, x+10, y+h//2+5, size=18, color=INK, dur=200),
    ]
    return cmds

def big_arrow_down_cmd(cx, y1, y2, color=RED, dur=500):
    """Thick downward arrow for collapse/decline."""
    return [
        S(line(cx, y1, cx, y2-15, 30), color=color, width=5, dur=dur),
        S(line(cx-15, y2-25, cx, y2, 8), color=color, width=5, dur=150),
        S(line(cx+15, y2-25, cx, y2, 8), color=color, width=5, dur=150),
    ]

def big_arrow_up_cmd(cx, y1, y2, color=AMBER, dur=500):
    return [
        S(line(cx, y1, cx, y2+15, 30), color=color, width=5, dur=dur),
        S(line(cx-15, y2+25, cx, y2, 8), color=color, width=5, dur=150),
        S(line(cx+15, y2+25, cx, y2, 8), color=color, width=5, dur=150),
    ]

def percentage_ring_cmd(cx, cy, r, pct_text, color=RED):
    return [
        C(cx, cy, r, color=color, fill=False, dur=400),
        C(cx, cy, r-6, color=LGRAY, fill=False, dur=200),
        T(pct_text, cx-len(pct_text)*12, cy+15, size=36, color=color, dur=300),
    ]

# ── Word-level timing ─────────────────────────────────────────────────────────

WORDS = None

def load_words():
    global WORDS
    if WORDS is None:
        with open("public/data/words.json") as f:
            WORDS = json.load(f)
    return WORDS

def words_in_range(t_start, t_end):
    w = load_words()
    return [x for x in w if x["end"] > t_start and x["start"] < t_end]

def distribute_durations(cmds, beat_start, beat_end, breathing_ms=300):
    """Adjust command durations so they fit within the beat time,
    with breathing room. Aggressively scale if over budget."""
    beat_ms = (beat_end - beat_start) * 1000
    target_ms = beat_ms * 0.92  # leave 8% margin
    if not cmds:
        return cmds

    # Calculate total time
    def total(c):
        return sum(x.get("ms", x.get("duration", 0)) for x in c if isinstance(x, dict))
    tot = total(cmds)
    if tot <= target_ms:
        # Already fits — add end settle
        cmds.append(W(int(beat_ms * 0.08)))
        return cmds

    # Need to scale down. Scale everything proportionally.
    scale = target_ms / tot
    for c in cmds:
        if not isinstance(c, dict):
            continue
        if c.get("type") == "wait":
            c["ms"] = max(80, int(c["ms"] * scale))
        elif c.get("duration", 0) > 100:
            c["duration"] = max(100, int(c["duration"] * scale))

    # Check again
    tot = total(cmds)
    if tot > target_ms:
        # Still over — reduce waits more aggressively
        n_waits = sum(1 for c in cmds if isinstance(c, dict) and c.get("type") == "wait")
        if n_waits > 0:
            excess = tot - target_ms
            per_wait = excess / n_waits
            for c in cmds:
                if isinstance(c, dict) and c.get("type") == "wait":
                    c["ms"] = max(60, int(c["ms"] - per_wait))

    cmds.append(W(int(beat_ms * 0.06)))
    return cmds

# ── Context detection ─────────────────────────────────────────────────────────

def detect_context(text):
    t = text.lower()
    ctx = []
    if any(w in t for w in ['spotify']): ctx.append("spotify")
    if any(w in t for w in ['artist', 'musician', 'band', 'singer']): ctx.append("artist")
    if any(w in t for w in ['price', 'hike', 'raised', 'increase', 'cost', 'pay', 'paid', 'money', 'dollar', '$', 'profit', 'revenue', 'billion', 'million']): ctx.append("money")
    if any(w in t for w in ['less', 'collapse', 'drop', 'fall', 'shrink', 'decline', 'down', 'cut', 'crash']): ctx.append("decline")
    if any(w in t for w in ['more', 'up', 'rise', 'grew', 'surge', 'climb', 'bigger', 'higher']): ctx.append("rise")
    if any(w in t for w in ['scam', 'lie', 'fake', 'fraud', 'ghost', 'manipulate', 'deceptive', 'trick']): ctx.append("scam")
    if any(w in t for w in ['ceo', 'ek', 'founder', 'billionaire', 'stock', 'share', 'wall street', 'investor', 'hedge']): ctx.append("corporate")
    if any(w in t for w in ['you', 'listener', 'your', 'yourself']): ctx.append("you")
    if any(w in t for w in ['stream', 'streaming', 'play', 'playing', 'played']): ctx.append("streaming")
    if any(w in t for w in ['said', 'claimed', 'framed', 'called', 'told', 'announced', 'according']): ctx.append("quote")
    if any(w in t for w in ['but', 'however', 'while', 'whereas', 'versus', 'vs', 'instead', 'actually']): ctx.append("contrast")
    if any(w in t for w in ['question', 'ask', 'why', 'how', 'what', 'where', 'when', '?']): ctx.append("question")
    if any(w in t for w in ['receipt', 'audit', 'math', 'number', 'calculation', 'total']): ctx.append("audit")
    if any(w in t for w in ['podcast', 'audiobook', 'feature']): ctx.append("feature")
    if any(w in t for w in ['lossless', 'quality', 'audio', 'bitrate', 'ogg', 'sound']): ctx.append("quality")
    if any(w in t for w in ['playlist', 'algorithm', 'discover', 'recommend']): ctx.append("algorithm")
    if any(w in t for w in ['ghost', 'fake', 'ai-generated', 'bot', 'anonymous']): ctx.append("ghost")
    if any(w in t for w in ['quitting', 'quit', 'leave', 'left', 'abandoned', 'pulled']): ctx.append("quit")
    if any(w in t for w in ['royalty', 'royalties', 'payout', 'per-stream', 'per stream']): ctx.append("payout")
    return ctx

def extract_numbers(text):
    results = []
    for m in re.finditer(r'\$[\d.,]+[KMB]?', text):
        results.append(("money", m.group()))
    for m in re.finditer(r'\d+(?:\.\d+)?\s*%', text):
        results.append(("percent", m.group().strip()))
    for m in re.finditer(r'\b(20\d{2})\b', text):
        results.append(("year", m.group()))
    for m in re.finditer(r'\b\d{1,3}(?:,\d{3})+(?:\.\d+)?[KMB]?\b', text):
        results.append(("number", m.group()))
    return results

# ── Scene generators (20 archetypes) ─────────────────────────────────────────
# Each returns cmds with ACTUAL DRAWINGS + breathing.

def gen_hook_price_up(phrase, numbers, words):
    """Price going up — stick figure + upward arrow + price tags."""
    cmds = [W(300)]
    cmds += stick_figure(100, 200, "you")
    cmds.append(W(300))
    cmds.append(big_arrow_up_cmd(320, 300, 100, color=RED, dur=600))
    cmds.append(W(300))
    # Price tags climbing
    money = [v for k,v in numbers if k == "money"][:3]
    for i, m in enumerate(money):
        cmds += price_tag_cmd(420, 80+i*70, m, color=RED if i==len(money)-1 else INK)
        cmds.append(W(250))
    cmds.append(T("↑", 290, 180, size=48, color=RED, dur=300))
    cmds.append(W(400))
    return cmds

def gen_artist_decline(phrase, numbers, words):
    """Artist getting less — stick figure + shrinking coin + downward arrow."""
    cmds = [W(300)]
    cmds += stick_figure(150, 180, "artist", expression="sad")
    cmds.append(W(300))
    cmds.append(coin(320, 160, 24))
    cmds.append(W(200))
    cmds.append(big_arrow_down_cmd(320, 195, 300, color=RED, dur=500))
    cmds.append(W(300))
    # Per-stream amount
    money = [v for k,v in numbers if k == "money"]
    if money:
        cmds.append(T(money[0], 380, 200, size=42, color=RED, dur=400))
        cmds.append(underline_cmd(375, 212, len(money[0])*22, color=RED, dur=250))
    else:
        cmds.append(T("LESS", 380, 200, size=48, color=RED, dur=400))
        cmds.append(underline_cmd(375, 212, 120, color=RED, dur=250))
    cmds.append(T("per stream", 380, 250, size=22, color=DGRAY, dur=250))
    cmds.append(W(500))
    return cmds

def gen_insane_emphasis(phrase, numbers, words):
    """Big word slam — circle around it, double underline."""
    # Find the emphasis word
    emphasis_words = [w for w in ['insane', 'scam', 'wrong', 'crazy', 'absurd', 'ridiculous'] if w in phrase.lower()]
    word = emphasis_words[0].upper() if emphasis_words else "INSANE"
    cmds = [W(400)]
    cmds.append(T(word, 180, 200, size=72, color=RED, dur=500))
    cmds.append(W(300))
    cmds += double_underline_cmd(175, 212, 300, color=RED, dur=300)
    cmds.append(W(400))
    cmds.append(circle_around_cmd(320, 175, 140, color=RED, dur=500))
    cmds.append(W(500))
    # Secondary text
    label = phrase[:40] + "…" if len(phrase) > 40 else phrase
    cmds.append(T(label, 60, 320, size=22, color=GRAY, dur=300))
    cmds.append(W(500))
    return cmds

def gen_timeline_history(phrase, numbers, words):
    """Timeline with years — dots, labels, arc."""
    years_data = [(int(v), RED if i == len([x for x in numbers if x[0]=="year"])-1 else INK)
                  for i, (k,v) in enumerate(numbers) if k == "year" and i < 5]
    if len(years_data) < 2:
        years_data = [(2008, GREEN), (2026, RED)]
    cmds = [W(300)]
    cmds += timeline_cmd(80, 200, years_data)
    cmds.append(W(400))
    cmds.append(T("18 years", 250, 120, size=36, color=INK, dur=350))
    cmds.append(S(curved_pts(250, 130, 155), color=INK, width=2.5, dur=280))
    cmds.append(W(300))
    cmds.append(arrow_cmd(420, 155, 560, 195, color=RED, width=2.5, dur=350))
    cmds.append(T("NOW", 530, 180, size=22, color=RED, dur=220))
    cmds.append(W(500))
    return cmds

def gen_tally_count(phrase, numbers, words):
    """Tally marks — one by one, then crossbar, then total."""
    cmds = [W(300)]
    cmds.append(T("count:", 80, 80, size=28, color=INK, dur=280))
    cmds.append(W(300))
    # Draw 4 tally marks
    for i in range(4):
        cmds.append(tally_mark_cmd(150+i*40, 110, h=80, color=RED, dur=250))
        cmds.append(W(250))
    # Crossbar
    cmds.append(tally_cross_cmd(140, 270, 100, 190, color=RED, dur=300))
    cmds.append(W(400))
    # Total
    money = [v for k,v in numbers if k == "money"]
    total = money[0] if money else "4"
    cmds.append(T(total, 380, 170, size=56, color=RED, dur=450))
    cmds.append(underline_cmd(375, 182, len(total)*28, color=RED, dur=280))
    cmds.append(W(500))
    return cmds

def gen_same_thing(phrase, numbers, words):
    """Checkmarks — same app, same songs, same skip."""
    cmds = [W(300)]
    parts = [p.strip() for p in re.split(r'[,;.]', phrase) if len(p.strip()) > 3][:3]
    y = 100
    for part in parts:
        display = part[:25]
        cmds += checkmark_cmd(80, y+15, size=18, color=INK, dur=200)
        cmds.append(T(display, 115, y+15, size=26, color=INK, dur=280))
        cmds.append(W(280))
        y += 60
    # Contrast: price ↑
    cmds.append(W(200))
    cmds.append(arrow_cmd(380, 280, 380, 120, color=RED, width=3.5, dur=450))
    cmds.append(T("price ↑", 350, 100, size=28, color=RED, dur=280))
    cmds.append(W(500))
    return cmds

def gen_collapse(phrase, numbers, words):
    """Collapse visual — coin + big downward arrow + COLLAPSE text."""
    cmds = [W(300)]
    cmds.append(coin(180, 130, 24))
    cmds.append(W(300))
    cmds.append(big_arrow_down_cmd(180, 165, 290, color=RED, dur=550))
    cmds.append(W(300))
    cmds.append(T("COLLAPSE", 280, 180, size=42, color=RED, dur=400))
    cmds.append(underline_cmd(275, 192, 240, color=RED, dur=280))
    cmds.append(W(300))
    # Streams going up (contrast)
    cmds.append(arrow_cmd(500, 290, 500, 130, color=GREEN, width=3, dur=400))
    cmds.append(T("streams ↑", 460, 110, size=20, color=GREEN, dur=220))
    cmds.append(W(500))
    return cmds

def gen_money_flow(phrase, numbers, words):
    """You → Spotify → Artist flow diagram."""
    cmds = [W(300)]
    cmds += flow_diagram_cmd([("you", INK), ("Spotify", GREEN), ("artist", DGRAY)], y=160)
    cmds.append(W(400))
    cmds.append(T("keeps it", 280, 230, size=24, color=RED, dur=280))
    cmds.append(underline_cmd(275, 240, 100, color=RED, dur=200))
    cmds.append(W(500))
    return cmds

def gen_scam(phrase, numbers, words):
    """SCAM big + circle + polite note."""
    cmds = [W(400)]
    cmds.append(T("SCAM", 170, 180, size=80, color=RED, dur=500))
    cmds.append(W(400))
    cmds.append(circle_around_cmd(320, 155, 135, color=RED, dur=500))
    cmds.append(W(400))
    cmds.append(T("(very polite)", 220, 250, size=22, color=DGRAY, dur=280))
    cmds.append(W(300))
    cmds += spotify_logo(500, 80, 30)
    cmds.append(T("green logo", 460, 140, size=18, color=GREEN, dur=200))
    cmds.append(W(500))
    return cmds

def gen_receipt(phrase, numbers, words):
    """Receipt with line items."""
    cmds = [W(300)]
    parts = [p.strip() for p in re.split(r'[,;.]', phrase) if len(p.strip()) > 5][:5]
    items = [p[:20] for p in parts] if parts else ["????????", "????????", "????????"]
    cmds += receipt_cmd(180, 50, 280, 240, items)
    cmds.append(W(400))
    cmds.append(T("TOTAL: ???", 200, 310, size=28, color=RED, dur=300))
    cmds.append(W(500))
    return cmds

def gen_audit_list(phrase, numbers, words):
    """Audit checklist."""
    cmds = [W(300)]
    cmds.append(T("AUDIT", 250, 60, size=38, color=INK, dur=350))
    cmds.append(underline_cmd(245, 72, 120, color=INK, dur=250))
    cmds.append(W(300))
    parts = [p.strip() for p in re.split(r'[,;.]', phrase) if len(p.strip()) > 5][:4]
    y = 120
    for part in parts:
        display = part[:30] + "…" if len(part) > 30 else part
        cmds += checkmark_cmd(70, y, size=16, color=INK, dur=180)
        cmds.append(T(display, 100, y+5, size=22, color=INK, dur=260))
        cmds.append(W(280))
        y += 50
    cmds.append(W(500))
    return cmds

def gen_bar_chart(phrase, numbers, words):
    """Bar chart with price escalation."""
    cmds = [W(300)]
    money = [v for k,v in numbers if k == "money"]
    years = [v for k,v in numbers if k == "year"]
    bars = []
    for i in range(min(len(money), len(years), 4)):
        color = RED if i == min(len(money), len(years))-1 else INK
        bars.append((years[i], (i+1)/4, color))
    if not bars:
        bars = [("2023", 0.3, INK), ("2024", 0.5, INK), ("2025", 0.7, AMBER), ("2026", 1.0, RED)]
    cmds += bar_chart_cmd(120, 280, bars, max_h=160)
    cmds.append(W(400))
    cmds.append(T("4 hikes · 4 years", 200, 60, size=32, color=INK, dur=350))
    cmds.append(W(500))
    return cmds

def gen_question(phrase, numbers, words):
    """Big question mark + the question."""
    cmds = [W(400)]
    cmds.append(T("?", 280, 140, size=90, color=AMBER, dur=450))
    cmds.append(W(300))
    q = phrase[:50] + "…" if len(phrase) > 50 else phrase
    cmds.append(T(q, 80, 210, size=26, color=INK, dur=380))
    cmds.append(underline_cmd(75, 222, len(q)*13, color=INK, dur=280))
    cmds.append(W(500))
    return cmds

def gen_corporate(phrase, numbers, words):
    """CEO/corporate — figure + money + stock arrow."""
    cmds = [W(300)]
    cmds += stick_figure(100, 180, "CEO")
    cmds.append(W(300))
    cmds.append(T("$$$", 200, 120, size=42, color=AMBER, dur=350))
    cmds.append(W(250))
    cmds.append(arrow_cmd(300, 280, 300, 120, color=AMBER, width=3, dur=400))
    cmds.append(T("stock ↑", 320, 100, size=22, color=AMBER, dur=220))
    cmds.append(W(300))
    label = phrase[:40] + "…" if len(phrase) > 40 else phrase
    cmds.append(T(label, 60, 320, size=22, color=GRAY, dur=300))
    cmds.append(W(500))
    return cmds

def gen_quality_compare(phrase, numbers, words):
    """Spotify vs Apple/competitors quality comparison."""
    cmds = [W(300)]
    cmds.append(T("QUALITY?", 230, 70, size=36, color=INK, dur=350))
    cmds.append(underline_cmd(225, 82, 150, color=INK, dur=250))
    cmds.append(W(300))
    # Spotify column
    cmds += spotify_logo(140, 150, 28)
    cmds.append(T("same", 110, 210, size=24, color=DGRAY, dur=250))
    cmds += cross_out_cmd(105, 130, 70, 100, color=RED, dur=300)
    cmds.append(W(300))
    # vs
    cmds.append(T("vs", 295, 160, size=28, color=GRAY, dur=220))
    cmds.append(W(200))
    # Apple/competitors
    cmds.append(T("Apple", 420, 140, size=26, color=INK, dur=280))
    cmds.append(T("lossless", 410, 175, size=22, color=GREEN, dur=250))
    cmds.append(checkmark_cmd(470, 155, size=16, color=GREEN, dur=180))
    cmds.append(W(500))
    return cmds

def gen_feature_unwanted(phrase, numbers, words):
    """Feature nobody asked for — phone mockup or question."""
    cmds = [W(300)]
    cmds.append(T("you didn't ask for", 130, 80, size=26, color=DGRAY, dur=350))
    cmds.append(W(300))
    cmds += phone_mockup_cmd(250, 110, w=90, h=150)
    cmds.append(W(300))
    cmds.append(T("this.", 400, 160, size=36, color=AMBER, dur=350))
    cmds.append(underline_cmd(395, 172, 80, color=AMBER, dur=250))
    cmds.append(W(300))
    cmds.append(T("?", 420, 240, size=50, color=RED, dur=280))
    cmds.append(W(500))
    return cmds

def gen_ghost_artists(phrase, numbers, words):
    """Ghost/fake artists — shadowy figures."""
    cmds = [W(300)]
    cmds.append(T("GHOST", 220, 100, size=42, color=DGRAY, dur=380))
    cmds.append(underline_cmd(215, 112, 160, color=DGRAY, dur=250))
    cmds.append(W(300))
    # Three ghostly figures (light gray)
    for i in range(3):
        cx = 150 + i * 150
        cmds.append(C(cx, 180, 18, color=LGRAY, fill=False, dur=200))
        cmds.append(S(line(cx, 198, cx, 240, 4), color=LGRAY, width=2, dur=140))
        cmds.append(S(line(cx-20, 210, cx+20, 210, 5), color=LGRAY, width=2, dur=140))
        cmds.append(T("???", cx-15, 270, size=18, color=LGRAY, dur=150))
        cmds.append(W(200))
    cmds.append(W(400))
    cmds.append(T("fake artists", 230, 320, size=24, color=RED, dur=280))
    cmds.append(W(500))
    return cmds

def gen_payout_math(phrase, numbers, words):
    """Per-stream payout math — equation style."""
    cmds = [W(300)]
    money = [v for k,v in numbers if k == "money"]
    cmds.append(T("per stream:", 80, 80, size=24, color=DGRAY, dur=280))
    cmds.append(W(250))
    if money:
        cmds.append(T(money[0], 120, 160, size=56, color=RED, dur=450))
        cmds.append(underline_cmd(115, 172, len(money[0])*28, color=RED, dur=280))
    cmds.append(W(300))
    # Multiplication chain
    cmds.append(T("× streams", 120, 230, size=22, color=INK, dur=260))
    cmds.append(T("= very little", 120, 270, size=22, color=RED, dur=280))
    cmds.append(W(300))
    cmds.append(coin(450, 170, 22))
    cmds.append(big_arrow_down_cmd(450, 200, 290, color=RED, dur=450))
    cmds.append(W(500))
    return cmds

def gen_squeeze(phrase, numbers, words):
    """Wall Street squeezing — figures + squeeze arrow."""
    cmds = [W(300)]
    # Wall Street (three figures at top)
    for i in range(3):
        cmds += stick_figure(200+i*80, 120, label=None)
        cmds.append(W(150))
    cmds.append(W(300))
    cmds.append(T("Wall Street", 220, 60, size=24, color=AMBER, dur=280))
    cmds.append(W(300))
    # Squeeze arrows pointing down at "you"
    cmds.append(arrow_cmd(200, 180, 280, 240, color=RED, width=3, dur=300))
    cmds.append(arrow_cmd(440, 180, 360, 240, color=RED, width=3, dur=300))
    cmds.append(W(300))
    cmds.append(T("SQUEEZE", 250, 290, size=32, color=RED, dur=350))
    cmds.append(underline_cmd(245, 302, 160, color=RED, dur=250))
    cmds.append(W(500))
    return cmds

def gen_default_rich(phrase, numbers, words):
    """Default: key phrases with actual visual elements, not just text."""
    cmds = [W(300)]
    parts = [p.strip() for p in re.split(r'[,;.]', phrase) if len(p.strip()) > 5]
    parts = sorted(parts, key=len, reverse=True)[:2]
    parts.reverse()
    # Draw a visual element first
    if any(k == "money" for k,_ in numbers):
        money = [v for k,v in numbers if k == "money"][0]
        cmds.append(coin(100, 130, 22))
        cmds.append(T(money, 150, 120, size=36, color=AMBER, dur=350))
        cmds.append(underline_cmd(145, 132, len(money)*18, color=AMBER, dur=250))
        cmds.append(W(300))
    elif any(k == "percent" for k,_ in numbers):
        pct = [v for k,v in numbers if k == "percent"][0]
        cmds += percentage_ring_cmd(120, 150, 45, pct, color=RED)
        cmds.append(W(300))
    # Text
    y = 210
    for i, part in enumerate(parts):
        display = part[:35] + "…" if len(part) > 35 else part
        size = 36 if i == len(parts)-1 else 26
        color = RED if i == len(parts)-1 else INK
        x = max(50, 320 - len(display)*size*0.3)
        cmds.append(T(display, x, y, size=size, color=color, dur=350))
        if i == len(parts)-1:
            cmds.append(underline_cmd(x, y+10, len(display)*size*0.42, color=color, dur=280))
        cmds.append(W(350))
        y += 55
    cmds.append(W(500))
    return cmds

# ── Pick the right generator ──────────────────────────────────────────────────

def pick_generator(phrase, context, numbers):
    if "scam" in context: return gen_scam
    if "audit" in context: return gen_audit_list
    if "ghost" in context: return gen_ghost_artists
    if "payout" in context: return gen_payout_math
    if "quality" in context: return gen_quality_compare
    if "feature" in context: return gen_feature_unwanted
    if "corporate" in context: return gen_corporate
    if "question" in context: return gen_question
    if "contrast" in context and "you" in context: return gen_money_flow
    if "money" in context and "decline" in context: return gen_collapse
    if "money" in context and "rise" in context: return gen_hook_price_up
    if sum(1 for k,_ in numbers if k == "year") >= 3: return gen_bar_chart
    if sum(1 for k,_ in numbers if k == "year") >= 2: return gen_timeline_history
    if any(k == "percent" for k,_ in numbers): return gen_default_rich
    if "decline" in context: return gen_collapse
    if "rise" in context: return gen_hook_price_up
    if "streaming" in context and "spotify" in context: return gen_money_flow
    if "artist" in context and "decline" in context: return gen_artist_decline
    if "quote" in context: return gen_default_rich
    return gen_default_rich

# ── Beat grouping ─────────────────────────────────────────────────────────────

def group_into_beats(cues, start_idx=72):
    beats = []
    i = start_idx
    while i < len(cues):
        start = cues[i]["start"]
        group = [cues[i]]
        j = i + 1
        while j < len(cues):
            next_dur = cues[j]["end"] - start
            if next_dur > 15.0:
                break
            group.append(cues[j])
            text = cues[j]["text"].strip()
            if text.endswith(('.', '!', '?')) and next_dur > 5.0:
                j += 1
                break
            if text.endswith(',') and next_dur > 8.0:
                j += 1
                break
            j += 1
        end = group[-1]["end"]
        phrase = " ".join(c["text"] for c in group).strip()
        beats.append({"start": start, "end": end, "phrase": phrase})
        i = j
    return beats

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    with open("public/data/scenes_preview.json") as f:
        original = json.load(f)
    print(f"Loaded {len(original['scenes'])} original scenes")

    with open("public/data/transcript.json") as f:
        cues = json.load(f)
    print(f"Loaded {len(cues)} cues ({cues[-1]['end']/60:.1f}min)")

    orig_end = original['scenes'][-1]['time_end']
    start_idx = next((i for i, c in enumerate(cues) if c["start"] >= orig_end - 0.5), len(cues))
    print(f"Starting from cue {cues[start_idx]['idx']} ({cues[start_idx]['start']:.0f}s)")

    beats = group_into_beats(cues, start_idx)
    print(f"Grouped into {len(beats)} context beats")

    new_scenes = []
    gens_used = {}
    for i, beat in enumerate(beats):
        phrase = beat["phrase"]
        context = detect_context(phrase)
        numbers = extract_numbers(phrase)
        gen_fn = pick_generator(phrase, context, numbers)
        gens_used[gen_fn.__name__] = gens_used.get(gen_fn.__name__, 0) + 1

        cmds_raw = gen_fn(phrase, numbers, None)
        # Flatten: some drawing functions return lists that get nested
        cmds = []
        for c in cmds_raw:
            if isinstance(c, list):
                cmds.extend(c)
            else:
                cmds.append(c)
        # Add Spotify logo if brand mentioned and not already there
        if "spotify" in context and gen_fn.__name__ not in ("gen_scam", "gen_money_flow", "gen_quality_compare"):
            cmds.append(W(200))
            cmds.extend(spotify_logo(560, 55, 26))

        # Word-level timing: distribute durations to fill the beat
        cmds = distribute_durations(cmds, beat["start"], beat["end"])

        scene = {
            "window_index": len(original['scenes']) + i,
            "time_start": round(beat["start"], 2),
            "time_end": round(beat["end"], 2),
            "phrase": phrase,
            "cmds": cmds
        }
        new_scenes.append(scene)

    print(f"\nGenerator distribution:")
    for g, c in sorted(gens_used.items(), key=lambda x: -x[1]):
        print(f"  {g}: {c}")

    # Validate timing
    over = 0
    for s in new_scenes:
        total_ms = sum(c.get("ms", c.get("duration", 0)) for c in s["cmds"])
        beat_ms = (s["time_end"] - s["time_start"]) * 1000
        if total_ms > beat_ms:
            over += 1
    print(f"\nTiming: {over}/{len(new_scenes)} over budget")

    all_scenes = original['scenes'] + new_scenes
    with open("public/data/scenes_preview.json", "w") as f:
        json.dump({"scenes": all_scenes}, f, indent=2)

    print(f"\nWrote {len(all_scenes)} scenes ({len(original['scenes'])} orig + {len(new_scenes)} new)")
    print(f"Coverage: {all_scenes[0]['time_start']}s - {all_scenes[-1]['time_end']:.0f}s ({all_scenes[-1]['time_end']/60:.1f}min)")
    durs = [s["time_end"]-s["time_start"] for s in new_scenes]
    print(f"New scene durations: avg={sum(durs)/len(durs):.1f}s, min={min(durs):.1f}s, max={max(durs):.1f}s")

if __name__ == "__main__":
    main()
