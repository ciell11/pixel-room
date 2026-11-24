# -*- coding: utf-8 -*-
"""RoomObjects: smooth curtain & lighting Lerp, dynamic shadows, drawers with draggable items."""
import math
import pygame
from constants import (
    VW, VH, FLOOR_Y, LAMP_POS, OUT, WHITE, LIGHT_TINTS,
    PILLOW_HOME, BOBA_HOME, GLASSES_DRAWER_POS, CAMERA_DRAWER_POS, clamp
)
from physics import blit_pivoted

MAX_PILLOW_VEL = 820.0


class RoomObjects:
    """Manages room lighting Lerp, sliding curtains, dynamic floor shadows, and all room props."""

    def __init__(self, save_data):
        # Persistent room state
        self.light = save_data["light"]
        self.lamp_on = save_data["lamp_on"]
        self.curtains_closed = save_data["curtains_closed"]
        self.poster_idx = save_data["poster_idx"]

        # Smooth Lerp visual state
        self.curtain_prog = 1.0 if self.curtains_closed else 0.0
        init_tint = self._target_tint()
        self.cur_tint = list(init_tint)
        self.cur_lamp_alpha = 255.0 if (self.light == 2 and self.lamp_on) else 0.0
        self.cur_sun_alpha = self._target_sun_alpha()
        self.cur_dark_alpha = self._target_dark_alpha()
        # Sky crossfade weights [day, sunset, night]
        self.sky_w = [1.0 if i == self.light else 0.0 for i in range(3)]
        self.flash_alpha = 0.0

        # Drawers & micro-animations
        self.drawer_top = False
        self.drawer_bot = False
        self.laundry_hop = 0.0
        self.manga_flip = 0.0
        self.ward_t = -1.0
        self.ward_swapped = False

        # Dynamic props
        self.pillow = {
            "x": PILLOW_HOME[0], "y": PILLOW_HOME[1],
            "vx": 0.0, "vy": 0.0, "ang": 0.0, "vang": 0.0,
            "on_bed": True, "hit_cd": 0.0
        }
        self.boba = {
            "x": BOBA_HOME[0], "y": BOBA_HOME[1],
            "returning": False, "drink_t": 0.0
        }
        # Draggable items inside nightstand drawers
        self.glasses_item = {"x": GLASSES_DRAWER_POS[0], "y": GLASSES_DRAWER_POS[1], "returning": False}
        self.camera_item = {"x": CAMERA_DRAWER_POS[0], "y": CAMERA_DRAWER_POS[1], "returning": False}

    def is_pitch_dark(self):
        return self.light == 2 and self.curtains_closed and not self.lamp_on

    def _target_tint(self):
        if self.light == 0:
            return LIGHT_TINTS["day_dim"] if self.curtains_closed else LIGHT_TINTS["day"]
        if self.light == 1:
            return LIGHT_TINTS["sun_dim"] if self.curtains_closed else LIGHT_TINTS["sunset"]
        if self.is_pitch_dark():
            return LIGHT_TINTS["dark"]
        return LIGHT_TINTS["evening"]

    def _target_sun_alpha(self):
        if self.light == 0 and not self.curtains_closed:
            return 42.0
        if self.light == 1 and not self.curtains_closed:
            return 52.0
        return 0.0

    def _target_dark_alpha(self):
        if self.is_pitch_dark():
            return 112.0
        if self.light in (0, 1) and self.curtains_closed:
            return 64.0
        return 0.0

    def sync_from_save(self, save_data):
        self.light = save_data["light"]
        self.lamp_on = save_data["lamp_on"]
        self.curtains_closed = save_data["curtains_closed"]
        self.poster_idx = save_data["poster_idx"]

    def reset_props(self):
        self.pillow.update({
            "x": PILLOW_HOME[0], "y": PILLOW_HOME[1],
            "vx": 0.0, "vy": 0.0, "ang": 0.0, "vang": 0.0,
            "on_bed": True, "hit_cd": 0.0
        })
        self.boba.update({"x": BOBA_HOME[0], "y": BOBA_HOME[1], "returning": False, "drink_t": 0.0})
        self.glasses_item.update({"x": GLASSES_DRAWER_POS[0], "y": GLASSES_DRAWER_POS[1], "returning": False})
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
        return self.drawer_top and abs(mx - self.glasses_item["x"]) <= 18 and abs(my - self.glasses_item["y"]) <= 11

    def camera_item_hit(self, mx, my):
        return self.drawer_bot and abs(mx - self.camera_item["x"]) <= 17 and abs(my - self.camera_item["y"]) <= 13

    def curtains_hit(self, mx, my):
        return 228 <= mx <= 412 and 50 <= my <= 184

    # ------------------------------------------------ update
    def update(self, dt, mode, char_phys, particles, audio, physics_inten):
        """Advance lighting Lerp, curtain Lerp, pillow collision, boba & drawer items.
        Returns dict of events triggered this frame (e.g. pillow_hit, wardrobe_swap).
        """
        events = {}
        lerp_f = min(1.0, dt * 4.8)

        # 1. Smooth curtain slide Lerp
        target_c = 1.0 if self.curtains_closed else 0.0
        self.curtain_prog += (target_c - self.curtain_prog) * min(1.0, dt * 6.5)

        # 2. Smooth lighting RGB & sky crossfade Lerp
        t_tint = self._target_tint()
        for i in range(3):
            self.cur_tint[i] += (t_tint[i] - self.cur_tint[i]) * lerp_f
        t_lamp = 255.0 if (self.light == 2 and self.lamp_on) else 0.0
        self.cur_lamp_alpha += (t_lamp - self.cur_lamp_alpha) * lerp_f
        self.cur_sun_alpha += (self._target_sun_alpha() - self.cur_sun_alpha) * lerp_f
        self.cur_dark_alpha += (self._target_dark_alpha() - self.cur_dark_alpha) * lerp_f
        for i in range(3):
            target_w = 1.0 if i == self.light else 0.0
            self.sky_w[i] += (target_w - self.sky_w[i]) * lerp_f

        # Camera flash decay
        if self.flash_alpha > 0:
            self.flash_alpha = max(0.0, self.flash_alpha - dt * 440.0)

        # Micro-animations
        self.laundry_hop = max(0.0, self.laundry_hop - dt * 2.8)
        self.manga_flip = max(0.0, self.manga_flip - dt * 3.0)

        # Wardrobe open & outfit swap timing
        if self.ward_t >= 0:
            self.ward_t += dt
            if self.ward_t > 0.42 and not self.ward_swapped:
                self.ward_swapped = True
                events["wardrobe_swap"] = True
            if self.ward_t > 0.88:
                self.ward_t = -1.0

        # Pillow physics (clamped velocity + dust puffs on floor impact!)
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
                    pl["hit_cd"] = 0.45
                    dx_dir = 1 if pl["vx"] >= 0 else -1
                    pl["vx"] = clamp(-pl["vx"] * 0.50 - dx_dir * 70, -MAX_PILLOW_VEL, MAX_PILLOW_VEL)
                    pl["vy"] = min(-160.0, -abs(pl["vy"]) * 0.45)
                    pl["vang"] = -dx_dir * 240
                    char_phys.vx = clamp(char_phys.vx + dx_dir * 130, -550, 550)
                    char_phys.kick_all(dx_dir, 1.35, physics_inten)
                    char_phys.land_sq.kick(-1.3)
                    events["pillow_hit"] = True

        # Bubble tea drinking & smooth return
        bb = self.boba
        if bb["drink_t"] > 0:
            bb["drink_t"] -= dt
            bb["x"] += (char_phys.rx + 10 - bb["x"]) * min(1.0, dt * 12.0)
            bb["y"] += (char_phys.ry - 144 - bb["y"]) * min(1.0, dt * 12.0)
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

        # Smooth return for drawer items
        for item, home in ((self.glasses_item, GLASSES_DRAWER_POS), (self.camera_item, CAMERA_DRAWER_POS)):
            if item["returning"]:
                item["x"] += (home[0] - item["x"]) * min(1.0, dt * 10.0)
                item["y"] += (home[1] - item["y"]) * min(1.0, dt * 10.0)
                if math.hypot(item["x"] - home[0], item["y"] - home[1]) < 1.5:
                    item["x"], item["y"] = home
                    item["returning"] = False

        return events

    # ------------------------------------------------ rendering helpers
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
        """Dynamic elliptical pixel shadow shrinking & fading proportionally with object height."""
        h = max(0.0, height_above_floor)
        scale = max(0.32, 1.0 - h / 220.0)
        alpha = int(clamp(max_alpha * (1.0 - h / 240.0), 16, max_alpha))
        sw = max(8, int(round(base_w * scale * (1.0 - squash * 0.65))))
        sh_h = max(4, int(round(base_h * scale)))
        sh = pygame.Surface((sw, sh_h), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (28, 14, 20, alpha), (0, 0, sw, sh_h))
        canvas.blit(sh, (int(round(x)) - sw // 2, FLOOR_Y - sh_h // 2))

    def draw_background(self, canvas, assets, hover_curtains):
        ward_open = 0.08 < self.ward_t < 0.78
        base = assets["room_base_open" if ward_open else "room_base"].copy()

        # Apply smooth real-time ambient room tint!
        tint = (int(self.cur_tint[0]), int(self.cur_tint[1]), int(self.cur_tint[2]))
        base.fill(tint, special_flags=pygame.BLEND_RGB_MULT)
        canvas.blit(base, (0, 0))

        # Smooth crossfading window sky (day / sunset / night stay vivid behind window!)
        for idx, key in enumerate(("sky_day", "sky_sunset", "sky_night")):
            w = self.sky_w[idx]
            if w > 0.02:
                sky = assets[key].copy()
                sky.set_alpha(int(clamp(w * 255, 0, 255)))
                canvas.blit(sky, (266, 62))

        # Dynamic wall poster
        canvas.blit(self.tint_surface(assets[f"poster_{self.poster_idx}"], 200, 105), (176, 72))

        # Smoothly sliding pleated curtains (width & folds expand dynamically from 36px -> 87px!)
        cw = int(round(36 + self.curtain_prog * 51))
        cp = self.tint_surface(pygame.transform.scale(assets["curtain_panel"], (cw, 132)), 320, 116)
        canvas.blit(cp, (234, 52))
        canvas.blit(cp, (406 - cw, 52))
        if hover_curtains:
            pygame.draw.rect(canvas, (255, 240, 190), (233, 51, cw + 2, 134), 1)
            pygame.draw.rect(canvas, (255, 240, 190), (405 - cw, 51, cw + 2, 134), 1)

        # Open nightstand drawers (empty shell; draggable items drawn dynamically on top!)
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

        # Smooth sunlit shaft & darkness overlays
        if self.cur_sun_alpha > 2.0:
            sun = pygame.Surface((VW, VH), pygame.SRCALPHA)
            a = int(self.cur_sun_alpha)
            col = (255, 248, 220, a) if self.sky_w[0] >= self.sky_w[1] else (255, 190, 110, a)
            pygame.draw.polygon(sun, col, [(266, 240), (374, 240), (434, 360), (296, 360)])
            canvas.blit(sun, (0, 0))

        if self.cur_dark_alpha > 2.0:
            dark = pygame.Surface((VW, VH), pygame.SRCALPHA)
            dark.fill((12, 10, 26, int(self.cur_dark_alpha)))
            canvas.blit(dark, (0, 0))

        # Smooth radial warm lamp glow + lit shade!
        if self.cur_lamp_alpha > 2.0:
            glow = assets["lamp_glow"].copy()
            glow.set_alpha(int(self.cur_lamp_alpha))
            canvas.blit(glow, (0, 0))
            la = self.cur_lamp_alpha / 255.0
            shade_c = (
                int(165 + 90 * la),
                int(150 + 96 * la),
                int(142 + 54 * la),
            )
            pygame.draw.polygon(canvas, shade_c, [(590, 146), (622, 146), (630, 172), (582, 172)])
            pygame.draw.polygon(canvas, OUT, [(590, 146), (622, 146), (630, 172), (582, 172)], 1)
            pygame.draw.line(canvas, (255, 255, 236), (586, 170), (626, 170), 2)

    def draw_props(self, canvas, assets, mode):
        # 1. Pillow (dynamic height-scaled shadow when off bed!)
        pl = self.pillow
        if not pl["on_bed"]:
            self.draw_floor_shadow(canvas, pl["x"], (FLOOR_Y - 6) - pl["y"], base_w=42, base_h=8, max_alpha=82)
        blit_pivoted(canvas, self.tint_surface(assets["pillow"], pl["x"], pl["y"]),
                     (24, 13), (pl["x"], pl["y"]), angle=pl["ang"])

        # 2. Bubble tea (dynamic shadow when dragged/in air!)
        bb = self.boba
        if mode == "boba" or bb["returning"] or bb["drink_t"] > 0:
            self.draw_floor_shadow(canvas, bb["x"], (FLOOR_Y - 12) - bb["y"], base_w=22, base_h=6, max_alpha=68)
        b_ang = -14.0 if bb["drink_t"] > 0 else 0.0
        blit_pivoted(canvas, self.tint_surface(assets["boba"], bb["x"], bb["y"]),
                     (11, 15), (bb["x"], bb["y"]), angle=b_ang)

        # 3. Draggable Cosplay Glasses (visible inside open top drawer or while dragging/returning)
        gi = self.glasses_item
        if self.drawer_top or mode == "glasses_item" or gi["returning"]:
            blit_pivoted(canvas, self.tint_surface(assets["item_glasses"], gi["x"], gi["y"]),
                         (16, 8), (gi["x"], gi["y"]))

        # 4. Draggable Retro Camera (visible inside open bottom drawer or while dragging/returning)
        ci = self.camera_item
        if self.drawer_bot or mode == "camera_item" or ci["returning"]:
            blit_pivoted(canvas, self.tint_surface(assets["item_camera"], ci["x"], ci["y"]),
                         (15, 11), (ci["x"], ci["y"]))

    def draw_flash(self, canvas):
        if self.flash_alpha > 2.0:
            fl = pygame.Surface((VW, VH), pygame.SRCALPHA)
            fl.fill((255, 252, 244, int(clamp(self.flash_alpha, 0, 245))))
            canvas.blit(fl, (0, 0))
