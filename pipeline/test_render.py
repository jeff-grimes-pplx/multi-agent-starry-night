import os, time, math
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, sobel

t0 = time.time()
BASE_DIR = "/home/user/workspace/multi-agent-starry-night"
REF_PATH = os.path.join(BASE_DIR, "assets/reference_1000x792.jpg")
W, H = 1000, 792

ref_img = Image.open(REF_PATH).convert("RGB")
ref_arr = np.asarray(ref_img, dtype=np.float32)

# Luminance & structure tensor flow
lum = 0.299 * ref_arr[:,:,0] + 0.587 * ref_arr[:,:,1] + 0.114 * ref_arr[:,:,2]
lum_s = gaussian_filter(lum, sigma=1.8)
gx = sobel(lum_s, axis=1)
gy = sobel(lum_s, axis=0)
Jxx = gaussian_filter(gx*gx, sigma=3.0)
Jxy = gaussian_filter(gx*gy, sigma=3.0)
Jyy = gaussian_filter(gy*gy, sigma=3.0)
flow_angle = 0.5 * np.arctan2(2.0 * Jxy, Jxx - Jyy) + (np.pi / 2.0)

def compute_metrics(rendered_arr, target_arr):
    # MSE & PSNR
    diff = rendered_arr - target_arr
    mse = float(np.mean(diff ** 2))
    psnr = float(10.0 * np.log10((255.0 ** 2) / max(mse, 1e-6)))
    
    # Approximate CIE Lab Delta E (fast vectorized sRGB -> XYZ -> Lab)
    def rgb2lab(rgb):
        v = np.clip(rgb / 255.0, 0.0, 1.0)
        v = np.where(v > 0.04045, ((v + 0.055) / 1.055) ** 2.4, v / 12.92)
        X = v[:,:,0]*0.4124 + v[:,:,1]*0.3576 + v[:,:,2]*0.1805
        Y = v[:,:,0]*0.2126 + v[:,:,1]*0.7152 + v[:,:,2]*0.0722
        Z = v[:,:,0]*0.0193 + v[:,:,1]*0.1192 + v[:,:,2]*0.9505
        X /= 0.95047; Z /= 1.08883
        def f(t):
            return np.where(t > 0.008856, np.cbrt(t), 7.787 * t + 16.0/116.0)
        fx, fy, fz = f(X), f(Y), f(Z)
        L = 116.0 * fy - 16.0
        a = 500.0 * (fx - fy)
        b = 200.0 * (fy - fz)
        return np.stack([L, a, b], axis=-1)
    
    lab1 = rgb2lab(rendered_arr)
    lab2 = rgb2lab(target_arr)
    delta_e = float(np.mean(np.linalg.norm(lab1 - lab2, axis=-1)))
    
    # Structural Similarity (SSIM) on luminance + color channels
    C1 = (0.01 * 255.0) ** 2
    C2 = (0.03 * 255.0) ** 2
    ssim_vals = []
    for c in range(3):
        x = rendered_arr[:,:,c]
        y = target_arr[:,:,c]
        mu_x = gaussian_filter(x, sigma=2.5)
        mu_y = gaussian_filter(y, sigma=2.5)
        sig_x2 = gaussian_filter(x*x, sigma=2.5) - mu_x**2
        sig_y2 = gaussian_filter(y*y, sigma=2.5) - mu_y**2
        sig_xy = gaussian_filter(x*y, sigma=2.5) - mu_x*mu_y
        num = (2*mu_x*mu_y + C1) * (2*sig_xy + C2)
        den = (mu_x**2 + mu_y**2 + C1) * (sig_x2 + sig_y2 + C2)
        ssim_vals.append(float(np.mean(num / den)))
    ssim = float(np.mean(ssim_vals))
    return {"psnr": round(psnr, 2), "ssim": round(ssim, 4), "delta_e": round(delta_e, 2)}

print("Metrics helper ready in", round(time.time() - t0, 2), "s")
