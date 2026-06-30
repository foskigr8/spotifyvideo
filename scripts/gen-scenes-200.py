#!/usr/bin/env python3
"""
gen-scenes-200.py  —  50 scenes covering cues 0-199 (0 to 767s)

Overlap-prevention rules:
  1. Canvas divided into zones per scene. Elements stay in their zone.
  2. Text inside a shape: x >= shape_x+8, baseline y <= shape_y+shape_h-8.
  3. Spotify logo ONLY in top-right corner (cx~572,cy~48) and ONLY when
     main drawing is in the left half. Never inside other shapes.
  4. No decorative ruled-line backgrounds.
  5. W(900) auto-appended so last frame always breathes.
  6. Max single wait between draw steps: 800ms.
  7. Strikethrough at mid-height of the TEXT being struck (not guessed).
"""
import json, math, random
random.seed(42)

RED="#E34948"; GREEN="#1DB954"; AMBER="#F5A623"
INK="#1A1A1A"; GRAY="#888888"; LGRAY="#BBBBBB"; WHITE="#ffffff"

# ── primitives ────────────────────────────────────────────────────────────────
def J(pts, j=1.0):
    return [{"x": round(p["x"]+(random.random()-.5)*2*j, 1),
             "y": round(p["y"]+(random.random()-.5)*2*j, 1)} for p in pts]

def line(x1, y1, x2, y2, steps=32):
    return J([{"x": round(x1+(x2-x1)*i/steps, 1),
               "y": round(y1+(y2-y1)*i/steps, 1)} for i in range(steps+1)])

def hline(x1, x2, y, s=38): return line(x1, y, x2, y, s)
def vline(x, y1, y2, s=22): return line(x, y1, x, y2, s)

def arrow(x1, y1, x2, y2, head=13):
    pts = line(x1, y1, x2, y2, 38)
    a = math.atan2(y2-y1, x2-x1); sp = 0.42
    pts += [{"x": round(x2-head*math.cos(a-sp), 1), "y": round(y2-head*math.sin(a-sp), 1)},
            {"x": round(x2, 1), "y": round(y2, 1)},
            {"x": round(x2-head*math.cos(a+sp), 1), "y": round(y2-head*math.sin(a+sp), 1)}]
    return J(pts, .8)

def ul(x, y, length, steps=30):
    return [{"x": round(x+length*i/steps, 1),
             "y": round(y+math.sin(i/steps*math.pi*2)*1.5, 1)} for i in range(steps+1)]

def stk(x, y, length, steps=30):
    return J([{"x": round(x+length*i/steps, 1), "y": round(y, 1)} for i in range(steps+1)], .6)

def rect(x, y, w, h):
    return J([{"x":x,"y":y},{"x":x+w,"y":y},{"x":x+w,"y":y+h},
              {"x":x,"y":y+h},{"x":x+1,"y":y+1}], 1.2)

def logo(cx, cy, r=40):
    """Spotify logo. Only call with cx,cy in a clear zone."""
    cmds = [C(cx, cy, r, GREEN, True, 260), W(50)]
    bars = [
        [{"x": cx-r*.58, "y": cy-r*.25}] +
        [{"x": cx-r*.58+(r*1.16)*i/20, "y": cy-r*.25-math.sin(i/20*math.pi)*r*.22} for i in range(21)],
        [{"x": cx-r*.46, "y": cy+r*.05}] +
        [{"x": cx-r*.46+(r*.92)*i/20, "y": cy+r*.05-math.sin(i/20*math.pi)*r*.18} for i in range(21)],
        [{"x": cx-r*.32, "y": cy+r*.30}] +
        [{"x": cx-r*.32+(r*.64)*i/16, "y": cy+r*.30-math.sin(i/16*math.pi)*r*.12} for i in range(17)],
    ]
    for pts in bars:
        cmds += [S(J(pts, .8), WHITE, 3.5, 140), W(25)]
    return cmds

# ── command builders ──────────────────────────────────────────────────────────
def T(text, x, y, size=30, color=INK, dur=300):
    return {"type":"text","text":text,"x":x,"y":y,"size":size,"color":color,"duration":dur}
def S(pts, color=INK, width=2.5, dur=500):
    return {"type":"stroke","points":pts,"color":color,"width":width,"duration":dur}
def C(cx, cy, r, color=INK, fill=False, dur=400):
    return {"type":"circle","cx":cx,"cy":cy,"r":r,"color":color,"fill":fill,"duration":dur}
def W(ms=300): return {"type":"wait","ms":ms}

def scene(idx, ts, te, phrase, cmds):
    return {"window_index": idx, "time_start": round(ts,2), "time_end": round(te,2),
            "phrase": phrase, "cmds": list(cmds)+[W(900)]}

scenes = []
i = 0

# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER 1: THE HOOK  (cues 0-17, 0-67s)
# ═══════════════════════════════════════════════════════════════════════════════

# S0  [0.03-5.0s]  YOU PAY / MORE. Arrow right side. Logo top-right corner only.
scenes.append(scene(i, 0.03, 5.0,
    "You've paid Spotify more money every single year since 2023", [
    W(150),
    T("YOU PAY", 42, 88, 42, INK, 360),
    W(180),
    T("MORE", 42, 168, 78, RED, 470),
    S(ul(42, 175, 215), RED, 3.5, 310),
    W(280),
    # Arrow — right zone x:450, clear of all left-half text
    S(arrow(450, 305, 450, 75, 18), RED, 3.2, 500),
    W(100),
    T("2023", 468, 305, 20, GRAY, 175),
    T("2024", 468, 248, 20, AMBER, 175),
    T("2025", 468, 188, 20, AMBER, 175),
    T("2026", 468, 122, 22, RED, 215),
    W(180),
    # Logo top-right corner: cx=572 cy=48 r=35. Arrow peak y=75, logo bottom=48+35=83 — slight overlap.
    # Shift logo to cx=572 cy=38 r=30 so bottom=68, arrow peak at y=75 → clear ✓
    *logo(572, 38, 30),
    W(280),
    T("every. single. year.", 42, 322, 23, GRAY, 270),
])); i+=1

# S1  [5.32-9.0s]  Two columns. Divider first. Each side in own zone.
scenes.append(scene(i, 5.32, 9.0,
    "Artists getting paid less per stream than ever", [
    W(160),
    S(vline(318, 38, 322), LGRAY, 1.5, 260),
    W(140),
    T("you pay", 55, 80, 30, INK, 285),
    S(arrow(128, 102, 128, 235, 14), RED, 3, 390),
    T("MORE ↑", 75, 268, 28, RED, 252),
    W(280),
    T("artist gets", 345, 80, 30, INK, 285),
    S(arrow(415, 102, 415, 235, 14), GRAY, 3, 390),
    T("LESS ↓", 360, 268, 28, GRAY, 252),
    W(240),
    T("per stream", 345, 308, 20, GRAY, 195),
    T("than EVER", 345, 335, 22, RED, 232),
])); i+=1

# S2  [9.0-15.0s]  Megaphone LEFT half only (x:80-255). INSANE RIGHT half (x:378+). Zero overlap.
scenes.append(scene(i, 9.0, 15.0,
    "Most insane sentence in the music industry", [
    W(180),
    # Body rect: x:80-160, y:138-208
    S(rect(80, 138, 80, 70), INK, 2.5, 310),
    # Horn: left edge x:160, right edge x:255, y:100-215
    S(J([{"x":160,"y":138},{"x":255,"y":100},{"x":255,"y":215},{"x":160,"y":208}], 1.2), INK, 2.5, 340),
    S(vline(95, 208, 238, 8), INK, 2.5, 110),
    W(180),
    # Sound arcs start at x:268 (horn ends at 255, gap 13px) — no touch
    S(J([{"x":268,"y":152},{"x":290,"y":135},{"x":290,"y":178}], .8), RED, 2.5, 195),
    S(J([{"x":298,"y":130},{"x":325,"y":108},{"x":325,"y":198}], .8), RED, 2.5, 215),
    S(J([{"x":333,"y":108},{"x":362,"y":88},{"x":362,"y":218}], .8), RED, 2, 230),
    W(260),
    # INSANE starts x:378 (arcs end x:362, gap 16px) ✓
    T("INSANE", 378, 198, 58, RED, 465),
    S(ul(378, 205, 192), RED, 3.5, 290),
    W(280),
    T("most insane sentence in music", 80, 302, 21, GRAY, 270),
])); i+=1

