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

# ------------------------------------------------------------------ palettes (3-4 tones)
SKIN_HI = (255, 240, 228, 255)
SKIN    = (255, 222, 202, 255)
SKIN_SH = (236, 184, 164, 255)
SKIN_D  = (208, 148, 132, 255)

HAIR_HI = (255, 247, 194, 255)
HAIR    = (248, 214, 122, 255)
HAIR_SH = (220, 170, 82, 255)
HAIR_D  = (180, 126, 62, 255)

PINK_HI = (255, 182, 202, 255)
PINK    = (244, 128, 158, 255)
PINK_SH = (206, 88, 124, 255)

SHIRT_HI = (255, 255, 252, 255)
SHIRT    = (244, 243, 242, 255)
SHIRT_SH = (206, 206, 220, 255)
SHIRT_D  = (166, 166, 186, 255)

TIE_HI = (146, 152, 168, 255)
TIE    = (104, 110, 128, 255)
TIE_SH = (72, 76, 94, 255)

SKIRT_HI = (74, 80, 114, 255)
SKIRT    = (50, 54, 82, 255)
SKIRT_SH = (34, 36, 58, 255)

HOME_BOT_HI = (86, 84, 106, 255)
HOME_BOT    = (62, 60, 80, 255)
HOME_BOT_SH = (44, 42, 60, 255)

SOCK_HI = (60, 58, 72, 255)
SOCK    = (36, 34, 46, 255)
SOCK_SH = (24, 22, 32, 255)

SHOE_HI = (122, 82, 74, 255)
SHOE    = (78, 50, 46, 255)
SHOE_SH = (48, 30, 32, 255)

SLIP_HI = (255, 198, 214, 255)
SLIP    = (242, 148, 176, 255)
SLIP_SH = (196, 104, 134, 255)

# Outfit 2: Oversized pastel-lavender/pink cozy hoodie + sneakers
HOOD_HI = (242, 206, 232, 255)
HOOD    = (218, 166, 206, 255)
HOOD_SH = (176, 122, 168, 255)
HOOD_D  = (134, 86, 132, 255)
SNEAK_HI = (255, 252, 252, 255)
SNEAK    = (232, 144, 174, 255)
SNEAK_SH = (182, 96, 130, 255)

# Outfit 3: Summer Casual (mint cropped top + blue denim shorts + white sneakers)
MINT_HI  = (204, 248, 232, 255)
MINT     = (148, 224, 202, 255)
MINT_SH  = (106, 184, 166, 255)
DENIM_HI = (118, 158, 206, 255)
DENIM    = (78, 118, 172, 255)
DENIM_SH = (52, 82, 132, 255)
BELT     = (124, 78, 56, 255)
GOLD     = (244, 208, 108, 255)

CHOKER   = (30, 26, 36, 255)
SILVER   = (224, 228, 240, 255)
SILVER_D = (146, 152, 168, 255)

# Marin's signature burgundy/violet -> magenta -> bright rose-pink eyes
EYE_TOP  = (96, 28, 68, 255)
EYE_MID  = (184, 58, 118, 255)
EYE_BOT  = (252, 134, 176, 255)
EYE_GLOW = (255, 196, 218, 255)
LASH     = (48, 26, 40, 255)
BROW     = (176, 128, 72, 255)
MOUTH_C  = (172, 78, 92, 255)
MOUTH_IN = (234, 122, 134, 255)
WHITE    = (255, 255, 255, 255)


# ------------------------------------------------------------------ drawing helpers
def new_char():
    return Image.new("RGBA", (CW, CH), (0, 0, 0, 0))


def sel_out(img, darken=(0.48, 0.40, 0.50), min_rgb=(40, 26, 38), alpha_thresh=128):
    """Selective colored pixel-art outline (sel-out) around opaque regions."""
    arr = np.array(img, dtype=np.uint8)
    opaque = arr[:, :, 3] >= alpha_thresh
    h, w = opaque.shape
    out = arr.copy()

    n_up = np.zeros_like(opaque); n_up[1:] = opaque[:-1]
    n_dn = np.zeros_like(opaque); n_dn[:-1] = opaque[1:]
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
    rr = np.clip(np.maximum(min_rgb[0], (r_sum / cnt) * darken[0]), 0, 255).astype(np.uint8)
    gg = np.clip(np.maximum(min_rgb[1], (g_sum / cnt) * darken[1]), 0, 255).astype(np.uint8)
    bb = np.clip(np.maximum(min_rgb[2], (b_sum / cnt) * darken[2]), 0, 255).astype(np.uint8)

    out[border, 0] = rr[border]
    out[border, 1] = gg[border]
    out[border, 2] = bb[border]
    out[border, 3] = 255
    return Image.fromarray(out, "RGBA")


def lerp_c(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(4))


def hair_gradient_fill(img, y_start, y_end, pink_start=0.54, steps=6):
    """Smooth 6-step pixel gradient from golden-blonde to coral-pink tips."""
    arr = np.array(img, dtype=np.uint8)
    h, w, _ = arr.shape
    for y in range(max(0, y_start), min(h, y_end)):
        f = (y - y_start) / max(1, (y_end - y_start))
        if f <= pink_start:
            continue
        t = (f - pink_start) / (1.0 - pink_start)
        tq = round(t * steps) / float(steps)
        row = arr[y]
        mask = row[:, 3] > 200
        if not np.any(mask):
            continue
        r = row[:, 0].astype(np.float32)
        g = row[:, 1].astype(np.float32)
        b = row[:, 2].astype(np.float32)
        for x in np.where(mask)[0]:
            lum = (r[x] + g[x] + b[x]) / 3.0
            if lum > 218:
                c = lerp_c(HAIR_HI, PINK_HI, tq)
            elif lum > 172:
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


