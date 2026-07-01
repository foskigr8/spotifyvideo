#!/usr/bin/env python3
"""
gen-rest.py — Generate scenes for cues 72+ (271s onwards), inspired by the
hand-authored scenes 0-19.

PRINCIPLES (learned from studying the approved 20 scenes):
  1. CONTEXT-BASED grouping: full sentences/ideas, not SRT lines.
     Scenes are 5-15s long, breathing — never rushed.
  2. BREATHING: 300-600ms waits between elements, 500-1000ms at scene end.
     This is the #1 thing that was missing.
  3. VISUAL VARIETY: not just text. Every scene has drawn elements —
     arrows, underlines, circles, tally marks, contrast columns, price tags.
  4. LARGE TEXT: minimum 22px. Hero words 50-72px. Nothing tiny.
  5. COLORS mean things: RED=bad, AMBER=money/warning, GREEN=Spotify/positive,
     INK=default, GRAY=secondary.

APPROACH:
  - Read transcript.json, group cues 72+ into context beats
  - For each beat, detect the topic and pick a visual approach
  - Generate commands with proper breathing waits
  - Validate: draw time ≤ beat duration (with margin for breathing)
  - Prepend the original 20 scenes, write combined output
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

# ── Primitives (matching gen-scenes.py exactly) ───────────────────────────────

def jitter(pts, j=1.2):
    return [{"x": round(p["x"] + (random.random()-0.5)*2*j, 1),
             "y": round(p["y"] + (random.random()-0.5)*2*j, 1)} for p in pts]

def line(x1, y1, x2, y2, steps=30):
    return jitter([{"x": round(x1+(x2-x1)*i/steps, 1),
                    "y": round(y1+(y2-y1)*i/steps, 1)} for i in range(steps+1)])

def hline(x1, x2, y, steps=35):
    return line(x1, y, x2, y, steps)

def vline(x, y1, y2, steps=20):
    return line(x, y1, x, y2, steps)

def arrow(x1, y1, x2, y2, head=12):
    pts = line(x1, y1, x2, y2, 32)
    a = math.atan2(y2-y1, x2-x1)
    s = 0.45
    pts += [
        {"x": round(x2-head*math.cos(a-s),1), "y": round(y2-head*math.sin(a-s),1)},
        {"x": round(x2,1), "y": round(y2,1)},
        {"x": round(x2-head*math.cos(a+s),1), "y": round(y2-head*math.sin(a+s),1)},
    ]
    return pts

def underline(x, y, length, steps=28):
    return jitter([{"x": round(x+length*i/steps,1), "y": round(y+math.sin(i/steps*math.pi*2)*1.0,1)}
                   for i in range(steps+1)], j=0.5)

def curved_underline(x, y, length, steps=35):
    return [{"x": round(x+length*i/steps,1), "y": round(y+math.sin(i/steps*math.pi)*4,1)}
            for i in range(steps+1)]

def wobbly(x1, y1, x2, y2, amp=3, freq=3, steps=35):
    return jitter([{"x": round(x1+(x2-x1)*i/steps,1),
                    "y": round(y1+(y2-y1)*i/steps + math.sin(i/steps*math.pi*freq)*amp,1)}
                   for i in range(steps+1)], j=0.5)

def quad_arc_pts(x1, y1, yP, x3, y3, n=20):
    pts = []
    for i in range(n+1):
        t = i/n
        x = x1 + (x3-x1)*t
        y = (1-t)**2*y1 + 2*t*(1-t)*yP + t**2*y3
        pts.append({"x": round(x,1), "y": round(y,1)})
    return jitter(pts, 0.8)

def cross_out(x, y, w, h):
    return [line(x, y, x+w, y+h, 12), line(x+w, y, x, y+h, 12)]

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

def spotify_logo(cx, cy, r=36):
    cmds = [C(cx, cy, r, color=GREEN, fill=True, dur=300), W(80)]
    arcs = [
        {"x1":cx-r*0.6,"y1":cy-r*0.25,"yP":cy-r*0.55,"x3":cx+r*0.6,"y3":cy-r*0.25},
        {"x1":cx-r*0.5,"y1":cy+r*0.05,"yP":cy-r*0.2, "x3":cx+r*0.5,"y3":cy+r*0.05},
        {"x1":cx-r*0.35,"y1":cy+r*0.3,"yP":cy+r*0.1, "x3":cx+r*0.35,"y3":cy+r*0.3},
    ]
    for arc in arcs:
        cmds += [S(quad_arc_pts(arc["x1"],arc["y1"],arc["yP"],arc["x3"],arc["y3"]),
                   color=WHITE, width=3.5, dur=160), W(40)]
    return cmds

# Breathing wait constants (learned from hand-authored scenes)
BREATHE_SHORT = 280   # between related elements
BREATHE_MED   = 400   # between sections within a scene
BREATHE_LONG  = 600   # between major visual changes
BREATHE_END   = 800   # at scene end, let it settle

# ── Context-based beat grouping ──────────────────────────────────────────────

def group_into_beats(cues, start_idx=72):
    """Group cues into context-based beats. Full ideas, 5-15s each."""
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
            # Break at sentence end if we have at least 4s of content
            if text.endswith(('.', '!', '?')) and next_dur > 4.0:
                j += 1
                break
            # Break at comma/semicolon if we have at least 8s (longer beats = breathing)
            if text.endswith(',') and next_dur > 8.0:
                j += 1
                break
            j += 1
        end = group[-1]["end"]
        phrase = " ".join(c["text"] for c in group).strip()
        beats.append({"start": start, "end": end, "phrase": phrase, "cues": group})
        i = j
    return beats

# ── Text analysis ─────────────────────────────────────────────────────────────

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

def detect_context(text):
    """Detect the contextual topic of a phrase."""
    t = text.lower()
    ctx = []
    if any(w in t for w in ['spotify']): ctx.append("spotify")
    if any(w in t for w in ['artist', 'musician', 'band']): ctx.append("artist")
    if any(w in t for w in ['price', 'hike', 'raised', 'increase', 'cost', 'pay', 'paid', 'money', 'dollar', '$', 'profit', 'revenue']): ctx.append("money")
    if any(w in t for w in ['less', 'collapse', 'drop', 'fall', 'shrink', 'decline', 'down', 'cut']): ctx.append("decline")
    if any(w in t for w in ['more', 'up', 'rise', 'grew', 'surge', 'climb', 'bigger']): ctx.append("rise")
    if any(w in t for w in ['scam', 'lie', 'fake', 'fraud', 'ghost', 'manipulate', 'deceptive']): ctx.append("scam")
    if any(w in t for w in ['ceo', 'ek', 'founder', 'billionaire', 'stock', 'share', 'wall street', 'investor']): ctx.append("corporate")
    if any(w in t for w in ['you', 'listener', 'your']): ctx.append("you")
    if any(w in t for w in ['stream', 'streaming', 'play', 'playing']): ctx.append("streaming")
    if any(w in t for w in ['said', 'claimed', 'framed', 'called', 'told', 'announced']): ctx.append("quote")
    if any(w in t for w in ['but', 'however', 'while', 'whereas', 'versus', 'vs', 'instead']): ctx.append("contrast")
    if any(w in t for w in ['question', 'ask', 'why', 'how', 'what', 'where', 'when']): ctx.append("question")
    if any(w in t for w in ['receipt', 'audit', 'math', 'number', 'calculation']): ctx.append("audit")
    if any(w in t for w in ['podcast', 'audiobook', 'feature', 'feature']): ctx.append("feature")
    if any(w in t for w in ['lossless', 'quality', 'audio', 'bitrate', 'ogg']): ctx.append("quality")
    return ctx

def pick_visual(phrase, context, numbers):
    """Pick a visual approach based on context. Returns (template_name, cmds_fn)."""
    # Priority: specific contexts first
    if "scam" in context:
        return "scam"
    if "audit" in context or "receipt" in phrase.lower():
        return "audit"
    if "contrast" in context:
        return "contrast"
    if "question" in context:
        return "question"
    if "corporate" in context:
        return "corporate"
    if "quality" in context:
        return "quality"
    if "feature" in context:
        return "feature"
    # Money + decline = collapse visual
    if "money" in context and "decline" in context:
        return "collapse"
    # Money + rise = growth visual
    if "money" in context and "rise" in context:
        return "growth"
    # Multiple money numbers = stat display
    if sum(1 for k,_ in numbers if k == "money") >= 2:
        return "stats_money"
    if any(k == "percent" for k,_ in numbers):
        return "stat_percent"
    if sum(1 for k,_ in numbers if k == "year") >= 2:
        return "timeline"
    if "quote" in context:
        return "quote"
    if "decline" in context:
        return "arrow_down"
    if "rise" in context:
        return "arrow_up"
    if "streaming" in context and "spotify" in context:
        return "spotify_flow"
    # Default: emphasis text with visual
    return "emphasis"

# ── Visual template generators ───────────────────────────────────────────────
# Each generates a list of cmds with BREATHING waits.
# Canvas 640×360, center-focused, large text.

def tpl_scam(phrase, numbers):
    """SCAM/fraud emphasis — big word + circle + secondary text."""
    cmds = [W(100)]
    scam_words = [w.upper() for w in ['scam', 'fraud', 'fake', 'lie', 'manipulated'] if w in phrase.lower()]
    word = scam_words[0] if scam_words else "SCAM"
    cmds.append(T(word, 180, 200, size=72, color=RED, dur=450))
    cmds.append(S(underline(175, 212, 280), color=RED, width=4, dur=300))
    cmds.append(W(BREATHE_LONG))
    cmds.append(C(320, 175, 130, color=RED, fill=False, dur=500))
    cmds.append(W(BREATHE_MED))
    # Secondary text below
    label = phrase[:45] + "…" if len(phrase) > 45 else phrase
    cmds.append(T(label, 60, 320, size=22, color=GRAY, dur=300))
    cmds.append(W(BREATHE_END))
    return cmds

def tpl_audit(phrase, numbers):
    """Audit/receipt — checklist or line items."""
    cmds = [W(100)]
    cmds.append(T("AUDIT", 250, 70, size=42, color=INK, dur=350))
    cmds.append(S(underline(245, 82, 130), color=INK, width=3, dur=250))
    cmds.append(W(BREATHE_MED))
    # Line items
    parts = [p.strip() for p in re.split(r'[,;.]', phrase) if len(p.strip()) > 5][:4]
    y = 130
    for part in parts:
        display = part[:30] + "…" if len(part) > 30 else part
        cmds.append(S(line(80, y-5, 95, y+10, 8), color=INK, width=2, dur=150))  # bullet
        cmds.append(T(display, 110, y+8, size=24, color=INK, dur=280))
        cmds.append(W(BREATHE_SHORT))
        y += 45
    cmds.append(W(BREATHE_END))
    return cmds

def tpl_contrast(phrase, numbers):
    """Two-column comparison."""
    cmds = [W(100)]
    parts = [p.strip() for p in re.split(r'[,;.]', phrase) if len(p.strip()) > 5]
    if len(parts) < 2:
        return tpl_emphasis(phrase, numbers)
    left = parts[0][:28]
    right = parts[-1][:28]
    # Divider
    cmds.append(S(vline(320, 60, 300), color=LGRAY, width=1.5, dur=300))
    cmds.append(W(BREATHE_SHORT))
    # Left column
    cmds.append(T(left, 50, 140, size=28, color=INK, dur=320))
    cmds.append(S(underline(50, 152, len(left)*14), color=INK, width=2.5, dur=250))
    cmds.append(W(BREATHE_MED))
    # Right column
    cmds.append(T(right, 350, 140, size=28, color=RED, dur=320))
    cmds.append(S(underline(350, 152, len(right)*14), color=RED, width=2.5, dur=250))
    cmds.append(W(BREATHE_MED))
    # VS
    cmds.append(T("vs", 300, 200, size=28, color=GRAY, dur=220))
    cmds.append(W(BREATHE_END))
    return cmds

def tpl_question(phrase, numbers):
    """Question — big '?' with the question text."""
    cmds = [W(100)]
    cmds.append(T("?", 280, 130, size=80, color=AMBER, dur=400))
    cmds.append(W(BREATHE_SHORT))
    # The question text, truncated
    q = phrase[:50] + "…" if len(phrase) > 50 else phrase
    cmds.append(T(q, 80, 200, size=26, color=INK, dur=350))
    cmds.append(S(underline(75, 212, len(q)*13), color=INK, width=2.5, dur=280))
    cmds.append(W(BREATHE_END))
    return cmds

def tpl_corporate(phrase, numbers):
    """Corporate/CEO — name + money indicator."""
    cmds = [W(100)]
    parts = [p.strip() for p in re.split(r'[,;.]', phrase) if len(p.strip()) > 5]
    headline = parts[0][:30] if parts else phrase[:30]
    cmds.append(T(headline, 60, 130, size=34, color=INK, dur=380))
    cmds.append(S(underline(55, 142, len(headline)*17), color=INK, width=2.5, dur=280))
    cmds.append(W(BREATHE_MED))
    if len(parts) > 1:
        sub = parts[1][:40]
        cmds.append(T(sub, 60, 190, size=22, color=DGRAY, dur=300))
    cmds.append(W(BREATHE_SHORT))
    # Money/stock indicator
    cmds.append(T("$$$", 500, 90, size=36, color=AMBER, dur=250))
    cmds.append(W(BREATHE_END))
    return cmds

def tpl_quality(phrase, numbers):
    """Audio quality comparison."""
    cmds = [W(100)]
    cmds.append(T("QUALITY?", 230, 80, size=38, color=INK, dur=350))
    cmds.append(S(underline(225, 92, 150), color=INK, width=3, dur=250))
    cmds.append(W(BREATHE_MED))
    # Comparison: Spotify vs others
    cmds.append(T("Spotify", 80, 160, size=28, color=GREEN, dur=300))
    cmds.append(T("= same", 80, 195, size=22, color=DGRAY, dur=250))
    cmds.append(S(cross_out(70, 150, 110, 30)[0], color=RED, width=2, dur=200))
    cmds.append(W(BREATHE_SHORT))
    cmds.append(T("Apple", 430, 160, size=28, color=INK, dur=300))
    cmds.append(T("lossless", 420, 195, size=22, color=INK, dur=250))
    cmds.append(W(BREATHE_MED))
    cmds.append(T("vs", 300, 175, size=26, color=GRAY, dur=200))
    cmds.append(W(BREATHE_END))
    return cmds

def tpl_feature(phrase, numbers):
    """Feature nobody asked for."""
    cmds = [W(100)]
    cmds.append(T("you didn't ask for", 140, 100, size=26, color=DGRAY, dur=350))
    cmds.append(W(BREATHE_SHORT))
    # Extract the feature name
    parts = [p.strip() for p in re.split(r'[,;.]', phrase) if len(p.strip()) > 5]
    feat = parts[0][:25] if parts else "this"
    cmds.append(T(feat, 180, 170, size=42, color=AMBER, dur=400))
    cmds.append(S(underline(175, 182, len(feat)*21), color=AMBER, width=3, dur=280))
    cmds.append(W(BREATHE_MED))
    cmds.append(T("?", 300, 240, size=50, color=RED, dur=250))
    cmds.append(W(BREATHE_END))
    return cmds

def tpl_collapse(phrase, numbers):
    """Money declining — coin + downward arrow + COLLAPSE."""
    cmds = [W(100)]
    # Coin
    cmds.append(C(180, 130, 22, color=AMBER, fill=True, dur=300))
    cmds.append(T("$", 172, 138, size=24, color=WHITE, dur=150))
    cmds.append(W(BREATHE_SHORT))
    # Downward arrow
    cmds.append(S(arrow(180, 165, 180, 280, head=14), color=RED, width=3.5, dur=450))
    cmds.append(W(BREATHE_MED))
    # Label
    vals = [v for k,v in numbers if k in ("money","percent","number")]
    if vals:
        cmds.append(T(vals[0], 250, 160, size=44, color=RED, dur=380))
        cmds.append(S(underline(245, 172, len(vals[0])*22), color=RED, width=3, dur=250))
    cmds.append(W(BREATHE_SHORT))
    cmds.append(T("↓", 400, 200, size=56, color=RED, dur=250))
    cmds.append(W(BREATHE_END))
    return cmds

def tpl_growth(phrase, numbers):
    """Money rising — upward arrow + number."""
    cmds = [W(100)]
    vals = [v for k,v in numbers if k in ("money","percent","number")]
    if vals:
        cmds.append(T(vals[0], 120, 220, size=48, color=AMBER, dur=400))
        cmds.append(S(underline(115, 232, len(vals[0])*24), color=AMBER, width=3, dur=280))
        cmds.append(W(BREATHE_MED))
    # Upward arrow
    cmds.append(S(arrow(400, 280, 400, 100, head=16), color=AMBER, width=3.5, dur=450))
    cmds.append(W(BREATHE_SHORT))
    cmds.append(T("↑", 380, 180, size=56, color=AMBER, dur=250))
    cmds.append(W(BREATHE_END))
    return cmds

def tpl_stats_money(phrase, numbers):
    """Multiple dollar amounts displayed."""
    cmds = [W(100)]
    money_vals = [v for k,v in numbers if k == "money"][:3]
    y = 100
    for i, val in enumerate(money_vals):
        size = 52 if i == 0 else 36
        color = RED if i == 0 else INK
        x = max(60, 320 - len(val)*size*0.3)
        cmds.append(T(val, x, y, size=size, color=color, dur=380))
        cmds.append(S(underline(x, y+10, len(val)*size*0.5), color=color, width=3, dur=250))
        cmds.append(W(BREATHE_SHORT))
        y += 60
    cmds.append(W(BREATHE_END))
    return cmds

def tpl_stat_percent(phrase, numbers):
    """Percentage big."""
    cmds = [W(100)]
    pct = [v for k,v in numbers if k == "percent"][0]
    cmds.append(T(pct, 180, 170, size=64, color=RED, dur=450))
    cmds.append(S(underline(175, 182, len(pct)*32), color=RED, width=3.5, dur=300))
    cmds.append(W(BREATHE_MED))
    label = phrase[:45] + "…" if len(phrase) > 45 else phrase
    cmds.append(T(label, 60, 290, size=22, color=GRAY, dur=300))
    cmds.append(W(BREATHE_END))
    return cmds

def tpl_timeline(phrase, numbers):
    """Years on a horizontal timeline."""
    cmds = [W(100)]
    years = sorted(set(int(v) for k,v in numbers if k == "year"))[:5]
    if len(years) < 2:
        return tpl_emphasis(phrase, numbers)
    cmds.append(S(hline(80, 560, 200, 40), color=INK, width=2.5, dur=450))
    cmds.append(W(BREATHE_SHORT))
    for i, yr in enumerate(years):
        x = 80 + (480 / max(1, len(years)-1)) * i
        color = RED if i == len(years)-1 else INK
        cmds.append(C(x, 200, 7, color=color, fill=True, dur=180))
        cmds.append(T(str(yr), x-22, 235, size=24, color=color, dur=220))
        cmds.append(W(BREATHE_SHORT))
    cmds.append(W(BREATHE_MED))
    label = phrase[:45] + "…" if len(phrase) > 45 else phrase
    cmds.append(T(label, 60, 300, size=22, color=GRAY, dur=300))
    cmds.append(W(BREATHE_END))
    return cmds

def tpl_quote(phrase, numbers):
    """Highlighted quote."""
    cmds = [W(100)]
    parts = [p.strip() for p in re.split(r'[,;.]', phrase) if len(p.strip()) > 8]
    quote = parts[0][:42] if parts else phrase[:42]
    cmds.append(T('"', 70, 120, size=56, color=GRAY, dur=220))
    cmds.append(W(BREATHE_SHORT))
    cmds.append(T(quote, 105, 170, size=32, color=INK, dur=420))
    cmds.append(S(underline(100, 182, len(quote)*16), color=RED, width=2.5, dur=280))
    cmds.append(W(BREATHE_END))
    return cmds

def tpl_arrow_down(phrase, numbers):
    """Downward flow."""
    cmds = [W(100)]
    cmds.append(T("↓", 290, 120, size=64, color=RED, dur=350))
    cmds.append(W(BREATHE_SHORT))
    cmds.append(S(arrow(320, 100, 320, 290, head=16), color=RED, width=3.5, dur=450))
    cmds.append(W(BREATHE_MED))
    label = phrase[:45] + "…" if len(phrase) > 45 else phrase
    cmds.append(T(label, 60, 330, size=22, color=GRAY, dur=300))
    cmds.append(W(BREATHE_END))
    return cmds

def tpl_arrow_up(phrase, numbers):
    """Upward flow."""
    cmds = [W(100)]
    cmds.append(T("↑", 290, 270, size=64, color=AMBER, dur=350))
    cmds.append(W(BREATHE_SHORT))
    cmds.append(S(arrow(320, 290, 320, 100, head=16), color=AMBER, width=3.5, dur=450))
    cmds.append(W(BREATHE_MED))
    label = phrase[:45] + "…" if len(phrase) > 45 else phrase
    cmds.append(T(label, 60, 330, size=22, color=GRAY, dur=300))
    cmds.append(W(BREATHE_END))
    return cmds

def tpl_spotify_flow(phrase, numbers):
    """Spotify + streaming — logo + flow."""
    cmds = [W(100)]
    cmds.extend(spotify_logo(120, 130, 36))
    cmds.append(W(BREATHE_SHORT))
    cmds.append(S(arrow(190, 130, 420, 130, head=14), color=INK, width=3, dur=400))
    cmds.append(W(BREATHE_SHORT))
    # What flows to
    parts = [p.strip() for p in re.split(r'[,;.]', phrase) if len(p.strip()) > 5]
    target = parts[-1][:25] if parts else "you"
    cmds.append(T(target, 440, 125, size=28, color=INK, dur=320))
    cmds.append(S(underline(435, 137, len(target)*14), color=INK, width=2.5, dur=250))
    cmds.append(W(BREATHE_END))
    return cmds

def tpl_emphasis(phrase, numbers):
    """Default: key phrase with underline + visual accent."""
    cmds = [W(100)]
    # Extract 1-2 key phrases
    parts = [p.strip() for p in re.split(r'[,;.]', phrase) if len(p.strip()) > 5]
    parts = sorted(parts, key=len, reverse=True)[:2]
    parts.reverse()
    y = 130
    for i, part in enumerate(parts):
        display = part[:35] + "…" if len(part) > 35 else part
        size = 40 if i == len(parts)-1 else 26
        color = RED if i == len(parts)-1 else INK
        x = max(50, 320 - len(display)*size*0.3)
        cmds.append(T(display, x, y, size=size, color=color, dur=350))
        if i == len(parts)-1:
            cmds.append(S(underline(x, y+10, len(display)*size*0.42), color=color, width=3, dur=280))
        cmds.append(W(BREATHE_MED))
        y += 60
    cmds.append(W(BREATHE_END))
    return cmds

# ── Generate a scene for a beat ───────────────────────────────────────────────

def gen_scene(idx, beat):
    phrase = beat["phrase"]
    context = detect_context(phrase)
    numbers = extract_numbers(phrase)
    template = pick_visual(phrase, context, numbers)

    if template == "scam":         cmds = tpl_scam(phrase, numbers)
    elif template == "audit":      cmds = tpl_audit(phrase, numbers)
    elif template == "contrast":   cmds = tpl_contrast(phrase, numbers)
    elif template == "question":   cmds = tpl_question(phrase, numbers)
    elif template == "corporate":  cmds = tpl_corporate(phrase, numbers)
    elif template == "quality":    cmds = tpl_quality(phrase, numbers)
    elif template == "feature":    cmds = tpl_feature(phrase, numbers)
    elif template == "collapse":   cmds = tpl_collapse(phrase, numbers)
    elif template == "growth":     cmds = tpl_growth(phrase, numbers)
    elif template == "stats_money":cmds = tpl_stats_money(phrase, numbers)
    elif template == "stat_percent":cmds = tpl_stat_percent(phrase, numbers)
    elif template == "timeline":   cmds = tpl_timeline(phrase, numbers)
    elif template == "quote":      cmds = tpl_quote(phrase, numbers)
    elif template == "arrow_down": cmds = tpl_arrow_down(phrase, numbers)
    elif template == "arrow_up":   cmds = tpl_arrow_up(phrase, numbers)
    elif template == "spotify_flow":cmds = tpl_spotify_flow(phrase, numbers)
    else:                           cmds = tpl_emphasis(phrase, numbers)

    # Add Spotify logo if brand is mentioned and template allows
    if "spotify" in context and template not in ("scam", "spotify_flow", "quality"):
        cmds.insert(-1, W(BREATHE_SHORT))
        cmds[-2:-2] = spotify_logo(560, 55, 26)

    # Validate timing: total draw time must be < beat duration (with margin)
    total_ms = sum(c.get("ms", c.get("duration", 0)) for c in cmds)
    beat_ms = (beat["end"] - beat["start"]) * 1000
    # If over budget, trim waits proportionally
    if total_ms > beat_ms * 0.9:
        ratio = (beat_ms * 0.85) / total_ms
        for c in cmds:
            if c.get("type") == "wait":
                c["ms"] = max(100, int(c["ms"] * ratio))
            elif c.get("duration", 0) > 200:
                c["duration"] = max(150, int(c["duration"] * ratio))
        total_ms = sum(c.get("ms", c.get("duration", 0)) for c in cmds)

    return {
        "window_index": idx,
        "time_start": round(beat["start"], 2),
        "time_end": round(beat["end"], 2),
        "phrase": phrase,
        "cmds": cmds
    }

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Load original 20 scenes (preserve exactly)
    with open("public/data/scenes_preview.json") as f:
        original = json.load(f)
    print(f"Loaded {len(original['scenes'])} original scenes (0-{original['scenes'][-1]['time_end']:.0f}s)")

    # Load transcript
    with open("public/data/transcript.json") as f:
        cues = json.load(f)
    print(f"Loaded {len(cues)} cues ({cues[-1]['end']:.0f}s / {cues[-1]['end']/60:.1f}min)")

    # Find where original scenes end (cue 72, ~271s)
    orig_end = original['scenes'][-1]['time_end']
    start_idx = next((i for i, c in enumerate(cues) if c["start"] >= orig_end - 0.5), len(cues))
    print(f"Original scenes end at {orig_end:.1f}s, starting new scenes from cue {cues[start_idx]['idx']}")

    # Group remaining cues into context beats
    beats = group_into_beats(cues, start_idx)
    print(f"Grouped into {len(beats)} context-based beats")

    # Generate scenes for each beat
    new_scenes = []
    templates_used = {}
    for i, beat in enumerate(beats):
        scene = gen_scene(len(original['scenes']) + i, beat)
        new_scenes.append(scene)
        ctx = detect_context(beat["phrase"])
        tpl = pick_visual(beat["phrase"], ctx, extract_numbers(beat["phrase"]))
        templates_used[tpl] = templates_used.get(tpl, 0) + 1

    print(f"\nTemplate distribution:")
    for t, c in sorted(templates_used.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")

    # Validate timing
    over = 0
    for s in new_scenes:
        total_ms = sum(c.get("ms", c.get("duration", 0)) for c in s["cmds"])
        beat_ms = (s["time_end"] - s["time_start"]) * 1000
        if total_ms > beat_ms:
            over += 1
    print(f"\nTiming: {over}/{len(new_scenes)} over budget, {len(new_scenes)-over} OK")

    # Combine: original 20 + new scenes
    all_scenes = original['scenes'] + new_scenes
    out = {"scenes": all_scenes}

    with open("public/data/scenes_preview.json", "w") as f:
        json.dump(out, f, indent=2)

    print(f"\nWrote {len(all_scenes)} total scenes ({len(original['scenes'])} original + {len(new_scenes)} new)")
    print(f"Coverage: {all_scenes[0]['time_start']}s - {all_scenes[-1]['time_end']:.0f}s ({all_scenes[-1]['time_end']/60:.1f}min)")
    # Beat duration stats
    durs = [s["time_end"] - s["time_start"] for s in new_scenes]
    print(f"New scene durations: avg={sum(durs)/len(durs):.1f}s, min={min(durs):.1f}s, max={max(durs):.1f}s")

if __name__ == "__main__":
    main()
