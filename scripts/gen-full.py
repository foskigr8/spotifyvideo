#!/usr/bin/env python3
"""
gen-full.py — Generate doodle scenes for the ENTIRE 68-minute transcript.

Approach:
  1. Read transcript.json (1064 cues with start/end/text)
  2. Group cues into idea-based beats (3-12s each) by detecting sentence
     boundaries and natural pauses
  3. For each beat, analyze the text and pick a visual template:
     - STAT     → big number/percentage/$ value reveal
     - CONTRAST → two-column comparison (X vs Y)
     - TIMELINE → years/events on a horizontal line
     - QUOTE    → highlighted phrase with underline/circle
     - EMPHASIS → single word slam (huge text + underline)
     - LIST     → sequential items with checkmarks/bullets
     - FLOW     → arrow showing direction (money flows, collapses)
     - TEXT     → default: key phrases written large
  4. Generate draw commands using the same primitives as the hand-authored
     scenes (text, stroke, circle, wait, clear)
  5. Validate: draw time ≤ beat duration, no element out of canvas bounds
  6. Write to public/data/scenes_preview.json

Style rules (matching the approved 20 scenes):
  - Colors: INK #1A1A1A, RED #E34948, GREEN #1DB954, AMBER #F5A623, GRAY #888
  - Text sizes: 22-72px, minimum 20 for labels
  - Canvas 640×360, center-focused composition
  - Sequential drawing with breathing waits (200-400ms between elements)
  - Spotify logo only when brand is mentioned, correct 3-arc design
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
WHITE  = "#ffffff"

# ── Primitives ────────────────────────────────────────────────────────────────

def J(pts, j=1.0):
    return [{"x": round(p["x"]+(random.random()-.5)*2*j, 1),
             "y": round(p["y"]+(random.random()-.5)*2*j, 1)} for p in pts]

def line(x1, y1, x2, y2, steps=30):
    return J([{"x": round(x1+(x2-x1)*i/steps, 1),
               "y": round(y1+(y2-y1)*i/steps, 1)} for i in range(steps+1)])

def hline(x1, x2, y, steps=35):
    return line(x1, y, x2, y, steps)

def vline(x, y1, y2, steps=20):
    return line(x, y1, x, y2, steps)

def arrow(x1, y1, x2, y2, head=12):
    pts = line(x1, y1, x2, y2, 30)
    a = math.atan2(y2-y1, x2-x1)
    s = 0.45
    pts += [
        {"x": round(x2-head*math.cos(a-s),1), "y": round(y2-head*math.sin(a-s),1)},
        {"x": round(x2,1), "y": round(y2,1)},
        {"x": round(x2-head*math.cos(a+s),1), "y": round(y2-head*math.sin(a+s),1)},
    ]
    return pts

def underline(x, y, length, steps=30):
    return J([{"x": round(x+length*i/steps,1), "y": round(y+math.sin(i/steps*math.pi*2)*1.0,1)}
              for i in range(steps+1)], j=0.5)

def wobbly_line(x1, y1, x2, y2, amp=3, freq=3, steps=35):
    return J([{"x": round(x1+(x2-x1)*i/steps,1),
               "y": round(y1+(y2-y1)*i/steps + math.sin(i/steps*math.pi*freq)*amp,1)}
              for i in range(steps+1)], j=0.5)

def quad_arc_pts(x1, y1, yP, x3, y3, n=20):
    pts = []
    for i in range(n+1):
        t = i/n
        x = x1 + (x3-x1)*t
        y = (1-t)**2*y1 + 2*t*(1-t)*yP + t**2*y3
        pts.append({"x": round(x,1), "y": round(y,1)})
    return J(pts, 0.8)

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

def spotify_logo(cx, cy, r=36):
    cmds = [C(cx, cy, r, color=GREEN, fill=True, dur=300), W(80)]
    arcs = [
        {"x1":cx-r*0.6,"y1":cy-r*0.25,"yP":cy-r*0.55,"x3":cx+r*0.6,"y3":cy-r*0.25},
        {"x1":cx-r*0.5,"y1":cy+r*0.05,"yP":cy-r*0.2, "x3":cx+r*0.5,"y3":cy+r*0.05},
        {"x1":cx-r*0.35,"y1":cy+r*0.3,"yP":cy+r*0.1, "x3":cx+r*0.35,"y3":cy+r*0.3},
    ]
    for arc in arcs:
        cmds += [S(quad_arc_pts(arc["x1"],arc["y1"],arc["yP"],arc["x3"],arc["y3"]),
                   color=WHITE, width=3.5, dur=150), W(40)]
    return cmds

# ── Beat grouping ─────────────────────────────────────────────────────────────

def group_into_beats(cues):
    """Group cues into idea-based beats (2-7s each). Tighter grouping = more scenes."""
    beats = []
    i = 0
    while i < len(cues):
        start = cues[i]["start"]
        group = [cues[i]]
        j = i + 1
        # Extend while total duration < 7s and no strong sentence end
        while j < len(cues):
            next_dur = cues[j]["end"] - start
            if next_dur > 7.0:
                break
            group.append(cues[j])
            text = cues[j]["text"].strip()
            # Break at sentence end if we have at least 2s
            if text.endswith(('.', '!', '?')) and next_dur > 2.0:
                j += 1
                break
            # Break at comma if we have at least 3.5s (clause boundary)
            if text.endswith(',') and next_dur > 3.5:
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
    """Find $ amounts, percentages, years, and plain numbers."""
    results = []
    for m in re.finditer(r'\$[\d.,]+[KMB]?', text):
        results.append(("money", m.group()))
    for m in re.finditer(r'\d+(?:\.\d+)?\s*%', text):
        results.append(("percent", m.group().strip()))
    for m in re.finditer(r'\b(20\d{2})\b', text):
        results.append(("year", m.group()))
    for m in re.finditer(r'\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b', text):
        results.append(("number", m.group()))
    return results

def detect_keywords(text):
    """Detect thematic keywords for template selection."""
    t = text.lower()
    kws = []
    if any(w in t for w in ['spotify', 'streaming', 'stream']):
        kws.append("spotify")
    if any(w in t for w in ['artist', 'musician', 'band', 'singer']):
        kws.append("artist")
    if any(w in t for w in ['price', 'hike', 'raised', 'increase', 'cost', 'pay', 'paid', 'money', 'dollar', '$']):
        kws.append("money")
    if any(w in t for w in ['less', 'collapse', 'drop', 'fall', 'shrink', 'decline', 'down']):
        kws.append("decline")
    if any(w in t for w in ['more', 'up', 'rise', 'grew', 'grew', 'surge', 'climb']):
        kws.append("rise")
    if any(w in t for w in ['scam', 'lie', 'fake', 'fraud', 'ghost', 'manipulate']):
        kws.append("scam")
    if any(w in t for w in ['ceo', 'ek', 'founder', 'billionaire', 'stock', 'share']):
        kws.append("corporate")
    if any(w in t for w in ['you', 'listener', 'your']):
        kws.append("you")
    if re.search(r'\b(20\d{2})\b.*\b(20\d{2})\b', t):
        kws.append("timeline")
    if any(w in t for w in ['but', 'however', 'while', 'whereas', 'versus', 'vs']):
        kws.append("contrast")
    if any(w in t for w in ['said', 'claimed', 'framed', 'called', 'told']):
        kws.append("quote")
    return kws

def pick_template(phrase, keywords, numbers):
    """Pick the best visual template for this beat."""
    # Priority order
    if "spotify" in keywords and any(k == "money" for k, _ in numbers):
        return "STAT_MONEY"
    if any(k == "money" for k, _ in numbers) and "decline" in keywords:
        return "STAT_DECLINE"
    if any(k == "money" for k, _ in numbers) and "rise" in keywords:
        return "STAT_RISE"
    if "contrast" in keywords or ("you" in keywords and "artist" in keywords):
        return "CONTRAST"
    if "timeline" in keywords or sum(1 for k, _ in numbers if k == "year") >= 2:
        return "TIMELINE"
    if "quote" in keywords:
        return "QUOTE"
    if "scam" in keywords:
        return "EMPHASIS_SCAM"
    if any(k == "percent" for k, _ in numbers):
        return "STAT_PERCENT"
    if "corporate" in keywords:
        return "CORPORATE"
    if "decline" in keywords:
        return "FLOW_DOWN"
    if "rise" in keywords:
        return "FLOW_UP"
    # Default: text emphasis on key words
    return "TEXT"

# ── Template generators ───────────────────────────────────────────────────────
# Each returns a list of cmds. Canvas is 640×360, center-focused.

def tpl_text(phrase, dur_s):
    """Default: write 2-4 key phrases from the text, centered, with underlines."""
    cmds = [W(200)]
    # Extract key phrases: split on punctuation, take longest 2-3
    parts = [p.strip() for p in re.split(r'[,;.]', phrase) if len(p.strip()) > 3]
    parts = sorted(parts, key=len, reverse=True)[:3]
    parts.reverse()  # shortest first, building up
    y = 120
    for i, part in enumerate(parts):
        # Truncate if too long
        display = part[:35] + "…" if len(part) > 35 else part
        size = 36 if i == len(parts)-1 else 28
        color = INK if i < len(parts)-1 else RED
        x = max(60, 320 - len(display)*size*0.3)
        cmds.append(T(display, x, y, size=size, color=color, dur=300))
        if i == len(parts)-1:
            cmds.append(S(underline(x, y+10, len(display)*size*0.45), color=color, width=3, dur=250))
        cmds.append(W(250))
        y += 60
    cmds.append(W(300))
    return cmds

def tpl_stat_money(phrase, numbers, dur_s):
    """Big dollar amount reveal with label."""
    cmds = [W(200)]
    money_vals = [v for k, v in numbers if k == "money"][:3]
    if not money_vals:
        return tpl_text(phrase, dur_s)
    # Show the money values big
    y = 100
    for i, val in enumerate(money_vals):
        size = 56 if i == 0 else 40
        color = RED if i == 0 else INK
        x = max(40, 320 - len(val)*size*0.3)
        cmds.append(T(val, x, y, size=size, color=color, dur=400))
        cmds.append(S(underline(x, y+10, len(val)*size*0.5), color=color, width=3, dur=250))
        cmds.append(W(300))
        y += 65
    # Label below
    label = phrase[:40] + "…" if len(phrase) > 40 else phrase
    cmds.append(T(label, 60, y+20, size=22, color=GRAY, dur=300))
    cmds.append(W(300))
    return cmds

def tpl_stat_decline(phrase, numbers, dur_s):
    """Number with downward arrow — declining."""
    cmds = [W(200)]
    vals = [v for k, v in numbers if k in ("money", "percent", "number")][:2]
    if vals:
        val = vals[0]
        cmds.append(T(val, 120, 130, size=56, color=RED, dur=400))
        cmds.append(S(underline(115, 142, len(val)*28), color=RED, width=3, dur=250))
        cmds.append(W(250))
    # Downward arrow
    cmds.append(S(arrow(420, 120, 420, 280, head=16), color=RED, width=3.5, dur=500))
    cmds.append(W(200))
    cmds.append(T("↓", 405, 220, size=48, color=RED, dur=200))
    # Label
    label = phrase[:45] + "…" if len(phrase) > 45 else phrase
    cmds.append(T(label, 80, 320, size=22, color=GRAY, dur=300))
    cmds.append(W(300))
    return cmds

def tpl_stat_rise(phrase, numbers, dur_s):
    """Number with upward arrow — rising."""
    cmds = [W(200)]
    vals = [v for k, v in numbers if k in ("money", "percent", "number")][:2]
    if vals:
        val = vals[0]
        cmds.append(T(val, 120, 200, size=56, color=AMBER, dur=400))
        cmds.append(S(underline(115, 212, len(val)*28), color=AMBER, width=3, dur=250))
        cmds.append(W(250))
    # Upward arrow
    cmds.append(S(arrow(420, 280, 420, 100, head=16), color=RED, width=3.5, dur=500))
    cmds.append(W(200))
    cmds.append(T("↑", 405, 180, size=48, color=RED, dur=200))
    label = phrase[:45] + "…" if len(phrase) > 45 else phrase
    cmds.append(T(label, 80, 330, size=22, color=GRAY, dur=300))
    cmds.append(W(300))
    return cmds

def tpl_contrast(phrase, dur_s):
    """Two-column comparison: left vs right."""
    cmds = [W(200)]
    parts = [p.strip() for p in re.split(r'[,;.]', phrase) if len(p.strip()) > 5]
    if len(parts) < 2:
        return tpl_text(phrase, dur_s)
    left = parts[0][:25]
    right = parts[-1][:25]
    # Divider
    cmds.append(S(vline(320, 60, 300), color=LGRAY, width=1.5, dur=250))
    cmds.append(W(150))
    # Left
    cmds.append(T(left, 50, 130, size=30, color=INK, dur=300))
    cmds.append(S(underline(50, 140, len(left)*15), color=INK, width=2, dur=200))
    cmds.append(W(200))
    # Right
    cmds.append(T(right, 350, 130, size=30, color=RED, dur=300))
    cmds.append(S(underline(350, 140, len(right)*15), color=RED, width=2, dur=200))
    cmds.append(W(250))
    # VS in center
    cmds.append(T("vs", 300, 180, size=24, color=GRAY, dur=200))
    cmds.append(W(300))
    return cmds

def tpl_timeline(phrase, numbers, dur_s):
    """Years on a horizontal timeline."""
    cmds = [W(200)]
    years = [int(v) for k, v in numbers if k == "year"]
    years = sorted(set(years))[:5]
    if len(years) < 2:
        return tpl_text(phrase, dur_s)
    # Base line
    cmds.append(S(hline(80, 560, 200, 40), color=INK, width=2.5, dur=400))
    cmds.append(W(150))
    # Year dots and labels
    for i, yr in enumerate(years):
        x = 80 + (480 / max(1, len(years)-1)) * i
        color = RED if i == len(years)-1 else INK
        cmds.append(C(x, 200, 6, color=color, fill=True, dur=150))
        cmds.append(T(str(yr), x-20, 230, size=22, color=color, dur=180))
        cmds.append(W(200))
    # Label
    label = phrase[:45] + "…" if len(phrase) > 45 else phrase
    cmds.append(T(label, 80, 300, size=22, color=GRAY, dur=300))
    cmds.append(W(300))
    return cmds

def tpl_quote(phrase, dur_s):
    """Highlighted quote with circle or box."""
    cmds = [W(250)]
    # Extract the quoted/claimed phrase
    parts = [p.strip() for p in re.split(r'[,;.]', phrase) if len(p.strip()) > 8]
    quote = parts[0][:40] if parts else phrase[:40]
    cmds.append(T('"', 80, 120, size=60, color=GRAY, dur=200))
    cmds.append(W(150))
    cmds.append(T(quote, 110, 160, size=34, color=INK, dur=450))
    cmds.append(S(underline(110, 172, len(quote)*17), color=RED, width=2.5, dur=300))
    cmds.append(W(250))
    cmds.append(T('"', 110+len(quote)*17+10, 120, size=60, color=GRAY, dur=200))
    cmds.append(W(300))
    return cmds

def tpl_emphasis_scam(phrase, dur_s):
    """SCAM or similar word slammed big with circle."""
    cmds = [W(250)]
    scam_words = [w for w in ['SCAM', 'FRAUD', 'FAKE', 'LIE'] if w.lower() in phrase.lower()]
    word = scam_words[0] if scam_words else "SCAM"
    cmds.append(T(word, 180, 200, size=72, color=RED, dur=500))
    cmds.append(S(underline(175, 212, 280), color=RED, width=4, dur=300))
    cmds.append(W(300))
    cmds.append(C(320, 175, 130, color=RED, fill=False, dur=500))
    cmds.append(W(300))
    # Secondary text
    label = phrase[:40] + "…" if len(phrase) > 40 else phrase
    cmds.append(T(label, 80, 320, size=22, color=GRAY, dur=300))
    cmds.append(W(300))
    return cmds

def tpl_stat_percent(phrase, numbers, dur_s):
    """Percentage big with visual indicator."""
    cmds = [W(200)]
    pct_vals = [v for k, v in numbers if k == "percent"][:2]
    if not pct_vals:
        return tpl_text(phrase, dur_s)
    val = pct_vals[0]
    cmds.append(T(val, 120, 160, size=64, color=RED, dur=450))
    cmds.append(S(underline(115, 172, len(val)*32), color=RED, width=3.5, dur=300))
    cmds.append(W(300))
    label = phrase[:45] + "…" if len(phrase) > 45 else phrase
    cmds.append(T(label, 60, 300, size=22, color=GRAY, dur=300))
    cmds.append(W(300))
    return cmds

def tpl_corporate(phrase, dur_s):
    """Corporate/CEO focused — name + label."""
    cmds = [W(200)]
    # Try to find a name or role
    parts = [p.strip() for p in re.split(r'[,;.]', phrase) if len(p.strip()) > 5]
    headline = parts[0][:30] if parts else phrase[:30]
    cmds.append(T(headline, 80, 140, size=38, color=INK, dur=400))
    cmds.append(S(underline(75, 152, len(headline)*19), color=INK, width=2.5, dur=250))
    cmds.append(W(250))
    if len(parts) > 1:
        sub = parts[1][:40]
        cmds.append(T(sub, 80, 200, size=24, color=GRAY, dur=300))
    cmds.append(W(200))
    # Small dollar/stock indicator
    cmds.append(T("$$$", 500, 100, size=36, color=AMBER, dur=250))
    cmds.append(W(300))
    return cmds

def tpl_flow_down(phrase, dur_s):
    """Flow downward — money/value dropping."""
    cmds = [W(200)]
    cmds.append(T("↓", 280, 100, size=56, color=RED, dur=300))
    cmds.append(W(150))
    cmds.append(S(arrow(320, 80, 320, 300, head=16), color=RED, width=3.5, dur=500))
    cmds.append(W(200))
    label = phrase[:45] + "…" if len(phrase) > 45 else phrase
    cmds.append(T(label, 80, 330, size=22, color=GRAY, dur=300))
    cmds.append(W(300))
    return cmds

def tpl_flow_up(phrase, dur_s):
    """Flow upward — rising."""
    cmds = [W(200)]
    cmds.append(T("↑", 280, 280, size=56, color=AMBER, dur=300))
    cmds.append(W(150))
    cmds.append(S(arrow(320, 300, 320, 80, head=16), color=AMBER, width=3.5, dur=500))
    cmds.append(W(200))
    label = phrase[:45] + "…" if len(phrase) > 45 else phrase
    cmds.append(T(label, 80, 330, size=22, color=GRAY, dur=300))
    cmds.append(W(300))
    return cmds

# ── Generate a scene for a beat ───────────────────────────────────────────────

def gen_beat(idx, beat):
    phrase = beat["phrase"]
    dur_s = beat["end"] - beat["start"]
    keywords = detect_keywords(phrase)
    numbers = extract_numbers(phrase)
    template = pick_template(phrase, keywords, numbers)

    # Generate commands based on template
    if template == "STAT_MONEY":
        cmds = tpl_stat_money(phrase, numbers, dur_s)
    elif template == "STAT_DECLINE":
        cmds = tpl_stat_decline(phrase, numbers, dur_s)
    elif template == "STAT_RISE":
        cmds = tpl_stat_rise(phrase, numbers, dur_s)
    elif template == "STAT_PERCENT":
        cmds = tpl_stat_percent(phrase, numbers, dur_s)
    elif template == "CONTRAST":
        cmds = tpl_contrast(phrase, dur_s)
    elif template == "TIMELINE":
        cmds = tpl_timeline(phrase, numbers, dur_s)
    elif template == "QUOTE":
        cmds = tpl_quote(phrase, dur_s)
    elif template == "EMPHASIS_SCAM":
        cmds = tpl_emphasis_scam(phrase, dur_s)
    elif template == "CORPORATE":
        cmds = tpl_corporate(phrase, dur_s)
    elif template == "FLOW_DOWN":
        cmds = tpl_flow_down(phrase, dur_s)
    elif template == "FLOW_UP":
        cmds = tpl_flow_up(phrase, dur_s)
    else:
        cmds = tpl_text(phrase, dur_s)

    # Add Spotify logo if brand is mentioned and there's room
    if "spotify" in keywords and template not in ("EMPHASIS_SCAM",):
        cmds.append(W(100))
        cmds += spotify_logo(560, 50, 26)

    # Ensure final wait for breathing
    cmds.append(W(400))

    # Validate: total draw time must be <= beat duration
    total_ms = sum(c.get("ms", c.get("duration", 0)) for c in cmds)
    beat_ms = dur_s * 1000
    if total_ms > beat_ms:
        # Trim: remove non-essential waits
        for c in cmds[:]:
            if c.get("type") == "wait" and c.get("ms", 0) > 200:
                c["ms"] = 150
                total_ms = sum(c.get("ms", c.get("duration", 0)) for c in cmds)
                if total_ms <= beat_ms:
                    break
        # If still over, remove the logo
        if total_ms > beat_ms:
            cmds = [c for c in cmds if not (c.get("type") == "circle" and c.get("color") == GREEN)]
            total_ms = sum(c.get("ms", c.get("duration", 0)) for c in cmds)
        # If still over, reduce text durations
        if total_ms > beat_ms:
            for c in cmds:
                if c.get("type") == "text" and c.get("duration", 0) > 200:
                    c["duration"] = 200
                if c.get("type") == "stroke" and c.get("duration", 0) > 300:
                    c["duration"] = 250
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
    with open("public/data/transcript.json") as f:
        cues = json.load(f)

    print(f"Loaded {len(cues)} cues, duration {cues[-1]['end']:.1f}s ({cues[-1]['end']/60:.1f} min)")

    beats = group_into_beats(cues)
    print(f"Grouped into {len(beats)} beats")

    # Template distribution
    templates = {}
    scenes = []
    for i, beat in enumerate(beats):
        scene = gen_beat(i, beat)
        scenes.append(scene)
        kw = detect_keywords(beat["phrase"])
        nums = extract_numbers(beat["phrase"])
        tpl = pick_template(beat["phrase"], kw, nums)
        templates[tpl] = templates.get(tpl, 0) + 1

    print(f"\nTemplate distribution:")
    for t, c in sorted(templates.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")

    # Timing validation
    print(f"\nTiming validation:")
    over = 0
    for s in scenes:
        total_ms = sum(c.get("ms", c.get("duration", 0)) for c in s["cmds"])
        beat_ms = (s["time_end"] - s["time_start"]) * 1000
        if total_ms > beat_ms:
            over += 1
            if over <= 5:
                print(f"  OVER: scene {s['window_index']} draw={total_ms}ms beat={beat_ms:.0f}ms")
    print(f"  {over}/{len(scenes)} scenes over budget")
    print(f"  {len(scenes) - over}/{len(scenes)} scenes OK")

    out = {"scenes": scenes}
    with open("public/data/scenes_preview.json", "w") as f:
        json.dump(out, f, indent=2)

    print(f"\nWrote {len(scenes)} scenes to public/data/scenes_preview.json")
    print(f"Coverage: {scenes[0]['time_start']}s - {scenes[-1]['time_end']}s ({scenes[-1]['time_end']/60:.1f} min)")

if __name__ == "__main__":
    main()
