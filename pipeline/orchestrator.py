"""
Perplexity Computer (Gemini 4 Argon) — Lead Art Director & Quantitative QA Critic
Extracts ground-truth luminance, CIE Lab color palette, and Sobel/structure-tensor
directional flow fields from Vincent van Gogh's The Starry Night (June 1889, MoMA).
"""
from synthesizer import W, H, ref_arr, lum, grad_norm, flow_angle, celestial_bodies, agent_map
from build_complete_pipeline import compute_painterly_metrics

QA_THRESHOLDS = {
    "min_global_ssim": 0.91,
    "max_global_delta_e": 3.80,
    "min_flow_alignment": 0.88,
}

def evaluate_subagent_submission(rendered_arr, agent_id):
    mask = (agent_map == agent_id)
    return compute_painterly_metrics(rendered_arr, ref_arr, mask=mask)