# ------------------------------------------------------------------ character layers (natural contrapposto stance)
def build_legs(outfit, air=False):
    """Layer 0: Natural anime stance (weight shifted slightly onto left leg, right leg relaxed)."""
    img = new_char()
    d = ImageDraw.Draw(img)
    school = (outfit == 0)

    if not air:
        # Left leg (viewer's left): supporting weight, graceful straight-slender curve
        l_pts = [
            (-12, -74), (-13, -60), (-11.5, -44), (-10.5, -36), (-11, -24), (-8.5, -12), (-8, -5),
            (-2, -5), (-2.5, -14), (-3.5, -26), (-3.5, -38), (-2, -54), (-1.5, -74)
        ]
        poly(d, l_pts, SKIN)
        poly(d, [(-4.5, -74), (-4.5, -54), (-5.5, -38), (-5.5, -26), (-4.5, -14), (-4, -5),
                 (-2, -5), (-2.5, -14), (-3.5, -26), (-3.5, -38), (-2, -54), (-1.5, -74)], SKIN_SH)
        ell(d, -8, -40, 4, 3, SKIN_HI)
        rect(d, -12, -74, 11, 4, SKIN_SH)

        # Right leg (viewer's right): relaxed, angled slightly outward for natural contrapposto
        r_pts = [
            (1.5, -74), (12, -74), (13.5, -58), (13, -44), (12.5, -35), (14, -22), (13.5, -10), (13, -4),
            (6.5, -4), (6.5, -13), (6, -25), (5, -37), (3.5, -52), (2, -66)
        ]
        poly(d, r_pts, SKIN)
        poly(d, [(9.5, -74), (12, -74), (13.5, -58), (13, -44), (12.5, -35), (14, -22), (13.5, -10), (13, -4),
                 (10.5, -4), (11, -22), (10, -44), (10.5, -58)], SKIN_SH)
        ell(d, 7, -39, 4, 3, SKIN_HI)
        rect(d, 2, -74, 11, 4, SKIN_SH)

        if outfit == 0:
            # Mid-calf black socks
            poly(d, [(-11, -26), (-8.5, -12), (-8, -5), (-2, -5), (-2.5, -14), (-3.5, -26)], SOCK)
            line(d, (-7, -25), (-5.5, -7), SOCK_HI, 2)
            poly(d, [(13.5, -25), (13.5, -10), (13, -4), (6.5, -4), (6.5, -13), (6, -25)], SOCK)
            line(d, (9, -24), (9.5, -6), SOCK_HI, 2)
            # Brown loafers
            poly(d, [(-9, -7), (-11, -2), (-10, 0), (-1.5, 0), (-1.5, -3), (-2, -7)], SHOE)
            rect(d, -9, -6, 6, 2, SHOE_HI)
            poly(d, [(6, -6), (13.5, -6), (16, -2), (15, 1), (6, 1), (5.5, -2)], SHOE)
            rect(d, 7, -5, 6, 2, SHOE_HI)
        elif outfit == 1:
            # Cute coral-pink indoor slippers
            poly(d, [(-9, -6), (-11, -2), (-10, 0), (-1.5, 0), (-1.5, -3), (-2, -6)], SLIP)
            rect(d, -9, -5, 6, 2, SLIP_HI)
            poly(d, [(6, -5), (13.5, -5), (16, -1), (15, 1), (6, 1), (5.5, -2)], SLIP)
            rect(d, 7, -4, 6, 2, SLIP_HI)
        elif outfit == 2:
            # Outfit 2 (Hoodie): Thigh-high dark socks with white stripes + pastel sneakers
            poly(d, [(-11.5, -46), (-10.5, -36), (-11, -24), (-8.5, -12), (-8, -5),
                     (-2, -5), (-2.5, -14), (-3.5, -26), (-3.5, -38), (-2.5, -46)], SOCK)
            line(d, (-11, -43), (-3, -43), WHITE, 1)
            line(d, (-11, -40), (-3, -40), WHITE, 1)
            poly(d, [(13, -45), (12.5, -35), (14, -22), (13.5, -10), (13, -4),
                     (6.5, -4), (6.5, -13), (6, -25), (5, -37), (4, -45)], SOCK)
            line(d, (4, -42), (12.5, -42), WHITE, 1)
            line(d, (4.5, -39), (12.5, -39), WHITE, 1)
            poly(d, [(-9.5, -8), (-11.5, -2), (-10.5, 0), (-1, 0), (-1, -3), (-2, -8)], SNEAK)
            rect(d, -10, -2, 9, 2, SNEAK_HI)
            poly(d, [(5.5, -7), (14, -7), (16.5, -2), (15.5, 1), (5.5, 1), (5, -2)], SNEAK)
            rect(d, 6, -1, 10, 2, SNEAK_HI)
        else:
            # Outfit 3 (Summer Casual): Low white ankle socks + crisp white & mint sneakers
            poly(d, [(-9, -13), (-8, -5), (-2, -5), (-2.5, -13)], WHITE)
            poly(d, [(13.5, -12), (13, -4), (6.5, -4), (6.5, -12)], WHITE)
            poly(d, [(-9.5, -7), (-11.5, -2), (-10.5, 0), (-1, 0), (-1, -3), (-2, -7)], WHITE)
            rect(d, -10, -5, 8, 2, MINT)
            rect(d, -10, -2, 9, 2, SHIRT_SH)
            poly(d, [(5.5, -6), (14, -6), (16.5, -2), (15.5, 1), (5.5, 1), (5, -2)], WHITE)
            rect(d, 6, -4, 9, 2, MINT)
            rect(d, 6, -1, 10, 2, SHIRT_SH)
    else:
        for side in (-1, 1):
            s = side
            thigh = [(s * 12, -74), (s * 15, -52), (s * 13, -42), (s * 4, -44), (s * 2, -62), (s * 2, -74)]
            poly(d, thigh, SKIN)
            calf = [(s * 14, -44), (s * 11, -22), (s * 9, -12), (s * 2.5, -13), (s * 4.5, -30), (s * 5.5, -44)]
            poly(d, calf, SKIN)
            poly(d, [(s * 11, -72), (s * 14, -52), (s * 12, -42), (s * 9, -43), (s * 9, -72)], SKIN_SH)
            if outfit == 0:
                poly(d, [(s * 11.5, -30), (s * 9, -12), (s * 2.5, -13), (s * 4.5, -30)], SOCK)
                poly(d, [(s * 10, -14), (s * 11, -8), (s * 8, -6), (s * 2, -7), (s * 2.5, -14)], SHOE)
                rect(d, min(s * 9, s * 3), -12, 5, 2, SHOE_HI)
            elif outfit == 1:
                poly(d, [(s * 10, -14), (s * 11, -8), (s * 8, -6), (s * 2, -7), (s * 2.5, -14)], SLIP)
                rect(d, min(s * 9, s * 3), -12, 5, 2, SLIP_HI)
            elif outfit == 2:
                poly(d, [(s * 13.5, -44), (s * 11, -22), (s * 9, -12), (s * 2.5, -13), (s * 4.5, -30), (s * 5.5, -44)], SOCK)
                poly(d, [(s * 10, -14), (s * 11.5, -8), (s * 8.5, -6), (s * 2, -7), (s * 2.5, -14)], SNEAK)
                rect(d, min(s * 9, s * 3), -8, 6, 2, SNEAK_HI)
            else:
                poly(d, [(s * 10, -17), (s * 9, -12), (s * 2.5, -13), (s * 3.5, -18)], WHITE)
                poly(d, [(s * 10, -14), (s * 11.5, -8), (s * 8.5, -6), (s * 2, -7), (s * 2.5, -14)], WHITE)
                rect(d, min(s * 9, s * 3), -11, 6, 2, MINT)

    return sel_out(img)


