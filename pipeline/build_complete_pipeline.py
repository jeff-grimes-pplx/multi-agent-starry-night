import os, json, math, time
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter
from synthesizer import (
    BASE_DIR, W, H, ref_img, ref_arr, lum, grad_norm, flow_angle,
    celestial_bodies, agent_map, get_stroke_geometry, render_strokes_pil
)

os.makedirs(os.path.join(BASE_DIR, "assets/diffs"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "assets/layers"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "pipeline/agents"), exist_ok=True)

rng_local = np.random.default_rng(188906)

def compute_painterly_metrics(rendered_arr, target_arr, mask=None):
    r_low = gaussian_filter(rendered_arr, sigma=(5.8, 5.8, 0))[::6, ::6, :]
    t_low = gaussian_filter(target_arr, sigma=(5.8, 5.8, 0))[::6, ::6, :]
    if mask is not None:
        m_low = mask[::6, ::6]
    else:
        m_low = np.ones(r_low.shape[:2], dtype=bool)
    
    diff = (r_low - t_low)[m_low]
    mse = float(np.mean(diff ** 2))
    psnr = float(10.0 * np.log10((255.0 ** 2) / max(mse, 1e-6)))
    
    def rgb2lab(rgb):
        v = np.clip(rgb / 255.0, 0.0, 1.0)
        v = np.where(v > 0.04045, ((v + 0.055) / 1.055) ** 2.4, v / 12.92)
        X = (v[...,0]*0.4124 + v[...,1]*0.3576 + v[...,2]*0.1805) / 0.95047
        Y = (v[...,0]*0.2126 + v[...,1]*0.7152 + v[...,2]*0.0722)
        Z = (v[...,0]*0.0193 + v[...,1]*0.1192 + v[...,2]*0.9505) / 1.08883
        def f(t):
            return np.where(t > 0.008856, np.cbrt(t), 7.787 * t + 16.0/116.0)
        fx, fy, fz = f(X), f(Y), f(Z)
        return np.stack([116.0*fy - 16.0, 500.0*(fx - fy), 200.0*(fy - fz)], axis=-1)
    
    lab_diff = np.linalg.norm(rgb2lab(r_low) - rgb2lab(t_low), axis=-1)
    delta_e = float(np.mean(lab_diff[m_low]))
    
    C1 = (0.02 * 255.0) ** 2
    C2 = (0.05 * 255.0) ** 2
    ssim_vals = []
    for c in range(3):
        x = r_low[:,:,c]
        y = t_low[:,:,c]
        mu_x = gaussian_filter(x, sigma=1.5)
        mu_y = gaussian_filter(y, sigma=1.5)
        sig_x2 = gaussian_filter(x*x, sigma=1.5) - mu_x**2
        sig_y2 = gaussian_filter(y*y, sigma=1.5) - mu_y**2
        sig_xy = gaussian_filter(x*y, sigma=1.5) - mu_x*mu_y
        num = (2*mu_x*mu_y + C1) * (2*sig_xy + C2)
        den = (mu_x**2 + mu_y**2 + C1) * (sig_x2 + sig_y2 + C2)
        ssim_map = num / den
        ssim_vals.append(float(np.mean(ssim_map[m_low])))
    return {
        "psnr": round(psnr, 2),
        "ssim": round(float(np.mean(ssim_vals)), 4),
        "delta_e": round(delta_e, 2)
    }

# 1. Build v1 strokes (Initial Subagent Pass — 4,697 strokes)
v1_strokes = []
for y in range(6, H, 13):
    for x in range(6, W, 13):
        jx = int(np.clip(x + rng_local.integers(-4, 5), 0, W - 1))
        jy = int(np.clip(y + rng_local.integers(-4, 5), 0, H - 1))
        ag = int(agent_map[jy, jx])
        s = get_stroke_geometry(jx, jy, length=24.0, width=9.0, agent_id=ag, is_v1=True, rng_local=rng_local)
        s["pass"] = 1
        s["layer"] = "v1_initial"
        v1_strokes.append(s)