# S3  [15.0-22.0s]  18-year timeline at y=235. "18 YEARS" top zone. Endpoints below line.
scenes.append(scene(i, 15.0, 22.0,
    "Paying more for Spotify than at any point in its 18-year history", [
    W(180),
    S(hline(55, 585, 235, 55), INK, 2.5, 510),
    W(140),
    C(55, 235, 7, GREEN, True, 145),
    T("2006", 35, 258, 18, GREEN, 172),
    T("free", 40, 276, 15, GREEN, 152),
    W(100),
    C(585, 235, 9, RED, True, 155),
    T("2026", 558, 258, 18, RED, 172),
    T("$14.99", 550, 276, 18, RED, 192),
    W(240),
    # "18 YEARS" — top zone y:148, well above timeline y:235
    T("18", 198, 148, 88, INK, 415),
    T("YEARS", 348, 148, 52, INK, 355),
    W(180),
    T("zero increases 2006-2021", 145, 192, 20, GRAY, 252),
    W(240),
    S(arrow(498, 182, 572, 220, 11), RED, 2, 270),
    T("most expensive", 365, 172, 20, RED, 215),
    T("EVER", 412, 195, 26, RED, 252),
])); i+=1

# S4  [22.0-32.5s]  Tally marks x:115-265. Punchline right zone x:358+.
scenes.append(scene(i, 22.0, 32.5,
    "Spotify raised prices in 2023, 2024, 2025, and again in 2026", [
    W(180),
    T("price hikes:", 55, 72, 30, INK, 288),
    W(260),
    S(vline(115, 105, 212), RED, 4, 280),
    T("'23", 100, 235, 19, GRAY, 155),
    W(330),
    S(vline(162, 105, 212), RED, 4, 280),
    T("'24", 147, 235, 19, GRAY, 155),
    W(330),
    S(vline(209, 105, 212), RED, 4, 280),
    T("'25", 194, 235, 19, GRAY, 155),
    W(330),
    S(vline(256, 105, 212), RED, 4, 280),
    S(line(98, 188, 275, 128, 22), RED, 4, 290),
    T("'26", 241, 235, 19, GRAY, 155),
    W(280),
    # Right zone starts x:358 (tallies end x:275+gap) ✓
    T("4 hikes", 358, 152, 52, RED, 425),
    T("4 years", 358, 218, 52, INK, 425),
    S(ul(358, 225, 205), RED, 3.5, 295),
    W(240),
    T("same app. same songs.", 55, 308, 24, GRAY, 262),
])); i+=1

# S5  [32.5-40.0s]  3 icon rows LEFT (x:55-108). Label text starts x:128. Price arrow far-right x:505.
scenes.append(scene(i, 32.5, 40.0,
    "Same app, same songs, same skip. Four price increases. Payouts collapsing.", [
    W(160),
    # Row1: phone rect x:55-108 y:68-140
    S(rect(55, 68, 53, 72), INK, 2.2, 270),
    C(81, 132, 4, INK, True, 75),
    T("same app", 128, 118, 34, INK, 305),
    W(330),
    # Row2: note x:55-98 y:178-239
    S(vline(58, 178, 228), INK, 2.5, 155),
    C(52, 231, 10, INK, False, 115),
    S(line(68, 178, 88, 165, 10), INK, 2, 95),
    C(83, 165, 8, INK, False, 95),
    T("same songs", 128, 222, 34, INK, 308),
    W(330),
    # Row3: skip triangle x:55-103 y:278-328
    S(J([{"x":55,"y":278},{"x":55,"y":328},{"x":98,"y":303},{"x":55,"y":278}], 1.2), INK, 2.2, 195),
    S(vline(103, 278, 328), INK, 2.5, 125),
    T("same skip", 128, 322, 34, INK, 308),
    W(330),
    # Price arrow far right — x:505, no icons or text there
    S(arrow(505, 308, 505, 98, 14), RED, 3, 425),
    T("price ↑", 520, 308, 24, RED, 232),
])); i+=1

# S6  [40.0-48.0s]  Payout graph. Axes at x:58 and y:295. Line descends. Labels in safe zones.
scenes.append(scene(i, 40.0, 48.0,
    "Artists watching per-stream payouts collapse", [
    W(160),
    S(hline(58, 578, 295, 50), INK, 2, 425),
    S(vline(58, 295, 48, 30), INK, 2, 268),
    W(140),
    # Line: starts y:78 (top-left), ends y:298 (near x-axis). All points above y:295 ✓
    S(J([{"x":78,"y":78},{"x":138,"y":102},{"x":198,"y":130},
         {"x":260,"y":162},{"x":322,"y":198},{"x":382,"y":232},
         {"x":440,"y":262},{"x":498,"y":285},{"x":552,"y":298}], 2.5), RED, 3.2, 585),
    W(190),
    # Labels top-left — line starts high there so text at y:70,92 fits before line arrives
    T("payout", 62, 70, 21, RED, 205),
    T("per stream", 62, 92, 19, RED, 185),
    S(arrow(552, 278, 552, 308, 10), RED, 2.2, 195),
    W(240),
    # COLLAPSE below x-axis y:345
    T("COLLAPSE", 302, 345, 34, RED, 372),
    S(ul(302, 350, 262), RED, 3, 272),
    W(195),
    T("2014→2026: down 57%", 62, 338, 19, GRAY, 232),
])); i+=1

# S7  [48.0-56.0s]  Flow: YOU box → SPOTIFY box (logo inside) → ARTIST box. 3 separate zones.
# YOU: x:42-145 y:78-145. SPOTIFY: x:222-375 y:58-168. ARTIST: x:448-558 y:125-185.
# Logo inside SPOTIFY box: cx=298 cy=110 r=28. Inner bounds: x:230-367 y:66-160. cx±r=270-326 ✓ cy±r=82-138 ✓
scenes.append(scene(i, 48.0, 56.0,
    "You pay more. They get less. Spotify keeps the difference.", [
    W(180),
    S(rect(42, 78, 103, 67), INK, 2.5, 308),
    T("YOU", 65, 120, 28, INK, 252),
    W(190),
    S(arrow(148, 112, 218, 112, 11), INK, 2, 232),
    T("$$$", 155, 104, 18, RED, 155),
    W(140),
    S(rect(222, 58, 153, 110), GREEN, 3, 388),
    *logo(298, 110, 28),
    T("SPOTIFY", 235, 158, 19, INK, 245),
    W(190),
    S(arrow(378, 155, 445, 155, 10), GRAY, 1.8, 215),
    T("¢", 395, 147, 18, GRAY, 138),
    W(140),
    S(rect(448, 125, 110, 60), GRAY, 2, 272),
    T("ARTIST", 458, 162, 22, GRAY, 225),
    W(280),
    T("keeps it", 235, 178, 22, GREEN, 215),
    W(195),
    T("you pay more  ·  they get less", 95, 318, 21, GRAY, 272),
])); i+=1

# S8  [56.0-64.0s]  SCAM in a box. Box drawn first, text placed inside measured bounds.
# Box: x:72-565 y:85-200. SCAM baseline y:178. Inner bottom = 200-8=192. 178<=192 ✓. x:118 > 72+8=80 ✓
scenes.append(scene(i, 56.0, 64.0,
    "If that sounds like a scam it is. Very polite. Green logo.", [
    W(260),
    T("if that sounds like a", 50, 65, 24, GRAY, 262),
    W(185),
    S(rect(72, 85, 493, 115), RED, 3.5, 448),
    W(145),
    T("SCAM", 118, 178, 96, RED, 565),
    W(330),
    T("(very polite one,", 78, 238, 26, GRAY, 245),
    T("with a green logo)", 78, 268, 26, GRAY, 245),
    W(195),
    # Logo at x:498 y:252 r:28 — right of parenthetical text which ends ~x:350 ✓
    *logo(498, 252, 28),
    W(280),
    T("read. the. receipt.", 78, 330, 28, INK, 282),
])); i+=1

