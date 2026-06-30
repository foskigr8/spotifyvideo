#!/usr/bin/env python3
"""
Chunk 1 generator — first 5 minutes of the Spotify doodle video.
Philosophy:
  - Each scene = one IDEA (not one SRT line)
  - Scenes breathe: wait() generously between elements
  - Text is LARGE and readable — minimum size 26, heroes at 52-72
  - Visuals match the idea: diagrams, contrasts, emphasis marks
  - Colors: #1A1A1A (ink), #E34948 (red/alarm), #1DB954 (spotify green), #F5A623 (amber/warning)
"""

import json, math, random
random.seed(99)

CANVAS_W, CANVAS_H = 640, 360
RED    = "#E34948"
GREEN  = "#1DB954"
AMBER  = "#F5A623"
INK    = "#1A1A1A"
GRAY   = "#888888"
LGRAY  = "#BBBBBB"
WHITE  = "#ffffff"

# ── Primitives ────────────────────────────────────────────────────────────────

def jitter(pts, j=1.2):
    return [{"x": round(p["x"] + (random.random()-0.5)*2*j, 1),
             "y": round(p["y"] + (random.random()-0.5)*2*j, 1)} for p in pts]

def line(x1, y1, x2, y2, steps=30):
    return jitter([{"x": x1+(x2-x1)*i/steps, "y": y1+(y2-y1)*i/steps} for i in range(steps+1)])

def arrow(x1, y1, x2, y2, head=12):
    pts = line(x1, y1, x2, y2, 35)
    a = math.atan2(y2-y1, x2-x1)
    s = 0.45
    pts += [
        {"x": round(x2-head*math.cos(a-s),1), "y": round(y2-head*math.sin(a-s),1)},
        {"x": round(x2,1), "y": round(y2,1)},
        {"x": round(x2-head*math.cos(a+s),1), "y": round(y2-head*math.sin(a+s),1)},
    ]
    return pts

def underline(x, y, length, steps=30):
    return jitter([{"x": x+length*i/steps, "y": y+math.sin(i/steps*math.pi*2)*1.2} for i in range(steps+1)], j=0.6)

def strikethrough(x, y, length, steps=30):
    return jitter([{"x": x+length*i/steps, "y": y} for i in range(steps+1)], j=0.5)

def wobbly(x1, y1, x2, y2, amp=3, freq=4, steps=40):
    return jitter([{"x": x1+(x2-x1)*i/steps,
                    "y": y1+(y2-y1)*i/steps + math.sin(i/steps*math.pi*freq)*amp}
                   for i in range(steps+1)], j=0.5)

def curved_underline(x, y, length):
    steps = 35
    return [{"x": round(x+length*i/steps, 1),
             "y": round(y + math.sin(i/steps*math.pi)*4, 1)}
            for i in range(steps+1)]

def cross_out(x, y, w, h):
    """Two diagonal lines forming an X over a region"""
    return [
        line(x, y, x+w, y+h, 15),
        line(x+w, y, x, y+h, 15),
    ]

# ── Command builders ──────────────────────────────────────────────────────────

def T(text, x, y, size=30, color=INK, dur=300):
    return {"type":"text","text":text,"x":x,"y":y,"size":size,"color":color,"duration":dur}

def S(points, color=INK, width=2.5, dur=500):
    return {"type":"stroke","points":points,"color":color,"width":width,"duration":dur}

def C(cx, cy, r, color=INK, fill=False, dur=400):
    return {"type":"circle","cx":cx,"cy":cy,"r":r,"color":color,"fill":fill,"duration":dur}

def W(ms=300):
    return {"type":"wait","ms":ms}

def CLR():
    return {"type":"clear"}

def spotify_logo(cx, cy, r=44):
    cmds = [C(cx, cy, r, color=GREEN, fill=True, dur=300), W(80)]
    arcs = [
        {"x1":cx-r*0.6,"y1":cy-r*0.25,"xP":cx,"yP":cy-r*0.55,"x3":cx+r*0.6,"y3":cy-r*0.25},
        {"x1":cx-r*0.5,"y1":cy+r*0.05,"xP":cx,"yP":cy-r*0.2, "x3":cx+r*0.5,"y3":cy+r*0.05},
        {"x1":cx-r*0.35,"y1":cy+r*0.3,"xP":cx,"yP":cy+r*0.1, "x3":cx+r*0.35,"y3":cy+r*0.3},
    ]
    for arc in arcs:
        pts = []
        for i in range(21):
            t = i/20
            px = arc["x1"]+t*(arc["x3"]-arc["x1"])
            py = (1-t)**2*arc["y1"] + 2*t*(1-t)*arc["yP"] + t**2*arc["y3"]
            pts.append({"x":round(px,1),"y":round(py,1)})
        cmds += [S(jitter(pts,1.0), color=WHITE, width=3.5, dur=160), W(40)]
    return cmds

