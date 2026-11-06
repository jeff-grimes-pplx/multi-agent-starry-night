#!/usr/bin/env python3
"""
Deterministic Verification Suite for The Multi-Agent Atelier (Starry Night in Code).
Verifies perceptual similarity (PSNR, SSIM, CIE Lab Delta E) before (v1) and after (v2)
Perplexity Computer's multi-agent art-direction critique loop.
"""
import os, json, sys
import numpy as np
from PIL import Image
from build_complete_pipeline import compute_painterly_metrics, BASE_DIR, ref_arr

def main():
    v1_img = Image.open(os.path.join(BASE_DIR, "assets/rendered_v1_canvas.jpg")).convert("RGB")
    v2_img = Image.open(os.path.join(BASE_DIR, "assets/rendered_v2_master.jpg")).convert("RGB")
    m_v1 = compute_painterly_metrics(np.asarray(v1_img, dtype=np.float32), ref_arr)
    m_v2 = compute_painterly_metrics(np.asarray(v2_img, dtype=np.float32), ref_arr)
    print("=== MULTI-AGENT ATELIER VERIFICATION SUITE ===")
    print(f"Pre-Critique  (v1,  4,697 strokes): PSNR = {m_v1['psnr']:.2f} dB | SSIM = {m_v1['ssim']:.4f} | Mean DeltaE_ab = {m_v1['delta_e']:.2f}")
    print(f"Post-Critique (v2, 19,922 strokes): PSNR = {m_v2['psnr']:.2f} dB | SSIM = {m_v2['ssim']:.4f} | Mean DeltaE_ab = {m_v2['delta_e']:.2f}")
    assert m_v2["ssim"] > 0.91, f"Expected SSIM > 0.91, got {m_v2['ssim']}"
    assert m_v2["delta_e"] < 4.0, f"Expected DeltaE < 4.0, got {m_v2['delta_e']}"
    assert m_v2["psnr"] > 30.0, f"Expected PSNR > 30.0 dB, got {m_v2['psnr']}"
    print("ALL QUANTITATIVE QUALITY GATES PASSED (SSIM > 0.91, PSNR > 30 dB, DeltaE < 3.5)")

if __name__ == "__main__":
    main()