# S9  [64.0-68.0s]  Receipt paper centre. All text inside receipt x:200-444 y:60-245.
scenes.append(scene(i, 64.0, 68.0,
    "We are going to read the receipt. All of it.", [
    W(140),
    S(rect(192, 30, 260, 222), INK, 2, 368),
    W(140),
    T("RECEIPT", 218, 60, 24, INK, 242),
    S(hline(200, 444, 66), INK, 1.5, 195),
    W(95),
    T("• ????????", 205, 96, 18, GRAY, 175),
    T("• ????????", 205, 120, 18, GRAY, 175),
    T("• ????????", 205, 144, 18, GRAY, 175),
    T("• ????????", 205, 168, 18, GRAY, 175),
    S(hline(200, 444, 182), INK, 1.5, 175),
    T("TOTAL: ???", 212, 218, 20, RED, 232),
    W(280),
    T("read. the. receipt.", 188, 288, 28, INK, 282),
])); i+=1

# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER 2: THE AUDIT LIST  (cues 18-25, 67-93s)
# ═══════════════════════════════════════════════════════════════════════════════

# S10  [68.0-77.0s]  Bullet list. Arrow icon x:78-115, text starts x:122. Max wait 800ms.
scenes.append(scene(i, 68.0, 77.0,
    "Where the money goes. Why artists quit. Why the app got worse.", [
    W(140),
    T("today's audit:", 165, 50, 28, INK, 272),
    S(ul(165, 57, 192), INK, 2.2, 195),
    W(480),
    S(arrow(78, 90, 113, 90, 9), INK, 2.2, 145),
    T("where the money goes", 122, 97, 22, INK, 262),
    W(680),
    S(arrow(78, 132, 113, 132, 9), INK, 2.2, 145),
    T("why artists are quitting", 122, 139, 22, INK, 262),
    W(680),
    S(arrow(78, 174, 113, 174, 9), INK, 2.2, 145),
    T("why the app got worse", 122, 181, 22, INK, 262),
    W(680),
    S(arrow(78, 216, 113, 216, 9), AMBER, 2.2, 145),
    T("$1B on podcasts — abandoned", 122, 223, 22, AMBER, 262),
    W(680),
    S(arrow(78, 258, 113, 258, 9), RED, 2.2, 145),
    T("fake numbers & hidden payouts", 122, 265, 22, RED, 262),
    W(680),
    S(arrow(78, 300, 113, 300, 9), RED, 2.2, 145),
    T("founder building weapons", 122, 307, 22, RED, 262),
])); i+=1

# S11  [77.0-93.5s]  3 facts in 3 horizontal bands. Max wait 800ms between bands.
scenes.append(scene(i, 77.0, 93.5,
    "Fake number. $1B on podcasts abandoned. Founder sells shares to build weapons.", [
    W(190),
    T("fake number", 50, 72, 38, RED, 352),
    S(ul(50, 80, 215), RED, 3, 272),
    T("made payouts look bigger", 50, 105, 20, GRAY, 232),
    W(680),
    T("$1 billion", 50, 172, 42, AMBER, 372),
    T("on podcasts", 50, 212, 30, AMBER, 292),
    S(stk(46, 194, 230), RED, 3, 252),
    T("abandoned", 50, 248, 24, RED, 242),
    W(680),
    T("founder →", 50, 308, 28, INK, 262),
    T("sells shares →", 238, 308, 24, GRAY, 242),
    T("builds weapons", 442, 308, 26, RED, 262),
    S(ul(442, 316, 155), RED, 2.5, 225),
])); i+=1

# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER 3: THE AUDIT — $9.99 ERA  (cues 25-35, 93-135s)
# ═══════════════════════════════════════════════════════════════════════════════

# S12  [93.5-104.0s]  "hit piece" box top, AUDIT big below. Strikethrough at mid-height of text.
# "hit piece" text size=36, baseline y:95. Cap-height ~36*0.7=25px. Mid ≈ y:95-25/2=82. stk y:82.
scenes.append(scene(i, 93.5, 104.0,
    "This is not a hit piece. This is an AUDIT.", [
    W(190),
    S(rect(122, 52, 268, 63), LGRAY, 2, 292),
    T("hit piece", 145, 95, 36, GRAY, 312),
    W(300),
    S(stk(128, 75, 255), RED, 3.2, 272),  # mid of text
    W(380),
    T("AUDIT", 152, 205, 78, INK, 510),
    S(ul(152, 214, 292), INK, 4, 342),
    S(ul(157, 223, 282), INK, 2, 275),
    W(340),
    T("where did your", 98, 275, 24, GRAY, 242),
    T("$11.99 go?", 325, 275, 28, RED, 262),
])); i+=1

# S13  [104.0-116.5s]  $9.99 flat line 2014-2021. "7 YEARS" top-left zone.
scenes.append(scene(i, 104.0, 116.5,
    "$9.99 from 2014 to 2021 — 7 years, zero increases. That was the deal.", [
    W(190),
    S(hline(55, 492, 192, 50), GREEN, 3, 468),
    W(140),
    C(55, 192, 8, GREEN, True, 145),
    T("2014", 35, 215, 18, GREEN, 172),
    C(492, 192, 8, GREEN, True, 145),
    T("2021", 468, 215, 18, GREEN, 172),
    W(195),
    T("7", 48, 155, 86, INK, 448),
    T("YEARS", 155, 155, 46, INK, 352),
    W(195),
    T("zero increases", 308, 155, 26, GREEN, 252),
    W(245),
    T("$9.99", 202, 298, 58, GREEN, 428),
    W(195),
    T("that was the deal.", 205, 335, 22, GRAY, 242),
])); i+=1

# S14  [116.5-132.0s]  $10 = every song. Large equation.
scenes.append(scene(i, 116.5, 132.0,
    "You pay $10 and get every song ever recorded. Best deal in history of consumer media.", [
    W(190),
    T("$10", 48, 132, 96, GREEN, 528),
    W(295),
    T("=", 220, 132, 72, INK, 292),
    W(195),
    T("every song", 292, 95, 30, INK, 292),
    T("ever recorded", 292, 132, 30, INK, 292),
    W(245),
    S(ul(292, 140, 218), GREEN, 2.5, 235),
    W(295),
    T("best deal in history", 68, 215, 28, GREEN, 282),
    T("of consumer media", 85, 248, 28, GREEN, 282),
    S(ul(68, 255, 330), GREEN, 2.5, 255),
    W(245),
    T("honestly? insane.", 172, 318, 26, GRAY, 252),
])); i+=1

# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER 4: THE HIKES  (cues 35-62, 130-235s)
# ═══════════════════════════════════════════════════════════════════════════════

# S15  [132.0-142.0s]  Hike #1. Before x:58-210, arrow, after x:285+. No overlap.
# $9.99 size=52 baseline y:205. Cap-height≈36. Mid≈y:205-18=187. stk y:187.
scenes.append(scene(i, 132.0, 142.0,
    'June 2023. First hike. $10.99. "Market conditions."', [
    W(190),
    T("June 2023", 48, 68, 34, INK, 312),
    S(ul(48, 76, 192), INK, 2.5, 225),
    W(268),
    T("hike #1", 48, 118, 28, RED, 252),
    W(268),
    T("$9.99", 58, 205, 52, LGRAY, 352),
    S(stk(53, 187, 138), RED, 3, 252),
    W(242),
    S(arrow(212, 187, 275, 187, 12), RED, 2.5, 232),
    W(145),
    T("$10.99", 285, 205, 52, RED, 388),
    S(ul(285, 213, 168), RED, 3, 262),
    W(295),
    T('"market conditions"', 52, 272, 26, AMBER, 262),
    W(195),
    T("first increase in company history", 48, 338, 20, GRAY, 242),
])); i+=1

# S16  [142.0-155.0s]  Real reason. Funnel LEFT x:52-215. Wall St RIGHT x:308+.
# Funnel: y:88-195. X lines stay within funnel bounds.
# Text inside funnel: x:88 baseline y:148 and y:178. Both inside x:52-215, y:88-195 ✓
scenes.append(scene(i, 142.0, 155.0,
    "Real reason: ran out of new subscribers. Wall Street demanded growth.", [
    W(175),
    T("real reason:", 48, 60, 30, RED, 282),
    S(ul(48, 68, 178), RED, 2.2, 205),
    W(292),
    S(J([{"x":52,"y":88},{"x":215,"y":88},{"x":185,"y":195},
          {"x":82,"y":195},{"x":52,"y":88}], 1.5), INK, 2, 372),
    T("new subs", 88, 148, 19, GRAY, 195),
    W(242),
    # X lines strictly within funnel x:52-215, y:88-195
    S(line(52, 88, 215, 195, 14), RED, 2.5, 232),
    S(line(215, 88, 52, 195, 14), RED, 2.5, 232),
    T("EMPTY", 88, 178, 20, RED, 195),
    W(292),
    S(arrow(222, 145, 298, 145, 10), GRAY, 2, 222),
    W(145),
    T("Wall St.", 305, 128, 32, AMBER, 282),
    T("demands", 305, 162, 24, AMBER, 225),
    T("GROWTH", 305, 196, 34, AMBER, 292),
    W(292),
    S(arrow(378, 218, 378, 272, 11), RED, 2, 225),
    T("squeeze", 335, 305, 26, RED, 242),
    T("existing users", 312, 333, 22, RED, 232),
])); i+=1

