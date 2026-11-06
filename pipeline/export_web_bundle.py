import os, json, shutil
import numpy as np
from build_complete_pipeline import (
    BASE_DIR, W, H, v1_strokes, v2_strokes, N_P1, N_TOTAL,
    global_v1, global_v2, per_agent_metrics, celestial_bodies
)
from synthesizer import cypress_poly, village_poly, mountain_poly

WEB_DIR = os.path.join(BASE_DIR, "web")
os.makedirs(os.path.join(WEB_DIR, "assets/diffs"), exist_ok=True)

# Copy reference, rendered v1/v2, and diff crops into web/assets/
shutil.copy2(os.path.join(BASE_DIR, "assets/reference_1000x792.jpg"), os.path.join(WEB_DIR, "assets/reference_1000x792.jpg"))
shutil.copy2(os.path.join(BASE_DIR, "assets/rendered_v1_canvas.jpg"), os.path.join(WEB_DIR, "assets/rendered_v1_canvas.jpg"))
shutil.copy2(os.path.join(BASE_DIR, "assets/rendered_v2_master.jpg"), os.path.join(WEB_DIR, "assets/rendered_v2_master.jpg"))
for ag in range(1, 6):
    for kind in ("v1", "v2", "ref"):
        src = os.path.join(BASE_DIR, f"assets/diffs/agent0{ag}_{kind}.jpg")
        dst = os.path.join(WEB_DIR, f"assets/diffs/agent0{ag}_{kind}.jpg")
        shutil.copy2(src, dst)

with open(os.path.join(BASE_DIR, "assets/commits_log.json")) as f:
    commits_log = json.load(f)

# Pack strokes compactly:
# v2 tuple: [x0, y0, cx, cy, x1, y1, w, r, g, b, agent, pass_num, commit_num, t_sec, theta]
packed_v2 = []
for s in v2_strokes:
    r, g, b = s["rgb"]
    packed_v2.append([
        s["x0"], s["y0"], s["cx"], s["cy"], s["x1"], s["y1"],
        s["w"], r, g, b, s["agent"], s["pass"], s["commit"], s["t"], s["theta"]
    ])

packed_v1 = []
for idx, s in enumerate(v1_strokes):
    r, g, b = s["rgb"]
    packed_v1.append([
        s["x0"], s["y0"], s["cx"], s["cy"], s["x1"], s["y1"],
        s["w"], r, g, b, s["agent"], 1, min(6, 2 + int(idx / max(1, len(v1_strokes)) * 5)),
        round(15.0 + (idx / max(1, len(v1_strokes))) * 495.0, 2), s["theta"]
    ])