def build_lower_garment(outfit):
    """Layer 1: Pleated skirt (0), Home shorts (1), Hoodie hem (2), Blue denim shorts (3)."""
    img = new_char()
    d = ImageDraw.Draw(img)
    if outfit == 0:
        pts = [
            (-12, -94), (12, -94),
            (20, -68), (15, -66), (8, -67), (0, -66), (-8, -67), (-15, -66), (-20, -68)
        ]
        poly(d, pts, SKIRT)
        rect(d, -12, -94, 24, 3, SKIRT_SH)
        for tx, bx in ((-10, -16), (-6, -10), (-2, -4), (2, 4), (6, 10), (10, 16)):
            line(d, (tx, -91), (bx, -67), SKIRT_SH, 2)
            line(d, (tx + 2, -91), (bx + 2, -68), SKIRT_HI, 1)
        line(d, (-19, -68), (19, -68), SKIRT_SH, 1)
    elif outfit == 1:
        pts = [(-12, -92), (12, -92), (16, -71), (3, -71), (0, -75), (-3, -71), (-16, -71)]
        poly(d, pts, HOME_BOT)
        rect(d, -12, -92, 24, 3, HOME_BOT_SH)
        line(d, (0, -89), (0, -75), HOME_BOT_SH, 1)
        line(d, (-10, -87), (-13, -73), HOME_BOT_HI, 2)
        line(d, (10, -87), (12, -73), HOME_BOT_SH, 2)
        rect(d, -16, -73, 13, 2, HOME_BOT_SH)
        rect(d, 3, -73, 13, 2, HOME_BOT_SH)
    elif outfit == 2:
        poly(d, [(-15, -77), (15, -77), (16, -70), (3, -70), (0, -73), (-3, -70), (-16, -70)], HOME_BOT)
        poly(d, [(-18, -94), (18, -94), (19, -76), (-19, -76)], HOOD)
        rect(d, -18, -81, 36, 5, HOOD_SH)
        for rx in range(-15, 16, 4):
            line(d, (rx, -81), (rx, -76), HOOD_D, 1)
        poly(d, [(-11, -93), (11, -93), (13, -82), (-13, -82)], HOOD_SH)
        poly(d, [(-10, -92), (10, -92), (11, -83), (-11, -83)], HOOD)
    else:
        # Outfit 3: Stylish blue denim shorts with brown leather belt & gold buckle
        pts = [(-12, -94), (12, -94), (16, -70), (3, -70), (0, -75), (-3, -70), (-16, -70)]
        poly(d, pts, DENIM)
        # Denim fade highlights & cuff folds
        poly(d, [(-11, -88), (-4, -88), (-5, -74), (-13, -74)], DENIM_HI)
        poly(d, [(4, -88), (11, -88), (13, -74), (5, -74)], DENIM_HI)
        line(d, (0, -90), (0, -75), DENIM_SH, 1)
        rect(d, -16, -73, 13, 3, DENIM_SH)
        rect(d, 3, -73, 13, 3, DENIM_SH)
        # Brown belt + gold buckle
        rect(d, -12, -94, 24, 3, BELT)
        rect(d, -2, -94, 4, 3, GOLD)
    return sel_out(img)