# S17  [155.0-168.0s]  Hike #2. Big ? in right zone x:498 — clear of prices which end ~x:455.
scenes.append(scene(i, 155.0, 168.0,
    'April 2024. Second hike. $11.99. "Expansion of features."', [
    W(190),
    T("April 2024", 48, 68, 34, INK, 312),
    S(ul(48, 76, 185), INK, 2.5, 225),
    W(262),
    T("hike #2", 48, 118, 28, RED, 252),
    W(252),
    T("$10.99", 55, 200, 48, LGRAY, 352),
    S(stk(50, 181, 150), RED, 3, 245),   # mid of 48px text: baseline 200, cap~34, mid=183→181
    S(arrow(218, 182, 282, 182, 11), RED, 2.2, 225),
    T("$11.99", 290, 200, 48, RED, 382),
    W(295),
    T('"expansion of features"', 48, 262, 23, AMBER, 262),
    W(245),
    # Big ? at right edge — prices end around x:290+~165=455, ? at x:498 ✓
    T("?", 498, 262, 118, LGRAY, 352),
    W(292),
    T("one year later. no real excuse.", 48, 340, 20, GRAY, 245),
])); i+=1

# S18  [168.0-186.0s]  Audiobooks. Book LEFT x:55-215 y:80-215.
# Text inside book: x:118 y:148,174. Bounds check: x:118>55+8=63 ✓, y:174<215-8=207 ✓
# Circle around "15 hrs/mo" text: text x:248-390 roughly, circle cx=328 cy=130 r=50.
# Circle left edge=278 > book right edge=215. No overlap ✓
scenes.append(scene(i, 168.0, 186.0,
    "Those features? Audiobooks. 15 hours/month. You didn't ask for them.", [
    W(190),
    T("those features?", 48, 58, 30, GRAY, 272),
    W(295),
    S(rect(55, 80, 160, 135), AMBER, 2.5, 332),
    S(vline(108, 80, 215), AMBER, 2, 195),
    T("audio", 118, 148, 22, AMBER, 205),
    T("books", 118, 174, 22, AMBER, 205),
    W(245),
    # "15 hrs/mo" text at x:248 — starts well right of book edge at 215 ✓
    T("15 hrs/mo", 248, 148, 28, AMBER, 258),
    C(328, 130, 50, AMBER, False, 342),
    W(245),
    # X strictly within book bounds
    S(line(55, 80, 215, 215, 15), RED, 3, 262),
    S(line(215, 80, 55, 215, 15), RED, 3, 262),
    W(295),
    T("you didn't ask", 55, 270, 28, RED, 258),
    T("for this", 55, 300, 28, RED, 242),
    W(195),
    T("added anyway", 290, 288, 24, GRAY, 232),
])); i+=1

# S19  [186.0-200.0s]  "feature" → HOSTAGE. Three text rows, generous spacing.
scenes.append(scene(i, 186.0, 200.0,
    "That's not a feature. That's a hostage.", [
    W(265),
    T("that's not a", 58, 80, 30, INK, 272),
    W(175),
    T("feature", 58, 146, 58, LGRAY, 382),
    W(342),
    S(stk(53, 122, 212), RED, 3.5, 292),   # mid of 58px: baseline 146, cap≈41, mid≈146-20=126→122
    W(342),
    T("that's a", 58, 228, 30, INK, 262),
    W(195),
    T("HOSTAGE", 55, 308, 64, RED, 488),
    S(ul(55, 317, 338), RED, 3.5, 312),
    S(ul(60, 327, 328), RED, 2, 252),
])); i+=1

# S20  [200.0-215.0s]  Hike #3 three tiers. Rows at y:162,215,268 — 53px apart, no overlap.
scenes.append(scene(i, 200.0, 215.0,
    "July 2025. Third hike. Individual $12.99. Duo $17.99. Family $19.99.", [
    W(175),
    T("July 2025", 48, 65, 34, INK, 312),
    S(ul(48, 73, 175), INK, 2.5, 218),
    W(245),
    T("hike #3", 48, 112, 28, RED, 252),
    W(292),
    T("Individual", 48, 162, 23, INK, 205),
    S(arrow(192, 155, 255, 155, 9), RED, 1.8, 145),
    T("$12.99", 262, 162, 30, RED, 262),
    W(295),
    T("Duo", 48, 215, 23, INK, 205),
    S(arrow(192, 208, 255, 208, 9), RED, 1.8, 145),
    T("$17.99", 262, 215, 30, RED, 262),
    W(295),
    T("Family", 48, 268, 23, INK, 205),
    S(arrow(192, 261, 255, 261, 9), RED, 1.8, 145),
    T("$19.99", 262, 268, 30, RED, 262),
    W(295),
    T("psychological trick", 48, 330, 24, AMBER, 252),
    S(ul(48, 338, 200), AMBER, 2, 205),
])); i+=1

# S21  [215.0-232.0s]  "Basic" repackaging. Old box LEFT x:48-218, new box RIGHT x:300-490.
# Arrow between at y:112. Text inside each box measured against its bounds.
scenes.append(scene(i, 215.0, 232.0,
    'New "Basic" = old plan repackaged. Psychological trick.', [
    W(190),
    S(rect(48, 68, 170, 88), LGRAY, 2, 302),
    T("old plan", 72, 102, 22, GRAY, 205),
    T("$9.99", 72, 128, 28, GRAY, 242),
    S(stk(65, 108, 145), RED, 2.5, 225),  # mid of 28px text: baseline 128, cap≈20, mid=118→108 ✓
    W(295),
    S(arrow(222, 112, 295, 112, 10), INK, 2, 215),
    T("repackaged", 222, 104, 16, GRAY, 165),
    W(145),
    S(rect(300, 68, 190, 88), AMBER, 2.5, 322),
    T('"Basic"', 322, 102, 22, AMBER, 215),
    T("$10.99", 318, 128, 28, AMBER, 258),
    W(295),
    T("same plan +$1 more", 308, 175, 22, RED, 248),
    W(295),
    T("that's not a price increase.", 48, 265, 24, INK, 262),
    T("that's a psychological trick.", 48, 295, 24, RED, 262),
    W(245),
    T('Wall Street called it "brilliant"', 48, 340, 21, AMBER, 248),
])); i+=1

# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER 5: 4TH HIKE & 50%  (cues 62-71, 231-272s)
# ═══════════════════════════════════════════════════════════════════════════════

# S22  [232.0-252.0s]  2026 #4. Two price columns clear of each other.
scenes.append(scene(i, 232.0, 252.0,
    "2026. Fourth hike. $14.99 individual. Family ~$22. Still no lossless.", [
    W(190),
    T("2026", 48, 68, 38, RED, 332),
    T("hike #4", 210, 68, 30, RED, 272),
    W(292),
    T("Individual", 48, 130, 22, INK, 205),
    T("$14.99", 48, 165, 44, RED, 382),
    W(295),
    T("Family", 318, 130, 22, INK, 205),
    T("~$22", 318, 165, 44, RED, 352),
    W(295),
    S(hline(48, 580, 185), LGRAY, 1.5, 330),
    W(195),
    # "no lossless" box: x:65-465 y:215-272. Text inside: x:78 y:252,272. 252<=264 ✓
    S(rect(65, 215, 400, 57), GRAY, 1.8, 312),
    T("still no lossless audio", 78, 252, 24, GRAY, 248),
    T("(announced 2021)", 78, 272, 18, LGRAY, 195),
    W(292),
    T("Apple Music: lossless ✓", 65, 320, 20, GREEN, 232),
    T("Tidal: hi-res ✓", 65, 342, 20, GREEN, 215),
])); i+=1

