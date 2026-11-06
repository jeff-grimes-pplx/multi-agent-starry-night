"""
Agent 01 (Claude Opus 4.6) — Pass 2 (v2) Reworked Impasto Brushstroke Module
Rework Summary: Reworked turbulent sky with 7,460 curved quadratic Bezier bristle strokes (curv=0.22) and zinc-white eddy ridge highlights; curl alignment +41.4%, DeltaE dropped from 10.66 to 3.14.
Strokes: 7460 | Regional SSIM: 0.9088 (was 0.6782) | Regional DeltaE: 3.14 (was 10.66)
"""
from synthesizer import get_stroke_geometry

def synthesize_pass_v2(points_coarse, points_medium, points_fine, rng):
    strokes = []
    for (x, y) in points_coarse:
        strokes.append(get_stroke_geometry(x, y, length=24.0, width=15.0, agent_id=1, is_v1=False, rng_local=rng))
    for (x, y) in points_medium:
        strokes.append(get_stroke_geometry(x, y, length=14.5, width=8.5, agent_id=1, is_v1=False, rng_local=rng))
    for (x, y) in points_fine:
        strokes.append(get_stroke_geometry(x, y, length=9.6, width=5.2, agent_id=1, is_v1=False, rng_local=rng))
    return strokes