def build_torso(outfit):
    """Layer 2: Narrow sloping shoulders, slender waist, open V-neck shirt with collarbones & waist knot."""
    img = new_char()
    d = ImageDraw.Draw(img)
    school = (outfit == 0)

    if school:
        pts = [
            (-5, -133), (5, -133),
            (13, -128), (14, -120),
            (12, -105), (11, -93),
            (5, -91), (0, -93), (-5, -91),
            (-11, -93), (-12, -105),
            (-14, -120), (-13, -128)
        ]
        poly(d, pts, SHIRT)
        # Soft cloth fold shading
        poly(d, [(8, -128), (13, -126), (13, -116), (11, -94), (7, -94), (9, -112)], SHIRT_SH)
        poly(d, [(-13, -122), (-10, -122), (-9, -94), (-11, -94)], SHIRT_SH)
        poly(d, [(-9, -124), (-3, -124), (-4, -106), (-9, -106)], SHIRT_HI)
        # Pocket
        rect(d, 4, -116, 6, 6, SHIRT_SH)
        rect(d, 5, -115, 4, 4, SHIRT)
        # Open V-neck showing delicate collarbones
        poly(d, [(-5, -134), (5, -134), (0, -121)], SKIN)
        line(d, (-4, -129), (-1, -128), SKIN_SH, 1)
        line(d, (4, -129), (1, -128), SKIN_SH, 1)
        # Collar lapels
        poly(d, [(-8, -133), (-4, -134), (-2, -122), (-8, -125)], SHIRT_HI)
        poly(d, [(8, -133), (4, -134), (2, -122), (8, -125)], SHIRT_HI)
        line(d, (-8, -125), (-2, -122), SHIRT_D, 1)
        line(d, (8, -125), (2, -122), SHIRT_D, 1)
        # Waist knot
        ell(d, -4, -96, 8, 5, SHIRT_SH)
        ell(d, -3, -96, 6, 4, SHIRT_HI)
        poly(d, [(-3, -92), (-8, -86), (-4, -85), (-1, -91)], SHIRT)
        poly(d, [(3, -92), (8, -86), (4, -85), (1, -91)], SHIRT_SH)
    elif outfit == 1:
        # Loose home white shirt with waist knot
        pts = [
            (-6, -133), (6, -133),
            (14, -128), (15, -116),
            (14, -96), (12, -90),
            (4, -89), (0, -92), (-4, -89),
            (-12, -90), (-14, -96),
            (-15, -116), (-14, -128)
        ]
        poly(d, pts, SHIRT)
        poly(d, [(8, -128), (14, -125), (14, -112), (12, -91), (8, -91), (10, -110)], SHIRT_SH)
        poly(d, [(-14, -120), (-11, -120), (-10, -91), (-12, -91)], SHIRT_SH)
        poly(d, [(-9, -122), (-3, -122), (-4, -102), (-9, -102)], SHIRT_HI)
        poly(d, [(-6, -134), (6, -134), (0, -119)], SKIN)
        line(d, (-4, -128), (-1, -127), SKIN_SH, 1)
        line(d, (4, -128), (1, -127), SKIN_SH, 1)
        poly(d, [(-9, -133), (-5, -134), (-2, -120), (-9, -124)], SHIRT_HI)
        poly(d, [(9, -133), (5, -134), (2, -120), (9, -124)], SHIRT_HI)
        line(d, (-9, -124), (-2, -120), SHIRT_D, 1)
        line(d, (9, -124), (2, -120), SHIRT_D, 1)
        line(d, (0, -119), (0, -94), SHIRT_SH, 1)
        for yb in (-114, -108, -102, -96):
            rect(d, -1, yb, 2, 2, SHIRT_D)
        ell(d, -4, -95, 8, 5, SHIRT_SH)
        ell(d, -3, -95, 6, 4, SHIRT_HI)
        poly(d, [(-3, -91), (-8, -84), (-4, -83), (-1, -90)], SHIRT)
        poly(d, [(3, -91), (8, -84), (4, -83), (1, -90)], SHIRT_SH)
    elif outfit == 2:
        # Outfit 2: Oversized cozy pastel hoodie with plush collar & white drawstrings
        pts = [
            (-9, -134), (9, -134),
            (17, -127), (19, -110), (18, -92),
            (-18, -92), (-19, -110), (-17, -127)
        ]
        poly(d, pts, HOOD)
        poly(d, [(10, -129), (17, -125), (18, -108), (17, -92), (11, -92), (12, -110)], HOOD_SH)
        poly(d, [(-17, -124), (-12, -124), (-12, -92), (-17, -92)], HOOD_SH)
        poly(d, [(-10, -122), (-2, -122), (-3, -100), (-10, -100)], HOOD_HI)
        ell(d, -11, -136, 22, 10, HOOD_SH)
        ell(d, -9, -135, 18, 7, HOOD_HI)
        poly(d, [(-4, -135), (4, -135), (0, -127)], SKIN)
        line(d, (-3, -127), (-4, -110), WHITE, 1)
        line(d, (3, -127), (4, -112), WHITE, 1)
        rect(d, -5, -110, 2, 2, HOOD_D)
        rect(d, 3, -112, 2, 2, HOOD_D)
        rect(d, -1, -111, 3, 3, WHITE)
        rect(d, 0, -113, 1, 7, WHITE)
        rect(d, -3, -110, 7, 1, WHITE)
    else:
        # Outfit 3: Summer Casual pastel mint fitted T-shirt with white collar trim & heart print
        pts = [
            (-5, -133), (5, -133),
            (13, -128), (14, -120),
            (12, -105), (11, -94),
            (-11, -94), (-12, -105),
            (-14, -120), (-13, -128)
        ]
        poly(d, pts, MINT)
        poly(d, [(8, -128), (13, -126), (13, -116), (11, -94), (7, -94), (9, -112)], MINT_SH)
        poly(d, [(-13, -122), (-10, -122), (-9, -94), (-11, -94)], MINT_SH)
        poly(d, [(-9, -123), (-2, -123), (-3, -102), (-9, -102)], MINT_HI)
        # Round summer crew neck with crisp white trim
        ell(d, -6, -137, 12, 9, SKIN)
        d.arc([OX - 6, OY - 137, OX + 6, OY - 128], 0, 180, fill=WHITE, width=2)
        # Cute small coral heart graphic on front
        rect(d, -2, -116, 2, 2, PINK)
        rect(d, 1, -116, 2, 2, PINK)
        rect(d, -2, -114, 5, 2, PINK)
        rect(d, -1, -112, 3, 1, PINK)
        rect(d, 0, -111, 1, 1, PINK)

    return sel_out(img)


def build_shirt_folds(outfit):
    """Layer 2b: Subtle upper cloth fold accent layer that squashes/sways gently with inertia."""
    img = new_char()
    d = ImageDraw.Draw(img)
    # Soft diagonal fabric fold creases on shirt
    line(d, (-10, -115), (-4, -110), SHIRT_SH, 2)
    line(d, (10, -115), (4, -110), SHIRT_SH, 2)
    line(d, (-9, -116), (-5, -112), SHIRT_HI, 1)
    line(d, (9, -116), (5, -112), SHIRT_HI, 1)
    return img


def build_tie():
    """Layer 5d: Loosely hanging sleek grey necktie (pivots around knot at (0, -126))."""
    img = new_char()
    d = ImageDraw.Draw(img)
    poly(d, [(-2, -127), (2, -127), (2, -123), (-2, -123)], TIE_SH)
    rect(d, -1, -126, 2, 2, TIE_HI)
    poly(d, [(-1.5, -123), (1.5, -123), (3, -99), (0, -93), (-3, -99)], TIE)
    poly(d, [(0, -123), (1.5, -123), (3, -99), (0, -93)], TIE_SH)
    line(d, (-1, -121), (-1.5, -100), TIE_HI, 1)
    return sel_out(img)


