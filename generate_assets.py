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
def build_legs(outfit, pose="stand"):
    """Layer 0: Natural contrapposto stance ('stand'), tucked ('air'), or dangling on bed edge ('sit')."""
    img = new_char()
    d = ImageDraw.Draw(img)

    if pose == "floor":
        # Cute slender anime yokozuwari (side-sit / mermaid pose): knees neatly together, calves tucked to one side!
        # Left thigh (viewer-left) angled gently toward center-left
        poly(d, [(-11, -82), (-14, -66), (-11, -50), (-3, -49), (-1, -66), (-1, -82)], SKIN)
        poly(d, [(-14, -66), (-11, -50), (-8, -50), (-10, -66)], SKIN_SH)
        # Right thigh tucked neatly right next to left knee, angling slightly right
        poly(d, [(0, -82), (11, -82), (13, -65), (9, -50), (-1, -50), (-2, -66)], SKIN)
        poly(d, [(7, -82), (11, -82), (13, -65), (9, -50), (6, -50), (9, -65)], SKIN_SH)
        # Subtle knee highlights (knees cleanly close together!)
        ell(d, -9, -54, 4, 3, SKIN_HI)
        ell(d, 2, -54, 4, 3, SKIN_HI)

        # Both slender calves folded gracefully to viewer-right side (classic neat anime floor sit!)
        # Back calf (from left knee tucked behind/beside right knee)
        poly(d, [(6, -56), (20, -52), (24, -46), (11, -46)], SKIN)
        # Front calf (from right knee curving neatly to right)
        poly(d, [(9, -53), (23, -49), (26, -44), (10, -45)], SKIN)
        poly(d, [(10, -47), (24, -46), (25, -44), (10, -45)], SKIN_SH)

        # Outfit-matched socks & dainty tucked shoes/slippers on the side
        if outfit in (0, 4):
            poly(d, [(13, -53), (23, -49), (25, -44), (14, -45)], SOCK)
            poly(d, [(21, -51), (28, -48), (27, -43), (20, -44)], SHOE)
            rect(d, 22, -49, 4, 2, SHOE_HI)
        elif outfit == 1:
            poly(d, [(20, -51), (28, -48), (27, -43), (19, -44)], SLIP)
            rect(d, 21, -49, 4, 2, SLIP_HI)
        elif outfit == 2:
            poly(d, [(11, -54), (23, -49), (25, -44), (12, -45)], SOCK)
            line(d, (12, -52), (13, -46), WHITE, 1)
            poly(d, [(21, -51), (28, -48), (27, -43), (20, -44)], SNEAK)
            rect(d, 22, -45, 5, 2, SNEAK_HI)
        else:
            poly(d, [(18, -51), (23, -49), (24, -44), (18, -45)], WHITE)
            poly(d, [(21, -51), (28, -48), (27, -43), (20, -44)], WHITE)
            rect(d, 22, -47, 5, 2, MINT)
        return sel_out(img)

    if pose == "sit":
        # Sitting naturally on the edge of the bed: thighs angled forward, calves dangling!
        for side in (-1, 1):
            s = side
            # Thigh resting forward on mattress
            poly(d, [(s * 12, -82), (s * 14, -64), (s * 13, -52), (s * 3, -52), (s * 2, -70), (s * 2, -82)], SKIN)
            poly(d, [(s * 10, -82), (s * 14, -64), (s * 13, -52), (s * 9, -52), (s * 9, -82)], SKIN_SH)
            # Dangling lower leg slightly angled
            poly(d, [(s * 12.5, -54), (s * 11, -30), (s * 9.5, -14), (s * 3.5, -14), (s * 4, -32), (s * 3.5, -54)], SKIN)
            ell(d, s * 8 - 2, -55, 4, 3, SKIN_HI)
            if outfit in (0, 4):
                poly(d, [(s * 11, -34), (s * 9.5, -14), (s * 3.5, -14), (s * 4, -34)], SOCK)
                poly(d, [(s * 10, -16), (s * 11.5, -9), (s * 9, -7), (s * 3, -8), (s * 3.5, -16)], SHOE)
                rect(d, min(s * 9, s * 4), -14, 5, 2, SHOE_HI)
            elif outfit == 1:
                poly(d, [(s * 10, -16), (s * 11.5, -9), (s * 9, -7), (s * 3, -8), (s * 3.5, -16)], SLIP)
                rect(d, min(s * 9, s * 4), -14, 5, 2, SLIP_HI)
            elif outfit == 2:
                poly(d, [(s * 12, -48), (s * 11, -30), (s * 9.5, -14), (s * 3.5, -14), (s * 4, -32), (s * 4, -48)], SOCK)
                line(d, (s * 4, -45), (s * 11.5, -45), WHITE, 1)
                poly(d, [(s * 10, -16), (s * 11.5, -9), (s * 9, -7), (s * 3, -8), (s * 3.5, -16)], SNEAK)
                rect(d, min(s * 9, s * 4), -9, 6, 2, SNEAK_HI)
            else:
                poly(d, [(s * 10, -21), (s * 9.5, -14), (s * 3.5, -14), (s * 4, -21)], WHITE)
                poly(d, [(s * 10, -16), (s * 11.5, -9), (s * 9, -7), (s * 3, -8), (s * 3.5, -16)], WHITE)
                rect(d, min(s * 9, s * 4), -12, 6, 2, MINT)
        return sel_out(img)

    air = (pose == "air")

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

        if outfit in (0, 4):
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
            if outfit in (0, 4):
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
    """Layer 1: Pleated skirt (0, 4), Home shorts (1), Hoodie hem (2), Blue denim shorts (3)."""
    img = new_char()
    d = ImageDraw.Draw(img)
    if outfit in (0, 4):
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


