# -*- coding: utf-8 -*-
"""High-bit 16/32-bit anime pixel art asset generator (640x360 room + redesigned Marin).
Generates crisp PNGs with multi-tone shading and sel-out colored outlines into ./assets/.
"""
import os
import math
import random
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
os.makedirs(ASSETS, exist_ok=True)

VW, VH = 640, 360
CW, CH = 160, 220
OX, OY = 80, 210  # feet origin on character canvas

# ------------------------------------------------------------------ hue-shifted 16-bit palettes (v0.6-beta Art Overhaul)
# Skin: warm porcelain-peach light -> rosy-peach & warm coral-terracotta shadows (zero muddy grey!)
SKIN_HI = (255, 245, 236, 255)
SKIN    = (255, 228, 212, 255)
SKIN_SH = (244, 190, 176, 255)
SKIN_D  = (216, 148, 140, 255)

# Hair: sunlit champagne halo -> golden blonde -> warm honey-orange shadows -> luscious coral-rose tips
HAIR_SHINE = (255, 253, 226, 255)
HAIR_HI    = (255, 238, 168, 255)
HAIR       = (250, 208, 112, 255)
HAIR_SH    = (224, 154, 72, 255)
HAIR_D     = (186, 110, 54, 255)

PINK_HI = (255, 194, 212, 255)
PINK    = (248, 122, 158, 255)
PINK_SH = (210, 76, 118, 255)

# White shirts: pure warm-white light -> cool periwinkle-lavender shadows
SHIRT_HI = (255, 255, 255, 255)
SHIRT    = (246, 247, 252, 255)
SHIRT_SH = (208, 214, 236, 255)
SHIRT_D  = (164, 172, 204, 255)

# Sleek school tie (cool slate-indigo)
TIE_HI = (132, 148, 178, 255)
TIE    = (88, 104, 136, 255)
TIE_SH = (56, 68, 96, 255)

# Pleated navy school skirt
SKIRT_HI = (78, 88, 128, 255)
SKIRT    = (48, 54, 86, 255)
SKIRT_SH = (30, 34, 60, 255)

HOME_BOT_HI = (88, 86, 112, 255)
HOME_BOT    = (60, 58, 82, 255)
HOME_BOT_SH = (40, 38, 58, 255)

SOCK_HI = (64, 64, 86, 255)
SOCK    = (38, 38, 54, 255)
SOCK_SH = (24, 24, 38, 255)

SHOE_HI = (142, 92, 80, 255)
SHOE    = (88, 52, 48, 255)
SHOE_SH = (50, 28, 30, 255)

SLIP_HI = (255, 210, 224, 255)
SLIP    = (244, 148, 178, 255)
SLIP_SH = (198, 100, 134, 255)

# Outfit 2: Oversized pastel-lavender/pink cozy hoodie + sneakers
HOOD_HI = (246, 214, 238, 255)
HOOD    = (220, 170, 210, 255)
HOOD_SH = (180, 124, 174, 255)
HOOD_D  = (138, 86, 136, 255)
SNEAK_HI = (255, 252, 254, 255)
SNEAK    = (236, 142, 174, 255)
SNEAK_SH = (186, 94, 130, 255)

# Outfit 3: Stylish Streetwear / Cosplay Casual (mint ringer crop top + high-waisted denim + chunky sneakers)
MINT_HI  = (212, 250, 236, 255)
MINT     = (146, 226, 204, 255)
MINT_SH  = (98, 180, 164, 255)
DENIM_HI = (124, 166, 214, 255)
DENIM    = (78, 120, 176, 255)
DENIM_SH = (50, 80, 134, 255)
BELT     = (126, 76, 54, 255)
GOLD     = (248, 212, 110, 255)

CHOKER   = (34, 28, 42, 255)
SILVER   = (228, 234, 246, 255)
SILVER_D = (148, 156, 176, 255)

# Marin's signature warm crimson-berry -> vibrant magenta-rose -> luminous pink eyes
EYE_TOP  = (106, 26, 70, 255)
EYE_MID  = (198, 56, 120, 255)
EYE_BOT  = (254, 136, 180, 255)
EYE_GLOW = (255, 206, 226, 255)
LASH     = (60, 28, 46, 255)
LASH_SFT = (114, 58, 80, 255)
BROW     = (178, 124, 68, 255)
MOUTH_C  = (178, 76, 92, 255)
MOUTH_IN = (238, 124, 138, 255)
WHITE    = (255, 255, 255, 255)


# ------------------------------------------------------------------ drawing helpers & material-aware sel-out
def new_char():
    return Image.new("RGBA", (CW, CH), (0, 0, 0, 0))


def sel_out(img, darken=(0.52, 0.44, 0.56), min_rgb=(36, 26, 40), alpha_thresh=128):
    """Material-aware directional Hue-Shifted Sel-Out (VA-11 Hall-A / modern 16-bit anime sprite technique).
    Top/left lit borders stay soft & warm; skin, blonde hair, pink tips & white cloth each get clean hue-shifted outlines!
    """
    arr = np.array(img, dtype=np.uint8)
    opaque = arr[:, :, 3] >= alpha_thresh
    h, w = opaque.shape
    out = arr.copy()

    n_up = np.zeros_like(opaque); n_up[1:] = opaque[:-1]   # neighbor is ABOVE -> this border is at BOTTOM (shaded)
    n_dn = np.zeros_like(opaque); n_dn[:-1] = opaque[1:]   # neighbor is BELOW -> this border is at TOP (lit!)
    n_lt = np.zeros_like(opaque); n_lt[:, 1:] = opaque[:, :-1]
    n_rt = np.zeros_like(opaque); n_rt[:, :-1] = opaque[:, 1:]
    border = (~opaque) & (n_up | n_dn | n_lt | n_rt)

    r_sum = np.zeros((h, w), dtype=np.float32)
    g_sum = np.zeros((h, w), dtype=np.float32)
    b_sum = np.zeros((h, w), dtype=np.float32)
    cnt = np.zeros((h, w), dtype=np.float32)

    shifts = [
        ((1, None), (None, -1), (None, None), (None, None)),
        ((None, -1), (1, None), (None, None), (None, None)),
        ((None, None), (None, None), (1, None), (None, -1)),
        ((None, None), (None, None), (None, -1), (1, None)),
    ]
    for (dy0, dy1), (sy0, sy1), (dx0, dx1), (sx0, sx1) in shifts:
        m = opaque[sy0:sy1, sx0:sx1]
        r_sum[dy0:dy1, dx0:dx1] += np.where(m, arr[sy0:sy1, sx0:sx1, 0], 0)
        g_sum[dy0:dy1, dx0:dx1] += np.where(m, arr[sy0:sy1, sx0:sx1, 1], 0)
        b_sum[dy0:dy1, dx0:dx1] += np.where(m, arr[sy0:sy1, sx0:sx1, 2], 0)
        cnt[dy0:dy1, dx0:dx1] += m.astype(np.float32)

    cnt = np.maximum(cnt, 1.0)
    ar = r_sum / cnt
    ag = g_sum / cnt
    ab = b_sum / cnt

    # Directional lighting factor: top/left edges are ~16% lighter & softer than bottom/right edges
    lit_edge = (n_dn | n_rt) & (~n_up)
    by_y, bx_x = np.where(border)
    for y, x in zip(by_y, bx_x):
        r, g, b = ar[y, x], ag[y, x], ab[y, x]
        lit = bool(lit_edge[y, x])
        # 1. Warm peach skin -> warm terracotta-rose outline (never grey/black!)
        if r > 200 and g > 135 and b > 120 and (r - b) > 20 and (r - g) < 75 and g > b:
            col = (184, 114, 108) if lit else (152, 86, 86)
        # 2. Sunlit golden-blonde hair -> warm honey-caramel outline
        elif r > 175 and g > 105 and (r - b) >= 62:
            col = (188, 122, 60) if lit else (152, 92, 46)
        # 3. Coral-pink hair tips / pink cloth -> rich berry-rose outline
        elif r > 185 and (r - g) > 40 and b > g - 16:
            col = (178, 76, 112) if lit else (144, 54, 88)
        # 4. Crisp white / periwinkle shirt -> cool slate-periwinkle outline
        elif r > 158 and g > 164 and b > 180 and abs(r - b) < 48:
            col = (138, 144, 182) if lit else (104, 110, 150)
        # 5. Pastel lavender hoodie
        elif r > 130 and b > 125 and b > g + 14:
            col = (136, 90, 142) if lit else (102, 60, 112)
        # 6. Pastel mint top
        elif g > r + 15 and g > 155:
            col = (76, 146, 138) if lit else (54, 114, 112)
        # 7. Dark garments / shoes / socks -> rich deep indigo-plum ink
        else:
            f = 1.12 if lit else 1.0
            col = (
                int(min(255, max(min_rgb[0], r * darken[0] * f))),
                int(min(255, max(min_rgb[1], g * darken[1] * f))),
                int(min(255, max(min_rgb[2], b * darken[2] * f))),
            )
        out[y, x, 0] = col[0]
        out[y, x, 1] = col[1]
        out[y, x, 2] = col[2]
        out[y, x, 3] = 255
    return Image.fromarray(out, "RGBA")


def lerp_c(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(4))


def hair_gradient_fill(img, y_start, y_end, pink_start=0.48, steps=10):
    """Organic strand-curved 10-step ombre from sunlit golden-blonde -> warm peach-gold -> vibrant coral-pink tips."""
    arr = np.array(img, dtype=np.uint8)
    h, w, _ = arr.shape
    span = max(1, y_end - y_start)
    for y in range(max(0, y_start), min(h, y_end)):
        row = arr[y]
        mask = row[:, 3] > 200
        if not np.any(mask):
            continue
        for x in np.where(mask)[0]:
            # Subtle wave across X so each hair lock transitions organically instead of a ruler-flat band!
            wave_dy = math.cos((x - OX) * 0.28) * 3.0
            f = ((y + wave_dy) - y_start) / span
            if f <= pink_start:
                continue
            t = min(1.0, (f - pink_start) / (1.0 - pink_start))
            tq = round(t * steps) / float(steps)
            r, g, b = float(row[x, 0]), float(row[x, 1]), float(row[x, 2])
            lum = (r + g + b) / 3.0
            if lum > 224:
                c = lerp_c(HAIR_HI, PINK_HI, tq)
            elif lum > 176:
                c = lerp_c(HAIR, PINK, tq)
            else:
                c = lerp_c(HAIR_SH, PINK_SH, tq)
            arr[y, x] = c
    return Image.fromarray(arr, "RGBA")


def bezier(p0, p1, p2, steps=14):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        x = u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0]
        y = u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]
        pts.append((round(x), round(y)))
    return pts


def poly(draw, pts, fill):
    draw.polygon([(OX + round(x), OY + round(y)) for x, y in pts], fill=fill)


def rect(draw, x, y, w, h, fill):
    draw.rectangle([OX + round(x), OY + round(y), OX + round(x + w) - 1, OY + round(y + h) - 1], fill=fill)


def ell(draw, x, y, w, h, fill):
    draw.ellipse([OX + round(x), OY + round(y), OX + round(x + w) - 1, OY + round(y + h) - 1], fill=fill)


def line(draw, p0, p1, fill, width=1):
    draw.line([(OX + round(p0[0]), OY + round(p0[1])), (OX + round(p1[0]), OY + round(p1[1]))],
              fill=fill, width=width)