def build_arm(outfit, side, pose="idle"):
    """Layer 6: Graceful slender arms — School (0), Home (1), Hoodie (2), Summer Tee (3)."""
    img = new_char()
    d = ImageDraw.Draw(img)
    hoodie = (outfit == 2)
    summer = (outfit == 3)
    school = (outfit == 0)

    if pose == "idle":
        if hoodie:
            if side == -1:
                poly(d, [(-13, -128), (-20, -124), (-29, -82), (-20, -79), (-14, -110)], HOOD)
                line(d, (-20, -122), (-28, -82), HOOD_SH, 2)
                poly(d, [(-29, -85), (-20, -83), (-19, -78), (-28, -80)], HOOD_SH)
                poly(d, [(-26, -79), (-21, -78), (-21, -73), (-25, -74)], SKIN)
            else:
                poly(d, [(13, -128), (20, -124), (29, -89), (21, -78), (15, -83), (18, -96), (14, -112)], HOOD)
                line(d, (20, -122), (28, -89), HOOD_SH, 2)
                poly(d, [(15, -85), (22, -80), (20, -76), (14, -81)], HOOD_SH)
                poly(d, [(15, -80), (19, -77), (18, -73), (14, -76)], SKIN)
        elif summer:
            # Short mint summer tee sleeves + graceful bare arms + cute pink bracelet!
            if side == -1:
                poly(d, [(-11, -128), (-17, -126), (-20, -114), (-14, -113), (-12, -118)], MINT)
                line(d, (-20, -114), (-14, -113), WHITE, 1)
                poly(d, [(-19, -113), (-14, -113), (-21, -82), (-25, -83)], SKIN)
                line(d, (-18, -112), (-24, -83), SKIN_SH, 1)
                poly(d, [(-25, -83), (-21, -82), (-20, -75), (-23, -73), (-26, -77)], SKIN)
                line(d, (-24, -85), (-20, -84), PINK, 2)  # cute bracelet
            else:
                poly(d, [(11, -128), (17, -126), (21, -114), (15, -113), (12, -118)], MINT)
                line(d, (15, -113), (21, -114), WHITE, 1)
                poly(d, [(16, -113), (21, -113), (25, -90), (20, -82), (16, -84), (19, -91)], SKIN)
                line(d, (20, -112), (24, -90), SKIN_SH, 1)
                poly(d, [(16, -84), (20, -82), (19, -76), (15, -75), (14, -79)], SKIN)
        elif side == -1:
            sl_y = -104 if school else -99
            sleeve = [(-11, -128), (-17, -126), (-23, sl_y), (-15, sl_y + 2), (-12, -115)]
            poly(d, sleeve, SHIRT)
            line(d, (-17, -125), (-22, sl_y), SHIRT_SH, 2)
            poly(d, [(-24, sl_y - 2), (-15, sl_y - 1), (-15, sl_y + 3), (-24, sl_y + 2)], SHIRT_HI)
            forearm = [(-22, sl_y + 2), (-16, sl_y + 2), (-21, -82), (-25, -83)]
            poly(d, forearm, SKIN)
            line(d, (-21, sl_y + 3), (-24, -83), SKIN_SH, 1)
            poly(d, [(-25, -83), (-21, -82), (-20, -75), (-23, -73), (-26, -77)], SKIN)
        else:
            sl_y = -104 if school else -99
            sleeve = [(11, -128), (17, -126), (24, sl_y), (16, sl_y + 2), (12, -115)]
            poly(d, sleeve, SHIRT)
            line(d, (17, -125), (23, sl_y), SHIRT_SH, 2)
            poly(d, [(16, sl_y - 1), (25, sl_y - 2), (25, sl_y + 2), (16, sl_y + 3)], SHIRT_HI)
            forearm = [(17, sl_y + 2), (23, sl_y + 2), (25, -90), (20, -82), (16, -84), (19, -91)]
            poly(d, forearm, SKIN)
            line(d, (22, sl_y + 3), (24, -90), SKIN_SH, 1)
            poly(d, [(16, -84), (20, -82), (19, -76), (15, -75), (14, -79)], SKIN)
    elif pose == "wave":
        c_main = HOOD if hoodie else (MINT if summer else SHIRT)
        c_hi = HOOD_HI if hoodie else (WHITE if summer else SHIRT_HI)
        sleeve = [(11, -128), (19, -130), (26, -141), (20, -147), (13, -137)]
        poly(d, sleeve, c_main)
        poly(d, [(19, -146), (26, -140), (28, -143), (22, -149)], c_hi)
        forearm = [(22, -146), (27, -143), (33, -164), (28, -166)]
        poly(d, forearm, HOOD if hoodie else SKIN)
        ell(d, 28, -173, 7, 9, SKIN)
        rect(d, 28, -172, 2, 4, SKIN_HI)

    return sel_out(img)


def build_head_base():
    """Layer 4 base: Slender neck with choker + proportional anime head with soft pointed chin."""
    img = new_char()
    d = ImageDraw.Draw(img)

    # Slender neck
    poly(d, [(-3, -148), (3, -148), (4, -132), (-4, -132)], SKIN)
    poly(d, [(-3, -147), (3, -147), (3.5, -142), (0, -140), (-3.5, -142)], SKIN_SH)
    # Black choker with metallic silver ring
    rect(d, -4, -139, 8, 3, CHOKER)
    ell(d, -2, -137, 4, 4, SILVER)
    rect(d, -1, -136, 2, 2, SKIN)

    # Delicate ears
    ell(d, -18, -164, 4, 7, SKIN)
    ell(d, -17, -163, 2, 4, SKIN_SH)
    ell(d, 14, -164, 4, 7, SKIN)
    ell(d, 15, -163, 2, 4, SKIN_SH)

    # Proportional anime head (~33px wide x 40px tall) with soft tapered V-chin (not a long oval!)
    head_pts = (
        bezier((-16, -169), (-16, -154), (-8, -147), 10) +
        bezier((-8, -147), (0, -142), (8, -147), 10) +
        bezier((8, -147), (16, -154), (16, -169), 10) +
        bezier((16, -169), (15, -186), (0, -188), 10) +
        bezier((0, -188), (-15, -186), (-16, -169), 10)
    )
    poly(d, head_pts, SKIN)
    # Subtle side-cheek warmth & forehead shadow (NO under-eye dark circles!)
    poly(d, [(11, -170), (16, -168), (14, -155), (8, -147), (7, -149), (12, -158)], SKIN_SH)
    rect(d, -14, -176, 28, 4, SKIN_SH)

    return sel_out(img)


