"""
Agent 04 (Claude Sonnet 4.6) — Pass 1 (v1) Initial Brushstroke Module
Strategy: Unframed rectilinear roof & church spire color blocks (width=14.4px)
Strokes: 546 | Regional SSIM: 0.6464 | Regional DeltaE: 12.19
"""
from synthesizer import get_stroke_geometry

def synthesize_pass_v1(points, rng):
    return [get_stroke_geometry(x, y, length=24.0, width=9.0, agent_id=4, is_v1=True, rng_local=rng) for (x, y) in points]