def build_torso(outfit, relaxed=False):
    """Layer 2: Narrow sloping shoulders, slender waist, crisp collared shirts + relaxed top-button variant."""
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
        poly(d, [(8, -128), (13, -126), (13, -116), (11, -94), (7, -94), (9, -112)], SHIRT_SH)
        poly(d, [(-13, -122), (-10, -122), (-9, -94), (-11, -94)], SHIRT_SH)
        poly(d, [(-9, -124), (-3, -124), (-4, -106), (-9, -106)], SHIRT_HI)
        rect(d, 4, -116, 6, 6, SHIRT_SH)
        rect(d, 5, -115, 4, 4, SHIRT)
        # V-neck depth: standard vs relaxed undone 1-2 top buttons
        v_bot = -111 if relaxed else -121
        v_w = 8 if relaxed else 5
        poly(d, [(-v_w, -134), (v_w, -134), (0, v_bot)], SKIN)
        poly(d, [(-v_w + 1, -134), (v_w - 1, -134), (0, -130)], SKIN_SH)
        line(d, (-5, -127), (-1, -125), SKIN_SH, 1)
        line(d, (5, -127), (1, -125), SKIN_SH, 1)
        if relaxed:
            line(d, (-v_w, -134), (0, v_bot), SHIRT_D, 1)
            line(d, (v_w, -134), (0, v_bot), SHIRT_D, 1)
        # Folded white shirt collar lapels
        lap_x = 12 if relaxed else 9
        poly(d, [(-lap_x, -133), (-v_w + 1, -134), (-2, v_bot + 2), (-lap_x, -121)], SHIRT_HI)
        poly(d, [(lap_x, -133), (v_w - 1, -134), (2, v_bot + 2), (lap_x, -121)], SHIRT_HI)
        line(d, (-lap_x, -121), (-2, v_bot + 2), SHIRT_D, 1)
        line(d, (lap_x, -121), (2, v_bot + 2), SHIRT_D, 1)
        # Waist knot
        ell(d, -4, -96, 8, 5, SHIRT_SH)
        ell(d, -3, -96, 6, 4, SHIRT_HI)
        poly(d, [(-3, -92), (-8, -86), (-4, -85), (-1, -91)], SHIRT)
        poly(d, [(3, -92), (8, -86), (4, -85), (1, -91)], SHIRT_SH)
    elif outfit == 1:
        # Loose home white shirt with waist knot (+ deeper unbuttoned relaxed variant!)
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
        v_bot = -109 if relaxed else -119
        v_w = 9 if relaxed else 6
        poly(d, [(-v_w, -134), (v_w, -134), (0, v_bot)], SKIN)
        poly(d, [(-v_w + 1, -134), (v_w - 1, -134), (0, -130)], SKIN_SH)
        line(d, (-5, -127), (-1, -125), SKIN_SH, 1)
        line(d, (5, -127), (1, -125), SKIN_SH, 1)
        if relaxed:
            line(d, (-v_w, -134), (0, v_bot), SHIRT_D, 1)
            line(d, (v_w, -134), (0, v_bot), SHIRT_D, 1)
        lap_x = 13 if relaxed else 9
        poly(d, [(-lap_x, -132), (-v_w + 1, -134), (-3, v_bot + 3), (-lap_x, -120)], SHIRT_HI)
        poly(d, [(lap_x, -132), (v_w - 1, -134), (3, v_bot + 3), (lap_x, -120)], SHIRT_HI)
        line(d, (-lap_x, -120), (-3, v_bot + 3), SHIRT_D, 1)
        line(d, (lap_x, -120), (3, v_bot + 3), SHIRT_D, 1)
        line(d, (0, v_bot), (0, -94), SHIRT_SH, 1)
        for yb in range(v_bot + 4, -95, 6):
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
    elif outfit == 3:
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
        ell(d, -6, -137, 12, 9, SKIN)
        d.arc([OX - 6, OY - 137, OX + 6, OY - 128], 0, 180, fill=WHITE, width=2)
        rect(d, -2, -116, 2, 2, PINK)
        rect(d, 1, -116, 2, 2, PINK)
        rect(d, -2, -114, 5, 2, PINK)
        rect(d, -1, -112, 3, 1, PINK)
        rect(d, 0, -111, 1, 1, PINK)
    else:
        # Outfit 4: Canon Relaxed Shirt — clearly readable unbuttoned V-neck, folded lapels & collarbones!
        pts = [
            (-6, -133), (6, -133),
            (14, -128), (15, -119),
            (13, -105), (12, -93),
            (-12, -93), (-13, -105),
            (-15, -119), (-14, -128)
        ]
        poly(d, pts, SHIRT)
        # Soft anime cloth shading & waist folds
        poly(d, [(8, -128), (14, -125), (14, -115), (12, -93), (7, -93), (9, -112)], SHIRT_SH)
        poly(d, [(-14, -121), (-10, -121), (-9, -93), (-12, -93)], SHIRT_SH)
        poly(d, [(-9, -122), (-3, -122), (-4, -104), (-9, -104)], SHIRT_HI)
        # Clearly readable wide unbuttoned V-neck showing neck & collarbones (1-2 buttons undone when relaxed!)
        v_bot = -108 if relaxed else -116
        v_w = 9 if relaxed else 7
        poly(d, [(-v_w, -134), (v_w, -134), (0, v_bot)], SKIN)
        poly(d, [(-v_w + 1, -134), (v_w - 1, -134), (0, -130)], SKIN_SH)
        # Crisp delicate collarbone shading inside V-neck
        line(d, (-5, -127), (-1, -125), SKIN_SH, 1)
        line(d, (5, -127), (1, -125), SKIN_SH, 1)
        line(d, (-v_w, -134), (0, v_bot), SHIRT_D, 1)
        line(d, (v_w, -134), (0, v_bot), SHIRT_D, 1)
        # Crisp folded-out white collar lapels!
        lap_x = 13 if relaxed else 11
        poly(d, [(-lap_x, -131), (-v_w + 1, -134), (-3, v_bot + 3), (-lap_x, -121)], SHIRT_HI)
        poly(d, [(lap_x, -131), (v_w - 1, -134), (3, v_bot + 3), (lap_x, -121)], SHIRT_HI)
        line(d, (-lap_x, -121), (-3, v_bot + 3), SHIRT_D, 1)
        line(d, (lap_x, -121), (3, v_bot + 3), SHIRT_D, 1)
        # Shirt pocket & neat placket buttons below V-opening
        rect(d, 5, -112, 6, 6, SHIRT_SH)
        rect(d, 6, -111, 4, 4, SHIRT)
        line(d, (0, v_bot), (0, -94), SHIRT_SH, 1)
        for yb in range(v_bot + 4, -95, 6):
            rect(d, -1, yb, 2, 2, SHIRT_D)

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