def draw_almond_eye(d, cx, cy, side, wide=False):
    """Marin's signature slanted almond-shaped anime eye: confident slight squint, clean winged lashes, NO dark under-eye!"""
    s = side  # -1 for viewer-left eye, +1 for viewer-right eye
    h = 9 if wide else 7
    in_x = cx - s * 4
    out_x = cx + s * 5
    # Clean slanted almond sclera (outer corner subtly lifted)
    sclera = [
        (in_x, cy),
        (cx - s * 1, cy - h // 2),
        (cx + s * 3, cy - h // 2 - 1),
        (out_x, cy - 1),
        (cx + s * 3, cy + h // 2 - 1),
        (cx - s * 2, cy + h // 2 - 1),
    ]
    poly(d, sclera, WHITE)
    # Soft 1px top sclera shade
    line(d, (cx - s * 1, cy - h // 2), (cx + s * 3, cy - h // 2 - 1), (228, 220, 234, 255), 1)

    # Clean thick upper eyeliner (starts delicately at inner corner, thickens outward!)
    line(d, (in_x, cy - 1), (cx - s * 1, cy - h // 2 - 1), LASH, 1)
    line(d, (cx - s * 1, cy - h // 2 - 1), (cx + s * 3, cy - h // 2 - 2), LASH, 2)
    line(d, (cx + s * 3, cy - h // 2 - 2), (out_x + s * 1, cy - 2), LASH, 2)
    # Confident winged outer eyelash flick
    line(d, (out_x, cy - 2), (out_x + s * 2, cy - 4), LASH, 1)
    # Delicate double eyelid crease
    line(d, (cx - s * 2, cy - h // 2 - 3), (cx + s * 2, cy - h // 2 - 4), SKIN_SH, 1)


def build_iris():
    """Almond-fitted iris (7x7): deep burgundy/purple top -> magenta -> bright pink bottom + crisp highlight & lower glow."""
    img = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([1, 1, 6, 6], fill=EYE_MID)
    arr = np.array(img, dtype=np.uint8)
    for y in range(1, 7):
        f = (y - 1) / 5.0
        col = lerp_c(EYE_TOP, EYE_MID, f * 2) if f < 0.5 else lerp_c(EYE_MID, EYE_BOT, (f - 0.5) * 2)
        for x in range(1, 7):
            if arr[y, x, 3] > 0:
                arr[y, x] = col
    # Deep pupil center
    arr[3:5, 3:5] = (62, 18, 48, 255)
    # Soft bright pink lower crescent glow
    arr[6, 3:5] = EYE_GLOW
    arr[5, 2] = EYE_GLOW
    arr[5, 5] = EYE_GLOW
    # Crisp white anime highlight at upper-left
    arr[2, 2] = WHITE
    arr[2, 3] = WHITE
    arr[3, 2] = WHITE
    return Image.fromarray(arr, "RGBA")


def build_face(emotion):
    """Layer 4 emotion overlay: 8 distinct expressions (+ blink)."""
    img = new_char()
    d = ImageDraw.Draw(img)

    # Cheek blush (clean warm pink)
    if emotion == "blush":
        bl = (255, 118, 148, 200)
        ell(d, -14, -156, 8, 4, bl)
        ell(d, 6, -156, 8, 4, bl)
        for bx in (-12, -10, -8, 8, 10, 12):
            line(d, (bx, -155), (bx + 1, -153), (236, 84, 116, 210), 1)
    elif emotion == "pout":
        bl = (252, 138, 160, 165)
        ell(d, -14, -155, 7, 4, bl)
        ell(d, 7, -155, 7, 4, bl)
    else:
        blush_a = 155 if emotion in ("pet", "starry", "smug") else 90
        bl = (252, 146, 166, blush_a)
        ell(d, -13, -155, 6, 3, bl)
        ell(d, 7, -155, 6, 3, bl)
        if emotion in ("pet", "starry"):
            line(d, (-11, -154), (-10, -153), (242, 114, 138, 170), 1)
            line(d, (9, -154), (10, -153), (242, 114, 138, 170), 1)

    # Eyebrows
    if emotion == "pout":
        line(d, (-12, -169), (-4, -166), BROW, 1)
        line(d, (4, -166), (12, -169), BROW, 1)
    elif emotion == "blush":
        line(d, (-12, -167), (-4, -170), BROW, 1)
        line(d, (4, -170), (12, -167), BROW, 1)
    elif emotion == "surprised":
        line(d, (-12, -170), (-4, -171), BROW, 1)
        line(d, (4, -171), (12, -170), BROW, 1)
    else:
        line(d, (-12, -167), (-4, -168), BROW, 1)
        line(d, (4, -168), (12, -167), BROW, 1)

    # Eyes (y = -161)
    if emotion in ("normal", "blush", "pout"):
        draw_almond_eye(d, -8, -161, -1, wide=False)
        draw_almond_eye(d, 8, -161, 1, wide=False)
    elif emotion == "surprised":
        draw_almond_eye(d, -8, -161, -1, wide=True)
        draw_almond_eye(d, 8, -161, 1, wide=True)
    elif emotion == "smug":
        # Playful confident half-lidded gaze
        draw_almond_eye(d, -8, -161, -1, wide=False)
        draw_almond_eye(d, 8, -161, 1, wide=False)
        rect(d, -13, -165, 10, 3, SKIN)
        rect(d, 3, -165, 10, 3, SKIN)
        line(d, (-13, -162), (-3, -162), LASH, 2)
        line(d, (3, -162), (13, -162), LASH, 2)
    elif emotion == "starry":
        # Bright excited eyes with golden pixel stars!
        draw_almond_eye(d, -8, -161, -1, wide=True)
        draw_almond_eye(d, 8, -161, 1, wide=True)
        for cx in (-8, 8):
            ell(d, cx - 3, -164, 6, 6, EYE_MID)
            # Bright golden 4-point star inside each eye
            rect(d, cx - 1, -163, 2, 4, (255, 240, 120, 255))
            rect(d, cx - 2, -162, 4, 2, (255, 240, 120, 255))
            rect(d, cx, -162, 1, 1, WHITE)
    elif emotion == "sleepy":
        # Droopy half-closed sleepy eyes
        for cx in (-8, 8):
            rect(d, cx - 4, -161, 8, 3, WHITE)
            rect(d, cx - 2, -161, 4, 2, EYE_MID)
            line(d, (cx - 5, -161), (cx + 5, -161), LASH, 2)
    elif emotion == "pet":
        # Happy squeezed ^ ^ eyes
        for cx in (-8, 8):
            pts = bezier((cx - 5, -160), (cx, -165), (cx + 5, -160), 10)
            for i in range(len(pts) - 1):
                line(d, pts[i], pts[i + 1], LASH, 2)
    elif emotion == "blink":
        for cx in (-8, 8):
            pts = bezier((cx - 5, -161), (cx, -159), (cx + 5, -161), 10)
            for i in range(len(pts) - 1):
                line(d, pts[i], pts[i + 1], LASH, 2)

    # Delicate nose dot
    rect(d, 0, -155, 1, 1, SKIN_D)

    # Mouth
    if emotion == "normal":
        line(d, (-3, -149), (2, -149), MOUTH_C, 1)
        rect(d, 3, -150, 1, 1, MOUTH_C)
        rect(d, 4, -151, 1, 1, SKIN_SH)
    elif emotion == "pet":
        pts = bezier((-4, -150), (0, -147), (4, -150), 8)
        for i in range(len(pts) - 1):
            line(d, pts[i], pts[i + 1], MOUTH_C, 1)
    elif emotion == "blush":
        for x, y in ((-3, -149), (-2, -150), (-1, -149), (0, -148), (1, -149), (2, -150), (3, -149)):
            rect(d, x, y, 1, 1, MOUTH_C)
    elif emotion == "smug":
        # Confident playful cat-like grin
        line(d, (-4, -150), (-1, -148), MOUTH_C, 1)
        line(d, (-1, -148), (2, -148), MOUTH_C, 1)
        line(d, (2, -148), (5, -151), MOUTH_C, 1)
    elif emotion == "surprised":
        ell(d, -2, -151, 4, 4, MOUTH_IN)
        d.ellipse([OX - 2, OY - 151, OX + 2, OY - 147], outline=MOUTH_C)
    elif emotion == "sleepy":
        # Cute soft yawning oval
        ell(d, -2, -152, 5, 5, MOUTH_IN)
        d.ellipse([OX - 2, OY - 152, OX + 2, OY - 147], outline=MOUTH_C)
    elif emotion == "pout":
        # Tiny pouty frown + puffed cheek lines
        line(d, (-2, -149), (0, -150), MOUTH_C, 1)
        line(d, (0, -150), (2, -149), MOUTH_C, 1)
        line(d, (-11, -151), (-11, -148), SKIN_D, 1)
        line(d, (11, -151), (11, -148), SKIN_D, 1)
    elif emotion == "starry":
        poly(d, [(-4, -151), (4, -151), (3, -146), (-3, -146)], MOUTH_IN)
        line(d, (-4, -151), (4, -151), MOUTH_C, 1)
        line(d, (-3, -146), (3, -146), MOUTH_C, 1)
    elif emotion == "blink":
        line(d, (-3, -149), (2, -149), MOUTH_C, 1)
        rect(d, 3, -150, 1, 1, MOUTH_C)

    return img


def build_hair_back():
    """Layer 5a: Long flowing golden-blonde back hair tapering to pointed coral-pink tips."""
    img = new_char()
    d = ImageDraw.Draw(img)

    left_edge = bezier((-18, -176), (-26, -138), (-31, -86), 14)
    bottom_wisps = [
        (-31, -86), (-27, -76), (-21, -86), (-16, -78),
        (-10, -86), (0, -80), (10, -86), (16, -78),
        (21, -86), (27, -76), (31, -86)
    ]
    right_edge = bezier((31, -86), (26, -138), (18, -176), 14)
    top_arc = bezier((18, -176), (0, -193), (-18, -176), 10)
    poly(d, left_edge + bottom_wisps + right_edge + top_arc, HAIR)

    poly(d, [(-15, -154), (15, -154), (19, -88), (-19, -88)], HAIR_SH)
    for sx in (-23, -17, 17, 23):
        line(d, (sx, -142), (sx + (3 if sx > 0 else -3), -92), HAIR_HI, 2)

    img = hair_gradient_fill(img, OY - 166, OY - 76, pink_start=0.52, steps=6)
    return sel_out(img)


def build_hair_side(side):
    """Layer 5b/5c: Tapered flowing front side locks past chest with 6-step coral-pink gradient."""
    img = new_char()
    d = ImageDraw.Draw(img)
    s = side

    # Smooth curved lock framing face and tapering to a graceful pointed tip past chest
    outer = bezier((s * 15, -178), (s * 20, -148), (s * 16, -104), 14)
    tip = [(s * 16, -104), (s * 12, -92), (s * 10, -106)]
    inner = bezier((s * 10, -106), (s * 14, -146), (s * 12, -174), 14)
    poly(d, outer + tip + inner, HAIR)

    sh = bezier((s * 13, -168), (s * 15, -144), (s * 12, -104), 10)
    for i in range(len(sh) - 1):
        line(d, sh[i], sh[i + 1], HAIR_SH, 1)
    hi = bezier((s * 15, -168), (s * 18, -146), (s * 15, -114), 10)
    for i in range(len(hi) - 1):
        line(d, hi[i], hi[i + 1], HAIR_HI, 1)

    img = hair_gradient_fill(img, OY - 170, OY - 92, pink_start=0.52, steps=6)
    return sel_out(img)


def build_hair_bangs():
    """Layer 4 top: Smooth rounded crown (NO ahoge!) + straight-cut wispy feathered bangs with gaps."""
    img = new_char()
    d = ImageDraw.Draw(img)

    # Smooth rounded crown with subtle natural center-left part (NO ahoge!)
    crown = (
        bezier((-18, -168), (-19, -189), (0, -191), 12) +
        bezier((0, -191), (19, -189), (18, -168), 12) +
        [(15, -169), (10, -175), (0, -174), (-10, -175), (-15, -169)]
    )
    poly(d, crown, HAIR)

    # Sharp, thin, uneven feathered bang strands lightly grazing top of eyes with clean skin gaps
    strands = [
        ((-16, -176), (-14, -162), (-11, -174)),
        ((-12, -178), (-10, -167), (-7, -176)),
        ((-7, -178), (-4, -165), (-2, -176)),
        ((-2, -179), (0, -166), (2, -176)),
        ((2, -178), (5, -165), (7, -176)),
        ((7, -178), (10, -167), (12, -175)),
        ((11, -176), (14, -162), (16, -173)),
    ]
    for p0, tip, p2 in strands:
        poly(d, [p0, tip, p2], HAIR)
        line(d, ((p0[0] + p2[0]) // 2, p0[1] + 2), tip, HAIR_SH, 1)

    # Soft anime crown halo highlight & subtle part shadow
    halo = bezier((-11, -182), (0, -185), (11, -182), 10)
    for i in range(len(halo) - 1):
        line(d, halo[i], halo[i + 1], HAIR_HI, 2)
    line(d, (-1, -190), (-1, -179), HAIR_SH, 1)

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

    # Rug & floor clutter
    d.ellipse([172, 304, 476, 356], fill=(138, 96, 86), outline=OUT)
    d.ellipse([178, 308, 470, 352], fill=(182, 136, 118))
    d.ellipse([204, 314, 444, 346], outline=(158, 112, 98), width=2)
    d.rectangle([216, 274, 244, 286], fill=(124, 72, 92), outline=OUT, width=1)
    d.line([(218, 283), (242, 283)], fill=(244, 240, 232), width=2)
    d.rounded_rectangle([464, 326, 514, 352], radius=8, fill=(214, 176, 142), outline=OUT, width=2)

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
    """3 distinct anime/cosplay pixel posters (48x66)."""
    OUT = (54, 36, 44, 255)
    img = Image.new("RGBA", (48, 66), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if idx == 0:
        # Original dark-haired anime idol poster (from reference)
        d.rectangle([0, 0, 47, 65], fill=(112, 96, 146, 255), outline=OUT, width=2)
        d.rectangle([6, 6, 42, 11], fill=(236, 220, 244, 255))
        d.ellipse([14, 20, 34, 42], fill=(64, 46, 58, 255))
        d.ellipse([17, 24, 30, 38], fill=(238, 198, 172, 255))
        d.polygon([(10, 63), (15, 42), (33, 42), (38, 63)], fill=(72, 52, 66, 255))
    elif idx == 1:
        # Magical-girl pink & gold star cosplay poster ("Shizuku-tan / Magical")
        d.rectangle([0, 0, 47, 65], fill=(232, 142, 176, 255), outline=OUT, width=2)
        d.rectangle([5, 5, 42, 11], fill=(255, 244, 178, 255))
        d.ellipse([13, 18, 35, 40], fill=(116, 76, 168, 255))
        d.ellipse([17, 22, 31, 36], fill=(255, 224, 206, 255))
        d.polygon([(9, 63), (15, 40), (33, 40), (39, 63)], fill=(76, 60, 122, 255))
        # Cute star motif
        d.rectangle([34, 16, 38, 20], fill=(255, 244, 160, 255))
        d.rectangle([8, 44, 12, 48], fill=(255, 244, 160, 255))
    else:
        # Neon cyan/magenta cyberpunk anime poster
        d.rectangle([0, 0, 47, 65], fill=(38, 46, 86, 255), outline=OUT, width=2)
        d.rectangle([5, 6, 42, 10], fill=(104, 236, 232, 255))
        d.ellipse([12, 18, 36, 42], fill=(236, 84, 148, 255))
        d.ellipse([17, 23, 31, 37], fill=(255, 224, 206, 255))
        d.rectangle([17, 27, 31, 30], fill=(104, 236, 232, 255))  # neon visor!
        d.polygon([(11, 63), (16, 42), (32, 42), (37, 63)], fill=(54, 184, 196, 255))
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
    """Wearable stylish red-framed cosplay glasses on head canvas (CW, CH)."""
    img = new_char()
    d = ImageDraw.Draw(img)
    frame = (212, 56, 78, 255)
    frame_hi = (255, 136, 152, 255)
    lens = (204, 238, 255, 115)
    for cx in (-8, 8):
        rect(d, cx - 5, -165, 10, 8, lens)
        d.rectangle([OX + cx - 6, OY - 166, OX + cx + 5, OY - 157], outline=frame, width=2)
        line(d, (cx - 4, -164), (cx - 2, -164), WHITE, 1)
        line(d, (cx - 4, -166), (cx + 3, -166), frame_hi, 1)
    # Bridge & temples
    line(d, (-2, -162), (2, -162), frame, 2)
    line(d, (-15, -163), (-14, -163), frame, 2)
    line(d, (14, -163), (15, -163), frame, 2)
    return img


def build_acc_ears():
    """Wearable cute plush cat-ear headband on head canvas (CW, CH)."""
    img = new_char()
    d = ImageDraw.Draw(img)
    ear_dark = (46, 34, 52, 255)
    ear_hi = (78, 60, 88, 255)
    ear_in = (248, 148, 178, 255)
    # Thin headband arc across crown
    pts = bezier((-15, -182), (0, -193), (15, -182), 12)
    for i in range(len(pts) - 1):
        line(d, pts[i], pts[i + 1], ear_dark, 2)
    # Left & right cat ears
    for s in (-1, 1):
        poly(d, [(s * 14, -184), (s * 15, -202), (s * 4, -189)], ear_dark)
        poly(d, [(s * 12, -186), (s * 13, -197), (s * 6, -189)], ear_in)
        line(d, (s * 14, -199), (s * 6, -189), ear_hi, 1)
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


def build_night_lamp_glow():
    return make_lamp_glow((606, 162), 290)


def generate_all():
    for outfit in (0, 1, 2, 3):
        build_legs(outfit, air=False).save(os.path.join(ASSETS, f"legs_{outfit}_stand.png"))
        build_legs(outfit, air=True).save(os.path.join(ASSETS, f"legs_{outfit}_air.png"))
        build_lower_garment(outfit).save(os.path.join(ASSETS, f"skirt_{outfit}.png"))
        build_torso(outfit).save(os.path.join(ASSETS, f"torso_{outfit}.png"))
        build_shirt_folds(outfit).save(os.path.join(ASSETS, f"folds_{outfit}.png"))
        build_arm(outfit, -1, "idle").save(os.path.join(ASSETS, f"arm_l_{outfit}.png"))
        build_arm(outfit, 1, "idle").save(os.path.join(ASSETS, f"arm_r_{outfit}.png"))
        build_arm(outfit, 1, "wave").save(os.path.join(ASSETS, f"arm_r_{outfit}_wave.png"))

    build_tie().save(os.path.join(ASSETS, "tie.png"))
    build_head_base().save(os.path.join(ASSETS, "head_base.png"))
    build_iris().save(os.path.join(ASSETS, "iris.png"))
    for emo in ("normal", "pet", "blush", "smug", "surprised", "sleepy", "pout", "starry", "blink"):
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
    build_curtain_panel(86, 132).save(os.path.join(ASSETS, "curtain_panel.png"))
    for i in range(3):
        build_poster(i).save(os.path.join(ASSETS, f"poster_{i}.png"))
    build_drawer_open().save(os.path.join(ASSETS, "drawer_open.png"))
    build_night_lamp_glow().save(os.path.join(ASSETS, "lamp_glow.png"))

    for kind in ("rock", "paper", "scissors"):
        build_rps_icon(kind).save(os.path.join(ASSETS, f"rps_{kind}.png"))

    # Neutral base room + standalone sky patches for buttery-smooth lighting lerp!
    build_room(0, False).save(os.path.join(ASSETS, "room_base.png"))
    build_room(0, True).save(os.path.join(ASSETS, "room_base_open.png"))
    for mode, name in ((0, "day"), (1, "sunset"), (2, "night")):
        build_sky_patch(mode).save(os.path.join(ASSETS, f"sky_{name}.png"))

    print("Generated v0.2-beta assets (4 outfits, 2 accessories, camera/glasses, RPS, lerp skies) in", ASSETS)


if __name__ == "__main__":
    generate_all()