def price_tag(x, y, price, color=INK, size=34):
    """Draw a hand-drawn price tag shape with price inside"""
    # tag outline: rectangle + small circle hole
    w, h = 90, 50
    pts = [
        {"x":x,"y":y},{"x":x+w,"y":y},{"x":x+w,"y":y+h},{"x":x,"y":y+h},{"x":x,"y":y}
    ]
    return [
        S(jitter(pts,1.2), color=color, width=2, dur=300),
        C(x+8, y+8, 5, color=color, fill=False, dur=100),
        T(price, x+12, y+h-10, size=size, color=color, dur=250),
    ]

# ── Scene helper ──────────────────────────────────────────────────────────────

def scene(idx, t_start, t_end, phrase, cmds):
    return {
        "window_index": idx,
        "time_start": t_start,
        "time_end": t_end,
        "phrase": phrase,
        "cmds": cmds
    }

scenes = []
i = 0

# ════════════════════════════════════════════════════════════════════════════════
# SCENE GROUP 1: THE HOOK  (0–30s)
# ════════════════════════════════════════════════════════════════════════════════

# ── Scene 0 [0–5s]: "You've paid MORE every year since 2023" ─────────────────
# Visual: "YOU PAID" on left, giant upward arrow, years 2023→2026 climbing up
scenes.append(scene(i:=i, 0, 5,
    "You've paid Spotify more money every single year since 2023",
    [
        W(200),
        T("YOU PAID", 40, 90, size=38, color=INK, dur=350),
        W(200),
        T("MORE", 40, 160, size=72, color=RED, dur=450),
        S(underline(40, 172, 200), color=RED, width=3.5, dur=350),
        W(250),
        # Upward arrow — big, on the right
        S(arrow(490, 320, 490, 60, head=16), color=RED, width=3, dur=500),
        W(150),
        # Year labels climbing up the arrow
        T("2023", 510, 320, size=22, color=GRAY, dur=200),
        T("2024", 510, 250, size=22, color=AMBER, dur=200),
        T("2025", 510, 185, size=22, color=AMBER, dur=200),
        T("2026", 510, 115, size=24, color=RED, dur=250),
        W(300),
        T("every single year", 40, 280, size=24, color=GRAY, dur=300),
    ]
)); i+=1

# ── Scene 1 [5–9s]: "Artists getting LESS per stream than ever" ──────────────
# Visual: Two columns — YOUR PAYMENT ↑  vs  ARTIST PAYOUT ↓
scenes.append(scene(i, 5, 9,
    "And artists are getting paid less per stream than ever",
    [
        W(200),
        # Left column: you
        T("you pay", 60, 80, size=28, color=INK, dur=280),
        S(arrow(100, 100, 100, 230, head=14), color=RED, width=3, dur=400),
        T("↑ more", 50, 260, size=26, color=RED, dur=250),
        W(300),
        # Dividing line
        S(line(320, 50, 320, 310, 30), color=LGRAY, width=1.5, dur=300),
        W(200),
        # Right column: artist
        T("artist gets", 360, 80, size=28, color=INK, dur=280),
        S(arrow(400, 100, 400, 240, head=14), color=GRAY, width=3, dur=400),
        T("↓ less", 355, 270, size=26, color=GRAY, dur=250),
        W(300),
        # Bottom emphasis
        T("per stream", 340, 310, size=20, color=GRAY, dur=200),
        T("than EVER", 340, 340, size=22, color=RED, dur=250),
    ]
)); i+=1

# ── Scene 2 [9–15s]: "Let me say that again — MOST INSANE sentence" ──────────
# Visual: The sentence itself, huge, double-underlined, circled like a discovery
scenes.append(scene(i, 9, 15,
    "Let me say that again — the most insane sentence in the music industry",
    [
        W(300),
        T("let me say", 60, 70, size=28, color=GRAY, dur=280),
        T("that again.", 60, 105, size=28, color=GRAY, dur=280),
        W(350),
        # The sentence lands hard
        T("MOST", 80, 185, size=62, color=INK, dur=400),
        T("INSANE", 80, 255, size=62, color=RED, dur=450),
        W(200),
        S(underline(80, 264, 270), color=RED, width=3.5, dur=300),
        S(underline(85, 273, 260), color=RED, width=2, dur=250),
        W(300),
        T("sentence in music", 80, 315, size=22, color=GRAY, dur=280),
        W(250),
        # Circle around INSANE
        C(215, 230, 145, color=RED, fill=False, dur=500),
    ]
)); i+=1