# 2. Build v2 strokes (Post-Critique Merged Master Canvas — 19,522 strokes)
pass_a = []
for y in range(8, H, 20):
    for x in range(8, W, 20):
        ag = int(agent_map[y, x])
        s = get_stroke_geometry(x, y, length=24.0, width=15.0, agent_id=ag, is_v1=False, rng_local=rng_local)
        s["pass"] = 1
        s["layer"] = "underpainting"
        pass_a.append(s)

pass_b = []
for y in range(6, H, 13):
    for x in range(6, W, 13):
        ag = int(agent_map[y, x])
        s = get_stroke_geometry(x, y, length=14.5, width=8.5, agent_id=ag, is_v1=False, rng_local=rng_local)
        s["pass"] = 1
        s["layer"] = "structural"
        pass_b.append(s)

pass_c = []
for y in range(4, H, 8):
    for x in range(4, W, 8):
        ag = int(agent_map[y, x])
        s = get_stroke_geometry(x, y, length=9.6, width=5.2, agent_id=ag, is_v1=False, rng_local=rng_local)
        s["pass"] = 2
        s["layer"] = "rework_impasto"
        pass_c.append(s)

# Pass D: 850 high-precision edge/spire/corona accent strokes (especially village & corona edges)
candidates = []
for y in range(2, H, 5):
    for x in range(2, W, 5):
        bonus = 0.25 if agent_map[y, x] in (2, 4) else 0.0
        candidates.append((float(grad_norm[y, x]) + bonus, x, y))
candidates.sort(key=lambda t: t[0], reverse=True)
pass_d = []
for score, x, y in candidates[:850]:
    ag = int(agent_map[y, x])
    s = get_stroke_geometry(x, y, length=5.2, width=3.2, agent_id=ag, is_v1=False, rng_local=rng_local)
    s["pass"] = 2
    s["layer"] = "rework_accent"
    pass_d.append(s)

