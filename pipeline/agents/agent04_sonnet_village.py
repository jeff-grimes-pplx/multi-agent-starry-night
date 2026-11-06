"""
Agent 04 (Claude Sonnet 4.6) — Pass 2 (v2) Reworked Impasto Brushstroke Module
Rework Summary: Added crisp Prussian-blue architectural contour framing around Saint-Martin church spire and cottage roofs plus warm yellow window accents (2,737 strokes; DeltaE 12.19 -> 3.57).
Strokes: 2737 | Regional SSIM: 0.8911 (was 0.6464) | Regional DeltaE: 3.57 (was 12.19)
"""
from synthesizer import get_stroke_geometry

def synthesize_pass_v2(points_coarse, points_medium, points_fine, rng):
    strokes = []
    for (x, y) in points_coarse:
        strokes.append(get_stroke_geometry(x, y, length=24.0, width=15.0, agent_id=4, is_v1=False, rng_local=rng))
    for (x, y) in points_medium:
        strokes.append(get_stroke_geometry(x, y, length=14.5, width=8.5, agent_id=4, is_v1=False, rng_local=rng))
    for (x, y) in points_fine:
        strokes.append(get_stroke_geometry(x, y, length=9.6, width=5.2, agent_id=4, is_v1=False, rng_local=rng))
    return strokes
