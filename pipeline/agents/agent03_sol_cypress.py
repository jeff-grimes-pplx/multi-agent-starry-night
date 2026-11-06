"""
Agent 03 (GPT-6.1 Sol) — Pass 1 (v1) Initial Brushstroke Module
Strategy: Straight vertical Prussian-blue silhouette strokes (theta=-pi/2, curv=0.0)
Strokes: 638 | Regional SSIM: 0.8373 | Regional DeltaE: 7.94
"""
from synthesizer import get_stroke_geometry

def synthesize_pass_v1(points, rng):
    return [get_stroke_geometry(x, y, length=24.0, width=9.0, agent_id=3, is_v1=True, rng_local=rng) for (x, y) in points]
