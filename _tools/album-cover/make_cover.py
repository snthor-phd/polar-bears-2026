"""Album cover for the NL&PB shared album.

Designed to sit UNDER Google Photos' own album-title overlay:
no type of its own, and a deliberately calm middle band where
that overlay lands. Original artwork generated here - nothing
licensed, so it is safe to use on a shared album.

Aurora model: each curtain is an undulating lower hem with
vertical rays streaming upward from it, green at the hem and
cooling to violet at the tips. That is what makes it read as
aurora rather than as ribbon or fog.
"""
import numpy as np
from PIL import Image, ImageFilter

W, H = 2400, 1800
rng = np.random.default_rng(70413)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
u = xx / W          # 0..1 left to right
v = yy / H          # 0..1 top to bottom


def blur(a, r):
    return np.asarray(
        Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8)).filter(
            ImageFilter.GaussianBlur(r)), np.float32) / 255.0


def noise1d(n, scale, octaves=5):
    """Smooth 1-D fractal noise, length n, in 0..1."""
    out = np.zeros(n, np.float32)
    amp, s = 1.0, float(scale)
    for _ in range(octaves):
        k = max(2, int(n / s))
        g = rng.random(k).astype(np.float32)
        idx = np.linspace(0, k - 1, n)
        i0 = np.floor(idx).astype(int)
        i1 = np.minimum(i0 + 1, k - 1)
        f = idx - i0
        f = f * f * (3 - 2 * f)                     # smoothstep
        out += amp * (g[i0] * (1 - f) + g[i1] * f)
        amp *= 0.55
        s *= 0.45
    out -= out.min()
    return out / out.max()


def noise2d(shape, scale, octaves=4):
    out = np.zeros(shape, np.float32)
    amp, s = 1.0, float(scale)
    for _ in range(octaves):
        h = max(2, int(shape[0] / s))
        w = max(2, int(shape[1] / s))
        g = rng.random((h, w)).astype(np.float32)
        g = np.asarray(Image.fromarray((g * 255).astype(np.uint8))
                       .resize((shape[1], shape[0]), Image.BICUBIC), np.float32) / 255.0
        out += amp * g
        amp *= 0.5
        s *= 0.5
    return out / out.max()


# ---------------------------------------------------------------- sky
sky_top = np.array([7, 14, 27], np.float32)
sky_mid = np.array([12, 25, 43], np.float32)
sky_low = np.array([20, 37, 53], np.float32)
t = np.clip(v / 0.80, 0, 1)[..., None]
img = np.where(t < 0.5,
               sky_top + (sky_mid - sky_top) * (t / 0.5),
               sky_mid + (sky_low - sky_mid) * ((t - 0.5) / 0.5)).astype(np.float32)

# ------------------------------------------------------------- aurora
# Kept in the upper third: the middle of the frame stays quiet sky so
# Google's white title reads over it wherever the crop happens to land.
# hem_y, tilt, amp1, f1, ph1, amp2, f2, ph2, ray_len, gain
curtains = [
    (0.300, -0.035, 0.042, 1.15, 0.7, 0.016, 2.7, 2.1, 0.150, 1.00),
    (0.225,  0.045, 0.030, 1.70, 2.6, 0.012, 3.9, 0.4, 0.115, 0.62),
    (0.355, -0.018, 0.022, 0.85, 4.1, 0.009, 2.2, 3.3, 0.080, 0.30),
]

# vertical striations come from noise that varies in x only
rays_hi = noise1d(W, 46, 5)          # fine
rays_lo = noise1d(W, 200, 3)         # broad brightness swells
wobble = noise2d((H, W), 150, 3)     # gentle life so rays aren't mechanical

# soften the striations so they read as light, not as a barcode
rays_hi = np.asarray(Image.fromarray((rays_hi[None, :] * 255).astype(np.uint8))
                     .filter(ImageFilter.GaussianBlur(3)), np.float32)[0] / 255.0

hem = np.zeros((H, W), np.float32)   # soft lower edge
body = np.zeros((H, W), np.float32)  # the rays above it
tipf = np.zeros((H, W), np.float32)  # how far up its own ray each pixel is

for (hy, tilt, a1, f1, p1, a2, f2, p2, rlen, gain) in curtains:
    base = (hy + tilt * (u - 0.5)
            + a1 * np.sin(2 * np.pi * f1 * u + p1)
            + a2 * np.sin(2 * np.pi * f2 * u + p2))

    ray = (0.45 + 0.55 * rays_hi)[None, :] * (0.40 + 0.70 * rays_lo)[None, :]
    ray = ray * (0.88 + 0.24 * wobble)

    d = base - v                                   # >0 above the hem
    up = np.clip(d, 0, None)

    # rays fade upward, each column reaching its own height
    reach = np.maximum(rlen * (0.55 + 0.85 * rays_lo)[None, :], 1e-3)
    amt = gain * ray * np.exp(-(up / reach) ** 1.25) * (d > 0)
    body += amt
    tipf += amt * np.clip(up / reach, 0, 1)        # weighted ray progress

    # a little spill below the hem, much shorter
    body += gain * 0.28 * ray * np.exp(-np.clip(-d, 0, None) / 0.030) * (d <= 0)

    # the hem: soft and wide, never a wire
    hem += gain * 0.20 * (0.55 + 0.55 * rays_lo)[None, :] * np.exp(-(d / 0.030) ** 2)

