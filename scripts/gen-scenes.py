#!/usr/bin/env python3
"""
Generate scenes_preview.json for the Spotify doodle video.
Style: text + underlines + arrows + simple shapes, drawn progressively on paper background.
Reference: doodle_canvas_renderer.html (the 4 scenes the user loved).
"""

import json, math, random

random.seed(42)  # reproducible jitter

# ── Helpers ──────────────────────────────────────────────────────────────────

def jitter(pts, j=1.5):
    """Add ±j px random jitter to every point."""
    return [{"x": round(p["x"] + (random.random()-0.5)*2*j, 1),
             "y": round(p["y"] + (random.random()-0.5)*2*j, 1)} for p in pts]

def line(x1, y1, x2, y2, steps=30):
    """Straight line with jitter."""
    return jitter([{"x": x1 + (x2-x1)*i/steps, "y": y1 + (y2-y1)*i/steps} for i in range(steps+1)])

def arrow(x1, y1, x2, y2, head=10):
    """Line with arrowhead at end."""
    pts = line(x1, y1, x2, y2, 35)
    angle = math.atan2(y2-y1, x2-x1)
    ha = 0.5  # head angle spread
    pts.append({"x": round(x2 - head*math.cos(angle-ha), 1), "y": round(y2 - head*math.sin(angle-ha), 1)})
    pts.append({"x": round(x2, 1), "y": round(y2, 1)})
    pts.append({"x": round(x2 - head*math.cos(angle+ha), 1), "y": round(y2 - head*math.sin(angle+ha), 1)})
    return pts

def underline(x, y, length, steps=30):
    """Horizontal underline with slight wobble."""
    return jitter([{"x": x + length*i/steps, "y": y + math.sin(i/steps*math.pi*2)*1.5} for i in range(steps+1)], j=0.8)

def wobbly_line(x1, y1, x2, y2, amp=3, freq=3, steps=40):
    """Wavy/squiggly line."""
    return jitter([{"x": x1 + (x2-x1)*i/steps, "y": y1 + (y2-y1)*i/steps + math.sin(i/steps*math.pi*freq)*amp} for i in range(steps+1)], j=0.5)

def text(text, x, y, size=28, color="#222", duration=400):
    return {"type": "text", "text": text, "x": x, "y": y, "size": size, "color": color, "duration": duration}

def stroke(points, color="#222", width=2.5, duration=500):
    return {"type": "stroke", "points": points, "color": color, "width": width, "duration": duration}

def circle(cx, cy, r, color="#222", fill=False, duration=400):
    return {"type": "circle", "cx": cx, "cy": cy, "r": r, "color": color, "fill": fill, "duration": duration}

def wait(ms=200):
    return {"type": "wait", "ms": ms}

def spotify_logo(cx, cy, r=50):
    """Correct Spotify logo: filled green circle + 3 white arc strokes."""
    cmds = [
        circle(cx, cy, r, color="#1DB954", fill=True, duration=350),
        wait(80),
    ]
    # 3 arcs (sound waves) - quadratic bezier curves
    arcs = [
        # Arc 1 (top/widest): from left to peak to right
        {"x1": cx - r*0.6, "y1": cy - r*0.25, "xPeak": cx, "yPeak": cy - r*0.55, "x3": cx + r*0.6, "y3": cy - r*0.25},
        # Arc 2 (middle)
        {"x1": cx - r*0.5, "y1": cy + r*0.05, "xPeak": cx, "yPeak": cy - r*0.2, "x3": cx + r*0.5, "y3": cy + r*0.05},
        # Arc 3 (bottom/slim)
        {"x1": cx - r*0.35, "y1": cy + r*0.3, "xPeak": cx, "yPeak": cy + r*0.1, "x3": cx + r*0.35, "y3": cy + r*0.3},
    ]
    for arc in arcs:
        pts = []
        steps = 20
        for i in range(steps + 1):
            t = i / steps
            px = arc["x1"] + t * (arc["x3"] - arc["x1"])
            py = (1-t)**2 * arc["y1"] + 2*t*(1-t) * arc["yPeak"] + t**2 * arc["y3"]
            pts.append({"x": round(px, 1), "y": round(py, 1)})
        pts = jitter(pts, j=1.0)
        cmds.append(stroke(pts, color="#ffffff", width=3.5, duration=180))
        cmds.append(wait(50))
    return cmds

