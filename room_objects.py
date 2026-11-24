# -*- coding: utf-8 -*-
"""RoomObjects: Dithered lighting & Fairy Lights, Living Window (clouds/stars/shooting stars), hover outlines & pillow counter-throw."""
import math
import random
import pygame
from constants import (
    VW, VH, FLOOR_Y, LAMP_POS, FAIRY_POS, OUT, WHITE, LIGHT_TINTS,
    PILLOW_HOME, BOBA_HOME, GLASSES_DRAWER_POS, GIFT_DRAWER_POS, CAMERA_DRAWER_POS, clamp
)
from physics import blit_pivoted

MAX_PILLOW_VEL = 820.0
FAIRY_BULBS = [
    (16, 17), (41, 22), (66, 24), (91, 21), (116, 14),
    (140, 18), (165, 24), (190, 23), (215, 19),
]
HOVER_COL = (255, 240, 196)


def _draw_sprite_hover(canvas, surf, pivot, dest_pivot, angle=0.0):
    """Draw a crisp 1px 16-bit highlight outline behind a hovered movable prop."""
    mask = pygame.mask.from_surface(surf)
    sil = mask.to_surface(setcolor=HOVER_COL + (220,), unsetcolor=(0, 0, 0, 0))
    for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        blit_pivoted(canvas, sil, pivot, (dest_pivot[0] + ox, dest_pivot[1] + oy), angle=angle)