# ------------------------------------------------------------------ character layers (v0.6-beta Commercial 16-bit Overhaul)
def _draw_shoe_front(d, x_in, x_out, y_ank, outfit, side):
    """Draw detailed 16-bit footwear for standing/dangling legs."""
    s = side
    x0, x1 = min(x_in, x_out), max(x_in, x_out)
    if outfit in (0, 4):
        # Glossy espresso-brown school penny loafers with sole, vamp strap & specular toe glint
        poly(d, [(x0 - (1 if s < 0 else 0), y_ank), (x1 + (1 if s > 0 else 0), y_ank),
                 (x1 + (2 if s > 0 else 0), y_ank + 5), (x0 - (2 if s < 0 else 0), y_ank + 5)], SHOE)
        rect(d, x0 - (2 if s < 0 else 0), y_ank + 5, (x1 - x0) + 3, 2, SHOE_SH)
        rect(d, x0 + 1, y_ank + 1, max(3, x1 - x0 - 1), 2, SHOE_HI)
        rect(d, x0 + 2, y_ank, 2, 1, WHITE)
    elif outfit == 1:
        # Plush pastel-coral indoor slippers with soft cream cuff & dainty ribbon dot
        poly(d, [(x0 - (1 if s < 0 else 0), y_ank + 1), (x1 + (1 if s > 0 else 0), y_ank + 1),
                 (x1 + (2 if s > 0 else 0), y_ank + 6), (x0 - (2 if s < 0 else 0), y_ank + 6)], SLIP)
        rect(d, x0, y_ank, (x1 - x0) + 1, 2, SKIN_HI)
        rect(d, x0 - (2 if s < 0 else 0), y_ank + 5, (x1 - x0) + 3, 2, SLIP_SH)
        rect(d, (x0 + x1) // 2, y_ank + 2, 2, 2, SLIP_HI)
    elif outfit == 2:
        # Sporty pastel-pink & white sneakers with rubber toe cap & crisp laces
        poly(d, [(x0 - (1 if s < 0 else 0), y_ank), (x1 + (1 if s > 0 else 0), y_ank),
                 (x1 + (2 if s > 0 else 0), y_ank + 5), (x0 - (2 if s < 0 else 0), y_ank + 5)], SNEAK)
        rect(d, x0 - (2 if s < 0 else 0), y_ank + 5, (x1 - x0) + 3, 2, SNEAK_HI)
        rect(d, x0 + 1, y_ank + 1, 3, 1, WHITE)
        rect(d, x0 + 1, y_ank + 3, 3, 1, WHITE)
    else:
        # Stylish white & mint chunky streetwear sneakers
        poly(d, [(x0 - (1 if s < 0 else 0), y_ank), (x1 + (1 if s > 0 else 0), y_ank),
                 (x1 + (2 if s > 0 else 0), y_ank + 5), (x0 - (2 if s < 0 else 0), y_ank + 5)], WHITE)
        rect(d, x0, y_ank + 2, (x1 - x0) + 1, 2, MINT)
        rect(d, x0 - (2 if s < 0 else 0), y_ank + 5, (x1 - x0) + 3, 2, SHIRT_SH)


def build_legs(outfit, pose="stand"):
    """Layer 0: Graceful anatomical anime legs (tapered thighs, smooth knees with ZERO crosses, slender ankles & detailed shoes)."""
    img = new_char()
    d = ImageDraw.Draw(img)

    if pose == "floor":
        # Graceful slender yokozuwari (mermaid side-sit): knees neatly together, slender calves & shoes folded to right!
        poly(d, [(-10, -82), (-12, -66), (-9, -50), (-2, -49), (-1, -66), (-1, -82)], SKIN)
        poly(d, [(-12, -66), (-9, -50), (-7, -50), (-9, -66)], SKIN_SH)
        poly(d, [(0, -82), (10, -82), (11, -65), (8, -50), (-1, -50), (-1, -66)], SKIN)
        poly(d, [(7, -82), (10, -82), (11, -65), (8, -50), (5, -50), (8, -65)], SKIN_SH)
        # Soft vertical thigh sheen + warm rosy knee dimple (no white cross!)
        line(d, (-7, -66), (-6, -54), SKIN_HI, 1)
        line(d, (3, -66), (4, -54), SKIN_HI, 1)
        rect(d, -6, -52, 2, 1, SKIN_SH)
        rect(d, 3, -52, 2, 1, SKIN_SH)

        # Slender folded calves tucked gracefully to viewer-right
        poly(d, [(6, -55), (19, -51), (22, -46), (10, -46)], SKIN)
        poly(d, [(8, -52), (21, -48), (24, -44), (9, -45)], SKIN)
        line(d, (9, -46), (23, -45), SKIN_SH, 1)

        if outfit in (0, 4):
            poly(d, [(13, -51), (21, -48), (23, -44), (13, -45)], SOCK)
            poly(d, [(20, -50), (27, -47), (26, -43), (19, -44)], SHOE)
            rect(d, 21, -48, 3, 2, SHOE_HI)
        elif outfit == 1:
            poly(d, [(19, -50), (27, -47), (26, -43), (18, -44)], SLIP)
            rect(d, 20, -48, 3, 2, SLIP_HI)
        elif outfit == 2:
            poly(d, [(10, -52), (21, -48), (23, -44), (11, -45)], SOCK)
            line(d, (12, -51), (12, -46), WHITE, 1)
            poly(d, [(20, -50), (27, -47), (26, -43), (19, -44)], SNEAK)
            rect(d, 21, -45, 4, 2, SNEAK_HI)
        else:
            poly(d, [(17, -50), (21, -48), (22, -44), (17, -45)], WHITE)
            poly(d, [(20, -50), (27, -47), (26, -43), (19, -44)], WHITE)
            rect(d, 21, -47, 4, 2, MINT)
        return sel_out(img)

    if pose == "sit":
        # Sitting naturally on bed edge: foreshortened thighs & cute shorter dangling calves!
        for s in (-1, 1):
            poly(d, [(s * 10, -82), (s * 11, -69), (s * 9.5, -60), (s * 3.5, -60), (s * 2, -71), (s * 2, -82)], SKIN)
            poly(d, [(s * 8, -82), (s * 11, -69), (s * 9.5, -60), (s * 7.5, -60), (s * 7.5, -82)], SKIN_SH)
            # Foreshortened dangling calf tapering to 4px ankle at y=-28
            poly(d, [(s * 9, -61), (s * 8.5, -45), (s * 7, -28), (s * 3.5, -28), (s * 3.5, -45), (s * 3.5, -61)], SKIN)
            line(d, (s * 5, -57), (s * 5, -39), SKIN_HI, 1)
            rect(d, min(s * 6, s * 5), -60, 2, 1, SKIN_SH)
            if outfit in (0, 4):
                poly(d, [(s * 8.5, -43), (s * 7, -28), (s * 3.5, -28), (s * 3.5, -43)], SOCK)
                line(d, (s * 4, -43), (s * 8, -43), SOCK_HI, 1)
            elif outfit == 2:
                poly(d, [(s * 9, -56), (s * 8.5, -45), (s * 7, -28), (s * 3.5, -28), (s * 3.5, -56)], SOCK)
                line(d, (s * 4, -53), (s * 8.5, -53), WHITE, 1)
                line(d, (s * 4, -50), (s * 8.5, -50), WHITE, 1)
            elif outfit == 3:
                poly(d, [(s * 7.5, -33), (s * 7, -28), (s * 3.5, -28), (s * 3.5, -33)], WHITE)
            _draw_shoe_front(d, s * 3, s * 8, -29, outfit, s)
        return sel_out(img)

    if pose == "air":
        for s in (-1, 1):
            poly(d, [(s * 10, -74), (s * 12, -53), (s * 10, -43), (s * 4, -44), (s * 2, -62), (s * 2, -74)], SKIN)
            poly(d, [(s * 10, -44), (s * 8.5, -25), (s * 7, -13), (s * 3, -14), (s * 4, -28), (s * 5, -44)], SKIN)
            line(d, (s * 6, -64), (s * 7, -48), SKIN_HI, 1)
            if outfit in (0, 4):
                poly(d, [(s * 8.5, -28), (s * 7, -13), (s * 3, -14), (s * 4, -28)], SOCK)
            elif outfit == 2:
                poly(d, [(s * 10, -44), (s * 8.5, -25), (s * 7, -13), (s * 3, -14), (s * 5, -44)], SOCK)
                line(d, (s * 5, -41), (s * 9.5, -41), WHITE, 1)
            elif outfit == 3:
                poly(d, [(s * 7.5, -19), (s * 7, -13), (s * 3, -14), (s * 3.5, -19)], WHITE)
            _draw_shoe_front(d, s * 3, s * 8, -14, outfit, s)
        return sel_out(img)

    # Natural graceful standing contrapposto: smooth taper from thighs -> soft knees -> curved calves -> 4px ankles!
    # Left leg (supporting): x around -9..-3 tapering cleanly to -7..-3.5 ankle
    l_pts = [
        (-10, -74), (-10, -58), (-8.5, -43), (-9, -30), (-7.5, -16), (-7, -6),
        (-3, -6), (-3, -16), (-3, -30), (-3, -43), (-2, -58), (-2, -74)
    ]
    poly(d, l_pts, SKIN)
    # Soft warm inner-leg & under-skirt shading
    poly(d, [(-4, -74), (-4, -56), (-4, -42), (-4, -16), (-3, -16), (-3, -43), (-2, -58), (-2, -74)], SKIN_SH)
    rect(d, -10, -74, 9, 5, SKIN_SH)
    # Smooth vertical front sheen + subtle warm knee contour (NO white crosses!)
    line(d, (-7, -64), (-6, -47), SKIN_HI, 1)
    line(d, (-6, -38), (-6, -26), SKIN_HI, 1)
    rect(d, -6, -43, 2, 1, SKIN_SH)

    # Right leg (relaxed gentle contrapposto): x around +2..+10 tapering to +5.5..+9.5 ankle
    r_pts = [
        (2, -74), (10, -74), (10.5, -58), (9.5, -43), (10.5, -29), (9.5, -15), (9, -6),
        (5, -6), (5, -15), (4.5, -30), (4, -43), (2.5, -58)
    ]
    poly(d, r_pts, SKIN)
    poly(d, [(8.5, -74), (10, -74), (10.5, -58), (9.5, -43), (10.5, -29), (9.5, -15), (9, -6),
             (8, -6), (8.5, -29), (8, -43), (8.5, -58)], SKIN_SH)
    rect(d, 2, -74, 9, 5, SKIN_SH)
    line(d, (5, -64), (6, -47), SKIN_HI, 1)
    line(d, (6, -38), (7, -26), SKIN_HI, 1)
    rect(d, 5, -43, 2, 1, SKIN_SH)

    # Hosiery & detailed shoes
    if outfit in (0, 4):
        # Sleek mid-calf navy-charcoal school socks with ribbed cuff & vertical highlight
        poly(d, [(-8.5, -27), (-7.5, -16), (-7, -6), (-3, -6), (-3, -16), (-3, -27)], SOCK)
        line(d, (-8.5, -27), (-3, -27), SOCK_HI, 1)
        line(d, (-6, -25), (-5.5, -8), SOCK_HI, 1)
        poly(d, [(10.5, -27), (9.5, -15), (9, -6), (5, -6), (5, -15), (4.5, -27)], SOCK)
        line(d, (4.5, -27), (10.5, -27), SOCK_HI, 1)
        line(d, (7, -25), (7, -8), SOCK_HI, 1)
    elif outfit == 2:
        # Cozy striped thigh-highs (*zettai ryouiki*)
        poly(d, [(-9, -49), (-8.5, -43), (-9, -30), (-7.5, -16), (-7, -6),
                 (-3, -6), (-3, -16), (-3, -30), (-3, -43), (-2.5, -49)], SOCK)
        line(d, (-8.5, -46), (-3, -46), WHITE, 1)
        line(d, (-8.5, -43), (-3, -43), WHITE, 1)
        poly(d, [(10, -48), (9.5, -43), (10.5, -29), (9.5, -15), (9, -6),
                 (5, -6), (5, -15), (4.5, -30), (4, -43), (3.5, -48)], SOCK)
        line(d, (4, -45), (9.5, -45), WHITE, 1)
        line(d, (4, -42), (9.5, -42), WHITE, 1)
    elif outfit == 3:
        # Crisp white ankle socks
        poly(d, [(-7.5, -14), (-7, -6), (-3, -6), (-3, -14)], WHITE)
        poly(d, [(9.5, -14), (9, -6), (5, -6), (5, -14)], WHITE)

    _draw_shoe_front(d, -7, -3, -7, outfit, -1)
    _draw_shoe_front(d, 5, 9, -7, outfit, 1)
    return sel_out(img)


def build_lower_garment(outfit):
    """Layer 1: Tailored box-pleated miniskirt (0, 4), Lounge shorts (1), Hoodie hem (2), High-waisted Denim (3)."""
    img = new_char()
    d = ImageDraw.Draw(img)
    if outfit in (0, 4):
        # Flared high-waisted box-pleated school skirt with scalloped pleat hem & subtle check trim!
        pts = [
            (-10, -95), (10, -95),
            (18, -69), (14, -67), (9, -68), (4, -67), (0, -68), (-4, -67), (-9, -68), (-14, -67), (-18, -69)
        ]
        poly(d, pts, SKIRT)
        rect(d, -10, -95, 20, 3, SKIRT_SH)
        line(d, (-9, -95), (4, -95), SKIRT_HI, 1)
        for tx, bx in ((-8, -14), (-4, -8), (0, -1), (4, 7), (8, 13)):
            line(d, (tx, -92), (bx, -68), SKIRT_SH, 2)
            line(d, (tx + 2, -92), (bx + 2, -69), SKIRT_HI, 1)
        # Subtle canon woven accent line 3px above hem
        line(d, (-16, -71), (16, -71), SKIRT_HI, 1)
    elif outfit == 1:
        # Tailored soft lounge shorts with curved athletic hem & cream drawstring
        pts = [(-10, -93), (10, -93), (14, -72), (3, -72), (0, -76), (-3, -72), (-14, -72)]
        poly(d, pts, HOME_BOT)
        rect(d, -10, -93, 20, 3, HOME_BOT_SH)
        line(d, (0, -90), (0, -76), HOME_BOT_SH, 1)
        line(d, (-8, -88), (-11, -74), HOME_BOT_HI, 2)
        line(d, (-13, -73), (-3, -73), HOME_BOT_HI, 1)
        line(d, (3, -73), (13, -73), HOME_BOT_SH, 1)
        line(d, (-1, -92), (-2, -87), SHIRT, 1)
        line(d, (1, -92), (2, -87), SHIRT, 1)
    elif outfit == 2:
        # Peekaboo lounge shorts beneath plush ribbed hoodie hem
        poly(d, [(-13, -78), (13, -78), (14, -71), (3, -71), (0, -74), (-3, -71), (-14, -71)], HOME_BOT)
        poly(d, [(-15, -94), (15, -94), (16, -76), (-16, -76)], HOOD)
        rect(d, -16, -81, 32, 5, HOOD_SH)
        for rx in range(-13, 14, 4):
            line(d, (rx, -81), (rx, -76), HOOD_D, 1)
        # Cozy kangaroo pocket bevel
        poly(d, [(-9, -93), (9, -93), (11, -82), (-11, -82)], HOOD_SH)
        poly(d, [(-8, -92), (8, -92), (9, -83), (-9, -83)], HOOD_HI)
    else:
        # High-waisted blue denim shorts with belt, gold buckle & rolled light-denim cuffs!
        pts = [(-10, -94), (10, -94), (14, -71), (3, -71), (0, -76), (-3, -71), (-14, -71)]
        poly(d, pts, DENIM)
        poly(d, [(-9, -89), (-3, -89), (-4, -75), (-11, -75)], DENIM_HI)
        poly(d, [(3, -89), (9, -89), (11, -75), (4, -75)], DENIM_SH)
        line(d, (0, -90), (0, -76), DENIM_SH, 1)
        rect(d, -14, -73, 11, 2, DENIM_HI)
        rect(d, 3, -73, 11, 2, DENIM_HI)
        rect(d, -10, -94, 20, 3, BELT)
        rect(d, -2, -94, 4, 3, GOLD)
    return sel_out(img)


def build_torso(outfit, relaxed=False):
    """Layer 2: Graceful sloping shoulders, natural bust volume, pinched 19px waist & all 5 outfits (+ relaxed variants!)."""
    img = new_char()
    d = ImageDraw.Draw(img)

    if outfit == 0:
        # Outfit 0: Canon School Blouse (sloped shoulders, tapered waist, crisp lapels & tied front bow-knot!)
        pts = [
            (-5, -134), (5, -134),
            (12, -129), (13, -118), (11.5, -108),
            (9.5, -99), (10.5, -93),
            (4, -91), (0, -93), (-4, -91),
            (-10.5, -93), (-9.5, -99),
            (-11.5, -108), (-13, -118), (-12, -129)
        ]
        poly(d, pts, SHIRT)
        # Cool periwinkle-lavender side & under-bust form shading
        poly(d, [(7, -128), (12, -126), (12.5, -116), (9.5, -99), (10, -93), (6, -93), (8, -110)], SHIRT_SH)
        poly(d, [(-12.5, -120), (-9.5, -120), (-8, -99), (-10, -93), (-9.5, -108)], SHIRT_SH)
        # Soft sunlit chest highlight + subtle natural under-bust drape curve
        poly(d, [(-8, -124), (-2, -124), (-3, -113), (-9, -113)], SHIRT_HI)
        line(d, (-8, -111), (-3, -110), SHIRT_SH, 1)
        line(d, (3, -110), (8, -111), SHIRT_SH, 1)
        # Neat breast pocket
        rect(d, 4, -118, 5, 5, SHIRT_SH)
        rect(d, 5, -117, 3, 3, SHIRT)

        v_bot = -114 if relaxed else -122
        v_w = 6 if relaxed else 5
        poly(d, [(-v_w, -134), (v_w, -134), (0, v_bot)], SKIN)
        poly(d, [(-v_w + 1, -134), (v_w - 1, -134), (0, -130)], SKIN_SH)
        line(d, (-4, -128), (-1, -126), SKIN_SH, 1)
        line(d, (4, -128), (1, -126), SKIN_SH, 1)
        if relaxed:
            line(d, (-v_w, -134), (0, v_bot), SHIRT_D, 1)
            line(d, (v_w, -134), (0, v_bot), SHIRT_D, 1)
        lap_x = 10 if relaxed else 9
        poly(d, [(-lap_x, -132), (-v_w + 1, -134), (-2, v_bot + 2), (-lap_x, -122)], SHIRT_HI)
        poly(d, [(lap_x, -132), (v_w - 1, -134), (2, v_bot + 2), (lap_x, -122)], SHIRT_HI)
        line(d, (-lap_x, -122), (-2, v_bot + 2), SHIRT_D, 1)
        line(d, (lap_x, -122), (2, v_bot + 2), SHIRT_D, 1)
        # Dainty front waist knot & tails
        ell(d, -3, -96, 6, 4, SHIRT_SH)
        ell(d, -2, -96, 4, 3, SHIRT_HI)
        poly(d, [(-2, -92), (-6, -86), (-3, -86), (-1, -91)], SHIRT_HI)
        poly(d, [(2, -92), (6, -86), (3, -86), (1, -91)], SHIRT_SH)

    elif outfit == 1:
        # Outfit 1: Breezy Home Tied-Waist Shirt (tiny warm waist peek + open collar when relaxed!)
        rect(d, -6, -95, 12, 3, SKIN)
        pts = [
            (-5, -134), (5, -134),
            (12, -129), (13.5, -117), (12, -107),
            (10, -98), (10.5, -93),
            (4, -92), (0, -95), (-4, -92),
            (-10.5, -93), (-10, -98),
            (-12, -107), (-13.5, -117), (-12, -129)
        ]
        poly(d, pts, SHIRT)
        poly(d, [(7, -128), (12, -125), (13, -115), (10, -93), (6, -93), (8, -110)], SHIRT_SH)
        poly(d, [(-13, -120), (-10, -120), (-9, -93), (-10, -93)], SHIRT_SH)
        poly(d, [(-8, -123), (-2, -123), (-3, -112), (-9, -112)], SHIRT_HI)
        line(d, (-8, -110), (-3, -109), SHIRT_SH, 1)
        line(d, (3, -109), (8, -110), SHIRT_SH, 1)

        v_bot = -113 if relaxed else -120
        v_w = 7 if relaxed else 6
        poly(d, [(-v_w, -134), (v_w, -134), (0, v_bot)], SKIN)
        poly(d, [(-v_w + 1, -134), (v_w - 1, -134), (0, -130)], SKIN_SH)
        line(d, (-4, -127), (-1, -125), SKIN_SH, 1)
        line(d, (4, -127), (1, -125), SKIN_SH, 1)
        line(d, (-v_w, -134), (0, v_bot), SHIRT_D, 1)
        line(d, (v_w, -134), (0, v_bot), SHIRT_D, 1)
        lap_x = 11 if relaxed else 9
        poly(d, [(-lap_x, -131), (-v_w + 1, -134), (-2, v_bot + 3), (-lap_x, -120)], SHIRT_HI)
        poly(d, [(lap_x, -131), (v_w - 1, -134), (2, v_bot + 3), (lap_x, -120)], SHIRT_HI)
        line(d, (-lap_x, -120), (-2, v_bot + 3), SHIRT_D, 1)
        line(d, (lap_x, -120), (2, v_bot + 3), SHIRT_D, 1)
        line(d, (0, v_bot), (0, -96), SHIRT_SH, 1)
        for yb in range(v_bot + 4, -97, 6):
            rect(d, -1, yb, 2, 1, SHIRT_D)
        ell(d, -3, -96, 6, 4, SHIRT_SH)
        ell(d, -2, -96, 4, 3, SHIRT_HI)
        poly(d, [(-2, -93), (-7, -85), (-4, -85), (-1, -92)], SHIRT_HI)
        poly(d, [(2, -93), (7, -85), (4, -85), (1, -92)], SHIRT_SH)

    elif outfit == 2:
        # Outfit 2: Cozy Pastel-Lavender Oversized Hoodie (+ cozy slipped wide hood neckline when relaxed!)
        pts = [
            (-8, -134), (8, -134),
            (15, -128), (16, -112), (15, -93),
            (-15, -93), (-16, -112), (-15, -128)
        ]
        poly(d, pts, HOOD)
        poly(d, [(9, -129), (15, -125), (16, -110), (15, -93), (10, -93), (11, -110)], HOOD_SH)
        poly(d, [(-15, -124), (-11, -124), (-11, -93), (-15, -93)], HOOD_SH)
        poly(d, [(-9, -122), (-2, -122), (-3, -104), (-9, -104)], HOOD_HI)
        if relaxed:
            ell(d, -11, -136, 23, 12, HOOD_SH)
            ell(d, -8, -136, 17, 10, SKIN)
            line(d, (-5, -129), (-1, -128), SKIN_SH, 1)
            line(d, (5, -129), (1, -128), SKIN_SH, 1)
            d.arc([OX - 9, OY - 136, OX + 9, OY - 125], 10, 170, fill=HOOD_HI, width=2)
            line(d, (-5, -125), (-7, -109), WHITE, 1)
            line(d, (5, -125), (6, -112), WHITE, 1)
        else:
            ell(d, -10, -136, 20, 9, HOOD_SH)
            ell(d, -8, -135, 16, 6, HOOD_HI)
            poly(d, [(-4, -135), (4, -135), (0, -127)], SKIN)
            line(d, (-4, -127), (-5, -111), WHITE, 1)
            line(d, (4, -127), (5, -113), WHITE, 1)
        rect(d, -1, -109, 3, 3, WHITE)
        rect(d, 0, -111, 1, 7, WHITE)
        rect(d, -3, -108, 7, 1, WHITE)

    elif outfit == 3:
        # Outfit 3: Stylish Streetwear Pastel-Mint Ringer Crop Top (+ wide summer scoop neckline when relaxed!)
        rect(d, -8, -96, 16, 3, SKIN)
        line(d, (-4, -95), (4, -95), SKIN_SH, 1)
        pts = [
            (-5, -134), (5, -134),
            (12, -129), (13, -119), (11, -108),
            (9.5, -96), (-9.5, -96),
            (-11, -108), (-13, -119), (-12, -129)
        ]
        poly(d, pts, MINT)
        poly(d, [(7, -128), (12, -126), (12.5, -117), (9.5, -96), (6, -96), (8, -112)], MINT_SH)
        poly(d, [(-12.5, -121), (-9.5, -121), (-8, -96), (-9.5, -96)], MINT_SH)
        poly(d, [(-8, -124), (-2, -124), (-3, -112), (-8, -112)], MINT_HI)
        line(d, (-7, -111), (-3, -110), MINT_SH, 1)
        line(d, (3, -110), (7, -111), MINT_SH, 1)
        if relaxed:
            ell(d, -8, -137, 17, 12, SKIN)
            line(d, (-5, -129), (-1, -127), SKIN_SH, 1)
            line(d, (5, -129), (1, -127), SKIN_SH, 1)
            d.arc([OX - 8, OY - 137, OX + 9, OY - 124], 5, 175, fill=WHITE, width=2)
        else:
            ell(d, -6, -137, 12, 9, SKIN)
            d.arc([OX - 6, OY - 137, OX + 6, OY - 128], 0, 180, fill=WHITE, width=2)
        rect(d, -2, -115, 2, 2, PINK)
        rect(d, 1, -115, 2, 2, PINK)
        rect(d, -2, -113, 5, 2, PINK)
        rect(d, -1, -111, 3, 1, PINK)
        rect(d, 0, -110, 1, 1, PINK)

    else:
        # Outfit 4: Canon Relaxed Short-Sleeve Shirt — tailored hourglass waist, open V-collar & crisp lapels!
        pts = [
            (-5, -134), (5, -134),
            (12, -129), (13, -118), (11.5, -108),
            (9.5, -99), (11, -92),
            (0, -90), (-11, -92), (-9.5, -99),
            (-11.5, -108), (-13, -118), (-12, -129)
        ]
        poly(d, pts, SHIRT)
        poly(d, [(7, -128), (12, -125), (12.5, -116), (11, -92), (6, -91), (8, -110)], SHIRT_SH)
        poly(d, [(-12.5, -120), (-9.5, -120), (-8, -99), (-11, -92), (-9.5, -108)], SHIRT_SH)
        poly(d, [(-8, -123), (-2, -123), (-3, -112), (-9, -112)], SHIRT_HI)
        line(d, (-8, -111), (-3, -110), SHIRT_SH, 1)
        line(d, (3, -110), (8, -111), SHIRT_SH, 1)

        v_bot = -111 if relaxed else -117
        v_w = 7 if relaxed else 6
        poly(d, [(-v_w, -134), (v_w, -134), (0, v_bot)], SKIN)
        poly(d, [(-v_w + 1, -134), (v_w - 1, -134), (0, -130)], SKIN_SH)
        line(d, (-4, -127), (-1, -125), SKIN_SH, 1)
        line(d, (4, -127), (1, -125), SKIN_SH, 1)
        line(d, (-v_w, -134), (0, v_bot), SHIRT_D, 1)
        line(d, (v_w, -134), (0, v_bot), SHIRT_D, 1)
        lap_x = 11 if relaxed else 10
        poly(d, [(-lap_x, -131), (-v_w + 1, -134), (-2, v_bot + 3), (-lap_x, -121)], SHIRT_HI)
        poly(d, [(lap_x, -131), (v_w - 1, -134), (2, v_bot + 3), (lap_x, -121)], SHIRT_HI)
        line(d, (-lap_x, -121), (-2, v_bot + 3), SHIRT_D, 1)
        line(d, (lap_x, -121), (2, v_bot + 3), SHIRT_D, 1)
        rect(d, 4, -112, 5, 5, SHIRT_SH)
        rect(d, 5, -111, 3, 3, SHIRT)
        line(d, (0, v_bot), (0, -91), SHIRT_SH, 1)
        for yb in range(v_bot + 4, -93, 6):
            rect(d, -1, yb, 2, 1, SHIRT_D)

    return sel_out(img)


def build_shirt_folds(outfit):
    """Layer 2b: Delicate cool-lavender waist & bust fabric creases that respond softly to spring motion."""
    img = new_char()
    d = ImageDraw.Draw(img)
    line(d, (-8, -104), (-3, -100), SHIRT_SH, 1)
    line(d, (8, -104), (3, -100), SHIRT_SH, 1)
    line(d, (-7, -105), (-4, -102), SHIRT_HI, 1)
    return img


def build_tie(relaxed=False):
    """Layer 5d (Outfit 0): Sleek, slender 3px tailored school necktie (no bulky grey shovel!)."""
    img = new_char()
    d = ImageDraw.Draw(img)
    ky = -119 if relaxed else -126
    if relaxed:
        line(d, (-4, -131), (-1, ky + 1), TIE_SH, 1)
        line(d, (4, -131), (1, ky + 1), TIE_SH, 1)
    # Compact dainty 2x3 knot + slender blade (with sel_out renders as a crisp 4px tie!)
    rect(d, -1, ky, 2, 3, TIE_SH)
    rect(d, -1, ky, 1, 2, TIE_HI)
    rect(d, -1, ky + 3, 2, 24, TIE)
    line(d, (0, ky + 4), (0, ky + 26), TIE_SH, 1)
    line(d, (-1, ky + 5), (-1, ky + 24), TIE_HI, 1)
    poly(d, [(-1, ky + 26), (1, ky + 26), (0, ky + 29)], TIE_SH)
    for sy in (ky + 10, ky + 18):
        line(d, (-1, sy), (0, sy + 1), TIE_HI, 1)
    return sel_out(img)


def build_tie_loose(relaxed=False):
    """Layer 5d (Outfit 4): Slender loosened royal-navy necktie hanging neatly below open V-collar."""
    img = new_char()
    d = ImageDraw.Draw(img)
    nt_hi = (112, 142, 198, 255)
    nt    = (66, 92, 148, 255)
    nt_sh = (42, 58, 104, 255)
    ky = -111 if relaxed else -117
    line(d, (-5, -131), (-1, ky + 1), nt_sh, 1)
    line(d, (5, -131), (1, ky + 1), nt_sh, 1)
    rect(d, -1, ky, 3, 3, nt_sh)
    rect(d, -1, ky, 2, 2, nt_hi)
    poly(d, [(-1, ky + 3), (1, ky + 3), (1.5, ky + 23), (0, ky + 27), (-1.5, ky + 23)], nt)
    line(d, (1, ky + 4), (1, ky + 23), nt_sh, 1)
    line(d, (-1, ky + 5), (-1, ky + 20), nt_hi, 1)
    for sy in (ky + 9, ky + 16):
        line(d, (-1, sy), (1, sy + 2), nt_hi, 1)
    return sel_out(img)


def _draw_dainty_hand(d, x, y, side):
    """Draw a slender, graceful anime hand (4x7px) with subtle inward thumb & tapered fingers (no boxy fist!)."""
    if side == -1:
        poly(d, [(x, y), (x + 3, y), (x + 4, y + 3), (x + 2, y + 7), (x, y + 6), (x - 1, y + 3)], SKIN)
        line(d, (x, y + 1), (x, y + 5), SKIN_HI, 1)
        rect(d, x + 3, y + 2, 1, 2, SKIN_SH)  # delicate thumb crease
    else:
        poly(d, [(x - 3, y), (x, y), (x + 1, y + 3), (x, y + 6), (x - 2, y + 7), (x - 4, y + 3)], SKIN)
        line(d, (x, y + 1), (x, y + 5), SKIN_SH, 1)
        rect(d, x - 4, y + 2, 1, 2, SKIN_HI)


def build_arm(outfit, side, pose="idle"):
    """Layer 6: Slender 4px anatomical anime arms & delicate open hands across all 5 outfits & poses."""
    img = new_char()
    d = ImageDraw.Draw(img)
    hoodie = (outfit == 2)
    summer = (outfit == 3)
    canon  = (outfit == 4)
    school = (outfit == 0)

    if pose == "idle":
        if hoodie:
            # Cozy oversized lavender sleeve tapering softly at ribbed cuff + peeking fingers
            if side == -1:
                poly(d, [(-11, -128), (-16, -125), (-20, -104), (-19, -84), (-14, -83), (-15, -104), (-12, -118)], HOOD)
                line(d, (-16, -123), (-19, -85), HOOD_SH, 1)
                rect(d, -19, -86, 5, 3, HOOD_D)
                rect(d, -18, -83, 4, 4, SKIN)
                rect(d, -18, -83, 1, 3, SKIN_HI)
            else:
                poly(d, [(11, -128), (16, -125), (19, -105), (17, -85), (12, -85), (14, -104), (12, -118)], HOOD)
                line(d, (16, -123), (18, -86), HOOD_SH, 1)
                rect(d, (12), -87, 5, 3, HOOD_D)
                rect(d, 13, -84, 4, 4, SKIN)
        elif summer or canon:
            # Short-sleeve (mint ringer or crisp white blouse) + slender 4px bare arm + bracelet & dainty hand!
            c_sl = MINT if summer else SHIRT
            c_sh = MINT_SH if summer else SHIRT_SH
            c_trim = WHITE if summer else SHIRT_HI
            if side == -1:
                poly(d, [(-10, -128), (-15, -126), (-17, -113), (-12, -112), (-11, -119)], c_sl)
                line(d, (-15, -125), (-17, -114), c_sh, 1)
                line(d, (-17, -113), (-12, -112), c_trim, 1)
                # Slender 4px forearm curving gently down to wrist
                poly(d, [(-16, -112), (-12, -112), (-14, -98), (-15, -85), (-18, -85), (-17, -98)], SKIN)
                line(d, (-13, -111), (-15, -86), SKIN_SH, 1)
                line(d, (-16, -110), (-18, -87), SKIN_HI, 1)
                # Signature Marin wrist bangles!
                line(d, (-18, -87), (-15, -87), PINK if summer else SILVER, 1)
                line(d, (-18, -86), (-15, -86), GOLD, 1)
                _draw_dainty_hand(d, -18, -85, -1)
            else:
                poly(d, [(10, -128), (15, -126), (17, -113), (12, -112), (11, -119)], c_sl)
                line(d, (15, -125), (17, -114), c_sh, 1)
                line(d, (12, -112), (17, -113), c_trim, 1)
                # Relaxed gentle inward contrapposto curve on right arm
                poly(d, [(12, -112), (16, -112), (17, -99), (16, -85), (13, -85), (14, -99)], SKIN)
                line(d, (16, -111), (16, -86), SKIN_SH, 1)
                line(d, (13, -110), (14, -87), SKIN_HI, 1)
                _draw_dainty_hand(d, 16, -85, 1)
        else:
            # Rolled 3/4 sleeve (School 0 / Home 1) + slender bare lower forearm & dainty hand
            sl_y = -104 if school else -101
            if side == -1:
                poly(d, [(-10, -128), (-15, -126), (-18, sl_y), (-13, sl_y + 1), (-11, -116)], SHIRT)
                line(d, (-15, -125), (-17, sl_y), SHIRT_SH, 1)
                rect(d, -18, sl_y - 1, 6, 2, SHIRT_HI)
                poly(d, [(-17, sl_y + 1), (-13, sl_y + 1), (-15, -85), (-18, -85)], SKIN)
                line(d, (-14, sl_y + 2), (-15, -86), SKIN_SH, 1)
                line(d, (-18, -87), (-15, -87), SILVER, 1)
                _draw_dainty_hand(d, -18, -85, -1)
            else:
                poly(d, [(10, -128), (15, -126), (18, sl_y), (13, sl_y + 1), (11, -116)], SHIRT)
                line(d, (15, -125), (17, sl_y), SHIRT_SH, 1)
                rect(d, 13, sl_y - 1, 6, 2, SHIRT_HI)
                poly(d, [(13, sl_y + 1), (17, sl_y + 1), (16, -85), (13, -85)], SKIN)
                line(d, (16, sl_y + 2), (16, -86), SKIN_SH, 1)
                _draw_dainty_hand(d, 16, -85, 1)

    elif pose == "wave":
        c_main = HOOD if hoodie else (MINT if summer else SHIRT)
        c_hi = HOOD_HI if hoodie else (WHITE if summer else SHIRT_HI)
        poly(d, [(10, -128), (16, -130), (22, -141), (18, -145), (12, -136)], c_main)
        line(d, (18, -145), (22, -141), c_hi, 2)
        poly(d, [(19, -144), (23, -142), (27, -162), (23, -163)], HOOD if hoodie else SKIN)
        # Cute open waving palm
        ell(d, 23, -170, 6, 8, SKIN)
        line(d, (24, -169), (24, -164), SKIN_HI, 1)

    elif pose == "collar":
        s = side
        c_main = HOOD if hoodie else (MINT if summer else SHIRT)
        poly(d, [(s * 10, -128), (s * 16, -126), (s * 19, -112), (s * 13, -112), (s * 11, -118)], c_main)
        poly(d, [(s * 14, -112), (s * 18, -113), (s * 10, -122), (s * 4, -125), (s * 4, -121), (s * 12, -115)],
             HOOD if hoodie else SKIN)
        ell(d, (1 if s == 1 else -6), -126, 5, 5, SKIN)

    elif pose == "stretch":
        s = side
        c_main = HOOD if hoodie else (MINT if summer else SHIRT)
        c_hi = HOOD_HI if hoodie else (WHITE if summer else SHIRT_HI)
        # Graceful outward elbow curve framing the head so arms & hands are 100% visible!
        poly(d, [(s * 10, -128), (s * 16, -130), (s * 24, -145), (s * 19, -149), (s * 12, -136)], c_main)
        line(d, (s * 19, -149), (s * 24, -145), c_hi, 2)
        poly(d, [(s * 20, -148), (s * 24, -146), (s * 22, -173), (s * 18, -174)], HOOD if hoodie else SKIN)
        ell(d, (17 if s == 1 else -22), -180, 5, 7, SKIN)
        line(d, (s * 19, -178), (s * 19, -174), SKIN_HI, 1)

    elif pose == "manga":
        s = side
        c_main = HOOD if hoodie else (MINT if summer else SHIRT)
        c_sh = HOOD_SH if hoodie else (MINT_SH if summer else SHIRT_SH)
        poly(d, [(s * 10, -128), (s * 16, -125), (s * 18, -107), (s * 13, -107), (s * 11, -118)], c_main)
        line(d, (s * 16, -124), (s * 18, -108), c_sh, 1)
        poly(d, [(s * 18, -108), (s * 13, -108), (s * 12, -97), (s * 17, -96)], HOOD if hoodie else SKIN)
        ell(d, (10 if s == 1 else -15), -102, 5, 6, SKIN)
        # Cute dainty fingers visibly gripping the manga cover edges!
        for fy in (-101, -99, -97):
            rect(d, (10 if s == 1 else -12), fy, 2, 1, SKIN_HI)

    elif pose == "manga_turn":
        c_main = HOOD if hoodie else (MINT if summer else SHIRT)
        poly(d, [(10, -128), (16, -125), (18, -108), (13, -108), (11, -118)], c_main)
        poly(d, [(17, -109), (13, -109), (6, -113), (7, -109), (15, -105)], HOOD if hoodie else SKIN)
        ell(d, 3, -115, 5, 5, SKIN)

    elif pose == "phone":
        c_main = HOOD if hoodie else (MINT if summer else SHIRT)
        poly(d, [(10, -128), (16, -126), (18, -110), (13, -110), (11, -118)], c_main)
        poly(d, [(14, -110), (18, -110), (12, -104), (6, -106), (6, -102), (13, -101)], HOOD if hoodie else SKIN)
        rect(d, 1, -116, 9, 14, (244, 134, 168, 255))
        rect(d, 2, -114, 7, 10, (186, 238, 255, 255))
        rect(d, 3, -113, 3, 2, WHITE)
        ell(d, 4, -108, 5, 5, SKIN)

    return sel_out(img)


def build_head_base():
    """Layer 4 base: Slender neck + thin canon choker with tiny silver ring + soft compact anime oval & dainty earrings."""
    img = new_char()
    d = ImageDraw.Draw(img)

    # Slender graceful neck (-143..-132) with warm rosy under-chin shadow
    poly(d, [(-3, -144), (3, -144), (3.5, -132), (-3.5, -132)], SKIN)
    poly(d, [(-3, -143), (3, -143), (3, -139), (0, -138), (-3, -139)], SKIN_SH)
    # Thin 2px canon black choker + dainty silver ring glint
    rect(d, -3, -138, 7, 2, CHOKER)
    rect(d, -1, -136, 3, 3, SILVER_D)
    rect(d, 0, -136, 1, 2, WHITE)

    # Neatly tucked ears aligned with eyes
    ell(d, -16, -157, 3, 6, SKIN)
    ell(d, 13, -157, 3, 6, SKIN)

    # Soft, graceful compact anime oval (~30px wide x 42px tall) with delicate short chin at y=-140
    head_pts = (
        bezier((-15, -162), (-14.5, -150), (-8, -143), 12) +
        bezier((-8, -143), (0, -140), (8, -143), 12) +
        bezier((8, -143), (14.5, -150), (15, -162), 12) +
        bezier((15, -162), (14, -180), (0, -182), 12) +
        bezier((0, -182), (-14, -180), (-15, -162), 12)
    )
    poly(d, head_pts, SKIN)
    # Hue-shifted rosy-peach side cheek & forehead bang shadow + porcelain left cheek highlight
    poly(d, [(11, -163), (15, -161), (13, -150), (8, -143), (7, -145), (11, -153)], SKIN_SH)
    rect(d, -13, -170, 26, 4, SKIN_SH)
    line(d, (-11, -151), (-8, -146), SKIN_HI, 1)

    out = sel_out(img)
    # Paint dainty 1-2px silver earring glints AFTER sel_out so they stay razor-sharp!
    od = ImageDraw.Draw(out)
    od.rectangle([OX - 16, OY - 152, OX - 15, OY - 151], fill=SILVER)
    od.point((OX - 16, OY - 152), fill=WHITE)
    od.rectangle([OX + 14, OY - 152, OX + 15, OY - 151], fill=SILVER)
    od.point((OX + 15, OY - 152), fill=WHITE)
    return out


def draw_almond_eye(d, cx, cy, side, wide=False):
    """Canon Marin expressive anime eye: warm plum winged lashes, anti-aliased tips & soft lower lid."""
    s = side
    h = 10 if wide else 9
    in_x = cx - s * 4
    out_x = cx + s * 4
    sclera = [
        (in_x, cy),
        (cx - s * 2, cy - h // 2),
        (cx + s * 2, cy - h // 2),
        (out_x, cy - 1),
        (cx + s * 2, cy + h // 2 - 1),
        (cx - s * 2, cy + h // 2 - 1),
    ]
    poly(d, sclera, WHITE)
    line(d, (cx - s * 2, cy - h // 2), (cx + s * 2, cy - h // 2), (232, 224, 240, 255), 1)

    # Rich plum-brown upper lash arch + delicate winged outer lash + soft anti-aliased outer pixel
    line(d, (in_x, cy - 1), (cx - s * 2, cy - h // 2 - 1), LASH_SFT, 1)
    line(d, (cx - s * 2, cy - h // 2 - 1), (cx + s * 2, cy - h // 2 - 1), LASH, 2)
    line(d, (cx + s * 2, cy - h // 2 - 1), (out_x + s * 1, cy - 1), LASH, 2)
    rect(d, out_x + s * 2, cy - 3, 1, 1, LASH)
    rect(d, out_x + s * 2, cy - 2, 1, 1, LASH_SFT)
    # Soft warm double-eyelid & subtle lower-outer lash accent
    line(d, (cx - s * 2, cy - h // 2 - 3), (cx + s * 2, cy - h // 2 - 3), SKIN_D, 1)
    line(d, (cx + s * 1, cy + h // 2), (cx + s * 3, cy + h // 2 - 1), SKIN_D, 1)


def build_iris():
    """Luminous 9x9 Marin iris: deep berry -> crimson-magenta -> rose-pink + glowing crescent & DOUBLE white sparkles!"""
    img = Image.new("RGBA", (9, 9), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([1, 1, 7, 7], fill=EYE_MID)
    arr = np.array(img, dtype=np.uint8)
    for y in range(1, 8):
        f = (y - 1) / 6.0
        col = lerp_c(EYE_TOP, EYE_MID, f * 2) if f < 0.5 else lerp_c(EYE_MID, EYE_BOT, (f - 0.5) * 2)
        for x in range(1, 8):
            if arr[y, x, 3] > 0:
                arr[y, x] = col
    arr[4:6, 4:6] = (64, 18, 48, 255)
    arr[7, 3:6] = EYE_GLOW
    arr[6, 2] = EYE_GLOW
    arr[6, 6] = EYE_GLOW
    arr[2:4, 2:4] = WHITE
    arr[2, 4] = (255, 240, 248, 255)
    arr[5, 6] = WHITE
    arr[6, 5] = (255, 236, 246, 255)
    return Image.fromarray(arr, "RGBA")


def build_face(emotion):
    """Layer 4 emotion overlay: 10 expressive VN-quality faces (incl. playful blushing wink!) + blink."""
    img = new_char()
    d = ImageDraw.Draw(img)

    # Soft rosy blush strictly UNDER outer eye corners (-12..-7 & +7..+12 at y=-149)
    if emotion in ("blush", "flustered"):
        bl = (255, 118, 150, 195)
        ell(d, -12, -150, 6, 3, bl)
        ell(d, 6, -150, 6, 3, bl)
        for bx in (-11, -9, 8, 10):
            line(d, (bx, -149), (bx + 1, -148), (236, 86, 118, 200), 1)
    elif emotion == "romantic":
        bl = (255, 136, 164, 165)
        ell(d, -12, -150, 6, 3, bl)
        ell(d, 6, -150, 6, 3, bl)
        line(d, (-10, -149), (-9, -148), (242, 106, 136, 170), 1)
        line(d, (9, -149), (10, -148), (242, 106, 136, 170), 1)
    elif emotion == "pout":
        bl = (252, 138, 162, 165)
        ell(d, -12, -149, 5, 3, bl)
        ell(d, 7, -149, 5, 3, bl)
    else:
        blush_a = 165 if emotion in ("pet", "starry", "smug") else 120
        bl = (255, 148, 172, blush_a)
        ell(d, -12, -149, 5, 3, bl)
        ell(d, 7, -149, 5, 3, bl)
        if emotion in ("pet", "starry", "normal"):
            line(d, (-10, -148), (-9, -147), (246, 118, 144, 145), 1)
            line(d, (9, -148), (10, -147), (246, 118, 144, 145), 1)

    # Eyebrows
    if emotion == "pout":
        line(d, (-12, -162), (-5, -159), BROW, 1)
        line(d, (5, -159), (12, -162), BROW, 1)
    elif emotion in ("flustered", "romantic"):
        line(d, (-12, -160), (-5, -162), BROW, 1)
        line(d, (5, -162), (12, -160), BROW, 1)
    elif emotion == "surprised":
        line(d, (-12, -163), (-5, -164), BROW, 1)
        line(d, (5, -164), (12, -163), BROW, 1)
    else:
        line(d, (-12, -160), (-5, -161), BROW, 1)
        line(d, (5, -161), (12, -160), BROW, 1)

    # Eyes (cx = ±8, y = -154)
    if emotion in ("normal", "flustered", "pout"):
        draw_almond_eye(d, -8, -154, -1, wide=False)
        draw_almond_eye(d, 8, -154, 1, wide=False)
    elif emotion == "blush":
        # Signature playful blushing Marin WINK: unmistakable happy '>' lash on viewer-left, sparkling open right eye!
        line(d, (-11, -156), (-5, -154), LASH, 2)
        line(d, (-5, -154), (-11, -151), LASH, 2)
        rect(d, -12, -156, 1, 1, LASH_SFT)
        draw_almond_eye(d, 8, -154, 1, wide=False)
    elif emotion == "romantic":
        draw_almond_eye(d, -8, -154, -1, wide=False)
        draw_almond_eye(d, 8, -154, 1, wide=False)
        rect(d, -13, -158, 10, 2, SKIN)
        rect(d, 3, -158, 10, 2, SKIN)
        line(d, (-13, -156), (-4, -156), LASH, 2)
        line(d, (4, -156), (13, -156), LASH, 2)
    elif emotion == "surprised":
        draw_almond_eye(d, -8, -154, -1, wide=True)
        draw_almond_eye(d, 8, -154, 1, wide=True)
    elif emotion == "smug":
        draw_almond_eye(d, -8, -154, -1, wide=False)
        draw_almond_eye(d, 8, -154, 1, wide=False)
        rect(d, -13, -158, 10, 3, SKIN)
        rect(d, 3, -158, 10, 3, SKIN)
        line(d, (-13, -155), (-4, -155), LASH, 2)
        line(d, (4, -155), (13, -155), LASH, 2)
    elif emotion == "starry":
        draw_almond_eye(d, -8, -154, -1, wide=True)
        draw_almond_eye(d, 8, -154, 1, wide=True)
        for cx in (-8, 8):
            ell(d, cx - 3, -157, 6, 6, EYE_MID)
            rect(d, cx - 1, -156, 2, 4, (255, 240, 120, 255))
            rect(d, cx - 2, -155, 4, 2, (255, 240, 120, 255))
            rect(d, cx, -155, 1, 1, WHITE)
    elif emotion == "sleepy":
        for cx in (-8, 8):
            rect(d, cx - 4, -154, 8, 3, WHITE)
            rect(d, cx - 2, -154, 4, 2, EYE_MID)
            line(d, (cx - 4, -154), (cx + 4, -154), LASH, 2)
    elif emotion == "pet":
        for cx in (-8, 8):
            pts = bezier((cx - 4, -153), (cx, -158), (cx + 4, -153), 10)
            for i in range(len(pts) - 1):
                line(d, pts[i], pts[i + 1], LASH, 2)
    elif emotion == "blink":
        for cx in (-8, 8):
            pts = bezier((cx - 4, -154), (cx, -152), (cx + 4, -154), 10)
            for i in range(len(pts) - 1):
                line(d, pts[i], pts[i + 1], LASH, 2)

    # Delicate nose dot
    rect(d, 0, -149, 1, 1, SKIN_D)

    # Expressive cute anime mouths (y = -146..-145, right below eyes!)
    if emotion == "normal":
        line(d, (-3, -146), (-1, -145), MOUTH_C, 1)
        line(d, (-1, -145), (1, -145), MOUTH_C, 1)
        line(d, (1, -145), (3, -146), MOUTH_C, 1)
    elif emotion == "pet":
        # Happy open beaming smile!
        poly(d, [(-3, -146), (3, -146), (2, -144), (-2, -144)], MOUTH_IN)
        line(d, (-3, -146), (3, -146), MOUTH_C, 1)
    elif emotion == "blush":
        # Playful cat-smile (:3) matching the blushing wink!
        line(d, (-3, -146), (-1, -145), MOUTH_C, 1)
        line(d, (-1, -145), (0, -146), MOUTH_C, 1)
        line(d, (0, -146), (2, -145), MOUTH_C, 1)
        line(d, (2, -145), (3, -146), MOUTH_C, 1)
    elif emotion == "romantic":
        line(d, (-3, -146), (-1, -145), MOUTH_C, 1)
        line(d, (-1, -145), (1, -145), MOUTH_C, 1)
        line(d, (1, -145), (3, -147), MOUTH_C, 1)
    elif emotion == "flustered":
        for x, y in ((-3, -146), (-2, -147), (-1, -146), (0, -145), (1, -146), (2, -147), (3, -146)):
            rect(d, x, y, 1, 1, MOUTH_C)
        rect(d, 13, -163, 2, 2, PINK)
        rect(d, 16, -163, 2, 2, PINK)
        rect(d, 13, -161, 5, 2, PINK)
        rect(d, 14, -159, 3, 1, PINK)
        rect(d, 15, -158, 1, 1, PINK)
    elif emotion == "smug":
        line(d, (-3, -146), (0, -145), MOUTH_C, 1)
        line(d, (0, -145), (2, -145), MOUTH_C, 1)
        line(d, (2, -145), (4, -147), MOUTH_C, 1)
    elif emotion == "surprised":
        ell(d, -2, -147, 4, 4, MOUTH_IN)
        d.ellipse([OX - 2, OY - 147, OX + 2, OY - 143], outline=MOUTH_C)
    elif emotion == "sleepy":
        ell(d, -2, -147, 4, 4, MOUTH_IN)
        d.ellipse([OX - 2, OY - 147, OX + 2, OY - 143], outline=MOUTH_C)
    elif emotion == "pout":
        line(d, (-2, -146), (0, -147), MOUTH_C, 1)
        line(d, (0, -147), (2, -146), MOUTH_C, 1)
        line(d, (-10, -147), (-10, -145), SKIN_D, 1)
        line(d, (10, -147), (10, -145), SKIN_D, 1)
    elif emotion == "starry":
        poly(d, [(-3, -147), (3, -147), (2, -143), (-2, -143)], MOUTH_IN)
        line(d, (-3, -147), (3, -147), MOUTH_C, 1)
        line(d, (-2, -143), (2, -143), MOUTH_C, 1)
        rect(d, 2, -146, 1, 1, WHITE)  # cute little anime fang glint!
    elif emotion == "blink":
        line(d, (-3, -146), (-1, -145), MOUTH_C, 1)
        line(d, (-1, -145), (1, -145), MOUTH_C, 1)
        line(d, (1, -145), (3, -146), MOUTH_C, 1)

    return img


def build_hair_back():
    """Layer 5a: Voluminous S-wavy long flowing hair separated into layered ribbon-locks (zero triangle tent!)."""
    img = new_char()
    d = ImageDraw.Draw(img)

    # Organic S-wave silhouette: rounds around head, tucks gently at neck (-138), swells in soft waves (-106), tapers into 7 locks!
    left_s = (
        bezier((-17, -172), (-21, -154), (-18, -138), 10) +
        bezier((-18, -138), (-26, -112), (-24, -84), 14)
    )
    bottom_locks = [
        (-24, -84), (-21, -74), (-17, -86),
        (-15, -72), (-10, -84),
        (-7, -75), (0, -83), (7, -75),
        (10, -84), (15, -72),
        (17, -86), (21, -74), (24, -84),
    ]
    right_s = (
        bezier((24, -84), (26, -112), (18, -138), 14) +
        bezier((18, -138), (21, -154), (17, -172), 10)
    )
    top_arc = bezier((17, -172), (0, -187), (-17, -172), 12)
    poly(d, left_s + bottom_locks + right_s + top_arc, HAIR)

    # Deep honey-amber inner neck/back shade so torso & neck pop crisply against hair!
    poly(d, [(-13, -152), (13, -152), (16, -86), (-16, -86)], HAIR_SH)
    poly(d, [(-10, -144), (10, -144), (12, -90), (-12, -90)], HAIR_D)

    # Curved sunlit ribbon highlights & warm shadow valleys along outer flowing waves
    for s in (-1, 1):
        w_hi = bezier((s * 17, -144), (s * 22, -114), (s * 19, -82), 12)
        w_sh = bezier((s * 15, -136), (s * 19, -110), (s * 15, -78), 12)
        for i in range(len(w_hi) - 1):
            line(d, w_hi[i], w_hi[i + 1], HAIR_HI, 2)
            line(d, w_sh[i], w_sh[i + 1], HAIR_SH, 1)

    img = hair_gradient_fill(img, OY - 160, OY - 72, pink_start=0.46, steps=10)
    return sel_out(img)


def build_hair_side(side):
    """Layer 5b/5c: Sleek cheek-framing S-wave front locks (leaves sloped shoulders & sleeves cleanly visible!)."""
    img = new_char()
    d = ImageDraw.Draw(img)
    s = side

    # Hugs cheek & drapes delicately over front collarbone with split coral-pink tips
    outer = bezier((s * 15, -173), (s * 16, -145), (s * 13, -105), 14)
    split_tips = [
        (s * 13, -105), (s * 15, -98), (s * 12, -102),
        (s * 11, -91), (s * 9, -106)
    ]
    inner = bezier((s * 9, -106), (s * 13, -144), (s * 11, -169), 14)
    poly(d, outer + split_tips + inner, HAIR)

    sh = bezier((s * 11, -164), (s * 13, -142), (s * 10, -102), 12)
    hi = bezier((s * 14, -164), (s * 15, -142), (s * 12, -110), 12)
    for i in range(len(sh) - 1):
        line(d, sh[i], sh[i + 1], HAIR_SH, 1)
        line(d, hi[i], hi[i + 1], HAIR_HI, 1)
    shine = bezier((s * 14, -160), (s * 15, -152), (s * 14, -146), 6)
    for i in range(len(shine) - 1):
        line(d, shine[i], shine[i + 1], HAIR_SHINE, 1)

    img = hair_gradient_fill(img, OY - 162, OY - 91, pink_start=0.48, steps=10)
    return sel_out(img)


def build_hair_bangs():
    """Layer 4 top: Canon Marin overlapping soft bangs with signature center forelock & curved angel halo (zero comb slots!)."""
    img = new_char()
    d = ImageDraw.Draw(img)

    # Smooth continuous anime bang curtain with canon center forelock dipping between eyes & clear arches over eyes!
    crown_top = (
        bezier((-17, -161), (-19, -182), (-2, -185), 12) +
        [(-2, -184), (0, -185)] +
        bezier((0, -185), (19, -182), (17, -161), 12)
    )
    bang_tips = [
        (17, -161),
        (14, -157),   # soft right temple lock tip
        (11, -161),   # arched cleanly above right eye!
        (6, -161),
        (4, -158),    # soft inner-right wisp
        (2, -160),
        (0, -155),    # Marin's signature delicate center forelock between her eyes!
        (-2, -160),
        (-5, -158),   # soft inner-left wisp
        (-7, -161),
        (-11, -161),  # arched cleanly above left eye!
        (-14, -157),  # soft left temple lock tip
        (-17, -161),
    ]
    poly(d, crown_top + bang_tips, HAIR)

    # Soft honey-amber internal strand curves (painted INSIDE the blonde volume so zero harsh dark comb slots!)
    for p0, p1 in (
        ((-12, -172), (-13, -160)),
        ((-6, -173), (-5, -160)),
        ((-1, -174), (0, -157)),
        ((5, -173), (4, -160)),
        ((12, -172), (13, -160)),
    ):
        line(d, p0, p1, HAIR_SH, 1)
    line(d, (-2, -184), (-1, -174), HAIR_SH, 1)

    # Signature curved anime angel-halo shine across upper volume!
    halo = bezier((-12, -174), (0, -179), (12, -174), 12)
    for i in range(len(halo) - 1):
        if i != 5:
            line(d, halo[i], halo[i + 1], HAIR_HI, 2)
    for hx, hy in ((-8, -176), (-7, -176), (-6, -177), (4, -177), (5, -176), (6, -176)):
        rect(d, hx, hy, 1, 1, HAIR_SHINE)

    return sel_out(img)


# ------------------------------------------------------------------ 640x360 room renderer
def make_lamp_glow(center, radius):
    y, x = np.ogrid[:VH, :VW]
    dist = np.sqrt((x - center[0]) ** 2 + ((y - center[1]) * 1.12) ** 2)
    f = np.clip(1.0 - dist / radius, 0.0, 1.0)
    a = (f ** 1.85) * 165.0
    arr = np.zeros((VH, VW, 4), dtype=np.uint8)
    arr[:, :, 0] = 255
    arr[:, :, 1] = np.clip(198 + 42 * f, 0, 255).astype(np.uint8)
    arr[:, :, 2] = np.clip(112 + 60 * f, 0, 255).astype(np.uint8)
    arr[:, :, 3] = np.clip(a, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def draw_sky_pil(d, mode):
    x0, y0, w, h = 266, 62, 108, 100
    palettes = [
        ((106, 174, 240), (186, 224, 252)),
        ((82, 58, 132), (252, 174, 104)),
        ((14, 18, 46), (42, 42, 86)),
    ]
    top, bot = palettes[mode]
    for y in range(h):
        f = y / (h - 1)
        if mode == 1:
            mid = (232, 114, 118)
            c = lerp_c(top + (255,), mid + (255,), f * 2) if f < 0.5 else lerp_c(mid + (255,), bot + (255,), (f - 0.5) * 2)
        else:
            c = lerp_c(top + (255,), bot + (255,), f)
        d.line([(x0, y0 + y), (x0 + w - 1, y0 + y)], fill=c[:3])

    if mode == 0:
        for cx, cy, cw, ch in ((276, 80, 30, 8), (324, 100, 36, 9), (288, 128, 24, 7)):
            d.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=4, fill=(252, 252, 255))
            d.rounded_rectangle([cx + 6, cy - 5, cx + cw - 6, cy + 3], radius=3, fill=(255, 255, 255))
    elif mode == 1:
        d.ellipse([322, 134, 354, 166], fill=(255, 228, 144))
        d.rectangle([x0, 152, x0 + w, y0 + h], fill=(134, 72, 106))
    else:
        rnd = random.Random(11)
        for _ in range(28):
            sx, sy = rnd.randint(x0 + 2, x0 + w - 3), rnd.randint(y0 + 2, y0 + h - 14)
            col = (255, 250, 210) if rnd.random() > 0.4 else (190, 210, 255)
            d.rectangle([sx, sy, sx + 1, sy + 1], fill=col)
        d.ellipse([338, 76, 358, 96], fill=(252, 246, 206))
        d.ellipse([343, 73, 361, 91], fill=top)

    d.rectangle([318, y0, 322, y0 + h], fill=(230, 220, 206))
    d.rectangle([x0, 110, x0 + w, 114], fill=(230, 220, 206))
    d.rectangle([318, y0, 319, y0 + h], fill=(186, 172, 156))
    d.rectangle([x0, 113, x0 + w, 114], fill=(186, 172, 156))


def build_room(mode, wardrobe_open=False):
    img = Image.new("RGBA", (VW, VH), (218, 184, 146, 255))
    d = ImageDraw.Draw(img)
    OUT = (54, 36, 44)

    for y in range(240):
        f = y / 240.0
        c = lerp_c((194, 158, 122, 255), (222, 188, 150, 255), f)
        d.line([(0, y), (VW, y)], fill=c[:3])

    d.rectangle([0, 0, VW, 16], fill=(176, 138, 106))
    d.line([(0, 16), (VW, 16)], fill=(142, 108, 82), width=2)
    d.line([(0, 18), (184, 32)], fill=(166, 130, 98), width=2)
    d.line([(VW, 18), (476, 32)], fill=(166, 130, 98), width=2)
    d.line([(184, 32), (476, 32)], fill=(166, 130, 98), width=1)
    d.line([(184, 32), (184, 240)], fill=(178, 142, 110), width=1)
    d.line([(476, 32), (476, 240)], fill=(178, 142, 110), width=1)

    d.rectangle([0, 240, VW, VH], fill=(156, 102, 66))
    plank_ys = [240, 252, 266, 282, 300, 320, 342, 360]
    for i in range(len(plank_ys) - 1):
        y0, y1 = plank_ys[i], plank_ys[i + 1]
        tone = (162, 106, 68) if i % 2 == 0 else (150, 96, 62)
        d.rectangle([0, y0, VW, y1], fill=tone)
        d.line([(0, y0), (VW, y0)], fill=(110, 68, 44), width=1)
        d.line([(0, y0 + 1), (VW, y0 + 1)], fill=(178, 120, 80), width=1)
        step = 76 + i * 12
        for x in range((i * 41) % step, VW, step):
            d.line([(x, y0), (x, y1)], fill=(110, 68, 44), width=1)

    d.rectangle([0, 232, VW, 240], fill=(122, 80, 54))
    d.line([(0, 232), (VW, 232)], fill=(154, 108, 76), width=1)
    d.line([(0, 240), (VW, 240)], fill=(86, 54, 36), width=1)

    sh = Image.new("RGBA", (VW, VH), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.polygon([(26, 262), (156, 262), (170, 274), (16, 274)], fill=(38, 22, 24, 90))
    sd.ellipse([156, 258, 212, 270], fill=(38, 22, 24, 80))
    sd.rectangle([386, 260, 550, 272], fill=(38, 22, 24, 105))
    sd.polygon([(568, 282), (636, 282), (636, 294), (558, 294)], fill=(38, 22, 24, 100))
    img.alpha_composite(sh)
    d = ImageDraw.Draw(img)

    # Poster cleanly between wardrobe & left curtain
    d.rectangle([176, 72, 224, 138], fill=(112, 96, 146), outline=OUT, width=2)
    d.rectangle([182, 78, 218, 83], fill=(236, 220, 244))
    d.ellipse([190, 92, 210, 114], fill=(64, 46, 58))
    d.ellipse([193, 96, 206, 110], fill=(238, 198, 172))
    d.polygon([(186, 136), (191, 114), (209, 114), (214, 136)], fill=(72, 52, 66))

    # Window & curtains
    d.rectangle([226, 48, 414, 52], fill=(96, 66, 46), outline=OUT)
    d.ellipse([221, 45, 229, 55], fill=(74, 48, 34), outline=OUT)
    d.ellipse([411, 45, 419, 55], fill=(74, 48, 34), outline=OUT)
    d.rectangle([258, 58, 382, 166], fill=(230, 220, 206), outline=OUT, width=2)
    draw_sky_pil(d, mode)
    d.rectangle([252, 164, 388, 171], fill=(238, 230, 218), outline=OUT)
    for cx in (234, 370):
        d.rectangle([cx, 52, cx + 36, 182], fill=(208, 162, 114), outline=OUT, width=1)
        for fx in (6, 14, 22, 30):
            d.line([(cx + fx, 54), (cx + fx, 180)], fill=(172, 126, 84), width=2)
            d.line([(cx + fx + 2, 54), (cx + fx + 2, 180)], fill=(230, 190, 144), width=1)
        d.line([(cx, 180), (cx + 36, 180)], fill=(146, 102, 68), width=2)

    # Wardrobe
    WD, WDL, WDD = (142, 86, 58), (168, 108, 74), (108, 64, 42)
    d.rectangle([26, 38, 154, 264], fill=WD, outline=OUT, width=2)
    d.rectangle([28, 40, 152, 49], fill=WDD)
    d.line([(28, 40), (152, 40)], fill=WDL, width=2)
    if not wardrobe_open:
        for dx in (34, 92):
            d.rectangle([dx, 54, dx + 54, 254], fill=WD, outline=OUT, width=1)
            d.line([(dx + 1, 55), (dx + 1, 253)], fill=WDL, width=2)
            d.rectangle([dx + 8, 64, dx + 46, 144], fill=WDD, outline=(92, 54, 36))
            d.rectangle([dx + 11, 67, dx + 43, 141], fill=WD)
            d.rectangle([dx + 8, 156, dx + 46, 242], fill=WDD, outline=(92, 54, 36))
            d.rectangle([dx + 11, 159, dx + 43, 239], fill=WD)
        d.rectangle([78, 134, 83, 154], fill=(210, 214, 226), outline=OUT)
        d.rectangle([97, 134, 102, 154], fill=(210, 214, 226), outline=OUT)
        d.rectangle([71, 141, 83, 145], fill=(180, 184, 198), outline=OUT)
        d.rectangle([97, 141, 109, 145], fill=(180, 184, 198), outline=OUT)
    else:
        d.rectangle([34, 54, 146, 254], fill=(56, 34, 28), outline=OUT)
        d.line([(36, 68), (144, 68)], fill=(200, 204, 218), width=2)
        clothes = [(244, 242, 240), (50, 54, 80), (242, 148, 176), (120, 162, 204), (244, 242, 240), (96, 74, 118)]
        for i, c in enumerate(clothes):
            cx = 42 + i * 16
            d.rectangle([cx, 70, cx + 12, 128 + (i % 2) * 14], fill=c, outline=OUT)
        d.rectangle([34, 204, 146, 210], fill=(96, 62, 44))
        d.rectangle([18, 52, 34, 256], fill=WD, outline=OUT, width=2)
        d.rectangle([146, 52, 162, 256], fill=WD, outline=OUT, width=2)

    # Laundry basket
    d.rectangle([162, 228, 208, 262], fill=(176, 136, 94), outline=OUT, width=2)
    for x in range(168, 206, 6):
        d.line([(x, 230), (x, 260)], fill=(142, 106, 70), width=1)
    d.rounded_rectangle([166, 220, 186, 232], radius=4, fill=(92, 116, 152), outline=OUT)
    d.rounded_rectangle([180, 218, 202, 232], radius=4, fill=(238, 162, 184), outline=OUT)

    # Bed
    d.rectangle([528, 146, 586, 250], fill=(152, 98, 64), outline=OUT, width=2)
    d.rectangle([534, 154, 580, 236], fill=(124, 78, 50))
    d.rectangle([388, 204, 548, 264], fill=(148, 94, 62), outline=OUT, width=2)
    d.rectangle([390, 246, 546, 258], fill=(116, 70, 44))
    d.rectangle([390, 204, 546, 228], fill=(242, 232, 218), outline=OUT)
    d.rounded_rectangle([388, 198, 506, 236], radius=4, fill=(214, 184, 150), outline=OUT, width=2)
    d.line([(392, 202), (502, 202)], fill=(238, 214, 182), width=2)
    d.line([(392, 232), (502, 232)], fill=(182, 150, 118), width=2)
    d.rounded_rectangle([490, 182, 532, 206], radius=6, fill=(232, 200, 168), outline=OUT, width=2)
    d.rounded_rectangle([514, 174, 548, 202], radius=6, fill=(238, 172, 140), outline=OUT, width=2)

    # Nightstand & Lamp
    d.rectangle([572, 192, 638, 286], fill=(146, 90, 58), outline=OUT, width=2)
    d.rectangle([570, 188, 640, 198], fill=(172, 112, 72), outline=OUT, width=2)
    for dy in (204, 240):
        d.rectangle([580, dy, 632, dy + 30], fill=(158, 100, 66), outline=(104, 62, 40), width=2)
        d.rectangle([602, dy + 12, 610, dy + 17], fill=(210, 214, 226), outline=OUT)

    d.rounded_rectangle([594, 182, 618, 190], radius=2, fill=(182, 150, 110), outline=OUT)
    d.rectangle([604, 168, 608, 183], fill=(156, 124, 90), outline=OUT)
    shade_col = (255, 242, 182) if mode == 2 else (238, 220, 190)
    d.polygon([(590, 146), (622, 146), (630, 172), (582, 172)], fill=shade_col, outline=OUT)
    d.line([(586, 170), (626, 170)], fill=(255, 252, 228) if mode == 2 else (210, 190, 160), width=2)

    # Rug & floor manga (removed stray bottom-right grey cushion artifact!)
    d.ellipse([172, 304, 476, 356], fill=(138, 96, 86), outline=OUT)
    d.ellipse([178, 308, 470, 352], fill=(182, 136, 118))
    d.ellipse([204, 314, 444, 346], outline=(158, 112, 98), width=2)
    d.rectangle([216, 274, 244, 286], fill=(124, 72, 92), outline=OUT, width=1)
    d.line([(218, 283), (242, 283)], fill=(244, 240, 232), width=2)

    # Lighting atmosphere (lamp glow & daylight shafts are composited dynamically at runtime!)
    if mode == 1:
        img.alpha_composite(Image.new("RGBA", (VW, VH), (255, 168, 112, 42)))
    elif mode == 2:
        arr = np.array(img, dtype=np.float32)
        arr[:, :, 0] *= 0.44
        arr[:, :, 1] *= 0.40
        arr[:, :, 2] *= 0.58
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
        draw_sky_pil(ImageDraw.Draw(img), 2)

    return img


def build_pillow():
    """Interactive throwable coral-pink plush pillow (46x24)."""
    img = Image.new("RGBA", (48, 26), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([3, 4, 44, 21], radius=7, fill=(224, 148, 138, 255))
    d.rounded_rectangle([5, 5, 42, 11], radius=4, fill=(246, 178, 166, 255))
    d.rounded_rectangle([5, 16, 42, 20], radius=3, fill=(186, 112, 108, 255))
    # Cute stitched corner tufts & crease
    d.line([(12, 11), (36, 11)], fill=(202, 126, 120, 255), width=1)
    return sel_out(img)


def build_boba():
    """Interactive bubble-tea cup (22x30) sitting on nightstand."""
    img = Image.new("RGBA", (22, 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Wide pink straw
    d.rectangle([10, 2, 13, 12], fill=(244, 128, 158, 255))
    d.rectangle([10, 2, 11, 11], fill=(255, 188, 208, 255))
    # Clear dome lid
    d.pieslice([4, 7, 17, 16], 180, 360, fill=(236, 242, 252, 230))
    d.rectangle([3, 11, 18, 13], fill=(255, 255, 255, 255))
    # Milk tea body
    d.polygon([(5, 13), (16, 13), (15, 27), (6, 27)], fill=(236, 198, 156, 255))
    d.polygon([(6, 14), (9, 14), (8, 26), (6, 26)], fill=(250, 224, 190, 255))
    # Tapioca pearls at bottom
    for px, py in ((7, 24), (10, 25), (13, 24), (9, 22), (12, 22)):
        d.ellipse([px, py, px + 2, py + 2], fill=(56, 36, 44, 255))
    return sel_out(img)


def build_curtain_panel(w=86, h=132):
    """Pleated warm-beige curtain panel (for smooth sliding open/closed animation)."""
    OUT = (54, 36, 44, 255)
    img = Image.new("RGBA", (w, h), (208, 162, 114, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], outline=OUT, width=1)
    for fx in range(8, w - 4, 12):
        d.line([(fx, 2), (fx, h - 3)], fill=(170, 124, 82, 255), width=2)
        d.line([(fx + 3, 2), (fx + 3, h - 3)], fill=(232, 192, 146, 255), width=2)
    d.line([(1, h - 3), (w - 2, h - 3)], fill=(144, 100, 66, 255), width=2)
    return img


def build_poster(idx):
    """3 detailed 16-bit anime cover / cosplay silhouette / cosmos posters (48x66)."""
    OUT = (54, 36, 44, 255)
    img = Image.new("RGBA", (48, 66), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if idx == 0:
        # Poster 0: Detailed 16-bit Anime Cover (sunset sky, shaded dark-haired heroine portrait, banner)
        for y in range(2, 64):
            f = (y - 2) / 62.0
            c = lerp_c((94, 72, 138, 255), (244, 164, 142, 255), f)
            d.line([(2, y), (45, y)], fill=c)
        # Background clouds & sparkle
        d.rounded_rectangle([5, 16, 24, 21], radius=2, fill=(255, 224, 214, 255))
        d.rounded_rectangle([26, 24, 43, 29], radius=2, fill=(255, 210, 200, 255))
        # Heroine hair & silhouette
        d.ellipse([11, 18, 37, 46], fill=(56, 38, 60, 255))
        d.polygon([(9, 63), (14, 43), (34, 43), (39, 63)], fill=(66, 48, 76, 255))
        # Red scarf & collar
        d.polygon([(16, 43), (32, 43), (24, 52)], fill=(224, 82, 108, 255))
        # Face, bangs, anime eyes & blush
        d.ellipse([16, 24, 32, 42], fill=(255, 224, 204, 255))
        d.polygon([(14, 25), (34, 25), (32, 31), (26, 28), (22, 32), (16, 28)], fill=(56, 38, 60, 255))
        d.rectangle([19, 32, 21, 34], fill=(142, 66, 152, 255))
        d.rectangle([27, 32, 29, 34], fill=(142, 66, 152, 255))
        d.point((19, 32), fill=WHITE); d.point((27, 32), fill=WHITE)
        d.rectangle([18, 36, 20, 36], fill=(248, 146, 166, 255))
        d.rectangle([28, 36, 30, 36], fill=(248, 146, 166, 255))
        # Title banner
        d.rectangle([5, 5, 42, 11], fill=(255, 246, 232, 255))
        d.rectangle([8, 7, 39, 9], fill=(116, 76, 148, 255))
        d.rectangle([0, 0, 47, 65], outline=OUT, width=2)
    elif idx == 1:
        # Poster 1: Gothic-Violet & Rose Cosplay Silhouette ("Shizuku-tan" dress + crescent moon + stars)
        for y in range(2, 64):
            f = (y - 2) / 62.0
            c = lerp_c((42, 26, 68, 255), (156, 68, 118, 255), f)
            d.line([(2, y), (45, y)], fill=c)
        # Crescent moon & golden sparkles
        d.ellipse([26, 12, 42, 28], fill=(255, 242, 178, 255))
        d.ellipse([29, 10, 44, 25], fill=(64, 34, 82, 255))
        for sx, sy in ((8, 18), (12, 28), (38, 34), (9, 46), (40, 50)):
            d.rectangle([sx, sy, sx + 1, sy + 1], fill=(255, 244, 176, 255))
        # Frilly gothic cosplay silhouette + ribbon bow
        d.ellipse([17, 22, 31, 36], fill=(28, 18, 42, 255))
        d.polygon([(14, 40), (34, 40), (41, 63), (7, 63)], fill=(28, 18, 42, 255))
        d.polygon([(18, 36), (30, 36), (34, 46), (14, 46)], fill=(48, 30, 72, 255))
        # Lace hem & rose ribbon
        for rx in range(9, 40, 4):
            d.ellipse([rx, 59, rx + 3, 62], fill=(244, 184, 212, 255))
        d.rectangle([21, 39, 27, 42], fill=(238, 92, 134, 255))
        # Ornate gold title strip
        d.rectangle([5, 5, 42, 10], fill=(255, 224, 134, 255))
        d.rectangle([9, 7, 38, 8], fill=(72, 32, 78, 255))
        d.rectangle([0, 0, 47, 65], outline=OUT, width=2)
    else:
        # Poster 2: Deep-Space Cosmos & Cyberpunk Neon Skyline
        for y in range(2, 64):
            f = (y - 2) / 62.0
            c = lerp_c((16, 18, 48, 255), (72, 34, 98, 255), f) if f < 0.65 else lerp_c((72, 34, 98, 255), (224, 88, 146, 255), (f - 0.65) / 0.35)
            d.line([(2, y), (45, y)], fill=c)
        # Starfield
        for sx, sy in ((6, 12), (14, 8), (38, 10), (41, 22), (8, 28), (34, 32), (18, 36)):
            d.point((sx, sy), fill=(255, 252, 226, 255))
        # Ringed planet (Saturn-style cosmos!)
        d.ellipse([16, 14, 34, 32], fill=(116, 218, 232, 255))
        d.pieslice([16, 14, 34, 32], 20, 200, fill=(68, 134, 182, 255))
        d.arc([8, 19, 42, 29], 340, 200, fill=(255, 206, 142, 255), width=2)
        # Cyberpunk neon skyline silhouette
        buildings = [(3, 46, 10), (11, 41, 18), (19, 48, 26), (27, 39, 35), (36, 45, 45)]
        for bx0, by0, bx1 in buildings:
            d.rectangle([bx0, by0, bx1, 63], fill=(24, 20, 44, 255))
            for wy in range(by0 + 3, 60, 4):
                d.rectangle([bx0 + 2, wy, bx1 - 2, wy + 1], fill=(104, 242, 236, 255))
        d.rectangle([5, 5, 42, 8], fill=(104, 242, 236, 255))
        d.rectangle([0, 0, 47, 65], outline=OUT, width=2)
    return img


def build_drawer_open():
    """Empty pulled-out nightstand drawer (64x36); draggable items sit dynamically inside!"""
    OUT = (54, 36, 44, 255)
    img = Image.new("RGBA", (64, 36), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([4, 2, 58, 16], fill=(58, 34, 26, 255), outline=OUT, width=1)
    d.rectangle([6, 4, 56, 14], fill=(74, 46, 34, 255))
    d.rectangle([0, 14, 62, 35], fill=(166, 106, 70, 255), outline=OUT, width=2)
    d.line([(2, 16), (60, 16)], fill=(196, 134, 92, 255), width=2)
    d.rectangle([26, 22, 36, 27], fill=(214, 218, 230, 255), outline=OUT, width=1)
    return img


def build_acc_glasses():
    """Wearable stylish red-framed cosplay glasses aligned to Marin's eyes (cx=±8, y=-154) with crisp 1px rim."""
    img = new_char()
    d = ImageDraw.Draw(img)
    frame = (212, 56, 78, 255)
    frame_hi = (255, 136, 152, 255)
    lens = (204, 238, 255, 75)
    for cx in (-8, 8):
        rect(d, cx - 5, -158, 10, 8, lens)
        d.rectangle([OX + cx - 6, OY - 159, OX + cx + 5, OY - 150], outline=frame, width=1)
        line(d, (cx - 5, -159), (cx + 4, -159), frame, 1)
        line(d, (cx - 3, -159), (cx + 1, -159), frame_hi, 1)
        line(d, (cx - 4, -157), (cx - 2, -157), WHITE, 1)
    line(d, (-2, -155), (2, -155), frame, 1)
    line(d, (-14, -156), (-13, -156), frame, 1)
    line(d, (13, -156), (14, -156), frame, 1)
    return img


def build_acc_ears():
    """Wearable cute plush cat-ear headband hugging crown (-185) seamlessly."""
    img = new_char()
    d = ImageDraw.Draw(img)
    ear_dark = (46, 34, 52, 255)
    ear_hi = (78, 60, 88, 255)
    ear_in = (248, 148, 178, 255)
    pts = bezier((-15, -175), (0, -185), (15, -175), 12)
    for i in range(len(pts) - 1):
        line(d, pts[i], pts[i + 1], ear_dark, 2)
    for s in (-1, 1):
        poly(d, [(s * 14, -176), (s * 15, -195), (s * 4, -182)], ear_dark)
        poly(d, [(s * 12, -178), (s * 13, -190), (s * 6, -182)], ear_in)
        line(d, (s * 14, -192), (s * 6, -182), ear_hi, 1)
    return sel_out(img)


def build_item_glasses():
    """Draggable cosplay glasses prop (32x16) from top nightstand drawer."""
    img = Image.new("RGBA", (32, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    frame = (212, 56, 78, 255)
    lens = (204, 238, 255, 200)
    d.rectangle([2, 3, 13, 12], fill=lens, outline=frame, width=2)
    d.rectangle([18, 3, 29, 12], fill=lens, outline=frame, width=2)
    d.line([(13, 6), (18, 6)], fill=frame, width=2)
    d.line([(4, 5), (7, 5)], fill=WHITE, width=1)
    d.line([(20, 5), (23, 5)], fill=WHITE, width=1)
    return sel_out(img)


def build_item_camera():
    """Draggable retro silver & dark-leather camera (30x22) from bottom nightstand drawer."""
    img = Image.new("RGBA", (30, 22), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Top silver plate + shutter button + flash
    d.rectangle([4, 3, 25, 8], fill=(216, 220, 232, 255))
    d.rectangle([6, 1, 11, 3], fill=(236, 108, 122, 255))
    d.rectangle([19, 4, 24, 7], fill=(255, 246, 186, 255))
    # Dark leather camera body
    d.rounded_rectangle([3, 7, 26, 19], radius=2, fill=(56, 48, 64, 255))
    # Lens barrel & glossy blue glass
    d.ellipse([9, 7, 20, 18], fill=(176, 182, 198, 255))
    d.ellipse([11, 9, 18, 16], fill=(64, 112, 164, 255))
    d.rectangle([12, 10, 14, 12], fill=WHITE)
    return sel_out(img)


def build_rps_icon(kind):
    """Crisp 28x28 16-bit pixel gesture icons for Rock-Paper-Scissors minigame."""
    img = Image.new("RGBA", (28, 28), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if kind == "rock":
        # Cute closed fist
        d.rounded_rectangle([6, 8, 22, 22], radius=5, fill=SKIN)
        d.rectangle([7, 17, 21, 21], fill=SKIN_SH)
        for fx in (10, 14, 18):
            d.line([(fx, 8), (fx, 14)], fill=SKIN_D, width=1)
        d.rounded_rectangle([5, 13, 13, 18], radius=2, fill=SKIN_HI)
    elif kind == "paper":
        # Open palm with 5 fingers
        d.rounded_rectangle([7, 13, 21, 23], radius=4, fill=SKIN)
        for fx, top in ((7, 6), (11, 4), (15, 4), (19, 7)):
            d.rounded_rectangle([fx, top, fx + 3, 15], radius=1, fill=SKIN)
        d.rounded_rectangle([4, 13, 8, 20], radius=2, fill=SKIN_HI)
        d.rectangle([8, 19, 20, 22], fill=SKIN_SH)
    else:
        # Peace / Scissors V-sign!
        d.rounded_rectangle([7, 14, 21, 23], radius=4, fill=SKIN)
        d.polygon([(9, 15), (6, 4), (10, 4), (13, 15)], fill=SKIN)
        d.polygon([(14, 15), (17, 4), (21, 4), (18, 15)], fill=SKIN)
        d.rounded_rectangle([14, 14, 21, 19], radius=2, fill=SKIN_SH)
        d.rounded_rectangle([6, 15, 13, 20], radius=2, fill=SKIN_HI)
    return sel_out(img)


def build_sky_patch(mode):
    """Standalone 108x100 window sky surface for smooth real-time crossfade lerp."""
    img = Image.new("RGBA", (108, 100), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    palettes = [
        ((106, 174, 240), (186, 224, 252)),
        ((82, 58, 132), (252, 174, 104)),
        ((14, 18, 46), (42, 42, 86)),
    ]
    top, bot = palettes[mode]
    for y in range(100):
        f = y / 99.0
        if mode == 1:
            mid = (232, 114, 118)
            c = lerp_c(top + (255,), mid + (255,), f * 2) if f < 0.5 else lerp_c(mid + (255,), bot + (255,), (f - 0.5) * 2)
        else:
            c = lerp_c(top + (255,), bot + (255,), f)
        d.line([(0, y), (107, y)], fill=c[:3])
    if mode == 0:
        for cx, cy, cw, ch in ((10, 18, 30, 8), (58, 38, 36, 9), (22, 66, 24, 7)):
            d.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=4, fill=(252, 252, 255))
            d.rounded_rectangle([cx + 6, cy - 5, cx + cw - 6, cy + 3], radius=3, fill=(255, 255, 255))
    elif mode == 1:
        d.ellipse([56, 72, 88, 104], fill=(255, 228, 144))
        d.rectangle([0, 90, 108, 100], fill=(134, 72, 106))
    else:
        rnd = random.Random(11)
        for _ in range(28):
            sx, sy = rnd.randint(2, 105), rnd.randint(2, 86)
            col = (255, 250, 210) if rnd.random() > 0.4 else (190, 210, 255)
            d.rectangle([sx, sy, sx + 1, sy + 1], fill=col)
        d.ellipse([72, 14, 92, 34], fill=(252, 246, 206))
        d.ellipse([77, 11, 95, 29], fill=top)
    # Window mullions
    d.rectangle([52, 0, 56, 100], fill=(230, 220, 206))
    d.rectangle([0, 48, 108, 52], fill=(230, 220, 206))
    d.rectangle([52, 0, 53, 100], fill=(186, 172, 156))
    d.rectangle([0, 51, 108, 52], fill=(186, 172, 156))
    return img


def build_fairy_lights(on=False):
    """Hanging catenary fairy-light strand (240x40) for upper-right wall over bed."""
    img = Image.new("RGBA", (240, 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    wire = (72, 54, 62, 255)
    # Two graceful catenary swags along the wall
    pts1 = bezier((4, 6), (62, 30), (120, 8), 24)
    pts2 = bezier((120, 8), (178, 30), (236, 6), 24)
    all_pts = pts1 + pts2[1:]
    for i in range(len(all_pts) - 1):
        d.line([all_pts[i], all_pts[i + 1]], fill=wire, width=1)
    # 11 cute hanging bulbs along the wire
    bulb_indices = [3, 8, 13, 18, 23, 28, 33, 38, 43]
    for bi, idx in enumerate(bulb_indices):
        bx, by = all_pts[idx]
        d.rectangle([bx - 1, by, bx + 1, by + 2], fill=wire)
        if on:
            col = (255, 240, 178, 255) if bi % 2 == 0 else (255, 198, 218, 255)
            d.ellipse([bx - 2, by + 2, bx + 2, by + 6], fill=col)
            d.point((bx, by + 3), fill=WHITE)
        else:
            d.ellipse([bx - 2, by + 2, bx + 2, by + 6], fill=(168, 158, 166, 255), outline=wire)
    return img


def build_item_gift():
    """Draggable pastel-pink candy/gift box with golden ribbon (24x22) for nightstand drawer."""
    img = Image.new("RGBA", (24, 22), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Box body & lid
    d.rounded_rectangle([3, 7, 20, 19], radius=2, fill=(248, 146, 178, 255))
    d.rectangle([2, 5, 21, 9], fill=(255, 176, 200, 255))
    # Golden vertical & horizontal ribbons
    d.rectangle([10, 5, 13, 19], fill=GOLD)
    d.rectangle([3, 12, 20, 14], fill=GOLD)
    # Cute bow loops on top
    d.ellipse([6, 1, 11, 6], fill=GOLD)
    d.ellipse([12, 1, 17, 6], fill=GOLD)
    d.rectangle([10, 3, 13, 5], fill=WHITE)
    return sel_out(img)


BAYER4 = np.array([
    [0,  8,  2, 10],
    [12, 4, 14,  6],
    [3, 11,  1,  9],
    [15, 7, 13,  5],
], dtype=np.float32) / 16.0


def build_dithered_halo(size, rgb, max_alpha=110, levels=5):
    """Crisp 16-bit Bayer-dithered circular halo sprite (no flat smooth-circle look!)."""
    y, x = np.ogrid[:size, :size]
    c = (size - 1) * 0.5
    dist = np.sqrt((x - c) ** 2 + (y - c) ** 2)
    f = np.clip(1.0 - dist / (size * 0.5), 0.0, 1.0) ** 1.5
    bayer = np.tile(BAYER4, (size // 4 + 1, size // 4 + 1))[:size, :size]
    q = f * levels
    lvl = np.floor(q) + ((q - np.floor(q)) > bayer).astype(np.float32)
    a = np.clip((lvl / levels) * max_alpha, 0, 255).astype(np.uint8)
    arr = np.zeros((size, size, 4), dtype=np.uint8)
    arr[:, :, 0] = rgb[0]
    arr[:, :, 1] = rgb[1]
    arr[:, :, 2] = rgb[2]
    arr[:, :, 3] = a
    return Image.fromarray(arr, "RGBA")


def build_night_lamp_glow():
    """16-bit Bayer-dithered warm lamp glow + warm floor & wall reflection bounce!"""
    y, x = np.ogrid[:VH, :VW]
    bayer = np.tile(BAYER4, (VH // 4 + 1, VW // 4 + 1))[:VH, :VW]
    # Primary lamp halo
    d1 = np.sqrt((x - 606) ** 2 + ((y - 162) * 1.1) ** 2)
    f1 = np.clip(1.0 - d1 / 280.0, 0.0, 1.0) ** 1.75
    # Warm bounce reflection on the wooden floor & lower wall right next to the nightstand
    d2 = np.sqrt(((x - 560) * 0.85) ** 2 + ((y - 296) * 1.65) ** 2)
    f2 = np.clip(1.0 - d2 / 140.0, 0.0, 1.0) ** 1.8 * 0.48
    f = np.clip(f1 + f2, 0.0, 1.0)

    levels = 8.0
    q = f * levels
    lvl = np.floor(q) + ((q - np.floor(q)) > bayer).astype(np.float32)
    v = lvl / levels
    arr = np.zeros((VH, VW, 4), dtype=np.uint8)
    arr[:, :, 0] = 255
    arr[:, :, 1] = np.clip(196 + 44 * v, 0, 255).astype(np.uint8)
    arr[:, :, 2] = np.clip(108 + 64 * v, 0, 255).astype(np.uint8)
    arr[:, :, 3] = np.clip(v * 168.0, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def build_clean_sky(mode):
    """Pure gradient sky (108x100) without baked clouds/stars so live clouds & shooting stars animate cleanly."""
    img = Image.new("RGBA", (108, 100), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if mode == 0:
        top, bot = (102, 172, 242, 255), (190, 228, 255, 255)
        for y in range(100):
            d.line([(0, y), (107, y)], fill=lerp_c(top, bot, y / 99.0)[:3])
    elif mode == 1:
        top, mid, bot = (78, 56, 134, 255), (232, 114, 118, 255), (255, 182, 108, 255)
        for y in range(100):
            f = y / 99.0
            c = lerp_c(top, mid, f * 2) if f < 0.5 else lerp_c(mid, bot, (f - 0.5) * 2)
            d.line([(0, y), (107, y)], fill=c[:3])
        d.ellipse([56, 72, 88, 104], fill=(255, 228, 144))
        d.rectangle([0, 90, 108, 100], fill=(134, 72, 106))
    elif mode == 2:
        top, bot = (14, 18, 48, 255), (42, 42, 88, 255)
        for y in range(100):
            d.line([(0, y), (107, y)], fill=lerp_c(top, bot, y / 99.0)[:3])
        d.ellipse([72, 14, 92, 34], fill=(252, 246, 206))
        d.ellipse([77, 11, 95, 29], fill=(20, 22, 54))
    else:
        top, mid, bot = (86, 48, 108, 255), (214, 104, 148, 255), (255, 192, 164, 255)
        for y in range(100):
            f = y / 99.0
            c = lerp_c(top, mid, f * 2) if f < 0.5 else lerp_c(mid, bot, (f - 0.5) * 2)
            d.line([(0, y), (107, y)], fill=c[:3])
    return img


def build_manga_open(flip=False):
    """Open 16-bit manga book held by Marin while sitting on the floor (32x22)."""
    img = Image.new("RGBA", (32, 22), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Soft coral-violet manga cover edges
    d.polygon([(2, 6), (15, 8), (15, 20), (3, 18)], fill=(142, 74, 108, 255))
    d.polygon([(16, 8), (29, 6), (28, 18), (16, 20)], fill=(124, 62, 94, 255))
    # Crisp open white pages with tiny comic panel ink lines
    d.polygon([(4, 4), (15, 7), (15, 18), (4, 16)], fill=(252, 248, 240, 255))
    d.polygon([(16, 7), (27, 4), (27, 16), (16, 18)], fill=(244, 238, 230, 255))
    # Tiny comic panel frames on pages
    d.rectangle([6, 7, 12, 10], outline=(84, 68, 86, 255))
    d.rectangle([6, 12, 13, 15], outline=(84, 68, 86, 255))
    d.rectangle([18, 7, 25, 11], outline=(84, 68, 86, 255))
    d.rectangle([18, 13, 24, 15], outline=(84, 68, 86, 255))
    if flip:
        # Curved fluttering mid-turn page!
        d.polygon([(15, 7), (22, 1), (20, 14), (15, 18)], fill=WHITE)
        d.line([(22, 1), (20, 14)], fill=(214, 204, 198, 255), width=1)
    return sel_out(img)


def build_window_mullions():
    """Crisp window mullions overlay (108x100) drawn ABOVE live drifting clouds & shooting stars."""
    img = Image.new("RGBA", (108, 100), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([52, 0, 56, 100], fill=(230, 220, 206, 255))
    d.rectangle([0, 48, 108, 52], fill=(230, 220, 206, 255))
    d.rectangle([52, 0, 53, 100], fill=(186, 172, 156, 255))
    d.rectangle([0, 51, 108, 52], fill=(186, 172, 156, 255))
    return img


def generate_all():
    for outfit in (0, 1, 2, 3, 4):
        build_legs(outfit, "stand").save(os.path.join(ASSETS, f"legs_{outfit}_stand.png"))
        build_legs(outfit, "air").save(os.path.join(ASSETS, f"legs_{outfit}_air.png"))
        build_legs(outfit, "sit").save(os.path.join(ASSETS, f"legs_{outfit}_sit.png"))
        build_legs(outfit, "floor").save(os.path.join(ASSETS, f"legs_{outfit}_floor.png"))
        build_lower_garment(outfit).save(os.path.join(ASSETS, f"skirt_{outfit}.png"))
        build_torso(outfit, False).save(os.path.join(ASSETS, f"torso_{outfit}.png"))
        build_torso(outfit, True).save(os.path.join(ASSETS, f"torso_{outfit}_relaxed.png"))
        build_shirt_folds(outfit).save(os.path.join(ASSETS, f"folds_{outfit}.png"))
        build_arm(outfit, -1, "idle").save(os.path.join(ASSETS, f"arm_l_{outfit}.png"))
        build_arm(outfit, 1, "idle").save(os.path.join(ASSETS, f"arm_r_{outfit}.png"))
        build_arm(outfit, 1, "wave").save(os.path.join(ASSETS, f"arm_r_{outfit}_wave.png"))
        build_arm(outfit, -1, "collar").save(os.path.join(ASSETS, f"arm_l_{outfit}_collar.png"))
        build_arm(outfit, 1, "collar").save(os.path.join(ASSETS, f"arm_r_{outfit}_collar.png"))
        build_arm(outfit, -1, "stretch").save(os.path.join(ASSETS, f"arm_l_{outfit}_stretch.png"))
        build_arm(outfit, 1, "stretch").save(os.path.join(ASSETS, f"arm_r_{outfit}_stretch.png"))
        build_arm(outfit, -1, "manga").save(os.path.join(ASSETS, f"arm_l_{outfit}_manga.png"))
        build_arm(outfit, 1, "manga").save(os.path.join(ASSETS, f"arm_r_{outfit}_manga.png"))
        build_arm(outfit, 1, "manga_turn").save(os.path.join(ASSETS, f"arm_r_{outfit}_manga_turn.png"))
        build_arm(outfit, 1, "phone").save(os.path.join(ASSETS, f"arm_r_{outfit}_phone.png"))

    build_tie(False).save(os.path.join(ASSETS, "tie.png"))
    build_tie(True).save(os.path.join(ASSETS, "tie_0_relaxed.png"))
    build_tie_loose(False).save(os.path.join(ASSETS, "tie_loose.png"))
    build_tie_loose(True).save(os.path.join(ASSETS, "tie_4_relaxed.png"))
    build_manga_open(False).save(os.path.join(ASSETS, "manga_open.png"))
    build_manga_open(True).save(os.path.join(ASSETS, "manga_open_flip.png"))

    build_head_base().save(os.path.join(ASSETS, "head_base.png"))
    build_iris().save(os.path.join(ASSETS, "iris.png"))
    for emo in ("normal", "pet", "blush", "smug", "surprised", "sleepy", "pout", "starry", "romantic", "flustered", "blink"):
        build_face(emo).save(os.path.join(ASSETS, f"face_{emo}.png"))

    build_acc_glasses().save(os.path.join(ASSETS, "acc_glasses.png"))
    build_acc_ears().save(os.path.join(ASSETS, "acc_ears.png"))

    build_hair_back().save(os.path.join(ASSETS, "hair_back.png"))
    build_hair_side(-1).save(os.path.join(ASSETS, "hair_front_l.png"))
    build_hair_side(1).save(os.path.join(ASSETS, "hair_front_r.png"))
    build_hair_bangs().save(os.path.join(ASSETS, "hair_bangs.png"))

    build_pillow().save(os.path.join(ASSETS, "pillow.png"))
    build_boba().save(os.path.join(ASSETS, "boba.png"))
    build_item_glasses().save(os.path.join(ASSETS, "item_glasses.png"))
    build_item_camera().save(os.path.join(ASSETS, "item_camera.png"))
    build_item_gift().save(os.path.join(ASSETS, "item_gift.png"))
    build_fairy_lights(False).save(os.path.join(ASSETS, "fairy_off.png"))
    build_fairy_lights(True).save(os.path.join(ASSETS, "fairy_on.png"))
    build_dithered_halo(32, (255, 228, 148), max_alpha=115, levels=5).save(os.path.join(ASSETS, "fairy_halo_gold.png"))
    build_dithered_halo(32, (255, 172, 206), max_alpha=115, levels=5).save(os.path.join(ASSETS, "fairy_halo_pink.png"))
    build_curtain_panel(86, 132).save(os.path.join(ASSETS, "curtain_panel.png"))
    for i in range(3):
        build_poster(i).save(os.path.join(ASSETS, f"poster_{i}.png"))
    build_drawer_open().save(os.path.join(ASSETS, "drawer_open.png"))
    build_night_lamp_glow().save(os.path.join(ASSETS, "lamp_glow.png"))

    for kind in ("rock", "paper", "scissors"):
        build_rps_icon(kind).save(os.path.join(ASSETS, f"rps_{kind}.png"))

    build_room(0, False).save(os.path.join(ASSETS, "room_base.png"))
    build_room(0, True).save(os.path.join(ASSETS, "room_base_open.png"))
    for mode, name in ((0, "day"), (1, "sunset"), (2, "night"), (3, "romantic")):
        build_clean_sky(mode).save(os.path.join(ASSETS, f"sky_{name}.png"))
    build_window_mullions().save(os.path.join(ASSETS, "window_frame.png"))

    print("Generated v0.6-beta Marin Art Overhaul assets (all 5 outfits + relaxed, wavy hair, VN faces, poses) in", ASSETS)


if __name__ == "__main__":
    generate_all()