# fade off the top edge and keep it out of the lower sky
env = np.clip((v - 0.020) / 0.075, 0, 1) * np.clip((0.52 - v) / 0.14, 0, 1)
body *= env
hem *= env
tipf *= env

body = blur(body, 9) * 0.62 + blur(body, 3) * 0.50
hem = blur(hem, 11) * 0.70 + blur(hem, 4) * 0.55
tipf = blur(tipf, 9)
# normalise ray progress into 0..1 without dividing by ~0
prog = np.clip(tipf / np.maximum(body, 1e-3), 0, 1)

AUR_G = np.array([48, 196, 136], np.float32)       # site --aurora
AUR_C = np.array([150, 236, 208], np.float32)      # pale core
VIO = np.array([124, 110, 200], np.float32)        # site --violet

# green at the hem, cooling to violet only at the ray tips
img += (body * (1 - prog))[..., None] * AUR_G * 1.05
img += (body * prog)[..., None] * VIO * 0.85
img += (hem)[..., None] * AUR_G * 0.95
img += (hem ** 1.6)[..., None] * AUR_C * 0.70

# ------------------------------------------------------------- stars
star = np.zeros((H, W), np.float32)
n = 2200
sx = rng.integers(0, W, n)
sy = (rng.random(n) ** 1.4 * H * 0.78).astype(int)
star[sy, sx] = rng.random(n) ** 3.0
star = blur(star, 1.0) * 3.0
n2 = 90
bx = rng.integers(0, W, n2)
by = (rng.random(n2) ** 1.4 * H * 0.65).astype(int)
big = np.zeros((H, W), np.float32)
big[by, bx] = 1.0
star += blur(big, 4.5) * 1.3 + blur(big, 1.1) * 2.0
star *= np.clip(1.0 - (body + hem) * 1.5, 0.10, 1.0)
img += star[..., None] * np.array([200, 216, 242], np.float32)

# ------------------------------------------------- horizon + treeline
ground = 0.885

# soft airglow just above the trees
haze = np.exp(-((v - ground) / 0.075) ** 2) * 0.26
img += haze[..., None] * np.array([34, 62, 78], np.float32)

tree = np.zeros((H, W), np.float32)
x = -40
while x < W + 40:
    w = int(rng.integers(70, 190))
    h = int(rng.integers(70, 230))
    if rng.random() < 0.12:
        h = int(h * 1.7)                           # the occasional tall one
    base_y = int(ground * H) + int(rng.integers(0, 30))
    cx = x + w // 2
    top = base_y - h
    rows = np.arange(max(0, top), min(H, base_y))
    if rows.size:
        f = (rows - top) / max(1, h)               # 0 tip, 1 base
        half = (w * 0.5 * np.clip(f, 0, 1) ** 1.25).astype(int) + 1
        jag = rng.integers(-2, 3, rows.size)
        half = np.maximum(1, half + jag)
        for r, hf in zip(rows, half):
            tree[r, max(0, cx - hf):min(W, cx + hf + 1)] = 1.0
    x += int(w * rng.uniform(0.34, 0.62))

tree[int(ground * H):, :] = 1.0
tree = np.clip(blur(tree, 2.0) * 1.7, 0, 1)

GROUND = np.array([6, 11, 19], np.float32)
img = img * (1 - tree[..., None]) + GROUND * tree[..., None]

# ------------------------------------------ keep the title area calm
# The middle is already empty sky; this just takes a little more light
# out of it so white type has guaranteed contrast wherever Google crops.
r = np.sqrt(((u - 0.5) / 0.72) ** 2 + ((v - 0.60) / 0.24) ** 2)
calm = np.clip(1.0 - r, 0, 1) ** 1.3
img *= (1.0 - 0.20 * calm)[..., None]

# gentle vignette
vig = np.sqrt(((u - 0.5) / 0.80) ** 2 + ((v - 0.5) / 0.88) ** 2)
img *= (1.0 - 0.28 * np.clip(vig - 0.48, 0, 1) ** 1.3)[..., None]

# fine grain so nothing bands on an OLED phone
img += rng.normal(0, 1.6, (H, W, 1)).astype(np.float32)

out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGB')
out.save('album-cover.jpg', quality=88, optimize=True, progressive=True)
print('wrote album-cover.jpg', out.size)