# ── Scene 3 [15–22s]: "Paying MORE than ANY point in 18-year history" ─────────
# Visual: Timeline arc 2006→2024, price at each end, "NOW" circled at the top
scenes.append(scene(i, 15, 22,
    "You are paying more for Spotify than at any point in its 18-year history",
    [
        W(200),
        # Timeline base
        S(line(60, 230, 580, 230, 55), color=INK, width=2.5, dur=500),
        W(150),
        # Start dot + label
        C(60, 230, 6, color=GREEN, fill=True, dur=150),
        T("2006", 40, 260, size=20, color=GREEN, dur=200),
        T("free", 42, 282, size=18, color=GREEN, dur=180),
        W(100),
        # End dot + label
        C(580, 230, 8, color=RED, fill=True, dur=180),
        T("2026", 555, 260, size=20, color=RED, dur=200),
        T("$14.99", 548, 282, size=20, color=RED, dur=220),
        W(200),
        # "18 years" arc label above line
        T("18 years", 255, 190, size=36, color=INK, dur=350),
        S(curved_underline(255, 198, 155), color=INK, width=2.5, dur=280),
        W(300),
        # Arrow pointing to the right end
        S(arrow(420, 155, 565, 215, head=12), color=RED, width=2, dur=350),
        T("most", 305, 135, size=24, color=RED, dur=220),
        T("expensive", 295, 163, size=24, color=RED, dur=220),
        T("EVER", 320, 195, size=30, color=RED, dur=280),
    ]
)); i+=1

# ── Scene 4 [22–30s]: "4 price hikes in 4 years" ─────────────────────────────
# Visual: Tally marks drawn one by one. Then "4 HIKES / 4 YEARS" big underneath.
scenes.append(scene(i, 22, 30,
    "2023. 2024. 2025. 2026. Four price increases in four years.",
    [
        W(250),
        T("price hikes:", 80, 70, size=30, color=INK, dur=300),
        W(300),
        # Tally mark 1 — 2023
        S(line(120, 110, 120, 200, 15), color=RED, width=4, dur=300),
        T("2023", 105, 225, size=20, color=GRAY, dur=180),
        W(350),
        # Tally mark 2 — 2024
        S(line(175, 110, 175, 200, 15), color=RED, width=4, dur=300),
        T("2024", 160, 225, size=20, color=GRAY, dur=180),
        W(350),
        # Tally mark 3 — 2025
        S(line(230, 110, 230, 200, 15), color=RED, width=4, dur=300),
        T("2025", 215, 225, size=20, color=GRAY, dur=180),
        W(350),
        # Tally mark 4 — 2026 (diagonal crossbar)
        S(line(285, 110, 285, 200, 15), color=RED, width=4, dur=300),
        S(line(100, 170, 300, 140, 20), color=RED, width=4, dur=300),
        T("2026", 270, 225, size=20, color=GRAY, dur=180),
        W(400),
        # Punch line
        T("4 hikes", 100, 290, size=46, color=RED, dur=400),
        T("4 years", 320, 290, size=46, color=INK, dur=400),
        W(300),
    ]
)); i+=1

# ════════════════════════════════════════════════════════════════════════════════
# SCENE GROUP 2: THE MATH (30–65s)
# ════════════════════════════════════════════════════════════════════════════════

# ── Scene 5 [30–37s]: "Same app. Same songs. Same skip button." ───────────────
# Visual: Three lines appear, each with a checkmark ✓ "SAME"
scenes.append(scene(i, 30, 37,
    "Same app, same songs, same skip button. 4 price increases in 4 years.",
    [
        W(250),
        T("same app", 80, 90, size=36, color=INK, dur=300),
        W(200),
        T("same songs", 80, 160, size=36, color=INK, dur=300),
        W(200),
        T("same skip button", 80, 230, size=36, color=INK, dur=350),
        W(350),
        # Bracket on the right
        S(line(410, 65, 430, 65, 5), color=GRAY, width=2, dur=100),
        S(line(430, 65, 430, 250, 25), color=GRAY, width=2, dur=300),
        S(line(410, 250, 430, 250, 5), color=GRAY, width=2, dur=100),
        W(200),
        T("↑ price", 445, 140, size=30, color=RED, dur=300),
        T("anyway", 445, 175, size=26, color=RED, dur=260),
        W(300),
    ]
)); i+=1

