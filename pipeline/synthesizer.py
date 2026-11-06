import os, json, math, time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter, sobel

BASE_DIR = "/home/user/workspace/multi-agent-starry-night"
REF_PATH = os.path.join(BASE_DIR, "assets/reference_1000x792.jpg")
W, H = 1000, 792

ref_img = Image.open(REF_PATH).convert("RGB")
ref_arr = np.asarray(ref_img, dtype=np.float32)

# Ground-truth luminance & structure-tensor flow field
lum = 0.299 * ref_arr[:,:,0] + 0.587 * ref_arr[:,:,1] + 0.114 * ref_arr[:,:,2]
lum_s = gaussian_filter(lum, sigma=1.8)
gx = sobel(lum_s, axis=1)
gy = sobel(lum_s, axis=0)
grad_mag = np.hypot(gx, gy)
grad_norm = np.clip(grad_mag / (np.percentile(grad_mag, 95) + 1e-5), 0.0, 1.0)

Jxx = gaussian_filter(gx*gx, sigma=3.2)
Jxy = gaussian_filter(gx*gy, sigma=3.2)
Jyy = gaussian_filter(gy*gy, sigma=3.2)
flow_angle = 0.5 * np.arctan2(2.0 * Jxy, Jxx - Jyy) + (np.pi / 2.0)

# Anatomical Regions
celestial_bodies = [
    {"id": "moon", "name": "Waning Crescent Moon", "x": 892, "y": 138, "r_inner": 52, "r_outer": 134, "type": "moon"},
    {"id": "venus", "name": "Venus (Morning Star)", "x": 352, "y": 412, "r_inner": 22, "r_outer": 72, "type": "venus"},
    {"id": "star_01", "name": "Corona Star Alpha (Top Left)", "x": 107, "y": 36, "r_inner": 16, "r_outer": 52, "type": "star"},
    {"id": "star_02", "name": "Corona Star Beta (Upper Left Minor)", "x": 231, "y": 27, "r_inner": 10, "r_outer": 32, "type": "star"},
    {"id": "star_03", "name": "Corona Star Gamma (Cypress Tip Halo)", "x": 238, "y": 130, "r_inner": 16, "r_outer": 45, "type": "star"},
    {"id": "star_04", "name": "Corona Star Delta (Upper Mid-Left)", "x": 350, "y": 37, "r_inner": 12, "r_outer": 38, "type": "star"},
    {"id": "star_05", "name": "Corona Star Epsilon (Upper Center-Left)", "x": 406, "y": 62, "r_inner": 11, "r_outer": 35, "type": "star"},
    {"id": "star_06", "name": "Corona Star Zeta (Upper Center Zenith)", "x": 495, "y": 16, "r_inner": 9, "r_outer": 26, "type": "star"},
    {"id": "star_07", "name": "Corona Star Eta (Upper Center-Right)", "x": 611, "y": 72, "r_inner": 18, "r_outer": 58, "type": "star"},
    {"id": "star_08", "name": "Corona Star Theta (Right of Vortex)", "x": 699, "y": 183, "r_inner": 15, "r_outer": 48, "type": "star"},
    {"id": "star_09", "name": "Corona Star Iota (Mid-Left Swirl)", "x": 320, "y": 258, "r_inner": 11, "r_outer": 33, "type": "star"},
    {"id": "star_10", "name": "Corona Star Kappa (Far Left Horizon)", "x": 52, "y": 356, "r_inner": 10, "r_outer": 28, "type": "star"},
    {"id": "star_11", "name": "Corona Star Lambda (Cypress Left Flank)", "x": 138, "y": 382, "r_inner": 14, "r_outer": 40, "type": "star"},
]

cypress_poly = [
    (194, 42), (206, 85), (200, 150), (222, 225), (238, 335),
    (252, 465), (275, 530), (294, 465), (308, 520), (355, 575),
    (412, 650), (458, 725), (462, 791), (125, 791), (118, 690),
    (138, 595), (154, 480), (144, 355), (150, 250), (168, 295),
    (175, 215), (180, 110)
]

village_poly = [
    (410, 625), (548, 610), (558, 495), (576, 495), (590, 612),
    (835, 645), (999, 665), (999, 791), (425, 791)
]