def cross_out(x, y, size=30):
    """Draw an X through something."""
    cmds = [
        stroke(line(x, y, x+size, y+size, 12), color="#E34948", width=2.5, duration=200),
        stroke(line(x+size, y, x, y+size, 12), color="#E34948", width=2.5, duration=200),
    ]
    return cmds


# ── Scene Definitions ────────────────────────────────────────────────────────

scenes = []

# ── Window 0: "You've paid Spotify more money every single year since" ───────
# Concept: Big "YOU" + "pay MORE" with red emphasis + upward arrow
scenes.append({
    "window_index": 0,
    "time_start": 0,
    "time_end": 3,
    "phrase": "You've paid Spotify more money every single year since",
    "cmds": [
        wait(150),
        text("YOU", 200, 100, size=62, color="#1A1A1A", duration=350),
        stroke(underline(200, 108, 95), color="#1A1A1A", width=3, duration=250),
        wait(150),
        text("pay", 215, 155, size=32, color="#555", duration=200),
        text("MORE", 200, 210, size=52, color="#E34948", duration=350),
        stroke(underline(200, 218, 190), color="#E34948", width=3.5, duration=300),
        wait(100),
        # Upward arrow showing money going up
        stroke(arrow(480, 280, 480, 100, head=14), color="#E34948", width=2.5, duration=400),
        text("every year", 415, 310, size=18, color="#888", duration=250),
        text("since", 460, 100, size=16, color="#888", duration=150),
    ]
})

# ── Window 1: "2023. And artists are getting paid less" ─────────────────────
# Concept: Big "2023" year stamp + "artists" + down arrow + "LESS" in red
scenes.append({
    "window_index": 1,
    "time_start": 3,
    "time_end": 6,
    "phrase": "2023. And artists are getting paid less",
    "cmds": [
        wait(150),
        # Big year stamp
        text("2023", 40, 120, size=72, color="#1A1A1A", duration=400),
        stroke(underline(40, 130, 185), color="#1A1A1A", width=3, duration=250),
        wait(200),
        # Right side: artists getting less
        text("artists", 360, 80, size=28, color="#1A1A1A", duration=300),
        text("getting", 370, 120, size=22, color="#888", duration=200),
        text("paid", 375, 150, size=22, color="#888", duration=150),
        wait(100),
        # Big red downward arrow
        stroke(arrow(450, 70, 450, 220, head=16), color="#E34948", width=3, duration=400),
        text("LESS", 400, 270, size=48, color="#E34948", duration=350),
        stroke(underline(400, 278, 120), color="#E34948", width=3.5, duration=250),
    ]
})

# ── Window 2: "per stream than ever. Let me say that again, because it should be the most" ──
# Concept: "per stream" underlined + rate collapsing + "than ever"
scenes.append({
    "window_index": 2,
    "time_start": 6,
    "time_end": 9,
    "phrase": "per stream than ever. Let me say that again, because it should be the most",
    "cmds": [
        wait(150),
        text("per stream", 50, 90, size=36, color="#1A1A1A", duration=400),
        stroke(underline(50, 98, 210), color="#1A1A1A", width=2.5, duration=300),
        wait(200),
        # Rate collapse: old → new
        text("$0.007", 80, 165, size=32, color="#1D9E75", duration=250),
        text("→", 230, 165, size=32, color="#E34948", duration=100),
        text("$0.003", 270, 165, size=32, color="#E34948", duration=250),
        # Wavy line connecting
        stroke(wobbly_line(80, 180, 400, 180, amp=2, freq=4), color="#E34948", width=1.5, duration=400),
        wait(100),
        text("than ever", 80, 230, size=26, color="#888", duration=300),
        text("let me say that again", 80, 280, size=20, color="#aaa", duration=350),
    ]
})