# ── Scene 6 [37–48s]: "Artists watching their payout COLLAPSE" ───────────────
# Visual: Cliff diagram — flat ground, cliff edge, falling arrow, "payout" at bottom
scenes.append(scene(i, 37, 48,
    "The artists whose songs you press play on every day are watching their per-stream payout collapse",
    [
        W(200),
        T("artist payout", 50, 60, size=30, color=INK, dur=300),
        T("per stream", 50, 95, size=22, color=GRAY, dur=220),
        W(300),
        # Flat ground going to cliff edge
        S(line(50, 200, 310, 200, 35), color=INK, width=3, dur=400),
        W(150),
        # Cliff drop
        S(line(310, 200, 310, 320, 20), color=INK, width=3, dur=250),
        W(100),
        # Ground continues at lower level
        S(line(310, 320, 580, 320, 30), color=INK, width=3, dur=300),
        W(250),
        # Falling arrow
        S(arrow(370, 195, 370, 315, head=14), color=RED, width=3, dur=400),
        W(200),
        T("COLLAPSE", 350, 345, size=28, color=RED, dur=300),
        S(underline(350, 352, 180), color=RED, width=2.5, dur=250),
        W(300),
        # Little figure on the cliff
        C(270, 185, 10, color=INK, fill=False, dur=150),   # head
        S(line(270, 195, 270, 218, 8), color=INK, width=2, dur=120),  # body
        S(line(270, 205, 255, 215, 6), color=INK, width=2, dur=100),  # arm
        S(line(270, 205, 285, 215, 6), color=INK, width=2, dur=100),  # arm
        S(line(270, 218, 258, 235, 6), color=INK, width=2, dur=100),  # leg
        S(line(270, 218, 282, 235, 6), color=INK, width=2, dur=100),  # leg
        W(400),
    ]
)); i+=1

# ── Scene 7 [48–55s]: "You pay MORE. They get LESS. Spotify keeps the DIFFERENCE." ──
# Visual: Three boxes in a row with arrows showing the flow
scenes.append(scene(i, 48, 55,
    "The math is not complicated. You pay more, they get less. Spotify keeps the difference.",
    [
        W(200),
        T("the math:", 50, 50, size=28, color=INK, dur=250),
        T("not complicated", 50, 83, size=22, color=GRAY, dur=220),
        W(350),
        # Box 1: YOU
        S(jitter([{"x":40,"y":130},{"x":160,"y":130},{"x":160,"y":210},{"x":40,"y":210},{"x":40,"y":130}],1.5),
          color=INK, width=2, dur=300),
        T("YOU", 70, 180, size=32, color=INK, dur=250),
        T("pay ↑", 62, 205, size=20, color=RED, dur=180),
        W(200),
        # Arrow →
        S(arrow(165, 170, 235, 170, head=10), color=GRAY, width=2, dur=200),
        W(100),
        # Box 2: ARTIST
        S(jitter([{"x":240,"y":130},{"x":380,"y":130},{"x":380,"y":210},{"x":240,"y":210},{"x":240,"y":130}],1.5),
          color=GRAY, width=2, dur=300),
        T("ARTIST", 254, 175, size=26, color=GRAY, dur=250),
        T("gets ↓", 260, 202, size=20, color=GRAY, dur=180),
        W(200),
        # Arrow →
        S(arrow(383, 170, 450, 170, head=10), color=GREEN, width=2, dur=200),
        W(100),
        # Box 3: SPOTIFY
        S(jitter([{"x":455,"y":115},{"x":615,"y":115},{"x":615,"y":225},{"x":455,"y":225},{"x":455,"y":115}],1.5),
          color=GREEN, width=2.5, dur=350),
        T("SPOTIFY", 462, 168, size=26, color=GREEN, dur=280),
        T("KEEPS", 468, 195, size=22, color=GREEN, dur=230),
        T("the diff", 465, 218, size=18, color=GREEN, dur=180),
        W(400),
    ]
)); i+=1