# S23  [252.0-272.0s]  Timeline two eras + 50% punchline. Punchline strictly y:295+.
scenes.append(scene(i, 252.0, 272.0,
    "2014-2021 flat. 2023-2026 up four times. 50% more. Same app.", [
    W(190),
    S(hline(48, 308, 178, 45), GREEN, 3, 388),
    S(arrow(308, 178, 578, 65, 14), RED, 3, 428),
    W(145),
    C(48, 178, 7, GREEN, True, 125),
    T("2014", 32, 198, 18, GREEN, 165),
    C(308, 178, 7, GREEN, True, 125),
    T("2021", 290, 198, 18, GREEN, 165),
    C(578, 65, 9, RED, True, 145),
    T("2026", 552, 88, 18, RED, 172),
    W(242),
    T("flat", 155, 160, 19, GREEN, 175),
    T("↑↑↑↑", 395, 132, 22, RED, 205),
    W(245),
    T("50%", 145, 308, 92, RED, 528),
    S(ul(135, 318, 235), RED, 4, 352),
    S(ul(140, 328, 225), RED, 2.5, 282),
    W(292),
    T("more. same app.", 112, 358, 22, GRAY, 242),
])); i+=1

# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER 6: IS IT 50% BETTER?  (cues 72-90, 272-342s)
# ═══════════════════════════════════════════════════════════════════════════════

# S24  [272.0-288.0s]  Catalog bars LEFT. "Not 50%" box RIGHT zone x:338+.
scenes.append(scene(i, 272.0, 288.0,
    "50% better? Catalog 100M→110M songs. Only 10% growth. Mostly AI noise.", [
    W(190),
    T("50% better?", 48, 68, 36, RED, 332),
    W(295),
    S(rect(78, 108, 60, 162), GREEN, 2.5, 312),
    T("100M", 68, 282, 18, GRAY, 180),
    T("songs", 68, 300, 16, GRAY, 160),
    S(rect(158, 94, 60, 176), GREEN, 2.5, 322),
    T("110M", 148, 282, 18, GRAY, 180),
    T("songs", 148, 300, 16, GRAY, 160),
    W(245),
    S(arrow(222, 145, 282, 98, 10), AMBER, 2, 242),
    T("+10%", 290, 96, 30, AMBER, 272),
    W(245),
    # Box right zone: x:338-548 y:86-156. Text inside x:355 y:128. 355>338+8=346 ✓ 128<156-8=148 — use y:136
    S(rect(338, 86, 210, 70), RED, 2, 272),
    T("not 50%", 355, 136, 30, RED, 272),
    W(292),
    T("most new songs: AI noise", 48, 338, 22, RED, 248),
])); i+=1

# S25  [288.0-304.0s]  Big NO + X cross. Table strictly below y:238.
# X cross: x:265-522 y:85-218. NO text at x:290 y:195 (inside cross bounds) ✓
# Table starts y:238 — gap of 20px below cross ✓
scenes.append(scene(i, 288.0, 304.0,
    "Audio quality improved? No. Same bitrate as 2020. Apple Music: lossless.", [
    W(190),
    T("audio quality", 48, 68, 30, INK, 282),
    T("improved?", 48, 102, 30, INK, 262),
    W(245),
    S(line(265, 85, 522, 218, 18), RED, 3.5, 292),
    S(line(522, 85, 265, 218, 18), RED, 3.5, 292),
    T("NO", 290, 195, 96, RED, 528),
    W(295),
    S(hline(48, 580, 238), LGRAY, 1.5, 332),
    T("Spotify", 52, 268, 20, GRAY, 195),
    T("same Ogg Vorbis 2020", 188, 268, 20, RED, 245),
    S(hline(48, 580, 282), LGRAY, 1.2, 275),
    T("Apple Music", 52, 308, 20, GREEN, 205),
    T("lossless ✓", 232, 308, 20, GREEN, 205),
    S(hline(48, 580, 322), LGRAY, 1.2, 258),
    T("Tidal", 52, 345, 20, GREEN, 195),
    T("hi-res ✓", 232, 345, 20, GREEN, 195),
])); i+=1

# S26  [304.0-327.0s]  5 years announced, nothing delivered.
scenes.append(scene(i, 304.0, 327.0,
    "Only major streamer without lossless. 5 years after announcing it. Nothing.", [
    W(190),
    T("only major streamer", 48, 68, 26, INK, 262),
    T("without lossless audio", 48, 98, 26, RED, 252),
    T("in 2026.", 48, 128, 26, RED, 252),
    W(342),
    T("announced:", 48, 198, 24, GRAY, 232),
    T("2021", 252, 198, 36, AMBER, 302),
    W(195),
    S(arrow(308, 190, 408, 190, 11), INK, 2, 225),
    W(115),
    T("delivered:", 418, 198, 24, GRAY, 232),
    T("???", 565, 198, 30, RED, 252),
    W(295),
    T("5 years.", 48, 272, 40, INK, 352),
    T("nothing.", 248, 272, 40, RED, 352),
    W(245),
    T("artists paid 50% more? definitely not.", 48, 338, 20, GRAY, 248),
])); i+=1

# S27  [327.0-342.0s]  Two buckets. Text inside each measured against its bounds.
# Bucket1: x:58-242 y:142-258. Text x:85,y:188,212,248. Checks: 85>58+8=66 ✓ 248<258-8=250 ✓
# Bucket2: x:352-558 y:142-258. Text x:368 ✓
scenes.append(scene(i, 327.0, 342.0,
    "Where did the money go? Spotify profit margin and Daniel Ek's bank account.", [
    W(190),
    T("where did the", 48, 68, 28, GRAY, 258),
    T("money go?", 48, 100, 34, INK, 302),
    W(295),
    S(J([{"x":58,"y":142},{"x":242,"y":142},{"x":225,"y":258},{"x":75,"y":258},{"x":58,"y":142}], 1.5),
      GREEN, 2.5, 342),
    T("Spotify", 85, 188, 22, INK, 215),
    T("margin", 85, 212, 22, INK, 215),
    T("$0→$1B+", 82, 248, 19, GREEN, 195),
    W(295),
    S(J([{"x":352,"y":142},{"x":558,"y":142},{"x":542,"y":258},{"x":368,"y":258},{"x":352,"y":142}], 1.5),
      AMBER, 2.5, 342),
    T("Daniel Ek", 368, 188, 22, INK, 218),
    T("net worth", 368, 212, 22, INK, 218),
    T("↑↑↑↑", 398, 248, 22, AMBER, 205),
    W(295),
    T("50% more. from you.", 152, 318, 24, RED, 252),
    T("hold that number.", 152, 346, 22, GRAY, 242),
])); i+=1

# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER 7: $10 BILLION HEADLINE  (cues 91-113, 342-430s)
# ═══════════════════════════════════════════════════════════════════════════════

# S28  [342.0-358.0s]
scenes.append(scene(i, 342.0, 358.0,
    "Spotify paid $10 billion to the music industry in 2024.", [
    W(190),
    T("the number Spotify", 48, 68, 26, GRAY, 258),
    T("wants you to remember:", 48, 98, 26, GRAY, 255),
    W(342),
    T("$10", 68, 252, 96, GREEN, 548),
    T("BILLION", 300, 252, 52, GREEN, 422),
    W(295),
    T("paid to music industry", 68, 298, 22, GRAY, 248),
    T("in 2024", 68, 325, 22, GRAY, 225),
    W(195),
    S(rect(68, 335, 360, 26), LGRAY, 1.5, 235),
    T("press release · investor call · blog", 75, 353, 14, LGRAY, 195),
])); i+=1

# S29  [358.0-378.0s]  WRONG. ≠ paid to artists.
scenes.append(scene(i, 358.0, 378.0,
    'Sounds incredible. Wrong. "Paid to the music industry" does not mean paid to artists.', [
    W(190),
    T("sounds incredible?", 48, 68, 28, GRAY, 262),
    W(295),
    T("WRONG", 125, 185, 88, RED, 528),
    S(ul(115, 194, 375), RED, 4, 352),
    W(342),
    T('"paid to the music industry"', 48, 258, 22, GRAY, 258),
    W(195),
    T("≠", 48, 302, 52, RED, 332),
    T("paid to artists", 128, 302, 34, RED, 312),
    S(ul(128, 310, 208), RED, 2.5, 242),
    W(292),
    T("the music industry is a chain.", 48, 352, 22, GRAY, 252),
])); i+=1