def build_tie(relaxed=False):
    """Layer 5d (Outfit 0): Sleek grey necktie (standard or loosened below V-neck)."""
    img = new_char()
    d = ImageDraw.Draw(img)
    ky = -120 if relaxed else -127
    if relaxed:
        line(d, (-5, -131), (-1, ky + 1), TIE_SH, 1)
        line(d, (5, -131), (1, ky + 1), TIE_SH, 1)
    poly(d, [(-2, ky), (2, ky), (2, ky + 4), (-2, ky + 4)], TIE_SH)
    rect(d, -1, ky + 1, 2, 2, TIE_HI)
    poly(d, [(-1.5, ky + 4), (1.5, ky + 4), (3, ky + 28), (0, ky + 34), (-3, ky + 28)], TIE)
    poly(d, [(0, ky + 4), (1.5, ky + 4), (3, ky + 28), (0, ky + 34)], TIE_SH)
    line(d, (-1, ky + 6), (-1.5, ky + 27), TIE_HI, 1)
    return sel_out(img)


def build_tie_loose(relaxed=False):
    """Layer 5d (Outfit 4): Loosened navy-blue necktie sitting cleanly BELOW the open V-neck."""
    img = new_char()
    d = ImageDraw.Draw(img)
    nt_hi = (98, 124, 178, 255)
    nt    = (64, 86, 138, 255)
    nt_sh = (42, 56, 98, 255)
    ky = -112 if relaxed else -117
    # Loose collar cords tucked neatly along inner V-neck edge (leaving V-neck skin clear!)
    line(d, (-6, -131), (-1, ky + 1), nt_sh, 1)
    line(d, (6, -131), (1, ky + 1), nt_sh, 1)
    poly(d, [(-2, ky), (2, ky), (2, ky + 4), (-2, ky + 4)], nt_sh)
    rect(d, -1, ky + 1, 2, 2, nt_hi)
    poly(d, [(-1.5, ky + 4), (1.5, ky + 4), (3, ky + 24), (0, ky + 29), (-3, ky + 24)], nt)
    poly(d, [(0, ky + 4), (1.5, ky + 4), (3, ky + 24), (0, ky + 29)], nt_sh)
    line(d, (-1, ky + 6), (-1.5, ky + 23), nt_hi, 1)
    return sel_out(img)