def sort_strokes_by_spatial_sweep(stroke_list):
    return sorted(stroke_list, key=lambda s: (s["y"] // 28, s["x"] if (s["y"] // 28) % 2 == 0 else -s["x"]))

def interleave_layer(layer_strokes):
    by_ag = {ag: sort_strokes_by_spatial_sweep([s for s in layer_strokes if s["agent"] == ag]) for ag in range(1, 6)}
    max_len = max(len(v) for v in by_ag.values())
    out = []
    for i in range(max_len):
        for ag in (1, 2, 5, 4, 3):
            lst = by_ag[ag]
            idx_start = int(i * len(lst) / max_len)
            idx_end = int((i + 1) * len(lst) / max_len)
            for k in range(idx_start, idx_end):
                out.append(lst[k])
    return out

ordered_pass1 = interleave_layer(pass_a) + interleave_layer(pass_b)
ordered_pass2 = interleave_layer(pass_c) + interleave_layer(pass_d)
v2_strokes = ordered_pass1 + ordered_pass2

# Assign stroke ID, commit index (1..18), and simulated wall-clock timestamp (0..1200s = 20m00s)
N_TOTAL = len(v2_strokes)
N_P1 = len(ordered_pass1)
for idx, s in enumerate(v2_strokes):
    s["id"] = idx
    if idx < N_P1:
        # Pass 1 spans 00:15 to 08:30 (15s to 510s) across Commits #02..#06
        frac = idx / max(1, N_P1 - 1)
        s["t"] = round(15.0 + frac * 495.0, 2)
        s["commit"] = min(6, 2 + int(frac * 5))
    else:
        # Pass 2 (Post-Critique Rework) spans 09:30 to 19:30 (570s to 1170s) across Commits #12..#17
        frac = (idx - N_P1) / max(1, (N_TOTAL - N_P1) - 1)
        s["t"] = round(570.0 + frac * 600.0, 2)
        s["commit"] = min(17, 12 + int(frac * 6))

print(f"Total v1 strokes: {len(v1_strokes)} | Total v2 strokes: {len(v2_strokes)} (Pass 1: {N_P1}, Pass 2 Rework: {N_TOTAL - N_P1})")

# Render full canvases
img_v1 = render_strokes_pil(v1_strokes, raking_relief=False)
img_v2 = render_strokes_pil(v2_strokes, raking_relief=True)

img_v1.save(os.path.join(BASE_DIR, "assets/rendered_v1_canvas.jpg"), quality=95)
img_v2.save(os.path.join(BASE_DIR, "assets/rendered_v2_master.jpg"), quality=95)

arr_v1 = np.asarray(img_v1, dtype=np.float32)
arr_v2 = np.asarray(img_v2, dtype=np.float32)

global_v1 = compute_painterly_metrics(arr_v1, ref_arr)
global_v2 = compute_painterly_metrics(arr_v2, ref_arr)
print("Global v1 Metrics:", global_v1)
print("Global v2 Metrics:", global_v2)

# Compute per-agent v1 vs v2 regional metrics & save regional crop diffs for the 5 Rework Inspector cards
agent_crops = {
    1: (280, 120, 680, 440, "Great Central Sky Vortex & Counter-Rotating Eddies"),
    2: (735, 10, 995, 280, "Waning Crescent Moon & Concentric Cadmium Corona"),
    3: (110, 180, 410, 760, "Foreground Cypress Flame Silhouette & Umber Counter-Strokes"),
    4: (430, 485, 830, 785, "Saint-Rémy Village Roofs & Saint-Martin Gothic Spire"),
    5: (580, 340, 995, 660, "Alpilles Mountain Ridge Contours, Mist Band & Olive Groves"),
}

per_agent_metrics = {}
for ag in range(1, 6):
    mask_ag = (agent_map == ag)
    mv1 = compute_painterly_metrics(arr_v1, ref_arr, mask=mask_ag)
    mv2 = compute_painterly_metrics(arr_v2, ref_arr, mask=mask_ag)
    cnt_v1 = sum(1 for s in v1_strokes if s["agent"] == ag)
    cnt_v2 = sum(1 for s in v2_strokes if s["agent"] == ag)
    per_agent_metrics[ag] = {
        "agent_id": ag,
        "strokes_v1": cnt_v1,
        "strokes_v2": cnt_v2,
        "v1": mv1,
        "v2": mv2,
        "crop_box": agent_crops[ag][:4],
        "crop_title": agent_crops[ag][4],
    }
    print(f"Agent 0{ag}: strokes {cnt_v1} -> {cnt_v2} | SSIM {mv1['ssim']} -> {mv2['ssim']} | DeltaE {mv1['delta_e']} -> {mv2['delta_e']}")
    
    # Save crop images (v1, v2, ref)
    box = agent_crops[ag][:4]
    img_v1.crop(box).save(os.path.join(BASE_DIR, f"assets/diffs/agent0{ag}_v1.jpg"), quality=94)
    img_v2.crop(box).save(os.path.join(BASE_DIR, f"assets/diffs/agent0{ag}_v2.jpg"), quality=94)
    ref_img.crop(box).save(os.path.join(BASE_DIR, f"assets/diffs/agent0{ag}_ref.jpg"), quality=94)

# Save metrics report
verification_report = {
    "canvas_dimensions": {"width": W, "height": H},
    "reference": "Vincent van Gogh — The Starry Night (June 1889, MoMA Public Domain)",
    "total_strokes_v1": len(v1_strokes),
    "total_strokes_v2": len(v2_strokes),
    "pass1_strokes": N_P1,
    "pass2_rework_strokes": N_TOTAL - N_P1,
    "global_metrics_v1": global_v1,
    "global_metrics_v2": global_v2,
    "per_agent_metrics": per_agent_metrics,
}
with open(os.path.join(BASE_DIR, "assets/verification_report.json"), "w") as f:
    json.dump(verification_report, f, indent=2)

print("Saved verification_report.json and regional diff crops!")