# ── Window 3: "insane sentence in the music industry, and somehow nobody" ─────
# Concept: "INSANE" huge in red, double underlined, "in the music industry" small
scenes.append({
    "window_index": 3,
    "time_start": 9,
    "time_end": 12,
    "phrase": "insane sentence in the music industry, and somehow nobody",
    "cmds": [
        wait(150),
        # The word that hits hardest
        text("INSANE", 110, 150, size=72, color="#E34948", duration=500),
        # Double underline for maximum emphasis
        stroke(underline(110, 158, 310), color="#E34948", width=3.5, duration=350),
        stroke(underline(115, 168, 300), color="#E34948", width=2.5, duration=300),
        wait(200),
        text("in the music industry", 100, 210, size=22, color="#888", duration=400),
        # Squiggly line showing disbelief
        stroke(wobbly_line(100, 240, 350, 240, amp=4, freq=5), color="#aaa", width=1.5, duration=300),
        text("...and somehow", 100, 280, size=20, color="#aaa", duration=250),
    ]
})

# ── Window 4: "talks about it. You, the listener, are paying more for" ────────
# Concept: "nobody" + X through it + "YOU" big
scenes.append({
    "window_index": 4,
    "time_start": 12,
    "time_end": 15,
    "phrase": "talks about it. You, the listener, are paying more for",
    "cmds": [
        wait(150),
        text("nobody", 60, 100, size=36, color="#1A1A1A", duration=300),
        text("talks about it", 55, 140, size=24, color="#888", duration=300),
        # Big X through "nobody talks about it"
        stroke(line(40, 60, 280, 160, 15), color="#E34948", width=2.5, duration=300),
        stroke(line(280, 60, 40, 160, 15), color="#E34948", width=2.5, duration=300),
        wait(150),
        # YOU - the punch
        text("YOU", 380, 160, size=62, color="#1A1A1A", duration=400),
        stroke(underline(380, 168, 110), color="#1DB954", width=3.5, duration=250),
        text("the listener", 370, 210, size=22, color="#888", duration=250),
        # Arrow pointing at YOU
        stroke(arrow(300, 145, 370, 145, head=10), color="#1DB954", width=2, duration=250),
    ]
})

# ── Window 5: "Spotify today than you have ever paid" ───────────────────────
# Concept: Correct Spotify logo + "EVER" underlined + emphasis
scenes.append({
    "window_index": 5,
    "time_start": 15,
    "time_end": 18,
    "phrase": "Spotify today than you have ever paid",
    "cmds": [
        wait(100),
        # Spotify logo on the left
        *spotify_logo(100, 120, r=55),
        wait(100),
        # "EVER" big on the right
        text("EVER", 300, 100, size=58, color="#1A1A1A", duration=400),
        stroke(underline(300, 108, 175), color="#1A1A1A", width=3, duration=300),
        wait(150),
        text("paid", 340, 155, size=28, color="#888", duration=200),
        text("by anyone", 330, 195, size=22, color="#aaa", duration=250),
        # Up arrow
        stroke(arrow(530, 280, 530, 80, head=14), color="#E34948", width=2.5, duration=350),
        text("more", 510, 305, size=20, color="#E34948", duration=150),
    ]
})

# ── Window 6: "in the company's 18-year history" ────────────────────────────
# Concept: Timeline from 2008 to 2026 with dots
scenes.append({
    "window_index": 6,
    "time_start": 18,
    "time_end": 21,
    "phrase": "in the company's 18-year history",
    "cmds": [
        wait(200),
        # Timeline base line
        stroke(line(80, 180, 560, 180, 50), color="#1A1A1A", width=2, duration=500),
        wait(100),
        # 2008 dot and label
        circle(80, 180, 5, color="#1D9E75", fill=True, duration=150),
        text("2008", 55, 210, size=20, color="#1D9E75", duration=200),
        text("$9.99", 50, 165, size=16, color="#1D9E75", duration=150),
        # 2026 dot and label
        circle(560, 180, 7, color="#E34948", fill=True, duration=200),
        text("2026", 535, 210, size=22, color="#E34948", duration=250),
        text("$14.99", 520, 165, size=18, color="#E34948", duration=200),
        wait(100),
        # 18 years label
        text("18 years", 270, 150, size=34, color="#1A1A1A", duration=350),
        stroke(underline(270, 158, 130), color="#1A1A1A", width=2.5, duration=250),
        # Arrow from 2008 to 2026
        stroke(arrow(130, 180, 510, 180, head=10), color="#E34948", width=2, duration=400),
    ]
})

