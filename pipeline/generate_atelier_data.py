import os, json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter, sobel

SEED = 188906
rng = np.random.default_rng(SEED)

BASE_DIR = "/home/user/workspace/multi-agent-starry-night"
REF_PATH = os.path.join(BASE_DIR, "assets/reference_1000x792.jpg")
W, H = 1000, 792

ref_img = Image.open(REF_PATH).convert("RGB")
ref_arr = np.asarray(ref_img, dtype=np.float32) # (792, 1000, 3) in 0..255

# 1. Compute luminance and Sobel structure tensor flow field (tangent to edges = perpendicular to gradient)
lum = 0.299 * ref_arr[:,:,0] + 0.587 * ref_arr[:,:,1] + 0.114 * ref_arr[:,:,2]
lum_smooth = gaussian_filter(lum, sigma=2.2)
gx = sobel(lum_smooth, axis=1)
gy = sobel(lum_smooth, axis=0)

# Structure tensor components smoothed
Jxx = gaussian_filter(gx * gx, sigma=4.0)
Jxy = gaussian_filter(gx * gy, sigma=4.0)
Jyy = gaussian_filter(gy * gy, sigma=4.0)

# Edge tangent angle (direction of stroke flow along isophotes)
grad_angle = 0.5 * np.arctan2(2.0 * Jxy, Jxx - Jyy)
flow_angle = grad_angle + (np.pi / 2.0)
grad_mag = np.hypot(gx, gy)
grad_mag_norm = np.clip(grad_mag / (np.percentile(grad_mag, 95) + 1e-5), 0.0, 1.0)

# 2. Define anatomical region masks for the 5 specialized subagents
# Agent 01: Turbulent Sky & Great Vortex Architect (Claude Opus 4.6)
# Agent 02: Celestial Corona & Astro-Luminance Specialist (Gemini 4 Argon)
# Agent 03: Foreground Cypress Flame Sculptor (GPT-6.1 Sol)
# Agent 04: Saint-Rémy Village & Church Spire Draftsman (Claude Sonnet 4.6)
# Agent 05: Alpilles Mountain Ridge, Mist & Olive Grove Colorist (DeepSeek V4 Pro)

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

mask_cypress = make_poly_mask(cypress_poly)
# Refine cypress mask using dark luminance inside/near polygon so the flame tips are exact
cypress_dilated = np.asarray(Image.fromarray((mask_cypress*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(15))) > 127
mask_cypress = mask_cypress & ((lum < 115) | (np.indices((H, W))[0] > 260))

mask_village = make_poly_mask(village_poly) & (~mask_cypress)

mask_corona = np.zeros((H, W), dtype=bool)
yy, xx = np.indices((H, W))
corona_center_map = np.full((H, W), -1, dtype=np.int32)
for idx, b in enumerate(celestial_bodies):
    dist = np.hypot(xx - b["x"], yy - b["y"])
    in_b = (dist <= b["r_outer"]) & (~mask_cypress)
    mask_corona |= in_b
    corona_center_map[in_b] = idx

mask_mountain = make_poly_mask(mountain_poly) & (~mask_cypress) & (~mask_village) & (~mask_corona)
mask_sky = (~mask_cypress) & (~mask_village) & (~mask_corona) & (~mask_mountain)

# Agent ID map (1..5)
agent_map = np.ones((H, W), dtype=np.uint8) # default 1 = Sky
agent_map[mask_corona] = 2
agent_map[mask_mountain] = 5
agent_map[mask_village] = 4
agent_map[mask_cypress] = 3

for ag in range(1, 6):
    cnt = int(np.sum(agent_map == ag))
    print(f"Agent 0{ag} pixel count: {cnt} ({cnt/(W*H)*100:.1f}%)")