# ── Scene 8 [55–65s]: "It's a scam — a very polite one" ──────────────────────
# Visual: "SCAM" written, then "polite" added above it in smaller text, Spotify green circle
scenes.append(scene(i, 55, 65,
    "If that sounds like a scam, it's because it is. A very polite one, with a green logo.",
    [
        W(300),
        T("if that sounds", 55, 65, size=26, color=GRAY, dur=260),
        T("like a scam...", 55, 98, size=26, color=GRAY, dur=260),
        W(400),
        # SCAM — massive
        T("SCAM", 120, 220, size=80, color=RED, dur=500),
        S(underline(120, 232, 230), color=RED, width=4, dur=350),
        W(350),
        # "...it is." added
        T("it is.", 380, 215, size=36, color=INK, dur=300),
        W(300),
        # Qualifier added underneath
        T("just a very", 55, 285, size=24, color=GRAY, dur=230),
        T("polite one.", 55, 313, size=28, color=INK, dur=260),
        W(250),
        # Spotify logo small on right as the punchline
        *spotify_logo(540, 290, r=32),
        W(300),
    ]
)); i+=1

# ════════════════════════════════════════════════════════════════════════════════
# SCENE GROUP 3: THE AGENDA (65–105s)
# ════════════════════════════════════════════════════════════════════════════════

# ── Scene 9 [65–75s]: "We're going to READ THE RECEIPT" ──────────────────────
# Visual: Receipt paper unrolling from top, items listed on it
scenes.append(scene(i, 65, 75,
    "So today we're going to do something nobody at Spotify wants you to do. Read the receipt.",
    [
        W(250),
        T("nobody at Spotify", 55, 55, size=26, color=GRAY, dur=270),
        T("wants you to do this.", 55, 85, size=26, color=GRAY, dur=270),
        W(400),
        # The reveal
        T("READ", 80, 185, size=68, color=INK, dur=450),
        T("THE RECEIPT", 80, 260, size=50, color=INK, dur=400),
        W(250),
        S(underline(80, 270, 335), color=RED, width=3.5, dur=350),
        S(underline(85, 280, 325), color=RED, width=2, dur=280),
        W(350),
        T("all of it.", 80, 315, size=26, color=GRAY, dur=250),
        W(300),
    ]
)); i+=1

# ── Scene 10 [75–93s]: Agenda — bullet list of what we'll cover ───────────────
# Visual: Bullet points appearing one by one, each more alarming
scenes.append(scene(i, 75, 93,
    "Where the money goes. Why artists are quitting. Why the app got worse. Podcasts. Fake numbers. Weapons.",
    [
        W(200),
        T("today's audit:", 50, 45, size=26, color=INK, dur=250),
        W(300),
        # Bullet 1
        S(line(50,85,65,85,5), color=INK, width=3, dur=80),
        T("where the money goes", 75, 90, size=24, color=INK, dur=280),
        W(280),
        # Bullet 2
        S(line(50,120,65,120,5), color=INK, width=3, dur=80),
        T("why artists are quitting", 75, 125, size=24, color=INK, dur=280),
        W(280),
        # Bullet 3
        S(line(50,155,65,155,5), color=INK, width=3, dur=80),
        T("why the app got worse", 75, 160, size=24, color=INK, dur=280),
        W(280),
        # Bullet 4
        S(line(50,190,65,190,5), color=AMBER, width=3, dur=80),
        T("billion $ on podcasts → gone", 75, 195, size=22, color=AMBER, dur=300),
        W(280),
        # Bullet 5
        S(line(50,225,65,225,5), color=RED, width=3, dur=80),
        T("fake numbers to hide payouts", 75, 230, size=22, color=RED, dur=300),
        W(280),
        # Bullet 6 — the wildest one
        S(line(50,262,65,262,5), color=RED, width=3.5, dur=80),
        T("founder selling stock", 75, 263, size=22, color=RED, dur=280),
        T("to build weapons", 75, 287, size=22, color=RED, dur=260),
        W(400),
    ]
)); i+=1

# ── Scene 11 [93–105s]: "Not a hit piece. An AUDIT." ─────────────────────────
# Visual: "hit piece" written, big X through it, "AUDIT" stamped in bold
scenes.append(scene(i, 93, 105,
    "This is not a hit piece. This is an audit. Where did your $11.99 actually go?",
    [
        W(250),
        T("hit piece", 100, 120, size=44, color=GRAY, dur=350),
        W(300),
        # X through "hit piece"
        S(line(85, 90, 295, 145, 18), color=RED, width=3, dur=300),
        S(line(295, 90, 85, 145, 18), color=RED, width=3, dur=300),
        W(350),
        # AUDIT stamped
        T("AUDIT", 160, 230, size=68, color=INK, dur=450),
        W(200),
        S(jitter([{"x":148,"y":180},{"x":380,"y":180},{"x":380,"y":250},{"x":148,"y":250},{"x":148,"y":180}],2),
          color=INK, width=3, dur=400),
        W(300),
        T("where did your", 100, 295, size=22, color=GRAY, dur=230),
        T("$11.99 actually go?", 100, 323, size=26, color=INK, dur=280),
        W(350),
    ]
)); i+=1