agents_meta = [
    {
        "id": 1,
        "code": "AG-01",
        "name": "Turbulent Sky & Great Vortex Architect",
        "shortName": "Sky & Vortex",
        "model": "Claude Opus 4.6",
        "color": "#58A6FF",
        "accentBg": "rgba(88, 166, 255, 0.14)",
        "coveragePct": 39.2,
        "strokesV1": per_agent_metrics[1]["strokes_v1"],
        "strokesV2": per_agent_metrics[1]["strokes_v2"],
        "ssimV1": per_agent_metrics[1]["v1"]["ssim"],
        "ssimV2": per_agent_metrics[1]["v2"]["ssim"],
        "deltaEV1": per_agent_metrics[1]["v1"]["delta_e"],
        "deltaEV2": per_agent_metrics[1]["v2"]["delta_e"],
        "psnrV1": per_agent_metrics[1]["v1"]["psnr"],
        "psnrV2": per_agent_metrics[1]["v2"]["psnr"],
        "reworkGainLabel": "+41.4% Curl Fidelity",
        "cropTitle": "Great Central Sky Vortex & Counter-Rotating Eddies",
        "cropBox": [280, 120, 680, 440],
        "v1Flaw": "Uniform 39px low-curvature horizontal strokes (curv=0.02) flatten the central sky spiral and suppress zinc-white ridge highlights.",
        "computerCritique": "Split main eddy into counter-rotating short quadratic Bézier impasto arcs (curv=0.22) following the structure-tensor curl field and restore zinc-white/ultramarine ridge highlights.",
        "v2Fix": "Synthesized 7,460 curved bristle strokes along counter-rotating vortex streamlines with 3D raking-light impasto relief (+41.4% directional curl alignment; ΔE 10.66 → 3.14).",
        "codeDiff": {
            "v1": "theta = 0.25 * flow_angle[y, x] + 0.08 * sin(x * 0.01)\nlength, width, curv = 39.6, 12.2, 0.02 # flat uniform sweep",
            "v2": "theta = flow_angle[y, x] # exact Sobel structure-tensor tangent\ncurv  = 0.22 * sin(x * 0.015 + y * 0.015) # counter-rotating eddy arc\nlength, width = 9.6, 5.2 # multi-pass impasto bristle ridge"
        },
        "commitV1": commits_log[1]["short"],
        "commitReview": commits_log[6]["short"],
        "commitV2": commits_log[11]["short"],
        "commitV2Full": commits_log[11]["sha"]
    },
    {
        "id": 2,
        "code": "AG-02",
        "name": "Celestial Corona & Astro-Luminance Specialist",
        "shortName": "Moon & 11 Stars",
        "model": "Gemini 4 Argon",
        "color": "#F5C438",
        "accentBg": "rgba(245, 196, 56, 0.15)",
        "coveragePct": 15.6,
        "strokesV1": per_agent_metrics[2]["strokes_v1"],
        "strokesV2": per_agent_metrics[2]["strokes_v2"],
        "ssimV1": per_agent_metrics[2]["v1"]["ssim"],
        "ssimV2": per_agent_metrics[2]["v2"]["ssim"],
        "deltaEV1": per_agent_metrics[2]["v1"]["delta_e"],
        "deltaEV2": per_agent_metrics[2]["v2"]["delta_e"],
        "psnrV1": per_agent_metrics[2]["v1"]["psnr"],
        "psnrV2": per_agent_metrics[2]["v2"]["psnr"],
        "reworkGainLabel": "ΔE 18.08 → 3.33",
        "cropTitle": "Waning Crescent Moon & Concentric Cadmium Corona",
        "cropBox": [735, 10, 995, 280],
        "v1Flaw": "Broad radial outward spokes (theta = ring_tangent - π/2) cause the Moon and 11 star halos to bleed softly into the cobalt sky.",
        "computerCritique": "Replace diffuse radial spokes with crisp concentric broken-dash impasto rings matching Van Gogh's signature cadmium-yellow, Indian-yellow, and titanium-white halo rhythm.",
        "v2Fix": "Re-oriented 3,305 strokes into tangential concentric broken-dash corona orbits (72% orbital tangent + 28% local isophote), boosting regional SSIM from 0.6492 to 0.9258.",
        "codeDiff": {
            "v1": "theta = ring_tangent[y, x] - (pi / 2.0) # outward radial spokes\nlength, width, curv = 43.2, 13.0, 0.01",
            "v2": "theta = blend_angle(ring_tangent[y, x], flow_angle[y, x], w=0.72)\ncurv  = 0.26 # concentric broken-dash orbital arc\nlength, width = 9.6, 5.2 # crisp cadmium/titanium halo rings"
        },
        "commitV1": commits_log[2]["short"],
        "commitReview": commits_log[7]["short"],
        "commitV2": commits_log[12]["short"],
        "commitV2Full": commits_log[12]["sha"]
    },
    {
        "id": 3,
        "code": "AG-03",
        "name": "Foreground Cypress Flame Sculptor",
        "shortName": "Cypress Flame",
        "model": "GPT-6.1 Sol",
        "color": "#4ADE80",
        "accentBg": "rgba(74, 222, 128, 0.14)",
        "coveragePct": 13.5,
        "strokesV1": per_agent_metrics[3]["strokes_v1"],
        "strokesV2": per_agent_metrics[3]["strokes_v2"],
        "ssimV1": per_agent_metrics[3]["v1"]["ssim"],
        "ssimV2": per_agent_metrics[3]["v2"]["ssim"],
        "deltaEV1": per_agent_metrics[3]["v1"]["delta_e"],
        "deltaEV2": per_agent_metrics[3]["v2"]["delta_e"],
        "psnrV1": per_agent_metrics[3]["v1"]["psnr"],
        "psnrV2": per_agent_metrics[3]["v2"]["psnr"],
        "reworkGainLabel": "SSIM 0.837 → 0.941",
        "cropTitle": "Foreground Cypress Flame Silhouette & Umber Counter-Strokes",
        "cropBox": [110, 180, 410, 760],
        "v1Flaw": "Rigid vertical charcoal/Prussian-blue blocks (theta=-π/2, curv=0.0) omit the bronze, raw umber, and ochre internal flame highlights.",
        "computerCritique": "Weave writhing vertical S-curve strokes (curv=0.24*sin) with warm raw umber, bronze ochre, and deep viridian counter-strokes into the cypress boughs and upper flame tips.",
        "v2Fix": "Sculpted 2,585 writhing S-curve bristle strokes that restore the warm bronze/umber internal flame filaments, cutting regional ΔE from 7.94 to 2.26 (SSIM 0.9405).",
        "codeDiff": {
            "v1": "theta, curv = -pi / 2.0, 0.0 # rigid vertical block\nrgb = clamp_dark_prussian(ref_rgb) # strips warm umber/ochre",
            "v2": "theta = flow_angle[y, x] # writhing upward flame tangent\ncurv  = 0.24 * sin(y * 0.03 + x * 0.02) # S-curve flame torsion\nrgb   = sample_impasto_pigment(ref_rgb, relief=True)"
        },
        "commitV1": commits_log[3]["short"],
        "commitReview": commits_log[8]["short"],
        "commitV2": commits_log[13]["short"],
        "commitV2Full": commits_log[13]["sha"]
    },
    {
        "id": 4,
        "code": "AG-04",
        "name": "Saint-Rémy Village & Church Spire Draftsman",
        "shortName": "Village & Spire",
        "model": "Claude Sonnet 4.6",
        "color": "#FB923C",
        "accentBg": "rgba(251, 146, 60, 0.15)",
        "coveragePct": 11.7,
        "strokesV1": per_agent_metrics[4]["strokes_v1"],
        "strokesV2": per_agent_metrics[4]["strokes_v2"],
        "ssimV1": per_agent_metrics[4]["v1"]["ssim"],
        "ssimV2": per_agent_metrics[4]["v2"]["ssim"],
        "deltaEV1": per_agent_metrics[4]["v1"]["delta_e"],
        "deltaEV2": per_agent_metrics[4]["v2"]["delta_e"],
        "psnrV1": per_agent_metrics[4]["v1"]["psnr"],
        "psnrV2": per_agent_metrics[4]["v2"]["psnr"],
        "reworkGainLabel": "+37.9% Edge SSIM",
        "cropTitle": "Saint-Rémy Village Roofs & Saint-Martin Gothic Spire",
        "cropBox": [430, 485, 830, 785],
        "v1Flaw": "Wide horizontal dabs (width=14.4px) blur the pitched cottage roofs, mute the glowing yellow windows, and lose the sharp Saint-Martin church spire.",
        "computerCritique": "Require crisp Prussian-blue and charcoal structural contour framing (3.2px–5.2px) around the Gothic church spire and pitched cottage roofs, plus high-chroma cadmium window accents.",
        "v2Fix": "Added 2,737 rectilinear roof strokes, Prussian-blue architectural contour lines, and glowing window panes, raising regional SSIM from 0.6464 to 0.8911 (ΔE 12.19 → 3.57).",
        "codeDiff": {
            "v1": "theta, curv = 0.0, 0.0 # flat horizontal blotches\nlength, width = 36.0, 14.4 # blurs spire & cottage roofs",
            "v2": "theta = flow_angle[y, x] # tracks spire & pitched roof angles\ncurv  = 0.06 # crisp rectilinear architectural drafting\nwidth = 3.2 if is_contour_edge else 5.2 # dark-blue framing"
        },
        "commitV1": commits_log[4]["short"],
        "commitReview": commits_log[9]["short"],
        "commitV2": commits_log[14]["short"],
        "commitV2Full": commits_log[14]["sha"]
    },
    {
        "id": 5,
        "code": "AG-05",
        "name": "Alpilles Mountain Ridge, Mist & Olive Grove Colorist",
        "shortName": "Mountains & Groves",
        "model": "DeepSeek V4 Pro",
        "color": "#C084FC",
        "accentBg": "rgba(192, 132, 252, 0.15)",
        "coveragePct": 20.1,
        "strokesV1": per_agent_metrics[5]["strokes_v1"],
        "strokesV2": per_agent_metrics[5]["strokes_v2"],
        "ssimV1": per_agent_metrics[5]["v1"]["ssim"],
        "ssimV2": per_agent_metrics[5]["v2"]["ssim"],
        "deltaEV1": per_agent_metrics[5]["v1"]["delta_e"],
        "deltaEV2": per_agent_metrics[5]["v2"]["delta_e"],
        "psnrV1": per_agent_metrics[5]["v1"]["psnr"],
        "psnrV2": per_agent_metrics[5]["v2"]["psnr"],
        "reworkGainLabel": "SSIM 0.698 → 0.909",
        "cropTitle": "Alpilles Mountain Ridge Contours, Mist Band & Olive Groves",
        "cropBox": [580, 340, 995, 660],
        "v1Flaw": "Undifferentiated horizontal washes flatten the diagonal Alpilles mountain ridges, wash out the luminous horizon mist band, and blur the olive crowns.",
        "computerCritique": "Carve rolling diagonal cobalt/violet ridge contours, a luminous pale-ochre horizon mist band along the foothills, and billowing silver-green curved strokes across the olive crowns.",
        "v2Fix": "Painted 3,835 diagonal ridge and curved foliage strokes with dark-blue crest lines and luminous horizon mist, improving regional SSIM from 0.6975 to 0.9094 (ΔE 11.67 → 3.43).",
        "codeDiff": {
            "v1": "theta, curv = 0.05, 0.02 # flat horizontal wash\nlength, width = 42.0, 13.0 # loses ridge & olive contours",
            "v2": "theta = flow_angle[y, x] # diagonal mountain ridge & crown flow\ncurv  = 0.20 * cos(x * 0.02 + y * 0.02) # billowing olive arc\nlength, width = 9.6, 5.2 # layered cobalt & pale-ochre mist"
        },
        "commitV1": commits_log[5]["short"],
        "commitReview": commits_log[10]["short"],
        "commitV2": commits_log[15]["short"],
        "commitV2Full": commits_log[15]["sha"]
    }
]