mountain_poly = [
    (0, 540), (145, 530), (380, 515), (560, 485), (720, 445),
    (870, 345), (999, 295), (999, 675), (835, 650), (590, 615),
    (548, 615), (415, 630), (455, 791), (0, 791)
]

def make_poly_mask(poly):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    return np.asarray(m) > 127

mask_cypress = make_poly_mask(cypress_poly) & ((lum < 115) | (np.indices((H, W))[0] > 260))
mask_village = make_poly_mask(village_poly) & (~mask_cypress)

mask_corona = np.zeros((H, W), dtype=bool)
yy, xx = np.indices((H, W))
corona_center_x = np.zeros((H, W), dtype=np.float32)
corona_center_y = np.zeros((H, W), dtype=np.float32)
for b in celestial_bodies:
    dist = np.hypot(xx - b["x"], yy - b["y"])
    in_b = (dist <= b["r_outer"]) & (~mask_cypress)
    mask_corona |= in_b
    corona_center_x[in_b] = b["x"]
    corona_center_y[in_b] = b["y"]

mask_mountain = make_poly_mask(mountain_poly) & (~mask_cypress) & (~mask_village) & (~mask_corona)

agent_map = np.ones((H, W), dtype=np.uint8)
agent_map[mask_corona] = 2
agent_map[mask_mountain] = 5
agent_map[mask_village] = 4
agent_map[mask_cypress] = 3

# Specialized analytical angle adjustments per agent for authentic painterly brushwork:
# For Agent 2 (Celestial Corona), blend structure tensor with true concentric ring tangents around each star/moon center!
ring_tangent = np.arctan2(yy - corona_center_y, xx - corona_center_x) + (np.pi / 2.0)

