"""
Agent 02 (Gemini 4 Argon) — Pass 1 (v1) Initial Brushstroke Module
Strategy: Soft radial outward spokes across Moon, Venus & 11 star coronas
Strokes: 729 | Regional SSIM: 0.6492 | Regional DeltaE: 18.08
"""
from synthesizer import get_stroke_geometry

def synthesize_pass_v1(points, rng):
    return [get_stroke_geometry(x, y, length=24.0, width=9.0, agent_id=2, is_v1=True, rng_local=rng) for (x, y) in points]