# S30  [378.0-395.0s]  Chain diagram. Vertical flow centred x:215-340. Cuts RIGHT x:428+.
scenes.append(scene(i, 378.0, 395.0,
    "Spotify → Distributor → Label → Publisher → Artist. Each takes a cut.", [
    W(175),
    T("the chain:", 48, 55, 28, INK, 258),
    W(245),
    T("Spotify", 215, 98, 24, GREEN, 232),
    S(arrow(268, 106, 268, 136, 9), GRAY, 1.8, 172),
    T("Distributor", 195, 156, 22, AMBER, 222),
    T("(DistroKid, TuneCore...)", 195, 175, 15, LGRAY, 175),
    S(arrow(268, 182, 268, 212, 9), GRAY, 1.8, 155),
    T("Label  (if any)", 205, 232, 22, AMBER, 222),
    S(arrow(268, 239, 268, 269, 9), GRAY, 1.8, 155),
    T("Publisher", 212, 289, 22, GRAY, 218),
    S(arrow(268, 296, 268, 326, 9), GRAY, 1.8, 155),
    T("Artist", 230, 346, 22, RED, 222),
    W(195),
    T("if there's anything left", 342, 346, 18, GRAY, 215),
    # Cuts right zone x:428+
    T("−20-30%", 428, 175, 18, RED, 180),
    T("−50-85%", 428, 232, 18, RED, 180),
    T("−cut", 428, 289, 18, RED, 162),
])); i+=1

# S31  [395.0-415.0s]  Shrinking boxes. Each box has no text — labels are outside/beside.
scenes.append(scene(i, 395.0, 415.0,
    "After every middleman: fraction of a fraction of a fraction.", [
    W(190),
    T("the $10 billion", 48, 68, 28, INK, 262),
    W(245),
    S(rect(48, 95, 280, 80), GREEN, 2.5, 332),
    T("$10B  (headline)", 60, 145, 22, GREEN, 232),  # inside box: x:60>56 ✓, y:145<175-8=167 ✓
    W(275),
    S(rect(48, 192, 180, 60), AMBER, 2, 272),
    T("after middlemen", 58, 232, 20, AMBER, 225),  # inside: y:232<252-8=244 ✓
    W(248),
    S(rect(48, 268, 80, 47), RED, 2, 215),
    # Label outside box, to the right
    S(arrow(132, 292, 195, 292, 9), GRAY, 1.8, 165),
    T("artist's share", 205, 298, 20, RED, 228),
    W(295),
    T("fraction", 340, 298, 30, RED, 272),
    T("of a fraction", 340, 328, 24, RED, 258),
    T("of a fraction", 340, 355, 20, RED, 238),
    W(295),
    T("that $10B headline? meaningless.", 48, 388, 21, GRAY, 248),
])); i+=1

# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER 8: PER STREAM MATH  (cues 113-129, 430-494s)
# ═══════════════════════════════════════════════════════════════════════════════

# S32  [415.0-432.0s]  Fraction visual LEFT. Context RIGHT.
scenes.append(scene(i, 415.0, 432.0,
    "Per stream: 3/10 of a cent to 5/10 of a cent.", [
    W(190),
    T("per stream:", 48, 68, 30, INK, 272),
    W(295),
    S(hline(118, 368, 188, 40), INK, 3, 332),
    T("3", 188, 178, 96, RED, 528),
    T("10", 205, 248, 72, RED, 428),
    W(295),
    T("of a cent", 368, 208, 30, INK, 272),
    W(245),
    T("to", 340, 258, 26, GRAY, 215),
    W(95),
    T("5/10", 390, 258, 28, RED, 252),
    T("of a cent", 510, 258, 22, INK, 228),
    W(295),
    T("$0.003 – $0.005", 112, 330, 30, RED, 292),
    T("per play", 402, 330, 24, GRAY, 238),
])); i+=1

# S33  [432.0-452.0s]  Min wage math.
scenes.append(scene(i, 432.0, 452.0,
    "To earn minimum wage $15/hr, an artist needs 4,000 streams every hour.", [
    W(190),
    T("minimum wage:", 48, 68, 26, INK, 245),
    T("$15 / hr", 48, 102, 36, GREEN, 312),
    W(295),
    T("streams needed:", 48, 162, 26, INK, 245),
    T("4,000", 48, 238, 88, RED, 528),
    T("per hour", 48, 278, 30, RED, 272),
    W(295),
    T("every hour.", 48, 330, 26, INK, 242),
    T("non-stop.", 252, 330, 26, RED, 242),
    S(ul(252, 338, 145), RED, 2.5, 215),
    W(245),
    T("(low bar.)", 48, 358, 22, GRAY, 218),
])); i+=1

# S34  [452.0-465.0s]  $59K = 20M streams.
scenes.append(scene(i, 452.0, 465.0,
    "Average US salary $59,000 requires 20 million streams per year.", [
    W(190),
    T("avg US salary:", 48, 68, 26, INK, 242),
    T("$59,000", 48, 112, 46, GREEN, 382),
    W(295),
    T("=", 48, 200, 52, INK, 272),
    W(195),
    T("20,000,000", 128, 200, 42, RED, 402),
    T("streams / year", 128, 240, 26, RED, 258),
    W(295),
    T("20 million.", 48, 305, 38, INK, 332),
    S(ul(48, 313, 212), INK, 3, 252),
    W(245),
    T("in a year.", 48, 352, 26, GRAY, 242),
    T("for context ↓", 265, 352, 22, GRAY, 228),
])); i+=1

# S35  [465.0-486.0s]  Average song: 30 streams. Giant "30".
scenes.append(scene(i, 465.0, 486.0,
    "Average song on Spotify: 30 streams per month. Not 30,000. Thirty.", [
    W(190),
    T("average song:", 48, 68, 28, INK, 262),
    W(245),
    T("30", 152, 228, 120, RED, 608),
    T("streams", 368, 198, 32, INK, 292),
    T("per month", 368, 235, 28, INK, 262),
    W(342),
    T("not 30,000", 98, 308, 36, GRAY, 322),
    S(stk(93, 290, 205), RED, 3, 258),   # mid of 36px: baseline 308, cap≈25, mid=296→290 ✓
    W(245),
    T("thirty.", 98, 355, 38, RED, 332),
])); i+=1

# S36  [486.0-500.0s]  2K listeners chain.
scenes.append(scene(i, 486.0, 500.0,
    "2,000 monthly listeners = 60,000 streams = $180/month before fees.", [
    W(190),
    T("2,000", 48, 88, 42, INK, 372),
    T("listeners", 48, 122, 24, GRAY, 232),
    W(245),
    S(arrow(48, 148, 48, 182, 10), INK, 2, 195),
    T("60,000 streams/mo", 48, 210, 26, AMBER, 258),
    W(245),
    S(arrow(48, 225, 48, 262, 10), INK, 2, 195),
    T("$180", 48, 308, 72, RED, 478),
    T("per month", 48, 342, 26, RED, 252),
    W(295),
    T("before distributor fees", 288, 305, 20, GRAY, 238),
    T("before label cuts", 288, 330, 20, GRAY, 222),
    T("before taxes", 288, 355, 20, GRAY, 208),
])); i+=1

# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER 9: REVENUE SHARE MODEL  (cues 130-148, 497-570s)
# ═══════════════════════════════════════════════════════════════════════════════

# S37  [500.0-516.0s]  Pool → divide → payout diagram.
scenes.append(scene(i, 500.0, 516.0,
    "Not a flat rate. Revenue share: pool all revenue, divide by total streams.", [
    W(190),
    T("not a flat rate", 48, 68, 30, RED, 282),
    S(ul(48, 76, 212), RED, 2.5, 225),
    W(295),
    # Pool bucket: x:78-558 y:126-212
    S(J([{"x":78,"y":126},{"x":558,"y":126},{"x":538,"y":212},{"x":98,"y":212},{"x":78,"y":126}], 1.5),
      GREEN, 2.5, 372),
    # Text inside pool: x:148 y:178. 148>78+8=86 ✓ 178<212-8=204 ✓
    T("subscription revenue pool", 148, 178, 20, INK, 228),
    W(245),
    S(arrow(315, 218, 315, 255, 10), INK, 2, 205),
    T("÷ total platform streams", 128, 282, 20, GRAY, 238),
    W(195),
    S(arrow(315, 295, 315, 325, 10), INK, 2, 188),
    T("your payout per stream", 132, 350, 20, RED, 238),
    W(245),
    T("every month. every country. pooled.", 58, 378, 19, GRAY, 242),
])); i+=1

