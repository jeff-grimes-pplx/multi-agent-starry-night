"""
Agent 05 (DeepSeek V4 Pro) — Pass 1 (v1) Initial Brushstroke Module
Strategy: Broad horizontal blue-gray wash across Alpilles hills & olive groves
Strokes: 948 | Regional SSIM: 0.6975 | Regional DeltaE: 11.67
"""
from synthesizer import get_stroke_geometry

def synthesize_pass_v1(points, rng):
    return [get_stroke_geometry(x, y, length=24.0, width=9.0, agent_id=5, is_v1=True, rng_local=rng) for (x, y) in points]