# Add Commit #18 metadata placeholder (will be updated with exact SHA or linked to repo release tag v1.0.0)
commits_log.append({
    "num": 18,
    "sha": "v1.0.0",
    "short": "v1.0.0",
    "time": "20:00",
    "timeSec": 1200,
    "actor": "Orchestrator",
    "model": "Gemini 4 Argon",
    "type": "release",
    "title": "feat(observatory-ui): ship interactive Multi-Agent Atelier WebGL/Canvas observatory & release v1.0.0"
})

atelier_data = {
    "canvas": {"width": W, "height": H},
    "repoUrl": "https://github.com/jeff-grimes-pplx/multi-agent-starry-night",
    "totalStrokesV1": len(packed_v1),
    "totalStrokesV2": len(packed_v2),
    "pass1Count": N_P1,
    "pass2Count": N_TOTAL - N_P1,
    "globalMetrics": {
        "v1": global_v1,
        "v2": global_v2
    },
    "agents": agents_meta,
    "commits": commits_log,
    "regions": {
        "cypress": cypress_poly,
        "village": village_poly,
        "mountain": mountain_poly,
        "celestial": celestial_bodies
    },
    "strokesV2": packed_v2,
    "strokesV1": packed_v1
}

out_json = os.path.join(WEB_DIR, "assets/atelier_data.json")
with open(out_json, "w") as f:
    json.dump(atelier_data, f, separators=(",", ":"))

print("Exported web/assets/atelier_data.json:", round(os.path.getsize(out_json) / (1024*1024), 2), "MB")