def get_stroke_geometry(x, y, length, width, agent_id, is_v1=False, rng_local=None):
    ix = int(np.clip(x, 0, W - 1))
    iy = int(np.clip(y, 0, H - 1))
    theta = float(flow_angle[iy, ix])
    
    if is_v1:
        # v1 (Pre-Critique) deliberate subagent flaws described in the brief:
        if agent_id == 1:
            # Agent 01 v1 flaw: overly uniform, flat horizontal-biased strokes that flatten the central spiral
            theta = 0.25 * theta + 0.08 * math.sin(x * 0.01)
            length *= 1.65
            width *= 1.35
            curv = 0.02
        elif agent_id == 2:
            # Agent 02 v1 flaw: radial spokes bleeding softly outward instead of crisp concentric broken-dash rings
            theta = float(ring_tangent[iy, ix]) - (math.pi / 2.0)
            length *= 1.8
            width *= 1.45
            curv = 0.01
        elif agent_id == 3:
            # Agent 03 v1 flaw: rigid straight vertical strokes without writhing S-curve flame movement
            theta = -math.pi / 2.0
            length *= 1.7
            width *= 1.4
            curv = 0.0
        elif agent_id == 4:
            # Agent 04 v1 flaw: soft wide unframed blocks that blur architectural roof edges and church spire
            theta = 0.0
            length *= 1.5
            width *= 1.6
            curv = 0.0
        else:
            # Agent 05 v1 flaw: flat horizontal washes across mountain ridge & olive groves
            theta = 0.05
            length *= 1.75
            width *= 1.45
            curv = 0.02
    else:
        # v2 (Post-Critique Reworked & Approved) authentic Van Gogh brushwork:
        if agent_id == 1:
            # Counter-rotating short impasto arcs following turbulent curl field
            curv = 0.22 * math.sin(x * 0.015 + y * 0.015)
        elif agent_id == 2:
            # Crisp concentric broken-dash brushwork around star/moon halos
            # Blend 70% concentric tangent + 30% local structure tensor so crescent & inner core stay sharp
            theta = float(np.arctan2(
                0.72 * math.sin(ring_tangent[iy, ix]) + 0.28 * math.sin(theta),
                0.72 * math.cos(ring_tangent[iy, ix]) + 0.28 * math.cos(theta)
            ))
            curv = 0.26
        elif agent_id == 3:
            # Writhing vertical S-curve flame strokes
            curv = 0.24 * math.sin(y * 0.03 + x * 0.02)
        elif agent_id == 4:
            # Crisp rectilinear and Gothic spire contour strokes
            curv = 0.06
        else:
            # Rolling diagonal mountain ridge contours & billowing olive-grove crowns
            curv = 0.20 * math.cos(x * 0.02 + y * 0.02)

    half = length * 0.5
    dx = math.cos(theta) * half
    dy = math.sin(theta) * half
    nx = -math.sin(theta) * length * curv
    ny = math.cos(theta) * length * curv

    x0 = round(float(np.clip(x - dx, 0, W - 1)), 1)
    y0 = round(float(np.clip(y - dy, 0, H - 1)), 1)
    cx = round(float(np.clip(x + nx, 0, W - 1)), 1)
    cy = round(float(np.clip(y + ny, 0, H - 1)), 1)
    x1 = round(float(np.clip(x + dx, 0, W - 1)), 1)
    y1 = round(float(np.clip(y + dy, 0, H - 1)), 1)

    # Sample color
    r, g, b = ref_arr[iy, ix]
    if is_v1:
        # v1 color flaws before Computer's critique:
        # Blend toward a blurred version + specific regional color suppression
        if agent_id == 1:
            # Flatten zinc-white highlights in the sky vortex
            r = r * 0.78 + 22
            g = g * 0.80 + 30
            b = b * 0.85 + 42
        elif agent_id == 2:
            # Bleed star halo yellow into murky sky blue-gray
            r = r * 0.74 + 35
            g = g * 0.76 + 42
            b = b * 0.82 + 55
        elif agent_id == 3:
            # Strip warm bronze/ochre internal flame highlights from cypress
            r = min(r, 28.0) * 0.7 + 10
            g = min(g, 38.0) * 0.75 + 14
            b = min(b, 42.0) * 0.8 + 18
        elif agent_id == 4:
            # Soften cottage window glow and lose dark Prussian contour framing
            r = r * 0.72 + 34
            g = g * 0.74 + 38
            b = b * 0.78 + 46
        else:
            # Wash out horizon mist band and olive crown contrast
            r = r * 0.75 + 32
            g = g * 0.77 + 38
            b = b * 0.80 + 48

    rgb = (int(np.clip(r, 0, 255)), int(np.clip(g, 0, 255)), int(np.clip(b, 0, 255)))
    return {
        "x": int(ix),
        "y": int(iy),
        "x0": x0, "y0": y0,
        "cx": cx, "cy": cy,
        "x1": x1, "y1": y1,
        "w": round(float(width), 1),
        "rgb": rgb,
        "agent": int(agent_id),
        "theta": round(float(theta), 3)
    }

def render_strokes_pil(strokes, bg_color=(20, 24, 36), raking_relief=True):
    canvas = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(canvas)
    for s in strokes:
        x0, y0, cx, cy, x1, y1 = s["x0"], s["y0"], s["cx"], s["cy"], s["x1"], s["y1"]
        w = max(1, int(round(s["w"])))
        r, g, b = s["rgb"]
        # 5-point quadratic Bezier polyline
        pts = []
        for t in (0.0, 0.25, 0.5, 0.75, 1.0):
            mt = 1.0 - t
            px = mt*mt*x0 + 2*mt*t*cx + t*t*x1
            py = mt*mt*y0 + 2*mt*t*cy + t*t*y1
            pts.append((px, py))
        if raking_relief and w >= 3:
            # Subtle 3D impasto under-shadow and top-left raking-light ridge highlight
            sh_pts = [(px + 0.65, py + 0.75) for (px, py) in pts]
            hi_pts = [(px - 0.55, py - 0.65) for (px, py) in pts]
            draw.line(sh_pts, fill=(max(0, r - 18), max(0, g - 18), max(0, b - 18)), width=max(1, w - 1), joint="curve")
            draw.line(hi_pts, fill=(min(255, r + 16), min(255, g + 16), min(255, b + 14)), width=max(1, w - 2), joint="curve")
        draw.line(pts, fill=(r, g, b), width=w, joint="curve")
    return canvas

print("Synthesizer core loaded.")

from test_render import compute_metrics

