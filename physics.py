# -*- coding: utf-8 -*-
"""CharacterPhysics: Clamped Spring-Damper physics, pivot rotation, squash-stretch, and lively idle."""
import math
import random
import pygame
from constants import CW, CH, OX, OY, PAD, COMP_W, COMP_H, COX, COY, VW, FLOOR_Y, PIVOTS, clamp

MAX_SPRING_VEL = 520.0
MAX_BODY_VEL = 1100.0


class Spring2D:
    """Clamped underdamped harmonic oscillator with elastic pull target & pivot rotation."""

    def __init__(self, k, c, inertia, cx, cy, rot_scale=1.6, stretch_scale=0.008):
        self.k, self.c, self.inertia = k, c, inertia
        self.cx, self.cy = cx, cy
        self.rot_scale, self.stretch_scale = rot_scale, stretch_scale
        self.x = self.y = self.vx = self.vy = 0.0
        self.pulled = False
        self.tx = self.ty = 0.0
        self.override_angle = None
        self.override_stretch = 0.0

    def update(self, dt, ax, ay, inten):
        # Hard-clamp incoming accelerations so sharp mouse flicks stay stable
        ax = clamp(ax, -32000.0, 32000.0)
        ay = clamp(ay, -32000.0, 32000.0)
        if self.pulled:
            pk, pc = self.k * 2.4, self.c * 2.6
            self.vx += (pk * (self.tx - self.x) - pc * self.vx) * dt
            self.vy += (pk * (self.ty - self.y) - pc * self.vy) * dt
        else:
            self.vx += (-self.k * self.x - self.c * self.vx - self.inertia * ax * inten) * dt
            self.vy += (-self.k * self.y - self.c * self.vy - self.inertia * ay * inten) * dt

        self.vx = clamp(self.vx, -MAX_SPRING_VEL, MAX_SPRING_VEL)
        self.vy = clamp(self.vy, -MAX_SPRING_VEL, MAX_SPRING_VEL)
        self.x += self.vx * dt
        self.y += self.vy * dt

        lim_x = self.cx * (1.85 if self.pulled else 1.0)
        lim_y = self.cy * (1.85 if self.pulled else 1.0)
        if abs(self.x) > lim_x:
            self.x = math.copysign(lim_x, self.x)
            self.vx *= -0.38
        if abs(self.y) > lim_y:
            self.y = math.copysign(lim_y, self.y)
            self.vy *= -0.38

    def kick(self, vx, vy, inten):
        self.vx = clamp(self.vx + vx * inten, -MAX_SPRING_VEL, MAX_SPRING_VEL)
        self.vy = clamp(self.vy + vy * inten, -MAX_SPRING_VEL, MAX_SPRING_VEL)

    def reset(self):
        self.x = self.y = self.vx = self.vy = self.tx = self.ty = 0.0
        self.pulled = False
        self.override_angle = None
        self.override_stretch = 0.0

    def angle(self):
        if self.override_angle is not None:
            return clamp(self.override_angle, -85.0, 85.0)
        lim = 36.0 if self.pulled else 22.0
        return clamp(self.x * self.rot_scale, -lim, lim)

    def scale(self):
        st = self.override_stretch if self.override_angle is not None else clamp(
            (abs(self.x) * 0.55 + self.y) * self.stretch_scale, -0.09, 0.12
        )
        return 1.0 - st * 0.45, 1.0 + st


class Spring1D:
    def __init__(self, k=260.0, c=11.0):
        self.k, self.c = k, c
        self.val = self.vel = 0.0

    def update(self, dt):
        self.vel = clamp(self.vel + (-self.k * self.val - self.c * self.vel) * dt, -14.0, 14.0)
        self.val = clamp(self.val + self.vel * dt, -0.15, 0.15)

    def kick(self, v):
        self.vel = clamp(self.vel + v, -14.0, 14.0)

    def reset(self):
        self.val = self.vel = 0.0