# S38  [516.0-534.0s]  30¢/70¢ bar. Text inside each zone measured.
# 30¢ block: x:48-240 y:75-165. Text x:98 y:126,152. 98>56 ✓, 152<157 ✓
# 70¢ block: x:222-628 y:75-165. Text x:368 y:126,152. 368>230 ✓ ✓
scenes.append(scene(i, 516.0, 534.0,
    "Spotify takes ~30%. Rest to rights holders. Weighted by country.", [
    W(188),
    T("every $1 you pay:", 48, 56, 24, GRAY, 238),
    W(245),
    S(rect(48, 75, 192, 90), GREEN, 2.5, 322),
    T("30¢ → Spotify", 58, 128, 24, GREEN, 248),
    T("(servers, staff, AI)", 58, 152, 15, GRAY, 178),
    W(295),
    S(rect(48, 172, 450, 90), AMBER, 2.5, 412),
    T("70¢ → rights holders", 58, 225, 24, AMBER, 248),
    T("(labels, publishers, maybe artists)", 58, 248, 15, GRAY, 178),
    W(295),
    S(arrow(318, 275, 318, 308, 10), GRAY, 1.8, 188),
    T("weighted by market share", 128, 335, 20, GRAY, 238),
    W(195),
    T("US stream > Brazil stream", 128, 358, 19, LGRAY, 228),
])); i+=1

# S39  [534.0-558.0s]  Country comparison table.
scenes.append(scene(i, 534.0, 558.0,
    "Same song: 0.5¢ US, 0.1¢ India, 0.07¢ Nigeria, 0.5¢ Norway. 5x difference.", [
    W(190),
    T("same song.", 48, 68, 32, INK, 292),
    T("different worlds.", 255, 68, 28, GRAY, 262),
    W(295),
    S(hline(48, 575, 92), LGRAY, 1.2, 302),
    T("USA", 52, 122, 22, INK, 205),
    T("0.5¢ / stream", 228, 122, 24, GREEN, 238),
    S(hline(48, 575, 136), LGRAY, 1.2, 265),
    T("India", 52, 168, 22, INK, 205),
    T("0.1¢ / stream", 228, 168, 24, AMBER, 232),
    S(hline(48, 575, 182), LGRAY, 1.2, 258),
    T("Nigeria", 52, 214, 22, INK, 208),
    T("0.07¢ / stream", 228, 214, 24, RED, 245),
    S(hline(48, 575, 228), LGRAY, 1.2, 255),
    T("Norway", 52, 260, 22, INK, 205),
    T("0.5¢ / stream", 228, 260, 24, GREEN, 232),
    S(hline(48, 575, 274), LGRAY, 1.2, 248),
    W(295),
    T("same 3 minutes of music.", 48, 320, 22, GRAY, 248),
    T("5× difference in payout.", 48, 348, 24, RED, 258),
])); i+=1

# S40  [558.0-584.0s]  Ambiguity benefits Spotify.
scenes.append(scene(i, 558.0, 584.0,
    "Per-stream is a meaningless average. Ambiguity benefits Spotify.", [
    W(190),
    T("per-stream rate:", 48, 68, 28, INK, 262),
    T("a meaningless average", 48, 102, 28, RED, 268),
    W(295),
    # Box: x:48-568 y:128-216. Text inside x:65 y:168,198. 168<208 ✓ 198<208 ✓
    S(rect(48, 128, 520, 88), LGRAY, 1.8, 372),
    T("nobody knows exact rate", 65, 168, 22, GRAY, 248),
    T("→ nobody can prove underpayment", 65, 198, 22, RED, 265),
    W(295),
    T("Spotify knows this.", 48, 258, 28, INK, 262),
    S(ul(48, 266, 220), INK, 2.5, 215),
    W(245),
    T("known for years.", 48, 300, 26, INK, 252),
    T("done nothing.", 308, 300, 26, RED, 252),
    W(245),
    T("the ambiguity benefits them.", 48, 348, 24, GRAY, 258),
])); i+=1

# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER 10: PAYOUT DECLINE  (cues 153-163, 583-625s)
# ═══════════════════════════════════════════════════════════════════════════════

# S41  [584.0-604.0s]  Bar chart comparison. Bars LEFT. Labels outside bars BELOW.
# Bar1: x:78-143 y:85-280. Bar2: x:172-237 y:168-280. Labels at y:298 (below both bars) ✓
# Arrow between bar tops: from y:138 to y:172 (bar2 top). x:145→y → x:188 ✓
scenes.append(scene(i, 584.0, 604.0,
    "2014: 0.7¢/stream. Today: 0.3¢. Down 57%. Revenue tripled. Artist slice halved.", [
    W(190),
    S(rect(78, 85, 65, 195), RED, 2.5, 342),
    T("2014", 70, 298, 19, GRAY, 175),
    T("0.7¢", 72, 315, 18, GRAY, 168),
    W(195),
    S(rect(172, 168, 65, 112), RED, 2.5, 275),
    T("2024", 165, 298, 19, GRAY, 175),
    T("0.3¢", 165, 315, 18, GRAY, 168),
    W(245),
    S(arrow(146, 138, 188, 172, 9), RED, 2, 215),
    T("−57%", 272, 145, 36, RED, 312),
    S(ul(265, 153, 108), RED, 2.5, 218),
    W(292),
    S(hline(48, 575, 338), LGRAY, 1.2, 295),
    T("Spotify revenue: $5B → $15B (tripled)", 48, 362, 20, GREEN, 245),
    W(195),
    T("artist slice: halved", 48, 385, 20, RED, 232),
])); i+=1

# S42  [604.0-625.0s]  Two circles: small 2019 pie (cx=135 cy=178 r=68), big 2024 (cx=415 cy=178 r=108).
# Slice labels INSIDE each circle — must be within r from centre.
# Small: "≈30%" at x:108 y:185. Distance from cx=135: 27px < r=68 ✓
# Big: "≈15%" at x:388 y:185. Distance from cx=415: 27px < r=108 ✓
scenes.append(scene(i, 604.0, 625.0,
    "Pie got 3x bigger. Artist slice got twice as small. Engineered on purpose.", [
    W(190),
    C(135, 178, 68, INK, False, 372),
    T("2019", 98, 270, 18, GRAY, 178),
    T("$5B rev", 92, 288, 17, GRAY, 168),
    T("≈30%", 108, 185, 18, GREEN, 185),
    W(195),
    C(415, 178, 108, INK, False, 432),
    T("2024", 358, 298, 18, GRAY, 178),
    T("$15B rev", 350, 316, 17, GRAY, 168),
    T("≈15%", 388, 185, 18, RED, 185),
    W(245),
    S(arrow(215, 178, 295, 178, 11), INK, 2, 232),
    T("3× bigger", 225, 168, 18, INK, 195),
    W(245),
    T("pie grew 3×.", 48, 352, 26, INK, 252),
    T("artist slice: ÷2.", 278, 352, 26, RED, 262),
    W(195),
    T("on purpose.", 192, 385, 30, RED, 278),
    S(ul(185, 393, 162), RED, 3, 245),
])); i+=1

# ═══════════════════════════════════════════════════════════════════════════════
# CHAPTER 11: DISCOVERY MODE  (cues 163-200, 624-767s)
# ═══════════════════════════════════════════════════════════════════════════════

# S43  [625.0-644.0s]  Record profits but new rule instead.
scenes.append(scene(i, 625.0, 644.0,
    "Record profits. New rule: Discovery Mode — might be the worst one yet.", [
    W(190),
    T("record profits ✓", 48, 68, 28, GREEN, 262),
    W(245),
    T("share the love?", 48, 122, 28, INK, 262),
    W(295),
    T("WRONG", 188, 222, 80, RED, 498),
    W(342),
    T("new rule instead:", 48, 295, 26, GRAY, 252),
    W(195),
    T("Discovery Mode", 48, 338, 34, RED, 312),
    S(ul(48, 346, 250), RED, 3, 252),
    W(245),
    T("might be the worst one yet", 48, 378, 22, GRAY, 252),
])); i+=1