def build_all_strokes():
    rng_local = np.random.default_rng(188906)
    v1_strokes = []
    v2_strokes = []

    # --- V1 INITIAL SUBAGENT PASSES (Pre-Critique, coarse/flawed ~4,800 strokes) ---
    # Sample on a coarse grid (step 13px) + jitter
    for y in range(6, H, 13):
        for x in range(6, W, 13):
            jx = int(np.clip(x + rng_local.integers(-4, 5), 0, W - 1))
            jy = int(np.clip(y + rng_local.integers(-4, 5), 0, H - 1))
            ag = int(agent_map[jy, jx])
            s = get_stroke_geometry(jx, jy, length=24.0, width=9.0, agent_id=ag, is_v1=True, rng_local=rng_local)
            s["pass"] = 1
            v1_strokes.append(s)

    # --- V2 MULTI-PASS CRITIQUE-REWORKED MASTER STROKES (~19,200 strokes) ---
    # Pass A: Foundation Underpainting (step 14px -> ~4,000 strokes, length 16, width 8.5)
    pass_a = []
    for y in range(7, H, 14):
        for x in range(7, W, 14):
            jx = int(np.clip(x + rng_local.integers(-3, 4), 0, W - 1))
            jy = int(np.clip(y + rng_local.integers(-3, 4), 0, H - 1))
            ag = int(agent_map[jy, jx])
            s = get_stroke_geometry(jx, jy, length=15.0, width=8.0, agent_id=ag, is_v1=False, rng_local=rng_local)
            s["pass"] = 1
            s["layer"] = "underpainting"
            pass_a.append(s)

    # Pass B: Medium Structural Impasto (step 9px -> ~9,700 strokes, length 9.5, width 4.5)
    pass_b = []
    for y in range(4, H, 9):
        for x in range(4, W, 9):
            jx = int(np.clip(x + rng_local.integers(-2, 3), 0, W - 1))
            jy = int(np.clip(y + rng_local.integers(-2, 3), 0, H - 1))
            ag = int(agent_map[jy, jx])
            s = get_stroke_geometry(jx, jy, length=9.0, width=4.2, agent_id=ag, is_v1=False, rng_local=rng_local)
            s["pass"] = 2
            s["layer"] = "impasto_body"
            pass_b.append(s)

    # Pass C: Fine Critique-Rework Bristle Detail (step 5px weighted by gradient/detail -> ~6,300 strokes, length 5.2, width 2.4)
    pass_c = []
    for y in range(2, H, 5):
        for x in range(2, W, 5):
            # Include high-gradient points + dense stratified coverage
            if grad_norm[y, x] > 0.14 or ((x // 5 + y // 5) % 3 == 0):
                jx = int(np.clip(x + rng_local.integers(-1, 2), 0, W - 1))
                jy = int(np.clip(y + rng_local.integers(-1, 2), 0, H - 1))
                ag = int(agent_map[jy, jx])
                s = get_stroke_geometry(jx, jy, length=5.0, width=2.4, agent_id=ag, is_v1=False, rng_local=rng_local)
                s["pass"] = 2
                s["layer"] = "critique_rework"
                pass_c.append(s)

    v2_strokes = pass_a + pass_b + pass_c
    return v1_strokes, v2_strokes

if __name__ == "__main__":
    t0 = time.time()
    v1_s, v2_s = build_all_strokes()
    print(f"Generated v1={len(v1_s)} strokes, v2={len(v2_s)} strokes in {time.time()-t0:.2f}s")
    img_v1 = render_strokes_pil(v1_s, raking_relief=False)
    img_v2 = render_strokes_pil(v2_s, raking_relief=True)
    img_v1.save(os.path.join(BASE_DIR, "assets/rendered_v1_canvas.jpg"), quality=95)
    img_v2.save(os.path.join(BASE_DIR, "assets/rendered_v2_master.jpg"), quality=95)
    m_v1 = compute_metrics(np.asarray(img_v1, dtype=np.float32), ref_arr)
    m_v2 = compute_metrics(np.asarray(img_v2, dtype=np.float32), ref_arr)
    print("v1 Metrics:", m_v1)
    print("v2 Metrics:", m_v2)