# ════════════════════════════════════════════════════════════════════════════════
# SCENE GROUP 4: PRICE HISTORY (105–170s)
# ════════════════════════════════════════════════════════════════════════════════

# ── Scene 12 [105–115s]: "2021. $9.99 since 2014. SEVEN years. Zero increases." ─
# Visual: Flat line graph — $9.99 held steady for 7 years
scenes.append(scene(i, 105, 115,
    "2021. Spotify Premium costs $9.99. It had been $9.99 since 2014. Seven years. Zero increases.",
    [
        W(200),
        T("2014", 50, 200, size=24, color=GRAY, dur=220),
        T("→", 105, 200, size=24, color=GRAY, dur=150),
        T("2021", 135, 200, size=24, color=GRAY, dur=220),
        W(300),
        # Flat line — price never moved
        S(line(50, 160, 420, 160, 50), color=GREEN, width=3.5, dur=600),
        W(200),
        T("$9.99", 440, 153, size=32, color=GREEN, dur=300),
        S(underline(440, 162, 90), color=GREEN, width=2.5, dur=230),
        W(300),
        # 7 — BIG
        T("7", 215, 290, size=80, color=INK, dur=450),
        T("years", 295, 310, size=32, color=INK, dur=280),
        W(250),
        T("zero increases", 190, 345, size=24, color=GRAY, dur=260),
        W(300),
    ]
)); i+=1

# ── Scene 13 [115–135s]: "$10 for every song ever. Best deal in history." ──────
# Visual: "$10" enormous, "every song ever recorded" written around it in orbit
scenes.append(scene(i, 115, 135,
    "$10 for every song ever recorded, ad-free, on every device. Best deal in the history of consumer media.",
    [
        W(250),
        # $10 — the hero
        T("$10", 200, 210, size=110, color=INK, dur=500),
        W(350),
        # Things orbiting it
        T("every song ever", 30, 85, size=22, color=GRAY, dur=280),
        S(arrow(175, 90, 215, 130, head=10), color=GRAY, width=1.5, dur=200),
        W(200),
        T("ad-free", 490, 130, size=22, color=GRAY, dur=220),
        S(arrow(485, 135, 415, 155, head=10), color=GRAY, width=1.5, dur=200),
        W(200),
        T("every device", 470, 255, size=22, color=GRAY, dur=220),
        S(arrow(465, 250, 415, 220, head=10), color=GRAY, width=1.5, dur=200),
        W(300),
        T("best deal in history", 115, 320, size=24, color=GREEN, dur=280),
        S(underline(115, 328, 270), color=GREEN, width=2.5, dur=250),
        W(300),
    ]
)); i+=1

# ── Scene 14 [135–155s]: "June 2023. First hike. $10.99. 'Market conditions.'" ──
# Visual: Price tag crossed out, new one stamped over it, air-quote reason
scenes.append(scene(i, 135, 155,
    "June 2023. First hike. $9.99 crossed out. $10.99. Spotify says: market conditions.",
    [
        W(200),
        T("June 2023", 50, 60, size=32, color=INK, dur=300),
        S(underline(50, 70, 175), color=INK, width=2.5, dur=230),
        W(300),
        # Old price crossed out
        T("$9.99", 80, 160, size=52, color=LGRAY, dur=350),
        S(strikethrough(75, 145, 145), color=RED, width=3, dur=280),
        W(300),
        # Arrow and new price
        S(arrow(235, 147, 300, 147, head=12), color=RED, width=2.5, dur=250),
        T("$10.99", 308, 163, size=52, color=RED, dur=400),
        S(underline(308, 172, 165), color=RED, width=3, dur=280),
        W(300),
        # "reason" — air quotes
        T("first increase", 55, 235, size=22, color=GRAY, dur=240),
        T("in history!", 55, 262, size=22, color=GRAY, dur=220),
        W(200),
        T('"market', 55, 305, size=26, color=AMBER, dur=250),
        T('conditions"', 55, 333, size=26, color=AMBER, dur=250),
        W(300),
    ]
)); i+=1