def build_arm(outfit, side, pose="idle"):
    """Layer 6: Graceful slender arms — School (0), Home (1), Hoodie (2), Summer (3), Canon Short-Sleeve (4)."""
    img = new_char()
    d = ImageDraw.Draw(img)
    hoodie = (outfit == 2)
    summer = (outfit == 3)
    relaxed = (outfit == 4)
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
        elif summer or relaxed:
            c_sl = MINT if summer else SHIRT
            c_trim = WHITE if summer else SHIRT_SH
            if side == -1:
                poly(d, [(-11, -128), (-17, -126), (-21, -112), (-14, -111), (-12, -118)], c_sl)
                line(d, (-21, -112), (-14, -111), c_trim, 1)
                poly(d, [(-19, -111), (-14, -111), (-21, -82), (-25, -83)], SKIN)
                line(d, (-18, -110), (-24, -83), SKIN_SH, 1)
                poly(d, [(-25, -83), (-21, -82), (-20, -75), (-23, -73), (-26, -77)], SKIN)
                line(d, (-24, -85), (-20, -84), PINK if summer else SILVER, 2)
            else:
                poly(d, [(11, -128), (17, -126), (22, -112), (15, -111), (12, -118)], c_sl)
                line(d, (15, -111), (22, -112), c_trim, 1)
                poly(d, [(16, -111), (21, -111), (25, -90), (20, -82), (16, -84), (19, -91)], SKIN)
                line(d, (20, -110), (24, -90), SKIN_SH, 1)
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
    elif pose == "collar":
        # Left OR right hand raised gently to top shirt collar/button for expressive 2-hand unbutton animation!
        s = side
        c_main = HOOD if hoodie else (MINT if summer else SHIRT)
        sleeve = [(s * 11, -128), (s * 18, -126), (s * 22, -112), (s * 14, -111), (s * 12, -118)]
        poly(d, sleeve, c_main)
        forearm = [(s * 15, -112), (s * 21, -113), (s * 12, -122), (s * 4, -125), (s * 4, -120), (s * 13, -115)]
        poly(d, forearm, HOOD if hoodie else SKIN)
        ell(d, (1 if s == 1 else -7), -126, 6, 5, SKIN)
    elif pose == "stretch":
        # Sweet overhead stretch arms (both left & right sides!)
        s = side
        c_main = HOOD if hoodie else (MINT if summer else SHIRT)
        c_hi = HOOD_HI if hoodie else (WHITE if summer else SHIRT_HI)
        sleeve = [(s * 11, -128), (s * 18, -130), (s * 24, -142), (s * 17, -147), (s * 12, -136)]
        poly(d, sleeve, c_main)
        poly(d, [(s * 17, -146), (s * 24, -141), (s * 26, -144), (s * 19, -149)], c_hi)
        forearm = [(s * 19, -146), (s * 24, -144), (s * 22, -172), (s * 17, -173)]
        poly(d, forearm, HOOD if hoodie else SKIN)
        ell(d, (16 if s == 1 else -23), -180, 7, 8, SKIN)
    elif pose == "manga":
        # Arms bent inward & forward visibly gripping the left/right sides of the open manga book!
        s = side
        c_main = HOOD if hoodie else (MINT if summer else SHIRT)
        c_sh = HOOD_SH if hoodie else (MINT_SH if summer else SHIRT_SH)
        # Upper arm going down & forward from shoulder
        sleeve = [(s * 11, -128), (s * 18, -125), (s * 21, -106), (s * 14, -106), (s * 12, -118)]
        poly(d, sleeve, c_main)
        line(d, (s * 18, -124), (s * 20, -107), c_sh, 1)
        # Bent forearm angling cleanly INWARD across waist to hold the open book edges
        forearm = [(s * 20, -107), (s * 14, -108), (s * 12, -96), (s * 19, -95)]
        poly(d, forearm, HOOD if hoodie else SKIN)
        # Cute hand & fingers gripping the outer edge of the manga at x = ±12..15, y = -101..-94
        ell(d, (10 if s == 1 else -16), -101, 6, 6, SKIN)
        rect(d, (10 if s == 1 else -12), -99, 2, 3, SKIN_HI)
    elif pose == "manga_turn":
        # Right hand lifted up toward upper page corner to flip a manga page!
        c_main = HOOD if hoodie else (MINT if summer else SHIRT)
        sleeve = [(11, -128), (18, -125), (21, -108), (14, -108), (12, -118)]
        poly(d, sleeve, c_main)
        forearm = [(19, -109), (14, -109), (6, -113), (8, -108), (16, -104)]
        poly(d, forearm, HOOD if hoodie else SKIN)
        ell(d, 3, -115, 6, 5, SKIN)
    elif pose == "phone":
        # Right hand holding a glowing 16-bit smartphone in front while sitting on bed!
        c_main = HOOD if hoodie else (MINT if summer else SHIRT)
        sleeve = [(11, -128), (18, -126), (21, -110), (14, -110), (12, -118)]
        poly(d, sleeve, c_main)
        forearm = [(15, -110), (20, -110), (13, -104), (6, -106), (6, -101), (14, -100)]
        poly(d, forearm, HOOD if hoodie else SKIN)
        # Cute pink-cased smartphone with glowing screen
        rect(d, 1, -116, 9, 14, (244, 134, 168, 255))
        rect(d, 2, -114, 7, 10, (186, 238, 255, 255))
        rect(d, 3, -113, 3, 2, WHITE)
        ell(d, 4, -108, 6, 6, SKIN)

    return sel_out(img)