def blit_pivoted(dest, surf, pivot, dest_pivot, angle=0.0, sx=1.0, sy=1.0):
    w, h = surf.get_size()
    work = surf
    px, py = float(pivot[0]), float(pivot[1])
    if abs(sx - 1.0) > 0.008 or abs(sy - 1.0) > 0.008:
        nw = max(2, int(round(w * sx)))
        nh = max(2, int(round(h * sy)))
        work = pygame.transform.scale(work, (nw, nh))
        px *= nw / w
        py *= nh / h
        w, h = nw, nh
    dx = px - w * 0.5
    dy = py - h * 0.5
    if abs(angle) > 0.4:
        work = pygame.transform.rotate(work, angle)
        rad = math.radians(-angle)
        ca, sa = math.cos(rad), math.sin(rad)
        dx, dy = dx * ca - dy * sa, dx * sa + dy * ca
    rw, rh = work.get_size()
    dest.blit(work, (int(round(dest_pivot[0] - (rw * 0.5 + dx))),
                     int(round(dest_pivot[1] - (rh * 0.5 + dy)))))


class CharacterPhysics:
    """Owns Marin's position, clamped springs, lively idle animations, and layered compositing."""

    def __init__(self):
        self.rx, self.ry = 320.0, float(FLOOR_Y)
        self.vx = self.vy = 0.0
        self.pvx = self.pvy = 0.0
        self.air = False

        # Clamped bouncy springs
        self.sp = {
            "head":  Spring2D(175, 6.8, 0.11,  9,  6, rot_scale=-1.40, stretch_scale=0.005),
            "bangs": Spring2D(135, 5.2, 0.16,  7,  5, rot_scale=1.45,  stretch_scale=0.006),
            "hairL": Spring2D(72,  3.3, 0.30, 15, 10, rot_scale=1.75,  stretch_scale=0.008),
            "hairR": Spring2D(76,  3.5, 0.30, 15, 10, rot_scale=1.75,  stretch_scale=0.008),
            "hairB": Spring2D(58,  3.0, 0.34, 16, 10, rot_scale=1.35,  stretch_scale=0.007),
            "tie":   Spring2D(96,  3.8, 0.28, 15,  8, rot_scale=2.05,  stretch_scale=0.008),
            "folds": Spring2D(155, 5.6, 0.14,  4,  3, rot_scale=0.75,  stretch_scale=0.010),
            "skirt": Spring2D(125, 4.8, 0.20, 10,  6, rot_scale=1.25,  stretch_scale=0.009),
            "armL":  Spring2D(98,  4.2, 0.22, 14, 10, rot_scale=2.05,  stretch_scale=0.006),
            "armR":  Spring2D(102, 4.4, 0.22, 14, 10, rot_scale=2.05,  stretch_scale=0.006),
        }
        self.land_sq = Spring1D(k=260.0, c=11.0)

        # Lively Idle state
        self.t = 0.0
        self.breath_y = 0.0
        self.weight_shift_x = 0.0
        self.shift_timer = random.uniform(6.0, 11.0)
        self.shift_target = 0.0
        self.micro_timer = random.uniform(5.0, 9.0)
        self.idle_look_t = 0.0
        self.idle_look_vec = (0.0, 0.0)
        self.blink_t, self.blinking = random.uniform(2.2, 4.8), 0.0
        self.pup = [0.0, 0.0]
        self.wave_t = 0.0

        self.comp = pygame.Surface((COMP_W, COMP_H), pygame.SRCALPHA)
        self.head_comp = pygame.Surface((CW, CH), pygame.SRCALPHA)
        self.mask = pygame.mask.from_surface(self.comp)

    def reset(self):
        self.rx, self.ry = 320.0, float(FLOOR_Y)
        self.vx = self.vy = self.pvx = self.pvy = 0.0
        self.air = False
        self.wave_t = 0.0
        self.weight_shift_x = 0.0
        self.shift_target = 0.0
        self.idle_look_t = 0.0
        for s in self.sp.values():
            s.reset()
        self.land_sq.reset()

    def kick_all(self, dx, strength, physics_inten):
        k = clamp(physics_inten * strength, 0.0, 2.2)
        self.sp["head"].kick(dx * 105, -40, k)
        self.sp["bangs"].kick(dx * 120, -32, k)
        self.sp["hairL"].kick(dx * 220, -90, k)
        self.sp["hairR"].kick(dx * 220, -90, k)
        self.sp["hairB"].kick(dx * 195, -75, k)
        self.sp["tie"].kick(dx * 250, -45, k)
        self.sp["folds"].kick(dx * 85, 35, k)
        self.sp["skirt"].kick(dx * 175, 50, k)
        self.sp["armL"].kick(dx * 170, -40, k)
        self.sp["armR"].kick(dx * 170, -40, k)

    def hit_zone(self, mx, my, outfit):
        lx, ly = int(mx - self.rx + COX), int(my - self.ry + COY)
        if 0 <= lx < COMP_W and 0 <= ly < COMP_H and self.mask.get_at((lx, ly)):
            hy = self.sp["head"].y
            rel_y = my - self.ry - hy
            rel_x = mx - self.rx
            if rel_y < -144:
                if rel_x < -12:
                    return "hairL"
                if rel_x > 12:
                    return "hairR"
                return "cheek"
            if -128 <= rel_y <= -70:
                if rel_x <= -16:
                    return "armL"
                if rel_x >= 16:
                    return "armR"
            if outfit == 0 and abs(rel_x) <= 6 and -128 < rel_y < -92:
                return "tie"
            if -144 <= rel_y < -98:
                if rel_x < -12:
                    return "hairL"
                if rel_x > 12:
                    return "hairR"
            if -95 <= rel_y < -66:
                return "skirt"
            return "body"
        return None

    def head_rmb_hit(self, mx, my):
        hx = self.rx + self.sp["head"].x
        hy = self.ry - 166 + self.sp["head"].y
        return abs(mx - hx) <= 28 and abs(my - hy) <= 32

    def update(self, dt, mouse, dragging, grab_offset, physics_inten, pitch_dark, interacting):
        """Advance body kinematics, clamped springs, breathing, weight-shift, and idle micro-actions.
        Returns (landed_impact, bounced_floor) for SFX/particles/reactions.
        """
        self.t += dt
        mx, my = mouse
        ox, oy = self.rx, self.ry
        landed_impact = 0.0

        if dragging:
            nx = clamp(mx + grab_offset[0], 42, VW - 42)
            ny = clamp(my + grab_offset[1], 202, FLOOR_Y)
            self.rx, self.ry = nx, ny
            self.vx = clamp(self.vx + ((nx - ox) / dt - self.vx) * 0.55, -MAX_BODY_VEL, MAX_BODY_VEL)
            self.vy = clamp(self.vy + ((ny - oy) / dt - self.vy) * 0.55, -MAX_BODY_VEL, MAX_BODY_VEL)
        elif self.air:
            self.vy = clamp(self.vy + 1550.0 * dt, -MAX_BODY_VEL, MAX_BODY_VEL)
            self.rx += self.vx * dt
            self.ry += self.vy * dt
            if self.rx < 42 or self.rx > VW - 42:
                self.rx = clamp(self.rx, 42, VW - 42)
                self.vx *= -0.52
            if self.ry < 202:
                self.ry, self.vy = 202, abs(self.vy) * 0.35
            if self.ry >= FLOOR_Y:
                self.ry = FLOOR_Y
                impact = self.vy
                if impact > 155:
                    landed_impact = impact
                    self.vy = -impact * 0.28
                    sq_imp = min(2.2, impact / 320.0) * max(0.5, physics_inten)
                    self.land_sq.kick(-sq_imp)
                    self.kick_all(1 if self.vx >= 0 else -1, min(1.4, impact / 500.0), physics_inten)
                else:
                    self.vy, self.air = 0.0, False
                self.vx *= 0.60
        else:
            self.vx *= math.exp(-8.5 * dt)
            self.rx = clamp(self.rx + self.vx * dt, 42, VW - 42)

        # Lively Idle: breathing, weight-shift, glancing around, brushing a hair strand!
        on_ground = not self.air and not dragging
        if on_ground and not interacting:
            # 1. Breathing cycle (shoulders, torso & hair)
            freq = 1.65 if pitch_dark else 2.35
            target_b = math.sin(self.t * freq) * 1.65
            self.breath_y += (target_b - self.breath_y) * min(1.0, dt * 8.0)

            # 2. Rare natural weight-shift from foot to foot
            self.shift_timer -= dt
            if self.shift_timer <= 0:
                self.shift_timer = random.uniform(7.5, 13.0)
                self.shift_target = random.choice((-2.2, 0.0, 2.2))
                self.sp["skirt"].kick(self.shift_target * 16, 0, physics_inten * 0.4)
            self.weight_shift_x += (self.shift_target - self.weight_shift_x) * min(1.0, dt * 2.2)

            # 3. Random idle micro-reactions (look around / brush a front hair lock!)
            if not pitch_dark:
                self.micro_timer -= dt
                if self.micro_timer <= 0:
                    self.micro_timer = random.uniform(6.5, 11.5)
                    if random.random() < 0.55:
                        # Glance curiously to the side or window
                        self.idle_look_t = random.uniform(1.2, 2.0)
                        self.idle_look_vec = (random.choice((-1.8, 1.8)), random.uniform(-0.8, 0.4))
                        self.sp["head"].kick(self.idle_look_vec[0] * 18, -6, physics_inten * 0.5)
                    else:
                        # Subtly brush/tuck a front hair strand!
                        side = random.choice(("L", "R"))
                        sgn = -1 if side == "L" else 1
                        self.sp[f"hair{side}"].kick(sgn * 75, -35, max(0.6, physics_inten))
                        self.sp[f"arm{side}"].kick(sgn * 55, -45, max(0.6, physics_inten))
                        self.sp["head"].kick(-sgn * 25, 8, max(0.6, physics_inten))
            else:
                # Drowsy head nod in pitch-dark room
                nod = math.sin(self.t * 1.4)
                self.sp["head"].y += (3.5 + nod * 2.4 - self.sp["head"].y) * min(1.0, dt * 3.0)
        else:
            self.breath_y += (0.0 - self.breath_y) * min(1.0, dt * 10.0)
            self.weight_shift_x += (0.0 - self.weight_shift_x) * min(1.0, dt * 6.0)

        # Root acceleration -> clamped spring sub-steps
        cvx = (self.rx - ox) / dt
        cvy = (self.ry - oy) / dt
        ax = clamp((cvx - self.pvx) / dt, -35000.0, 35000.0)
        ay = clamp((cvy - self.pvy) / dt, -35000.0, 35000.0)
        self.pvx, self.pvy = cvx, cvy

        for _ in range(3):
            sdt = dt / 3.0
            for s in self.sp.values():
                s.update(sdt, ax, ay, physics_inten)
            self.land_sq.update(sdt)

        # Natural blinking
        self.blink_t -= dt
        if self.blink_t <= 0:
            self.blinking = 0.13
            self.blink_t = random.uniform(2.0, 4.9)
        self.blinking = max(0.0, self.blinking - dt)

        # Smooth pupil tracking (cursor OR idle glance!)
        if self.idle_look_t > 0 and not interacting:
            self.idle_look_t -= dt
            tx, ty = self.idle_look_vec
        else:
            tx = clamp((mx - self.rx) / 65.0, -2.0, 2.0)
            ty = clamp((my - (self.ry - 161)) / 85.0, -1.2, 1.2)
        self.pup[0] += (tx - self.pup[0]) * min(1.0, dt * 11.0)
        self.pup[1] += (ty - self.pup[1]) * min(1.0, dt * 11.0)
        self.wave_t = max(0.0, self.wave_t - dt)
        return landed_impact

    def compose(self, assets, outfit, accessory, emotion, dragging, grab_part):
        """Composite all character layers (4 outfits + 2 accessories + 8 emotions) with pivots."""
        comp = self.comp
        comp.fill((0, 0, 0, 0))
        by = self.breath_y
        wx = self.weight_shift_x

        def dp(name, extra_x=0.0, extra_y=0.0):
            px, py = PIVOTS[name]
            return (px + PAD + extra_x + wx, py + PAD + extra_y)

        def draw_spring(surf, sp_name, extra_x=0.0, extra_y=0.0, angle_add=0.0):
            sp = self.sp[sp_name]
            sx, sy = sp.scale()
            ox_s = 0.0 if sp.override_angle is not None else sp.x * 0.52
            oy_s = 0.0 if sp.override_angle is not None else sp.y * 0.52
            blit_pivoted(
                comp, surf, PIVOTS[sp_name],
                dp(sp_name, ox_s + extra_x, oy_s + extra_y),
                angle=sp.angle() + angle_add, sx=sx, sy=sy
            )

        hd = self.sp["head"]
        h_ang = hd.angle()
        hx, hy = hd.x * 0.5, hd.y * 0.5 + by

        # Layer 5a: Back hair (moves gently with breathing & head)
        draw_spring(assets["hair_back"], "hairB", extra_x=hx * 0.6, extra_y=hy * 0.65, angle_add=h_ang * 0.45)

        # Layer 0: Legs & shoes (stays grounded, slight upper lean via torso shift)
        legs_key = f"legs_{outfit}_air" if (self.air or dragging) else f"legs_{outfit}_stand"
        comp.blit(assets[legs_key], (PAD, PAD))

        # Layer 1: Skirt / shorts / hoodie hem
        draw_spring(assets[f"skirt_{outfit}"], "skirt")

        # Layer 2: Torso & shoulders (breathing + gentle weight shift)
        comp.blit(assets[f"torso_{outfit}"], (int(round(PAD + wx)), int(round(PAD + by))))

        if outfit in (0, 1):
            draw_spring(assets[f"folds_{outfit}"], "folds", extra_y=by)

        # Layer 6: Arms
        draw_spring(assets[f"arm_l_{outfit}"], "armL", extra_y=by)
        if self.wave_t > 0 and grab_part != "armR":
            wob = math.sin(self.t * 15) * 14.0
            blit_pivoted(comp, assets[f"arm_r_{outfit}_wave"], PIVOTS["armR"], dp("armR", 0, by), angle=wob)
        else:
            draw_spring(assets[f"arm_r_{outfit}"], "armR", extra_y=by)

        if outfit == 0:
            draw_spring(assets["tie"], "tie", extra_y=by)

        # Layer 4: Head + Face + Tracking Irises + Wearable Accessories!
        hc = self.head_comp
        hc.fill((0, 0, 0, 0))
        hc.blit(assets["head_base"], (0, 0))
        eye_track_emos = ("normal", "blush", "smug", "surprised", "pout")
        if self.blinking > 0 and emotion in eye_track_emos:
            hc.blit(assets["face_blink"], (0, 0))
        else:
            hc.blit(assets[f"face_{emotion}"], (0, 0))
            if emotion in eye_track_emos:
                iris = assets["iris"]
                px = int(round(self.pup[0]))
                py = int(round(self.pup[1]))
                if emotion == "blush":
                    px = -1 if self.pup[0] >= 0 else 1
                hc.blit(iris, (OX - 8 - 4 + px, OY - 161 - 4 + py))
                hc.blit(iris, (OX + 8 - 4 + px, OY - 161 - 4 + py))

        # Wearable glasses sit cleanly over eyes (behind bangs tips? Actually in front of eyes!)
        if accessory == 1:
            hc.blit(assets["acc_glasses"], (0, 0))

        hsx, hsy = hd.scale()
        blit_pivoted(comp, hc, PIVOTS["head"], dp("head", hx, hy), angle=h_ang, sx=hsx, sy=hsy)

        # Front side hair locks & bangs
        draw_spring(assets["hair_front_l"], "hairL", extra_x=hx, extra_y=hy, angle_add=h_ang * 0.65)
        draw_spring(assets["hair_front_r"], "hairR", extra_x=hx, extra_y=hy, angle_add=h_ang * 0.65)
        draw_spring(assets["hair_bangs"], "bangs", extra_x=hx, extra_y=hy, angle_add=h_ang * 0.85)

        # Wearable cat-ear headband sits cleanly atop her crown & follows head rotation!
        if accessory == 2:
            blit_pivoted(comp, assets["acc_ears"], PIVOTS["head"], dp("head", hx, hy), angle=h_ang, sx=hsx, sy=hsy)

        self.mask = pygame.mask.from_surface(comp)
        return comp