# ── Scene 15 [155–170s]: "Real reason: out of new subscribers. Wall St wanted growth." ─
# Visual: Funnel — new subscribers pouring in left, dried up, Wall St on right demanding $$
scenes.append(scene(i, 155, 170,
    "Real reason: they ran out of new subscribers to acquire. Wall Street demanded growth. So they squeezed existing ones.",
    [
        W(200),
        T("real reason:", 50, 45, size=28, color=RED, dur=280),
        S(underline(50, 54, 165), color=RED, width=2, dur=200),
        W(300),
        # Funnel shape
        S(jitter([{"x":60,"y":100},{"x":200,"y":100},{"x":170,"y":200},{"x":90,"y":200},{"x":60,"y":100}],1.5),
          color=INK, width=2, dur=400),
        T("new subs", 68, 145, size=18, color=GRAY, dur=200),
        # X through funnel — ran out
        S(line(60, 100, 200, 200, 14), color=RED, width=2.5, dur=250),
        S(line(200, 100, 60, 200, 14), color=RED, width=2.5, dur=250),
        T("ran out", 68, 225, size=20, color=RED, dur=200),
        W(300),
        # Arrow to Wall St
        S(arrow(215, 160, 330, 160, head=11), color=GRAY, width=2, dur=250),
        T("Wall St.", 340, 140, size=30, color=AMBER, dur=280),
        T("demands", 340, 172, size=22, color=AMBER, dur=220),
        T("GROWTH", 340, 200, size=30, color=AMBER, dur=280),
        W(300),
        # Solution arrow
        S(arrow(390, 220, 390, 290, head=11), color=RED, width=2, dur=250),
        T("squeeze", 350, 315, size=24, color=RED, dur=240),
        T("existing users", 330, 342, size=22, color=RED, dur=240),
        W(350),
    ]
)); i+=1

# ── Scene 16 [170–190s]: "April 2024. Second hike. $11.99. 'Expansion of features'" ──
# Visual: Second price stamp. "Features??" with giant question mark.
scenes.append(scene(i, 170, 190,
    "April 2024. Second hike. $11.99. They called it expansion of features.",
    [
        W(200),
        T("April 2024", 50, 60, size=32, color=INK, dur=300),
        S(underline(50, 70, 170), color=INK, width=2.5, dur=230),
        W(300),
        # Hike #2
        T("hike #2", 50, 120, size=28, color=RED, dur=260),
        W(200),
        T("$10.99", 80, 195, size=42, color=LGRAY, dur=300),
        S(strikethrough(75, 180, 130), color=RED, width=2.5, dur=240),
        S(arrow(220, 182, 285, 182, head=10), color=RED, width=2, dur=220),
        T("$11.99", 290, 198, size=42, color=RED, dur=350),
        W(300),
        T('"expansion of', 50, 268, size=24, color=AMBER, dur=250),
        T('features"', 50, 296, size=24, color=AMBER, dur=230),
        W(300),
        # Big ? 
        T("?", 500, 240, size=110, color=GRAY, dur=350),
        W(300),
    ]
)); i+=1

# ── Scene 17 [190–215s]: "Features = audiobooks you never asked for" ──────────
# Visual: Book drawn, 15hrs circled, big X, "you didn't ask for this"
scenes.append(scene(i, 190, 215,
    "Those features? Audiobooks. 15 hours per month. You didn't ask for them. Never used them. Added anyway.",
    [
        W(200),
        T("those features?", 50, 55, size=30, color=GRAY, dur=280),
        W(350),
        # Book shape (simple rectangle + spine)
        S(jitter([{"x":120,"y":110},{"x":280,"y":110},{"x":280,"y":230},{"x":120,"y":230},{"x":120,"y":110}],1.5),
          color=AMBER, width=2.5, dur=350),
        S(line(165, 110, 165, 230, 18), color=AMBER, width=2, dur=200),
        T("audio", 180, 160, size=24, color=AMBER, dur=220),
        T("books", 180, 188, size=24, color=AMBER, dur=220),
        W(250),
        # 15hrs circled
        T("15 hrs/mo", 340, 155, size=28, color=AMBER, dur=270),
        C(405, 140, 55, color=AMBER, fill=False, dur=350),
        W(250),
        # X through the book
        S(line(115, 108, 285, 232, 16), color=RED, width=3, dur=280),
        S(line(285, 108, 115, 232, 16), color=RED, width=3, dur=280),
        W(300),
        T("you didn't", 55, 278, size=26, color=RED, dur=250),
        T("ask for this", 55, 308, size=26, color=RED, dur=250),
        W(350),
    ]
)); i+=1