def build_head_base():
    """Layer 4 base: Shorter natural neck with choker + compact soft cute anime oval face + dainty 1-2px earrings."""
    img = new_char()
    d = ImageDraw.Draw(img)

    # Slightly shorter natural neck (-142..-132) so head sits snugly on shoulders
    poly(d, [(-3, -144), (3, -144), (4, -132), (-4, -132)], SKIN)
    poly(d, [(-3, -143), (3, -143), (3.5, -139), (0, -138), (-3.5, -139)], SKIN_SH)
    # Crisp canon black choker with metallic silver ring/pendant
    rect(d, -4, -138, 8, 3, CHOKER)
    rect(d, -4, -138, 8, 1, (64, 56, 74, 255))
    d.ellipse([OX - 2, OY - 136, OX + 2, OY - 132], outline=SILVER, width=1)
    rect(d, -1, -136, 1, 1, WHITE)

    # Neatly tucked ears aligned with lowered eyes (-156..-150)
    ell(d, -16, -157, 3, 6, SKIN)
    ell(d, 13, -157, 3, 6, SKIN)

    # Compact, soft, cute anime oval (~30px wide x 42px tall) with short neat chin at y=-140!
    head_pts = (
        bezier((-15, -162), (-15, -150), (-8, -143), 10) +
        bezier((-8, -143), (0, -140), (8, -143), 10) +
        bezier((8, -143), (15, -150), (15, -162), 10) +
        bezier((15, -162), (14, -180), (0, -182), 10) +
        bezier((0, -182), (-14, -180), (-15, -162), 10)
    )
    poly(d, head_pts, SKIN)
    poly(d, [(11, -163), (15, -161), (13, -150), (8, -143), (7, -145), (11, -153)], SKIN_SH)
    rect(d, -13, -170, 26, 4, SKIN_SH)

    out = sel_out(img)
    # Paint dainty 1-2px silver earring studs/glints AFTER sel_out so they stay crisp & tiny!
    od = ImageDraw.Draw(out)
    od.rectangle([OX - 16, OY - 152, OX - 15, OY - 151], fill=SILVER)
    od.point((OX - 16, OY - 152), fill=WHITE)
    od.rectangle([OX + 14, OY - 152, OX + 15, OY - 151], fill=SILVER)
    od.point((OX + 15, OY - 152), fill=WHITE)
    return out