# ── Window 7: "Spotify raised its prices in 2023" ───────────────────────────
# Concept: Spotify logo + "RAISED" stamp + first price hike
scenes.append({
    "window_index": 7,
    "time_start": 21,
    "time_end": 24,
    "phrase": "Spotify raised its prices in 2023",
    "cmds": [
        wait(100),
        *spotify_logo(100, 130, r=50),
        wait(100),
        # RAISED in red (like a stamp)
        text("RAISED", 230, 80, size=40, color="#E34948", duration=350),
        stroke(underline(230, 88, 165), color="#E34948", width=3, duration=250),
        text("prices", 240, 120, size=26, color="#555", duration=200),
        wait(150),
        # First price hike
        text("$9.99", 260, 190, size=30, color="#888", duration=250),
        text("→", 370, 190, size=30, color="#E34948", duration=100),
        text("$10.99", 400, 190, size=30, color="#E34948", duration=250),
        stroke(underline(260, 198, 230), color="#E34948", width=2, duration=300),
        wait(100),
        text("2023", 300, 250, size=22, color="#888", duration=200),
    ]
})

# ── Window 8: "Then again in 2024. Then again in 2025" ──────────────────────
# Concept: Building the price chain left to right
scenes.append({
    "window_index": 8,
    "time_start": 24,
    "time_end": 27,
    "phrase": "Then again in 2024. Then again in 2025",
    "cmds": [
        wait(100),
        # Price chain building left to right
        text("$9.99", 40, 130, size=26, color="#888", duration=200),
        text("→", 135, 130, size=26, color="#aaa", duration=80),
        text("$10.99", 165, 130, size=26, color="#BA7517", duration=200),
        text("→", 290, 130, size=26, color="#aaa", duration=80),
        text("$11.99", 320, 130, size=26, color="#E34948", duration=200),
        # Year labels under each
        text("2023", 55, 160, size=16, color="#aaa", duration=100),
        text("2024", 180, 160, size=16, color="#aaa", duration=100),
        text("2025", 335, 160, size=16, color="#aaa", duration=100),
        wait(200),
        # "then again" emphasized
        text("then again", 50, 220, size=28, color="#1A1A1A", duration=300),
        text("then again", 50, 260, size=28, color="#1A1A1A", duration=300),
        # Arrow pointing right showing the pattern
        stroke(arrow(350, 260, 580, 260, head=12), color="#E34948", width=2.5, duration=300),
        text("???", 555, 245, size=24, color="#E34948", duration=200),
    ]
})

# ── Window 9: "and they just announced another hike for 2026" ───────────────
# Concept: The 4th hike reveal — "$14.99" big red + "#4" badge + "in 4 years"
scenes.append({
    "window_index": 9,
    "time_start": 27,
    "time_end": 30,
    "phrase": "and they just announced another hike for 2026",
    "cmds": [
        wait(150),
        # The final price - biggest and reddest
        text("$14.99", 200, 120, size=58, color="#E34948", duration=450),
        stroke(underline(200, 128, 220), color="#E34948", width=3.5, duration=350),
        wait(200),
        # #4 badge
        circle(530, 100, 30, color="#E34948", fill=True, duration=250),
        text("#4", 516, 110, size=28, color="#fff", duration=200),
        wait(100),
        # "in 4 years" 
        text("in 4 years", 200, 190, size=26, color="#1A1A1A", duration=300),
        stroke(underline(200, 198, 120), color="#1A1A1A", width=2, duration=200),
        wait(100),
        # Same app, same songs callout
        text("same app", 200, 250, size=20, color="#888", duration=200),
        text("same songs", 200, 280, size=20, color="#888", duration=200),
        text("same skip button", 200, 310, size=20, color="#888", duration=200),
        # Angry wavy underline
        stroke(wobbly_line(190, 318, 360, 318, amp=3, freq=6), color="#E34948", width=2, duration=300),
    ]
})


# ── Output ───────────────────────────────────────────────────────────────────

output = {"scenes": scenes}

with open("public/data/scenes_preview.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"Generated {len(scenes)} scenes (windows 0-{scenes[-1]['window_index']})")
for s in scenes:
    total_dur = sum(c.get("duration", c.get("ms", 0)) for c in s["cmds"])
    print(f"  Win {s['window_index']}: {s['time_start']:.0f}-{s['time_end']:.0f}s  total_dur={total_dur}ms  {s['phrase'][:55]}")