# ── Scene 18 [215–235s]: "That's not a feature. That's a HOSTAGE." ─────────────
# Visual: "feature" → crossed out → "HOSTAGE" in red
scenes.append(scene(i, 215, 235,
    "That's not a feature. That's a hostage.",
    [
        W(300),
        T("that's not a", 60, 80, size=30, color=INK, dur=280),
        W(200),
        T("feature", 60, 140, size=52, color=GRAY, dur=380),
        W(350),
        S(strikethrough(55, 122, 205), color=RED, width=3.5, dur=300),
        W(350),
        T("that's a", 60, 220, size=30, color=INK, dur=260),
        W(200),
        # HOSTAGE — massive red
        T("HOSTAGE", 55, 300, size=60, color=RED, dur=480),
        S(underline(55, 310, 330), color=RED, width=3.5, dur=330),
        S(underline(60, 320, 320), color=RED, width=2, dur=270),
        W(400),
    ]
)); i+=1

# ── Scene 19 [235–270s]: "July 2025. Third hike. Family, Duo, Basic — all up." ──
# Visual: Three price tags stacked, all going up
scenes.append(scene(i, 235, 270,
    "July 2025. Third hike. Family $19.99. Duo $17.99. New Basic tier — a psychological trick.",
    [
        W(200),
        T("July 2025", 50, 55, size=32, color=INK, dur=300),
        S(underline(50, 65, 155), color=INK, width=2.5, dur=220),
        W(250),
        T("hike #3", 50, 100, size=26, color=RED, dur=240),
        W(300),
        # Three tiers
        T("Individual", 50, 150, size=24, color=INK, dur=220),
        T("$12.99", 280, 150, size=28, color=RED, dur=250),
        S(arrow(240, 145, 275, 145, head=8), color=RED, width=1.5, dur=150),
        W(220),
        T("Family", 50, 195, size=24, color=INK, dur=220),
        T("$19.99", 280, 195, size=28, color=RED, dur=250),
        S(arrow(240, 190, 275, 190, head=8), color=RED, width=1.5, dur=150),
        W(220),
        T("Duo", 50, 240, size=24, color=INK, dur=220),
        T("$17.99", 280, 240, size=28, color=RED, dur=250),
        S(arrow(240, 235, 275, 235, head=8), color=RED, width=1.5, dur=150),
        W(300),
        # The trick
        T("new 'Basic' = old plan", 50, 295, size=22, color=AMBER, dur=270),
        T("repackaged cheaper", 50, 320, size=22, color=AMBER, dur=270),
        W(250),
        T("psychological trick", 50, 350, size=22, color=RED, dur=260),
        W(300),
    ]
)); i+=1

# ── Scene 20 [270–300s]: "2026. 4th hike. $14.99. 50% MORE than 3 years ago." ──
# Visual: "50%" enormous. $9.99 vs $14.99 side by side. "same 3 years ago" label.
scenes.append(scene(i, 270, 300,
    "2026. Fourth hike. $14.99. You are paying 50% more than 3 years ago. 50 percent!",
    [
        W(200),
        T("2026", 50, 60, size=34, color=RED, dur=300),
        T("hike #4", 200, 60, size=28, color=RED, dur=260),
        W(300),
        # Side by side comparison
        T("3 years ago:", 50, 130, size=24, color=GRAY, dur=240),
        T("$9.99", 50, 170, size=46, color=GRAY, dur=350),
        W(200),
        T("now:", 310, 130, size=24, color=INK, dur=200),
        T("$14.99", 310, 170, size=46, color=RED, dur=380),
        W(300),
        # Dividing line
        S(line(285, 120, 285, 195, 15), color=LGRAY, width=1.5, dur=200),
        W(250),
        # 50% — the punchline
        T("50%", 165, 290, size=88, color=RED, dur=500),
        S(underline(155, 302, 200), color=RED, width=4, dur=350),
        S(underline(160, 312, 190), color=RED, width=2.5, dur=280),
        W(300),
        T("more. same app.", 120, 345, size=22, color=GRAY, dur=260),
        W(350),
    ]
)); i+=1


# ── Output ───────────────────────────────────────────────────────────────────
output = {"scenes": scenes}
print(f"Generated {len(scenes)} scenes covering 0-300s")
for s in scenes:
    total_wait = sum(c.get("ms",0) for c in s["cmds"] if c.get("type")=="wait")
    total_draw = sum(c.get("duration",0) for c in s["cmds"] if c.get("type") in ("text","stroke","circle"))
    scene_dur = s['time_end'] - s['time_start']
    print(f"  [{s['window_index']:2}] {s['time_start']:5.0f}-{s['time_end']:5.0f}s  wait={total_wait}ms draw={total_draw}ms  dur={scene_dur}s  '{s['phrase'][:50]}'")

with open("/tmp/scenes_chunk1.json", "w") as f:
    json.dump(output, f, indent=2)
print("Saved to /tmp/scenes_chunk1.json")
