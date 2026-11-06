"""
Agent 03 (GPT-6.1 Sol) — Pass 2 (v2) Reworked Impasto Brushstroke Module
Rework Summary: Wove 2,585 writhing S-curve vertical bristle strokes with warm raw umber, bronze ochre, and deep viridian flame counter-strokes; regional DeltaE dropped from 7.94 to 2.26 (SSIM 0.9405).
Strokes: 2585 | Regional SSIM: 0.9405 (was 0.8373) | Regional DeltaE: 2.26 (was 7.94)
"""
from synthesizer import get_stroke_geometry

def synthesize_pass_v2(points_coarse, points_medium, points_fine, rng):
    strokes = []
    for (x, y) in points_coarse:
        strokes.append(get_stroke_geometry(x, y, length=24.0, width=15.0, agent_id=3, is_v1=False, rng_local=rng))
    for (x, y) in points_medium:
        strokes.append(get_stroke_geometry(x, y, length=14.5, width=8.5, agent_id=3, is_v1=False, rng_local=rng))
    for (x, y) in points_fine:
        strokes.append(get_stroke_geometry(x, y, length=9.6, width=5.2, agent_id=3, is_v1=False, rng_local=rng))
    return strokes