def draw_almond_eye(d, cx, cy, side, wide=False):
    """Cute, luminous anime eye fitted cleanly inside Marin's slender face oval."""
    s = side  # -1 for viewer-left eye, +1 for viewer-right eye
    h = 10 if wide else 9
    in_x = cx - s * 4
    out_x = cx + s * 4
    # Larger, softly rounded bright anime sclera
    sclera = [
        (in_x, cy),
        (cx - s * 2, cy - h // 2),
        (cx + s * 2, cy - h // 2),
        (out_x, cy - 1),
        (cx + s * 2, cy + h // 2 - 1),
        (cx - s * 2, cy + h // 2 - 1),
    ]
    poly(d, sclera, WHITE)
    line(d, (cx - s * 2, cy - h // 2), (cx + s * 2, cy - h // 2), (232, 224, 238, 255), 1)

    # Gentle rounded upper eyeliner with delicate winged outer eyelash flick
    line(d, (in_x, cy - 1), (cx - s * 2, cy - h // 2 - 1), LASH, 1)
    line(d, (cx - s * 2, cy - h // 2 - 1), (cx + s * 2, cy - h // 2 - 1), LASH, 2)
    line(d, (cx + s * 2, cy - h // 2 - 1), (out_x + s * 1, cy - 1), LASH, 2)
    line(d, (out_x, cy - 2), (out_x + s * 2, cy - 3), LASH, 1)
    line(d, (cx - s * 2, cy - h // 2 - 3), (cx + s * 2, cy - h // 2 - 3), SKIN_SH, 1)


def build_iris():
    """Cute luminous 9x9 anime iris: burgundy-rose gradient, glowing lower crescent & bright DOUBLE white highlights!"""
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
    # Deep cute pupil center
    arr[4:6, 4:6] = (58, 18, 46, 255)
    # Warm bright pink lower crescent glow (soft dreamy eyes!)
    arr[7, 3:6] = EYE_GLOW
    arr[6, 2] = EYE_GLOW
    arr[6, 6] = EYE_GLOW
    # Bright DOUBLE white anime highlights: large upper-left sparkle + cute lower-right glint!
    arr[2:4, 2:4] = WHITE
    arr[2, 4] = (255, 240, 248, 255)
    arr[5, 6] = WHITE
    arr[6, 5] = (255, 236, 246, 255)
    return Image.fromarray(arr, "RGBA")


def build_face(emotion):
    """Layer 4 emotion overlay: compact cute anime proportions (eyes lower at -154, blush directly under outer eyes, mouth close at -146)."""
    img = new_char()
    d = ImageDraw.Draw(img)

    # Cheek blush strictly UNDER outer eye corners (-12..-7 & +7..+12 at y=-149, NOT on jaw edge!)
    if emotion in ("blush", "flustered"):
        bl = (255, 114, 146, 200)
        ell(d, -12, -150, 6, 3, bl)
        ell(d, 6, -150, 6, 3, bl)
        for bx in (-11, -9, -7, 7, 9, 11):
            line(d, (bx, -149), (bx + 1, -148), (236, 84, 116, 210), 1)
    elif emotion == "romantic":
        bl = (255, 134, 162, 165)
        ell(d, -12, -150, 6, 3, bl)
        ell(d, 6, -150, 6, 3, bl)
        line(d, (-10, -149), (-9, -148), (242, 106, 136, 170), 1)
        line(d, (9, -149), (10, -148), (242, 106, 136, 170), 1)
    elif emotion == "pout":
        bl = (252, 138, 160, 165)
        ell(d, -12, -149, 5, 3, bl)
        ell(d, 7, -149, 5, 3, bl)
    else:
        blush_a = 170 if emotion in ("pet", "starry", "smug") else 125
        bl = (255, 146, 170, blush_a)
        ell(d, -12, -149, 5, 3, bl)
        ell(d, 7, -149, 5, 3, bl)
        if emotion in ("pet", "starry", "normal"):
            line(d, (-10, -148), (-9, -147), (246, 118, 144, 145), 1)
            line(d, (9, -148), (10, -147), (246, 118, 144, 145), 1)

    # Eyebrows (right above lowered eyes at y=-161..-162)
    if emotion == "pout":
        line(d, (-12, -162), (-5, -159), BROW, 1)
        line(d, (5, -159), (12, -162), BROW, 1)
    elif emotion in ("blush", "flustered", "romantic"):
        line(d, (-12, -160), (-5, -162), BROW, 1)
        line(d, (5, -162), (12, -160), BROW, 1)
    elif emotion == "surprised":
        line(d, (-12, -163), (-5, -164), BROW, 1)
        line(d, (5, -164), (12, -163), BROW, 1)
    else:
        line(d, (-12, -160), (-5, -161), BROW, 1)
        line(d, (5, -161), (12, -160), BROW, 1)

    # Eyes: lower half of head (y = -154) & slightly wider apart (cx = ±8) right beneath bangs!
    if emotion in ("normal", "blush", "flustered", "pout"):
        draw_almond_eye(d, -8, -154, -1, wide=False)
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

    # Delicate tiny nose dot right between lower eyes
    rect(d, 0, -149, 1, 1, SKIN_D)

    # Mouth raised close to eyes (y = -146..-145, just 2-3px below lower eye edge -> zero empty gap!)
    if emotion == "normal":
        line(d, (-3, -146), (-1, -145), MOUTH_C, 1)
        line(d, (-1, -145), (1, -145), MOUTH_C, 1)
        line(d, (1, -145), (3, -146), MOUTH_C, 1)
    elif emotion == "pet":
        pts = bezier((-3, -147), (0, -144), (3, -147), 8)
        for i in range(len(pts) - 1):
            line(d, pts[i], pts[i + 1], MOUTH_C, 1)
    elif emotion == "blush":
        for x, y in ((-3, -146), (-2, -147), (-1, -146), (0, -145), (1, -146), (2, -147), (3, -146)):
            rect(d, x, y, 1, 1, MOUTH_C)
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
        line(d, (-3, -147), (-1, -145), MOUTH_C, 1)
        line(d, (-1, -145), (2, -145), MOUTH_C, 1)
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
    elif emotion == "blink":
        line(d, (-3, -146), (2, -146), MOUTH_C, 1)
        rect(d, 3, -147, 1, 1, MOUTH_C)

    return img


def build_hair_back():
    """Layer 5a: Long flowing golden-blonde back hair seamlessly aligned to compact anime crown (-186)."""
    img = new_char()
    d = ImageDraw.Draw(img)

    left_edge = bezier((-18, -171), (-26, -135), (-31, -86), 14)
    bottom_wisps = [
        (-31, -86), (-27, -76), (-21, -86), (-16, -78),
        (-10, -86), (0, -80), (10, -86), (16, -78),
        (21, -86), (27, -76), (31, -86)
    ]
    right_edge = bezier((31, -86), (26, -135), (18, -171), 14)
    top_arc = bezier((18, -171), (0, -187), (-18, -171), 10)
    poly(d, left_edge + bottom_wisps + right_edge + top_arc, HAIR)

    poly(d, [(-15, -150), (15, -150), (19, -88), (-19, -88)], HAIR_SH)
    for sx in (-23, -17, 17, 23):
        line(d, (sx, -138), (sx + (3 if sx > 0 else -3), -92), HAIR_HI, 2)

    img = hair_gradient_fill(img, OY - 162, OY - 76, pink_start=0.52, steps=6)
    return sel_out(img)


def build_hair_side(side):
    """Layer 5b/5c: Tapered flowing front side locks framing compact face with 6-step coral-pink gradient."""
    img = new_char()
    d = ImageDraw.Draw(img)
    s = side

    outer = bezier((s * 15, -173), (s * 20, -145), (s * 16, -104), 14)
    tip = [(s * 16, -104), (s * 12, -92), (s * 10, -106)]
    inner = bezier((s * 10, -106), (s * 14, -144), (s * 12, -170), 14)
    poly(d, outer + tip + inner, HAIR)

    sh = bezier((s * 13, -164), (s * 15, -142), (s * 12, -104), 10)
    for i in range(len(sh) - 1):
        line(d, sh[i], sh[i + 1], HAIR_SH, 1)
    hi = bezier((s * 15, -164), (s * 18, -144), (s * 15, -114), 10)
    for i in range(len(hi) - 1):
        line(d, hi[i], hi[i + 1], HAIR_HI, 1)

    img = hair_gradient_fill(img, OY - 166, OY - 92, pink_start=0.52, steps=6)
    return sel_out(img)


def build_hair_bangs():
    """Layer 4 top: Smooth rounded crown (-185) + straight-cut wispy bangs grazing right above lowered eyes (-158)."""
    img = new_char()
    d = ImageDraw.Draw(img)

    crown = (
        bezier((-18, -163), (-19, -183), (0, -185), 12) +
        bezier((0, -185), (19, -183), (18, -163), 12) +
        [(15, -164), (10, -170), (0, -169), (-10, -170), (-15, -164)]
    )
    poly(d, crown, HAIR)

    # Feathered bang strands softly grazing right above eyebrows/eyes (-158..-161)
    strands = [
        ((-16, -171), (-14, -157), (-11, -169)),
        ((-12, -173), (-10, -161), (-7, -171)),
        ((-7, -173), (-4, -159), (-2, -171)),
        ((-2, -174), (0, -160), (2, -171)),
        ((2, -173), (5, -159), (7, -171)),
        ((7, -173), (10, -161), (12, -170)),
        ((11, -171), (14, -157), (16, -168)),
    ]
    for p0, tip, p2 in strands:
        poly(d, [p0, tip, p2], HAIR)
        line(d, ((p0[0] + p2[0]) // 2, p0[1] + 2), tip, HAIR_SH, 1)

    halo = bezier((-11, -177), (0, -180), (11, -177), 10)
    for i in range(len(halo) - 1):
        line(d, halo[i], halo[i + 1], HAIR_HI, 2)
    line(d, (-1, -184), (-1, -174), HAIR_SH, 1)

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
    """Wearable stylish red-framed cosplay glasses aligned to Marin's compact lowered eyes (cx=±8, y=-154)."""
    img = new_char()
    d = ImageDraw.Draw(img)
    frame = (212, 56, 78, 255)
    frame_hi = (255, 136, 152, 255)
    lens = (204, 238, 255, 115)
    for cx in (-8, 8):
        rect(d, cx - 5, -158, 10, 8, lens)
        d.rectangle([OX + cx - 5, OY - 159, OX + cx + 4, OY - 150], outline=frame, width=2)
        line(d, (cx - 3, -157), (cx - 1, -157), WHITE, 1)
        line(d, (cx - 3, -159), (cx + 2, -159), frame_hi, 1)
    line(d, (-3, -155), (3, -155), frame, 2)
    line(d, (-14, -156), (-13, -156), frame, 2)
    line(d, (13, -156), (14, -156), frame, 2)
    return img


def build_acc_ears():
    """Wearable cute plush cat-ear headband aligned cleanly onto compact crown (-185)."""
    img = new_char()
    d = ImageDraw.Draw(img)
    ear_dark = (46, 34, 52, 255)
    ear_hi = (78, 60, 88, 255)
    ear_in = (248, 148, 178, 255)
    pts = bezier((-15, -177), (0, -187), (15, -177), 12)
    for i in range(len(pts) - 1):
        line(d, pts[i], pts[i + 1], ear_dark, 2)
    for s in (-1, 1):
        poly(d, [(s * 14, -178), (s * 15, -196), (s * 4, -183)], ear_dark)
        poly(d, [(s * 12, -180), (s * 13, -191), (s * 6, -183)], ear_in)
        line(d, (s * 14, -193), (s * 6, -183), ear_hi, 1)
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

    # Relaxed undone-top-buttons variants for School (0), Home Shirt (1) & Canon Relaxed Shirt (4)
    build_torso(0, True).save(os.path.join(ASSETS, "torso_0_relaxed.png"))
    build_torso(1, True).save(os.path.join(ASSETS, "torso_1_relaxed.png"))
    build_torso(4, True).save(os.path.join(ASSETS, "torso_4_relaxed.png"))
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

    print("Generated v0.5-beta assets (cute face, relaxed shirts 0/1/4, floor-sit manga, stretch, dithered halos) in", ASSETS)


if __name__ == "__main__":
    generate_all()