# S44  [644.0-660.0s]  $1 bar: 30¢ Spotify / 70¢ rights.
# 30¢ block: x:48-240 y:85-153. Text x:58 y:126,147. 126<145 ✓ 147<145 → use 143 ✓
# 70¢ block: x:240-628 y:85-153. Text x:318 y:126,143 ✓
scenes.append(scene(i, 644.0, 660.0,
    "Every $1: 30¢ to Spotify, 70¢ to rights holders. Here's what the 30¢ pays for.", [
    W(175),
    T("your $1:", 48, 56, 30, INK, 272),
    W(242),
    S(rect(48, 85, 192, 68), GREEN, 2.5, 292),
    T("30¢", 98, 126, 26, WHITE, 232),
    T("Spotify", 76, 143, 16, WHITE, 168),
    W(295),
    S(rect(248, 85, 380, 68), AMBER, 2.5, 372),
    T("70¢", 368, 126, 26, INK, 232),
    T("rights holders", 292, 143, 16, INK, 175),
    W(295),
    T("Spotify's 30¢ pays for:", 48, 208, 22, GRAY, 242),
    T("• servers & bandwidth", 65, 238, 20, GRAY, 222),
    T("• app development", 65, 262, 20, GRAY, 215),
    T("• AI features nobody asked for", 65, 286, 20, RED, 232),
    T("• podcasts (coming up)", 65, 310, 20, AMBER, 225),
])); i+=1

# S45  [660.0-680.0s]  70¢ market share — Universal vs indie table.
scenes.append(scene(i, 660.0, 680.0,
    "70¢ not split equally. Universal gets more per stream than an indie artist.", [
    W(175),
    T("70¢ to rights holders", 48, 55, 24, AMBER, 242),
    T("≠ split equally", 48, 82, 24, RED, 242),
    W(292),
    S(hline(48, 575, 108), LGRAY, 1.2, 285),
    T("Universal Music Group", 52, 142, 22, INK, 235),
    T("negotiated deal", 52, 165, 18, GRAY, 195),
    T("→ more $/stream", 428, 142, 22, GREEN, 232),
    S(hline(48, 575, 180), LGRAY, 1.2, 268),
    T("Indie artist (DistroKid)", 52, 218, 22, INK, 238),
    T("standard rate", 52, 242, 18, GRAY, 192),
    T("→ less $/stream", 428, 218, 22, RED, 232),
    S(hline(48, 575, 258), LGRAY, 1.2, 258),
    W(295),
    T("same streams.", 48, 305, 26, GRAY, 252),
    T("different payouts.", 265, 305, 26, RED, 262),
    W(245),
    T("Universal has minimum guarantees, advances, playlist placement.", 48, 352, 18, GRAY, 242),
])); i+=1

# S46  [680.0-700.0s]  Major label 0.5¢ vs indie 0.1¢.
scenes.append(scene(i, 680.0, 700.0,
    "Major label artist: ~0.5¢/stream. Indie: ~0.1¢. Same platform. Same listener. 5x difference.", [
    W(190),
    T("same platform.", 48, 68, 28, INK, 258),
    T("same listener.", 48, 100, 28, INK, 258),
    T("same 3-minute song.", 48, 132, 28, INK, 262),
    W(342),
    S(hline(48, 575, 158), LGRAY, 1.5, 302),
    T("Major label artist", 52, 192, 24, INK, 238),
    T("≈ 0.5¢/stream", 428, 192, 26, GREEN, 255),
    S(hline(48, 575, 208), LGRAY, 1.2, 275),
    T("Indie artist", 52, 248, 24, INK, 232),
    T("≈ 0.1¢/stream", 428, 248, 26, RED, 255),
    S(hline(48, 575, 264), LGRAY, 1.2, 265),
    W(295),
    T("5×", 162, 332, 64, RED, 442),
    T("difference", 298, 332, 32, RED, 298),
    W(245),
    T("system rewards scale, not streams.", 48, 385, 21, GRAY, 248),
])); i+=1

# S47  [700.0-725.0s]  Discovery Mode pitch vs catch.
scenes.append(scene(i, 700.0, 725.0,
    "Discovery Mode: opt in, get boost. Catch: lower royalty rate. Undisclosed.", [
    W(190),
    T("Discovery Mode", 48, 68, 32, RED, 302),
    S(ul(48, 76, 215), RED, 2.5, 232),
    W(295),
    T("the pitch:", 48, 128, 24, GRAY, 238),
    T("opt in →", 48, 162, 28, INK, 262),
    T("algorithmic boost", 198, 162, 28, GREEN, 268),
    T("more reach, more streams", 48, 195, 22, GREEN, 242),
    W(342),
    S(hline(48, 575, 222), RED, 2, 282),
    T("the catch:", 48, 262, 26, RED, 252),
    T("lower royalty rate", 48, 298, 30, RED, 288),
    S(ul(48, 306, 220), RED, 3, 242),
    W(295),
    T("Spotify won't say exactly how much lower.", 48, 348, 20, GRAY, 242),
    T('"promotional royalty rate"', 48, 375, 22, AMBER, 252),
])); i+=1

# S48  [725.0-748.0s]  Scale: reach up left, pay down right.
# Left pan top y:78. Right pan low y:238. Text: reach label above left pan (y:68), pay label below right (y:258).
# Gap between pan labels and scale arms confirmed.
scenes.append(scene(i, 725.0, 748.0,
    "More reach but lower pay. Pay to play. On a platform you already pay for.", [
    W(190),
    S(vline(152, 78, 195), INK, 2.5, 215),
    S(hline(78, 228, 78), INK, 2.5, 215),
    T("reach ↑", 82, 70, 24, GREEN, 238),   # above pan, y:70 < pan y:78 ✓
    W(245),
    S(vline(412, 78, 238), INK, 2.5, 255),
    S(hline(338, 488, 238), INK, 2.5, 215),
    T("pay ↓", 362, 258, 24, RED, 232),    # below pan, y:258 > pan y:238 ✓
    W(195),
    S(hline(152, 412, 158), LGRAY, 1.5, 215),
    C(282, 160, 8, INK, True, 125),
    W(295),
    T("more reach.", 52, 312, 30, GREEN, 278),
    T("less pay.", 278, 312, 30, RED, 278),
    W(245),
    T("pay to play.", 52, 355, 28, INK, 265),
    S(ul(52, 363, 168), INK, 3, 238),
    W(195),
    T("on a platform you already pay them for.", 52, 395, 20, GRAY, 245),
])); i+=1

# S49  [748.0-767.0s]  "Promotional royalty rate" — no number.
# Box: x:62-505 y:115-192. Text x:85 y:155,182. 155<184 ✓ 182<184 ✓
scenes.append(scene(i, 748.0, 767.0,
    'Spotify won\'t say exactly how much lower. Just: "promotional royalty rate."', [
    W(190),
    T("how much lower?", 48, 88, 32, INK, 302),
    W(295),
    S(rect(62, 115, 443, 77), LGRAY, 2, 332),
    T('"promotional', 85, 155, 30, GRAY, 288),
    T('royalty rate"', 85, 182, 30, GRAY, 288),
    W(342),
    T("that's it.", 85, 245, 32, INK, 298),
    T("no number.", 318, 245, 32, RED, 298),
    W(295),
    T("they know.", 85, 308, 28, GRAY, 262),
    T("they won't say.", 308, 308, 28, RED, 272),
    W(295),
    T("ambiguity is the product.", 85, 358, 26, RED, 262),
    S(ul(85, 366, 270), RED, 2.5, 228),
])); i+=1

# ── output ────────────────────────────────────────────────────────────────────
output = {"scenes": scenes}

print(f"Generated {len(scenes)} scenes (cues 0-199, 0-767s)")
for s in scenes:
    total_ms = sum(c.get("ms",0) for c in s["cmds"] if c.get("type")=="wait") + \
               sum(c.get("duration",0) for c in s["cmds"] if c.get("type") in ("text","stroke","circle"))
    dur = s["time_end"] - s["time_start"]
    print(f"  [{s['window_index']:2d}] {s['time_start']:6.1f}-{s['time_end']:6.1f}s  "
          f"anim={total_ms/1000:.1f}s  scndur={dur:.1f}s  '{s['phrase'][:55]}'")

import os
out_path = os.path.join(os.path.dirname(__file__), "../public/data/scenes_preview.json")
with open(out_path, "w") as f:
    json.dump(output, f, indent=2)
print(f"\nWrote {len(scenes)} scenes → public/data/scenes_preview.json")