class RoomObjects:
    """Manages room lighting Lerp, dithered Fairy Lights, Living Window, hover outlines, and props."""

    def __init__(self, save_data):
        self.light = save_data["light"]            # 0=day, 1=sunset, 2=evening/night, 3=romantic glow
        self.lamp_on = save_data["lamp_on"]
        self.fairy_on = save_data["fairy_on"]
        self.curtains_closed = save_data["curtains_closed"]
        self.poster_idx = save_data["poster_idx"]

        self.curtain_prog = 1.0 if self.curtains_closed else 0.0
        self.cur_tint = list(self._target_tint())
        self.cur_lamp_alpha = 255.0 if (self.light == 2 and self.lamp_on) else 0.0
        self.cur_sun_alpha = self._target_sun_alpha()
        self.cur_dark_alpha = self._target_dark_alpha()
        self.cur_vig_alpha = 1.0 if self.light == 3 else 0.0
        self.sky_w = [1.0 if i == self.light else 0.0 for i in range(4)]
        self.flash_alpha = 0.0
        self.t = 0.0

        self._vignette = self._build_vignette()
        self._win_surf = pygame.Surface((108, 100), pygame.SRCALPHA)

        # Living Window entities: drifting clouds, twinkling stars & occasional shooting stars!
        self.clouds = [
            {"x": 8.0,  "y": 18, "w": 28, "h": 7, "spd": 3.4},
            {"x": 58.0, "y": 36, "w": 34, "h": 8, "spd": 2.3},
            {"x": 22.0, "y": 64, "w": 24, "h": 6, "spd": 4.2},
            {"x": 82.0, "y": 22, "w": 22, "h": 6, "spd": 2.9},
        ]
        rnd = random.Random(42)
        self.stars = [
            (rnd.randint(3, 104), rnd.randint(3, 82), rnd.uniform(0, 6.28),
             rnd.uniform(1.8, 4.2), (255, 250, 210) if rnd.random() > 0.35 else (196, 218, 255))
            for _ in range(28)
        ]
        self.shooting_star = None
        self.shoot_cd = random.uniform(4.5, 9.5)

        self.drawer_top = False
        self.drawer_bot = False
        self.laundry_hop = 0.0
        self.manga_flip = 0.0
        self.ward_t = -1.0
        self.ward_swapped = False

        self.pillow = {
            "x": PILLOW_HOME[0], "y": PILLOW_HOME[1],
            "vx": 0.0, "vy": 0.0, "ang": 0.0, "vang": 0.0,
            "on_bed": True, "hit_cd": 0.0
        }
        self.pillow_hit_streak = 0
        self.pillow_streak_t = 0.0

        self.boba = {
            "x": BOBA_HOME[0], "y": BOBA_HOME[1],
            "returning": False, "drink_t": 0.0
        }
        self.glasses_item = {"x": GLASSES_DRAWER_POS[0], "y": GLASSES_DRAWER_POS[1], "returning": False}
        self.gift_item = {"x": GIFT_DRAWER_POS[0], "y": GIFT_DRAWER_POS[1], "returning": False}
        self.camera_item = {"x": CAMERA_DRAWER_POS[0], "y": CAMERA_DRAWER_POS[1], "returning": False}

    @staticmethod
    def _build_vignette():
        v = pygame.Surface((VW, VH), pygame.SRCALPHA)
        for i in range(18):
            a = int((18 - i) * 3.8)
            pad = i * 8
            pygame.draw.rect(v, (68, 22, 46, a), (pad, pad, VW - pad * 2, VH - pad * 2), 8)
        return v

    def is_pitch_dark(self):
        return self.light == 2 and self.curtains_closed and not self.lamp_on

    def is_dim_or_dark(self):
        return self.light == 2 or self.curtains_closed

    def _target_tint(self):
        if self.light == 0:
            return LIGHT_TINTS["day_dim"] if self.curtains_closed else LIGHT_TINTS["day"]
        if self.light == 1:
            return LIGHT_TINTS["sun_dim"] if self.curtains_closed else LIGHT_TINTS["sunset"]
        if self.light == 3:
            return LIGHT_TINTS["rom_dim"] if self.curtains_closed else LIGHT_TINTS["romantic"]
        if self.is_pitch_dark():
            return LIGHT_TINTS["dark"]
        return LIGHT_TINTS["evening"]

    def _target_sun_alpha(self):
        if self.curtains_closed:
            return 0.0
        if self.light == 0:
            return 42.0
        if self.light == 1:
            return 52.0
        if self.light == 3:
            return 46.0
        return 0.0

    def _target_dark_alpha(self):
        if self.is_pitch_dark():
            return 112.0
        if self.light in (0, 1, 3) and self.curtains_closed:
            return 60.0
        return 0.0

    def sync_from_save(self, save_data):
        self.light = save_data["light"]
        self.lamp_on = save_data["lamp_on"]
        self.fairy_on = save_data["fairy_on"]
        self.curtains_closed = save_data["curtains_closed"]
        self.poster_idx = save_data["poster_idx"]

    def reset_props(self):
        self.pillow.update({
            "x": PILLOW_HOME[0], "y": PILLOW_HOME[1],
            "vx": 0.0, "vy": 0.0, "ang": 0.0, "vang": 0.0,
            "on_bed": True, "hit_cd": 0.0
        })
        self.pillow_hit_streak = 0
        self.pillow_streak_t = 0.0
        self.boba.update({"x": BOBA_HOME[0], "y": BOBA_HOME[1], "returning": False, "drink_t": 0.0})
        self.glasses_item.update({"x": GLASSES_DRAWER_POS[0], "y": GLASSES_DRAWER_POS[1], "returning": False})
        self.gift_item.update({"x": GIFT_DRAWER_POS[0], "y": GIFT_DRAWER_POS[1], "returning": False})
        self.camera_item.update({"x": CAMERA_DRAWER_POS[0], "y": CAMERA_DRAWER_POS[1], "returning": False})
        self.drawer_top = False
        self.drawer_bot = False

    def trigger_flash(self):
        self.flash_alpha = 240.0

    # ------------------------------------------------ hitboxes
    def pillow_hit(self, mx, my):
        return abs(mx - self.pillow["x"]) <= 24 and abs(my - self.pillow["y"]) <= 14

    def boba_hit(self, mx, my):
        return self.boba["drink_t"] <= 0 and abs(mx - self.boba["x"]) <= 13 and abs(my - self.boba["y"]) <= 16

    def glasses_item_hit(self, mx, my):
        return self.drawer_top and abs(mx - self.glasses_item["x"]) <= 14 and abs(my - self.glasses_item["y"]) <= 11

    def gift_item_hit(self, mx, my):
        return self.drawer_top and abs(mx - self.gift_item["x"]) <= 14 and abs(my - self.gift_item["y"]) <= 12

    def camera_item_hit(self, mx, my):
        return self.drawer_bot and abs(mx - self.camera_item["x"]) <= 17 and abs(my - self.camera_item["y"]) <= 13

    def curtains_hit(self, mx, my):
        return 228 <= mx <= 412 and 50 <= my <= 184

    def fairy_hit(self, mx, my):
        return FAIRY_POS[0] <= mx <= FAIRY_POS[0] + 240 and FAIRY_POS[1] <= my <= FAIRY_POS[1] + 38

    def hit_object_name(self, mx, my, char_hit=False):
        """Identify which interactive room object is currently hovered (for 1px soft outline)."""
        if self.gift_item_hit(mx, my):
            return "gift_item"
        if self.glasses_item_hit(mx, my):
            return "glasses_item"
        if self.camera_item_hit(mx, my):
            return "camera_item"
        if self.boba_hit(mx, my):
            return "boba"
        if self.pillow_hit(mx, my):
            return "pillow"
        if char_hit:
            return None
        if self.fairy_hit(mx, my):
            return "fairy"
        if self.curtains_hit(mx, my):
            return "curtains"
        if 176 <= mx < 224 and 72 <= my < 138:
            return "poster"
        if 580 <= mx < 634 and 144 <= my < 192:
            return "lamp"
        if 576 <= mx < 636 and 202 <= my < 236:
            return "drawer_top"
        if 576 <= mx < 636 and 238 <= my < 272:
            return "drawer_bot"
        if 160 <= mx < 210 and 216 <= my < 264:
            return "laundry"
        if 214 <= mx < 248 and 270 <= my < 290:
            return "manga"
        if 26 <= mx < 154 and 38 <= my < 264:
            return "wardrobe"
        return None

    # ------------------------------------------------ update
    def update(self, dt, mode, char_phys, particles, audio, physics_inten, mouse=(320.0, 180.0)):
        dt = min(dt, 0.05)
        events = {}
        self.t += dt
        lerp_f = min(1.0, dt * 4.8)

        # Smooth curtain & lighting Lerp
        target_c = 1.0 if self.curtains_closed else 0.0
        self.curtain_prog += (target_c - self.curtain_prog) * min(1.0, dt * 6.5)

        t_tint = self._target_tint()
        for i in range(3):
            self.cur_tint[i] += (t_tint[i] - self.cur_tint[i]) * lerp_f
        t_lamp = 255.0 if (self.light == 2 and self.lamp_on) else (130.0 if self.light == 3 else 0.0)
        self.cur_lamp_alpha += (t_lamp - self.cur_lamp_alpha) * lerp_f
        self.cur_sun_alpha += (self._target_sun_alpha() - self.cur_sun_alpha) * lerp_f
        self.cur_dark_alpha += (self._target_dark_alpha() - self.cur_dark_alpha) * lerp_f
        self.cur_vig_alpha += ((1.0 if self.light == 3 else 0.0) - self.cur_vig_alpha) * lerp_f
        for i in range(4):
            self.sky_w[i] += ((1.0 if i == self.light else 0.0) - self.sky_w[i]) * lerp_f

        # Living Window: clouds & shooting stars
        for cl in self.clouds:
            cl["x"] += cl["spd"] * dt
            if cl["x"] > 112.0:
                cl["x"] = -cl["w"] - 4.0

        if self.sky_w[2] > 0.25 or self.sky_w[3] > 0.35:
            if self.shooting_star is not None:
                ss = self.shooting_star
                ss[0] += ss[2] * dt
                ss[1] += ss[3] * dt
                ss[4] -= dt
                if ss[4] <= 0 or ss[0] > 112 or ss[1] > 96:
                    self.shooting_star = None
            else:
                self.shoot_cd -= dt
                if self.shoot_cd <= 0:
                    self.shoot_cd = random.uniform(6.0, 12.5)
                    self.shooting_star = [
                        random.uniform(6.0, 48.0), random.uniform(4.0, 28.0),
                        random.uniform(72.0, 108.0), random.uniform(34.0, 56.0),
                        0.75, 0.75
                    ]
        else:
            self.shooting_star = None

        if self.flash_alpha > 0:
            self.flash_alpha = max(0.0, self.flash_alpha - dt * 440.0)

        self.laundry_hop = max(0.0, self.laundry_hop - dt * 2.8)
        self.manga_flip = max(0.0, self.manga_flip - dt * 3.0)

        if self.ward_t >= 0:
            self.ward_t += dt
            if self.ward_t > 0.42 and not self.ward_swapped:
                self.ward_swapped = True
                events["wardrobe_swap"] = True
            if self.ward_t > 0.88:
                self.ward_t = -1.0

        # Pillow streak decay
        if self.pillow_streak_t > 0:
            self.pillow_streak_t -= dt
            if self.pillow_streak_t <= 0:
                self.pillow_hit_streak = 0

        # Pillow physics + Pillow Counter-Throw!
        pl = self.pillow
        pl["hit_cd"] = max(0.0, pl["hit_cd"] - dt)
        if mode != "pillow" and not pl["on_bed"]:
            pl["vy"] = clamp(pl["vy"] + 1150.0 * dt, -MAX_PILLOW_VEL, MAX_PILLOW_VEL)
            pl["vx"] = clamp(pl["vx"], -MAX_PILLOW_VEL, MAX_PILLOW_VEL)
            pl["x"] += pl["vx"] * dt
            pl["y"] += pl["vy"] * dt
            pl["ang"] += pl["vang"] * dt
            if pl["x"] < 24 or pl["x"] > VW - 24:
                pl["x"] = clamp(pl["x"], 24, VW - 24)
                pl["vx"] *= -0.60
                pl["vang"] *= -0.65
            if pl["y"] < 18:
                pl["y"], pl["vy"] = 18, abs(pl["vy"]) * 0.4
            if pl["y"] >= FLOOR_Y - 6:
                pl["y"] = FLOOR_Y - 6
                if abs(pl["vy"]) > 110:
                    if abs(pl["vy"]) > 180:
                        particles.spawn("dust", pl["x"], FLOOR_Y - 2, 4)
                    pl["vy"] *= -0.36
                    pl["vx"] *= 0.72
                    pl["vang"] *= 0.65
                else:
                    pl["vy"] = 0.0
                    pl["vx"] *= math.exp(-6.0 * dt)
                    pl["vang"] *= math.exp(-8.0 * dt)
                    pl["ang"] += (0.0 - pl["ang"]) * min(1.0, dt * 6.0)

            spd = math.hypot(pl["vx"], pl["vy"])
            if pl["hit_cd"] <= 0 and spd > 95:
                if abs(pl["x"] - char_phys.rx) < 34 and (char_phys.ry - 188) < pl["y"] < (char_phys.ry - 40):
                    pl["hit_cd"] = 0.55
                    self.pillow_hit_streak += 1
                    self.pillow_streak_t = 9.0
                    if self.pillow_hit_streak >= 2:
                        # Marin catches the pillow & throws it right back at the player's cursor!
                        self.pillow_hit_streak = 0
                        tx, ty = mouse[0] - pl["x"], mouse[1] - pl["y"]
                        dist = max(20.0, math.hypot(tx, ty))
                        pl["vx"] = clamp((tx / dist) * 460.0, -MAX_PILLOW_VEL, MAX_PILLOW_VEL)
                        pl["vy"] = clamp((ty / dist) * 320.0 - 210.0, -MAX_PILLOW_VEL, MAX_PILLOW_VEL)
                        pl["vang"] = 340.0 if pl["vx"] >= 0 else -340.0
                        char_phys.wave_t = 0.85
                        char_phys.kick_all(1 if pl["vx"] >= 0 else -1, 1.0, physics_inten)
                        events["pillow_counter"] = True
                    else:
                        dx_dir = 1 if pl["vx"] >= 0 else -1
                        pl["vx"] = clamp(-pl["vx"] * 0.50 - dx_dir * 70, -MAX_PILLOW_VEL, MAX_PILLOW_VEL)
                        pl["vy"] = min(-160.0, -abs(pl["vy"]) * 0.45)
                        pl["vang"] = -dx_dir * 240
                        if not char_phys.sitting:
                            char_phys.vx = clamp(char_phys.vx + dx_dir * 130, -550, 550)
                        char_phys.kick_all(dx_dir, 1.35, physics_inten)
                        char_phys.land_sq.kick(-1.3)
                        events["pillow_hit"] = True

        # Bubble tea drinking & return
        bb = self.boba
        if bb["drink_t"] > 0:
            bb["drink_t"] -= dt
            bb["x"] += (char_phys.rx + 10 - bb["x"]) * min(1.0, dt * 12.0)
            bb["y"] += (char_phys.ry - 144 + char_phys.crouch_y - bb["y"]) * min(1.0, dt * 12.0)
            if int(bb["drink_t"] * 4) != int((bb["drink_t"] + dt) * 4):
                particles.spawn("heart", char_phys.rx, char_phys.ry - 186, 1)
            if bb["drink_t"] <= 0:
                bb["returning"] = True
        elif bb["returning"]:
            bb["x"] += (BOBA_HOME[0] - bb["x"]) * min(1.0, dt * 9.0)
            bb["y"] += (BOBA_HOME[1] - bb["y"]) * min(1.0, dt * 9.0)
            if math.hypot(bb["x"] - BOBA_HOME[0], bb["y"] - BOBA_HOME[1]) < 1.5:
                bb["x"], bb["y"] = BOBA_HOME
                bb["returning"] = False

        # Smooth return for all 3 drawer items
        for item, home in (
            (self.glasses_item, GLASSES_DRAWER_POS),
            (self.gift_item, GIFT_DRAWER_POS),
            (self.camera_item, CAMERA_DRAWER_POS),
        ):
            if item["returning"]:
                item["x"] += (home[0] - item["x"]) * min(1.0, dt * 10.0)
                item["y"] += (home[1] - item["y"]) * min(1.0, dt * 10.0)
                if math.hypot(item["x"] - home[0], item["y"] - home[1]) < 1.5:
                    item["x"], item["y"] = home
                    item["returning"] = False

        return events

    # ------------------------------------------------ rendering
    def tint_surface(self, surf, x, y):
        lit = surf.copy()
        tint = (int(self.cur_tint[0]), int(self.cur_tint[1]), int(self.cur_tint[2]))
        lit.fill(tint, special_flags=pygame.BLEND_RGB_MULT)
        if self.cur_lamp_alpha > 4.0:
            la = self.cur_lamp_alpha / 255.0
            d = math.hypot(x - LAMP_POS[0], y - LAMP_POS[1])
            f = (max(0.0, 1.0 - d / 340.0) ** 1.5) * la
            lit.fill((int(115 * f), int(80 * f), int(36 * f)), special_flags=pygame.BLEND_RGB_ADD)
        return lit

    @staticmethod
    def draw_floor_shadow(canvas, x, height_above_floor, base_w, base_h=10, max_alpha=95, squash=0.0):
        h = max(0.0, height_above_floor)
        scale = max(0.32, 1.0 - h / 220.0)
        alpha = int(clamp(max_alpha * (1.0 - h / 240.0), 16, max_alpha))
        sw = max(8, int(round(base_w * scale * (1.0 - squash * 0.65))))
        sh_h = max(4, int(round(base_h * scale)))
        sh = pygame.Surface((sw, sh_h), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (28, 14, 20, alpha), (0, 0, sw, sh_h))
        canvas.blit(sh, (int(round(x)) - sw // 2, FLOOR_Y - sh_h // 2))

    def _draw_living_window(self, canvas, assets):
        ws = self._win_surf
        ws.fill((0, 0, 0, 0))
        # 1. Crossfading gradient sky
        for idx, key in enumerate(("sky_day", "sky_sunset", "sky_night", "sky_romantic")):
            w = self.sky_w[idx]
            if w > 0.02:
                sky = assets[key].copy()
                sky.set_alpha(int(clamp(w * 255, 0, 255)))
                ws.blit(sky, (0, 0))

        # 2. Live drifting pixel clouds (Day / Sunset / Romantic)
        cloud_w = clamp(self.sky_w[0] + self.sky_w[1] * 0.85 + self.sky_w[3] * 0.65, 0.0, 1.0)
        if cloud_w > 0.05:
            ca = int(clamp(cloud_w * 235, 0, 240))
            if self.sky_w[3] > 0.4:
                c_top, c_bot = (255, 224, 236, ca), (240, 180, 206, ca)
            elif self.sky_w[1] > self.sky_w[0]:
                c_top, c_bot = (255, 222, 184, ca), (236, 158, 138, ca)
            else:
                c_top, c_bot = (255, 255, 255, ca), (222, 238, 252, ca)
            cl_layer = pygame.Surface((108, 100), pygame.SRCALPHA)
            for cl in self.clouds:
                cx, cy, cw, ch = int(round(cl["x"])), cl["y"], cl["w"], cl["h"]
                pygame.draw.rect(cl_layer, c_bot, (cx, cy + 2, cw, ch - 1))
                pygame.draw.rect(cl_layer, c_top, (cx + 2, cy, cw - 4, ch - 2))
                pygame.draw.rect(cl_layer, c_top, (cx + 6, cy - 3, max(6, cw - 12), 4))
            ws.blit(cl_layer, (0, 0))

        # 3. Live twinkling stars & shooting star (Night / Romantic)
        star_w = clamp(self.sky_w[2] + self.sky_w[3] * 0.72, 0.0, 1.0)
        if star_w > 0.05:
            st_layer = pygame.Surface((108, 100), pygame.SRCALPHA)
            for sx, sy, ph, freq, col in self.stars:
                tw = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(self.t * freq + ph))
                a = int(clamp(star_w * tw * 255, 0, 255))
                st_layer.fill(col + (a,), (sx, sy, 2 if tw > 0.85 else 1, 1))
                if tw > 0.90:
                    st_layer.fill(col + (int(a * 0.7),), (sx, sy - 1, 1, 3))
            if self.shooting_star is not None:
                sx, sy, svx, svy, life, ml = self.shooting_star
                frac = clamp(life / ml, 0.0, 1.0)
                tx, ty = sx - svx * 0.14, sy - svy * 0.14
                pygame.draw.line(st_layer, (255, 252, 224, int(230 * frac)), (int(tx), int(ty)), (int(sx), int(sy)), 1)
                st_layer.fill((255, 255, 255, int(255 * frac)), (int(sx), int(sy), 2, 2))
            ws.blit(st_layer, (0, 0))

        # 4. Crisp window mullions ABOVE live sky elements
        ws.blit(assets["window_frame"], (0, 0))
        canvas.blit(ws, (266, 62))

    def draw_background(self, canvas, assets, hover_obj=None):
        ward_open = 0.08 < self.ward_t < 0.78
        base = assets["room_base_open" if ward_open else "room_base"].copy()
        tint = (int(self.cur_tint[0]), int(self.cur_tint[1]), int(self.cur_tint[2]))
        base.fill(tint, special_flags=pygame.BLEND_RGB_MULT)
        canvas.blit(base, (0, 0))

        # Living animated window (clouds / stars / shooting stars + mullions)
        self._draw_living_window(canvas, assets)

        # Dynamic detailed 16-bit wall poster
        canvas.blit(self.tint_surface(assets[f"poster_{self.poster_idx}"], 200, 105), (176, 72))

        # Smoothly sliding pleated curtains
        cw = int(round(36 + self.curtain_prog * 51))
        cp = self.tint_surface(pygame.transform.scale(assets["curtain_panel"], (cw, 132)), 320, 116)
        canvas.blit(cp, (234, 52))
        canvas.blit(cp, (406 - cw, 52))

        # Fairy Lights along upper-right wall over bed with 16-bit Bayer-dithered halos!
        if self.fairy_on:
            for bi, (bx, by) in enumerate(FAIRY_BULBS):
                tw = 0.62 + 0.38 * math.sin(self.t * 3.1 + bi * 1.15)
                halo = assets["fairy_halo_gold" if bi % 2 == 0 else "fairy_halo_pink"].copy()
                halo.set_alpha(int(clamp(tw * 235, 90, 255)))
                canvas.blit(halo, (FAIRY_POS[0] + bx - 16, FAIRY_POS[1] + by - 16))
            canvas.blit(assets["fairy_on"], FAIRY_POS)
        else:
            canvas.blit(self.tint_surface(assets["fairy_off"], 510, 54), FAIRY_POS)

        # Open nightstand drawers
        if self.drawer_top:
            canvas.blit(self.tint_surface(assets["drawer_open"], 604, 218), (576, 200))
        if self.drawer_bot:
            canvas.blit(self.tint_surface(assets["drawer_open"], 604, 254), (576, 236))

        # Laundry basket hop & manga page-flip
        if self.laundry_hop > 0:
            dy = int(round(math.sin(self.laundry_hop * math.pi) * 10))
            pygame.draw.ellipse(canvas, (92, 116, 152), (166, 218 - dy, 20, 12))
            pygame.draw.ellipse(canvas, (238, 162, 184), (180, 216 - dy, 22, 12))
        if self.manga_flip > 0:
            fy = int(round(math.sin(self.manga_flip * math.pi) * 8))
            pygame.draw.polygon(canvas, WHITE, [(228, 282), (242, 276 - fy), (228, 272 - fy)])

        # Sunbeam / Romantic Glow beam
        if self.cur_sun_alpha > 2.0:
            sun = pygame.Surface((VW, VH), pygame.SRCALPHA)
            a = int(self.cur_sun_alpha)
            if self.sky_w[3] > 0.35:
                col = (255, 182, 208, a)
            elif self.sky_w[1] > self.sky_w[0]:
                col = (255, 190, 110, a)
            else:
                col = (255, 248, 220, a)
            pygame.draw.polygon(sun, col, [(266, 240), (374, 240), (434, 360), (296, 360)])
            canvas.blit(sun, (0, 0))

        if self.cur_dark_alpha > 2.0:
            dark = pygame.Surface((VW, VH), pygame.SRCALPHA)
            dark.fill((12, 10, 26, int(self.cur_dark_alpha)))
            canvas.blit(dark, (0, 0))

        # Warm 16-bit Bayer-dithered lamp glow + floor/wall warm reflection!
        if self.cur_lamp_alpha > 2.0:
            glow = assets["lamp_glow"].copy()
            glow.set_alpha(int(self.cur_lamp_alpha))
            canvas.blit(glow, (0, 0))
            la = self.cur_lamp_alpha / 255.0
            shade_c = (int(165 + 90 * la), int(150 + 96 * la), int(142 + 54 * la))
            pygame.draw.polygon(canvas, shade_c, [(590, 146), (622, 146), (630, 172), (582, 172)])
            pygame.draw.polygon(canvas, OUT, [(590, 146), (622, 146), (630, 172), (582, 172)], 1)
            pygame.draw.line(canvas, (255, 255, 236), (586, 170), (626, 170), 2)

        # Romantic Glow soft corner vignette
        if self.cur_vig_alpha > 0.02:
            vig = self._vignette.copy()
            vig.set_alpha(int(clamp(self.cur_vig_alpha * 190, 0, 210)))
            canvas.blit(vig, (0, 0))

        # Crisp 1px soft hover outline for static room objects!
        if hover_obj == "curtains":
            pygame.draw.rect(canvas, HOVER_COL, (233, 51, cw + 2, 134), 1)
            pygame.draw.rect(canvas, HOVER_COL, (405 - cw, 51, cw + 2, 134), 1)
        elif hover_obj == "fairy":
            pygame.draw.rect(canvas, HOVER_COL, (FAIRY_POS[0], FAIRY_POS[1], 240, 36), 1)
        elif hover_obj == "poster":
            pygame.draw.rect(canvas, HOVER_COL, (175, 71, 50, 68), 1)
        elif hover_obj == "lamp":
            pygame.draw.rect(canvas, HOVER_COL, (580, 144, 52, 46), 1)
        elif hover_obj == "drawer_top":
            pygame.draw.rect(canvas, HOVER_COL, (577, 201, 58, 34), 1)
        elif hover_obj == "drawer_bot":
            pygame.draw.rect(canvas, HOVER_COL, (577, 237, 58, 34), 1)
        elif hover_obj == "laundry":
            pygame.draw.rect(canvas, HOVER_COL, (160, 216, 50, 48), 1)
        elif hover_obj == "manga":
            pygame.draw.rect(canvas, HOVER_COL, (214, 271, 32, 18), 1)
        elif hover_obj == "wardrobe":
            pygame.draw.rect(canvas, HOVER_COL, (25, 37, 130, 228), 1)

    def draw_bed_pillow(self, canvas, assets, mode, hover_obj=None):
        """Draw the pillow BEHIND Marin when it is resting on the bed so she sits naturally in front of it."""
        pl = self.pillow
        if not pl["on_bed"]:
            return
        p_surf = self.tint_surface(assets["pillow"], pl["x"], pl["y"])
        if hover_obj == "pillow" and mode != "pillow":
            _draw_sprite_hover(canvas, p_surf, (24, 13), (pl["x"], pl["y"]), angle=pl["ang"])
        blit_pivoted(canvas, p_surf, (24, 13), (pl["x"], pl["y"]), angle=pl["ang"])

    def draw_props(self, canvas, assets, mode, hover_obj=None):
        pl = self.pillow
        if not pl["on_bed"]:
            self.draw_floor_shadow(canvas, pl["x"], (FLOOR_Y - 6) - pl["y"], base_w=42, base_h=8, max_alpha=82)
            p_surf = self.tint_surface(assets["pillow"], pl["x"], pl["y"])
            if hover_obj == "pillow" and mode != "pillow":
                _draw_sprite_hover(canvas, p_surf, (24, 13), (pl["x"], pl["y"]), angle=pl["ang"])
            blit_pivoted(canvas, p_surf, (24, 13), (pl["x"], pl["y"]), angle=pl["ang"])

        bb = self.boba
        if mode == "boba" or bb["returning"] or bb["drink_t"] > 0:
            self.draw_floor_shadow(canvas, bb["x"], (FLOOR_Y - 12) - bb["y"], base_w=22, base_h=6, max_alpha=68)
        b_ang = -14.0 if bb["drink_t"] > 0 else 0.0
        b_surf = self.tint_surface(assets["boba"], bb["x"], bb["y"])
        if hover_obj == "boba" and mode != "boba":
            _draw_sprite_hover(canvas, b_surf, (11, 15), (bb["x"], bb["y"]), angle=b_ang)
        blit_pivoted(canvas, b_surf, (11, 15), (bb["x"], bb["y"]), angle=b_ang)

        gi = self.glasses_item
        if self.drawer_top or mode == "glasses_item" or gi["returning"]:
            g_surf = self.tint_surface(assets["item_glasses"], gi["x"], gi["y"])
            if hover_obj == "glasses_item" and mode != "glasses_item":
                _draw_sprite_hover(canvas, g_surf, (16, 8), (gi["x"], gi["y"]))
            blit_pivoted(canvas, g_surf, (16, 8), (gi["x"], gi["y"]))

        gf = self.gift_item
        if self.drawer_top or mode == "gift_item" or gf["returning"]:
            gf_surf = self.tint_surface(assets["item_gift"], gf["x"], gf["y"])
            if hover_obj == "gift_item" and mode != "gift_item":
                _draw_sprite_hover(canvas, gf_surf, (12, 11), (gf["x"], gf["y"]))
            blit_pivoted(canvas, gf_surf, (12, 11), (gf["x"], gf["y"]))

        ci = self.camera_item
        if self.drawer_bot or mode == "camera_item" or ci["returning"]:
            c_surf = self.tint_surface(assets["item_camera"], ci["x"], ci["y"])
            if hover_obj == "camera_item" and mode != "camera_item":
                _draw_sprite_hover(canvas, c_surf, (15, 11), (ci["x"], ci["y"]))
            blit_pivoted(canvas, c_surf, (15, 11), (ci["x"], ci["y"]))

    def draw_flash(self, canvas):
        if self.flash_alpha > 2.0:
            fl = pygame.Surface((VW, VH), pygame.SRCALPHA)
            fl.fill((255, 252, 244, int(clamp(self.flash_alpha, 0, 245))))
            canvas.blit(fl, (0, 0))
