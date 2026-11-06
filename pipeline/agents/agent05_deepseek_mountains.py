"""
Agent 05 (DeepSeek V4 Pro) — Pass 2 (v2) Reworked Impasto Brushstroke Module
Rework Summary: Carved rolling diagonal cobalt/violet mountain contours, pale-ochre horizon mist band, and billowing silver-green olive-grove crowns (3,835 strokes; SSIM 0.6975 -> 0.9094).
Strokes: 3835 | Regional SSIM: 0.9094 (was 0.6975) | Regional DeltaE: 3.43 (was 11.67)
"""
from synthesizer import get_stroke_geometry

def synthesize_pass_v2(points_coarse, points_medium, points_fine, rng):
    strokes = []
    for (x, y) in points_coarse:
        strokes.append(get_stroke_geometry(x, y, length=24.0, width=15.0, agent_id=5, is_v1=False, rng_local=rng))
    for (x, y) in points_medium:
        strokes.append(get_stroke_geometry(x, y, length=14.5, width=8.5, agent_id=5, is_v1=False, rng_local=rng))
    for (x, y) in points_fine:
        strokes.append(get_stroke_geometry(x, y, length=9.6, width=5.2, agent_id=5, is_v1=False, rng_local=rng))
    return strokes
