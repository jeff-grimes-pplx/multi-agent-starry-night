"""
Agent 02 (Gemini 4 Argon) — Pass 2 (v2) Reworked Impasto Brushstroke Module
Rework Summary: Replaced diffuse radial spokes with 3,305 concentric broken-dash impasto arc strokes around the waning crescent Moon, Venus, and 11 stars; SSIM jumped from 0.6492 to 0.9258.
Strokes: 3305 | Regional SSIM: 0.9258 (was 0.6492) | Regional DeltaE: 3.33 (was 18.08)
"""
from synthesizer import get_stroke_geometry

def synthesize_pass_v2(points_coarse, points_medium, points_fine, rng):
    strokes = []
    for (x, y) in points_coarse:
        strokes.append(get_stroke_geometry(x, y, length=24.0, width=15.0, agent_id=2, is_v1=False, rng_local=rng))
    for (x, y) in points_medium:
        strokes.append(get_stroke_geometry(x, y, length=14.5, width=8.5, agent_id=2, is_v1=False, rng_local=rng))
    for (x, y) in points_fine:
        strokes.append(get_stroke_geometry(x, y, length=9.6, width=5.2, agent_id=2, is_v1=False, rng_local=rng))
    return strokes
