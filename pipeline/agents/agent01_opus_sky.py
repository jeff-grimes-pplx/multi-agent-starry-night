"""
Agent 01 (Claude Opus 4.6) — Pass 1 (v1) Initial Brushstroke Module
Strategy: Uniform low-curvature horizontal sky strokes (length=39.6px, curv=0.02)
Strokes: 1836 | Regional SSIM: 0.6782 | Regional DeltaE: 10.66
"""
from synthesizer import get_stroke_geometry

def synthesize_pass_v1(points, rng):
    return [get_stroke_geometry(x, y, length=24.0, width=9.0, agent_id=1, is_v1=True, rng_local=rng) for (x, y) in points]
