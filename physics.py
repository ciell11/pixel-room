# -*- coding: utf-8 -*-
"""CharacterPhysics: Clamped springs, multi-phase collar anim, floor-sit manga, Lo-Fi dance, stretch & Living Room AI."""
import math
import random
import pygame
from constants import (
    CW, CH, OX, OY, PAD, COMP_W, COMP_H, COX, COY,
    VW, FLOOR_Y, BED_SIT_POS, PIVOTS, clamp
)

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
    """Owns Marin's kinematics, springs, multi-phase collar anim, floor-sit manga & Living Room AI."""

    def __init__(self):
        self.rx, self.ry = 320.0, float(FLOOR_Y)
        self.vx = self.vy = 0.0
        self.pvx = self.pvy = 0.0
        self.air = False

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

        # Lively Idle & Pose timers
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

        # Multi-phase expressive collar unbutton/button animation:
        # phase 0: idle | 1: blush + raise hands | 2: tug collar + cloth shake + toggle | 3: exhale & relax!
        self.collar_seq_phase = 0
        self.collar_seq_t = 0.0
        self.collar_seq_target = True

        # Living Room AI State Machine
        # States: "stand" | "walk" | "bed_phone" | "bed_nap" | "read_manga" | "watch_window"
        #       | "wardrobe_check" | "self_boba" | "lofi_dance" | "stretch" | "attention"
        self.ai_state = "stand"
        self.ai_next_state = "stand"
        self.ai_target_x = 320.0
        self.ai_timer = random.uniform(7.0, 12.0)
        self.ai_action_cd = 3.0
        self.sitting = False
        self.walk_phase = 0.0
        self.walk_bob = 0.0
        self.floor_sit_y = 0.0    # Smoothly drops to 46.0 when seated on floor reading manga!
        self.manga_turn_t = 0.0   # Brief page-flip hand lift & open-manga flip frame!
        self.stretch_t = 0.0      # Raised arms sweet stretch pose!
        self.twirl_t = 0.0        # Cute wardrobe half-turn spin!
        self.dance_note_cd = 0.0

        self.comp = pygame.Surface((COMP_W, COMP_H), pygame.SRCALPHA)
        self.head_comp = pygame.Surface((CW, CH), pygame.SRCALPHA)
        self.mask = pygame.mask.from_surface(self.comp)

    @property
    def crouch_y(self):
        """Vertical downward offset when seated on the floor reading manga."""
        return self.floor_sit_y

    @property
    def is_floor_manga(self):
        return self.ai_state == "read_manga" and not self.air and not self.sitting and self.floor_sit_y > 18.0

    def reset(self):
        self.rx, self.ry = 320.0, float(FLOOR_Y)
        self.vx = self.vy = self.pvx = self.pvy = 0.0
        self.air = False
        self.wave_t = 0.0
        self.collar_seq_phase = 0
        self.collar_seq_t = 0.0
        self.weight_shift_x = 0.0
        self.shift_target = 0.0
        self.idle_look_t = 0.0
        self.ai_state = "stand"
        self.ai_next_state = "stand"
        self.ai_target_x = 320.0
        self.ai_timer = random.uniform(7.0, 12.0)
        self.sitting = False
        self.walk_phase = 0.0
        self.walk_bob = 0.0
        self.floor_sit_y = 0.0
        self.manga_turn_t = 0.0
        self.stretch_t = 0.0
        self.twirl_t = 0.0
        for s in self.sp.values():
            s.reset()
        self.land_sq.reset()

    def start_collar_anim(self, target_relaxed=True):
        """Launch the expressive 3-phase collar unbutton/button animation."""
        self.collar_seq_phase = 1
        self.collar_seq_t = 0.55
        self.collar_seq_target = bool(target_relaxed)
        self.stretch_t = 0.0

    def sit_on_bed(self, nap=False):
        self.rx, self.ry = BED_SIT_POS[0], BED_SIT_POS[1]
        self.vx = self.vy = 0.0
        self.air = False
        self.sitting = True
        self.floor_sit_y = 0.0
        self.walk_bob = 0.0
        self.ai_state = "bed_nap" if nap else "bed_phone"
        self.ai_timer = random.uniform(14.0, 22.0)
        self.ai_action_cd = random.uniform(4.5, 8.0)
        self.land_sq.kick(-0.75)

    def go_to_activity(self, next_state, target_x=None):
        """Command Marin (e.g. from Chat) to walk to and perform a specific activity."""
        if next_state in ("bed_phone", "bed_nap"):
            self._start_walk(BED_SIT_POS[0], next_state)
        elif next_state == "read_manga":
            self._start_walk(242.0, "read_manga")
        elif next_state == "watch_window":
            self._start_walk(320.0, "watch_window")
        elif next_state == "wardrobe_check":
            self._start_walk(158.0, "wardrobe_check")
        elif next_state == "lofi_dance":
            self.stand_up("lofi_dance")
            self.ai_timer = random.uniform(10.0, 16.0)
        elif next_state == "stretch":
            self.stand_up("stretch")
            self.stretch_t = 2.6
            self.ai_timer = 3.2
        else:
            self._start_walk(target_x if target_x is not None else 320.0, next_state)

    def stand_up(self, target_state="stand"):
        prev = self.ai_state
        if self.sitting:
            self.sitting = False
            self.ry = float(FLOOR_Y)
            self.land_sq.kick(-0.65)
        self.ai_state = target_state
        self.ai_timer = random.uniform(7.0, 12.0)
        self.walk_bob = 0.0
        self.stretch_t = 0.0
        return prev

    def interrupt_for_drag(self):
        prev = self.ai_state
        self.sitting = False
        self.ai_state = "stand"
        self.ai_timer = random.uniform(8.0, 14.0)
        self.walk_bob = 0.0
        self.stretch_t = 0.0
        self.twirl_t = 0.0
        return prev

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
            hy = self.sp["head"].y + self.floor_sit_y
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
            if outfit in (0, 4) and abs(rel_x) <= 6 and -128 < rel_y < -92:
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
        hy = self.ry - 166 + self.sp["head"].y + self.floor_sit_y
        return abs(mx - hx) <= 28 and abs(my - hy) <= 32

    def _pick_next_ai(self, pitch_dark, boba_busy, music_on, rain_on, aff_lvl, idle_t):
        """Choose the next autonomous Living Room activity."""
        if pitch_dark or (idle_t > 55.0 and self.ai_state != "bed_nap" and random.random() < 0.35):
            if self.ai_state == "bed_nap":
                self.ai_timer = random.uniform(14.0, 22.0)
                return
            self._start_walk(BED_SIT_POS[0], "bed_nap")
            return

        # High-affinity attention seeking if ignored for a while!
        if aff_lvl >= 3 and idle_t > 26.0 and self.ai_state != "attention" and random.random() < 0.38:
            self._start_walk(320.0, "attention")
            return

        choices = [
            ("bed_phone",      BED_SIT_POS[0],               22),
            ("read_manga",     242.0,                        24),
            ("watch_window",   320.0,                        30 if rain_on else 16),
            ("wardrobe_check", 158.0,                        15),
            ("stretch",        random.uniform(270.0, 368.0), 14),
            ("stand",          random.uniform(264.0, 382.0), 10),
        ]
        if music_on:
            choices.append(("lofi_dance", random.uniform(265.0, 375.0), 28))
        if not boba_busy:
            choices.append(("self_boba", 530.0, 11))

        choices = [c for c in choices if c[0] != self.ai_state]
        total = sum(w for _, _, w in choices)
        r = random.uniform(0, total)
        acc = 0.0
        picked_state, picked_x = "stand", 320.0
        for st, tx, w in choices:
            acc += w
            if r <= acc:
                picked_state, picked_x = st, tx
                break
        self._start_walk(picked_x, picked_state)

    def _start_walk(self, target_x, next_state):
        if self.sitting:
            self.sitting = False
            self.ry = float(FLOOR_Y)
            self.land_sq.kick(-0.55)
        self.ai_state = "walk"
        self.ai_target_x = clamp(target_x, 96.0, VW - 96.0)
        self.ai_next_state = next_state
        self.ai_timer = random.uniform(10.0, 18.0)
        self.stretch_t = 0.0

    def update(self, dt, mouse, dragging, grab_offset, physics_inten, pitch_dark,
               interacting, aff_lvl=1, free_life=True, boba_busy=False,
               music_on=False, rain_on=False, idle_t=0.0):
        """Advance kinematics, springs, multi-phase collar anim & Living Room AI.
        Returns (landed_impact, idle_event).
        """
        dt = min(dt, 0.05)
        self.t += dt
        mx, my = mouse
        ox, oy = self.rx, self.ry
        landed_impact = 0.0
        idle_event = None

        # Advance multi-phase collar animation (blush+raise -> tug+toggle -> stretch+exhale!)
        if self.collar_seq_phase > 0:
            self.collar_seq_t -= dt
            if self.collar_seq_phase == 2:
                # Subtle fabric wobble while unbuttoning/buttoning
                wob = math.sin(self.t * 28.0)
                self.sp["folds"].kick(wob * 22.0, 12.0, max(0.6, physics_inten))
                self.sp["tie"].kick(wob * 28.0, 0.0, max(0.6, physics_inten))
            if self.collar_seq_t <= 0:
                if self.collar_seq_phase == 1:
                    self.collar_seq_phase = 2
                    self.collar_seq_t = 0.65
                    self.sp["folds"].kick(65.0, 30.0, max(0.7, physics_inten))
                    self.sp["tie"].kick(110.0, -25.0, max(0.7, physics_inten))
                    self.land_sq.kick(-0.45)
                    idle_event = ("collar_commit_relax" if self.collar_seq_target else "collar_commit_button")
                elif self.collar_seq_phase == 2:
                    self.collar_seq_phase = 3
                    self.collar_seq_t = 0.90
                    self.sp["head"].kick(25.0, -18.0, max(0.6, physics_inten))
                    self.land_sq.kick(0.35)
                    idle_event = ("collar_done_relax" if self.collar_seq_target else "collar_done_button")
                else:
                    self.collar_seq_phase = 0

        if dragging:
            nx = clamp(mx + grab_offset[0], 42, VW - 42)
            ny = clamp(my + grab_offset[1], 202, FLOOR_Y)
            self.rx, self.ry = nx, ny
            self.vx = clamp(self.vx + ((nx - ox) / max(dt, 1e-4) - self.vx) * 0.55, -MAX_BODY_VEL, MAX_BODY_VEL)
            self.vy = clamp(self.vy + ((ny - oy) / max(dt, 1e-4) - self.vy) * 0.55, -MAX_BODY_VEL, MAX_BODY_VEL)
            self.walk_bob = 0.0
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
            self.walk_bob = 0.0
        else:
            if self.sitting:
                self.rx += (BED_SIT_POS[0] - self.rx) * min(1.0, dt * 10.0)
                self.ry += (BED_SIT_POS[1] - self.ry) * min(1.0, dt * 10.0)
                self.vx = self.vy = 0.0
            else:
                self.vx *= math.exp(-8.5 * dt)
                self.rx = clamp(self.rx + self.vx * dt, 42, VW - 42)

            # ---- Living Room AI State Machine ----
            if not free_life:
                if self.ai_state == "walk":
                    self.ai_state = "stand"
                elif self.ai_state in ("watch_window", "wardrobe_check", "self_boba", "lofi_dance", "stretch", "attention"):
                    self.ai_state = "stand"
                self.walk_bob += (0.0 - self.walk_bob) * min(1.0, dt * 10.0)
            elif not interacting and self.collar_seq_phase == 0 and abs(self.vx) < 18.0:
                if self.ai_state == "walk":
                    diff = self.ai_target_x - self.rx
                    if abs(diff) <= 2.5:
                        self.rx = self.ai_target_x
                        self.walk_bob = 0.0
                        nxt = self.ai_next_state
                        if nxt in ("bed_phone", "bed_nap"):
                            self.sit_on_bed(nap=(nxt == "bed_nap"))
                        else:
                            self.ai_state = nxt
                            if nxt == "stretch":
                                self.stretch_t = 2.6
                                self.ai_timer = 3.4
                            elif nxt == "wardrobe_check":
                                self.twirl_t = 0.95
                                self.ai_timer = random.uniform(7.5, 11.5)
                            elif nxt == "attention":
                                self.wave_t = 2.2
                                self.ai_timer = 4.5
                            elif nxt == "lofi_dance":
                                self.ai_timer = random.uniform(10.0, 16.0)
                                self.dance_note_cd = 1.2
                            else:
                                self.ai_timer = random.uniform(10.0, 16.0)
                            self.ai_action_cd = random.uniform(2.8, 5.2)
                        idle_event = idle_event or f"ai_enter_{self.ai_state}"
                    else:
                        step = math.copysign(min(abs(diff), 52.0 * dt), diff)
                        self.rx = clamp(self.rx + step, 42, VW - 42)
                        self.walk_phase += dt * 7.8
                        self.walk_bob = -abs(math.sin(self.walk_phase)) * 2.8
                        sway = math.sin(self.walk_phase)
                        self.sp["skirt"].kick(sway * 28.0 * dt * 15, 0, physics_inten * 0.25)
                        self.sp["armL"].kick(sway * 24.0 * dt * 15, 0, physics_inten * 0.22)
                        self.sp["armR"].kick(-sway * 24.0 * dt * 15, 0, physics_inten * 0.22)
                        self.idle_look_t = 0.2
                        self.idle_look_vec = (1.6 if diff > 0 else -1.6, 0.0)
                else:
                    # Lo-Fi dance groove bobbing & swaying!
                    if self.ai_state == "lofi_dance" and music_on:
                        beat_w = self.t * (90.0 / 60.0) * math.pi  # 90 BPM sync!
                        self.walk_bob = -abs(math.sin(beat_w)) * 2.4
                        sway = math.sin(beat_w * 0.5)
                        self.weight_shift_x = sway * 3.4
                        self.sp["head"].x += (sway * 2.6 - self.sp["head"].x) * min(1.0, dt * 7.0)
                        self.sp["armL"].kick(sway * 18.0 * dt * 12, -10.0 * dt * 12, physics_inten * 0.2)
                        self.sp["armR"].kick(-sway * 18.0 * dt * 12, -10.0 * dt * 12, physics_inten * 0.2)
                        self.sp["skirt"].kick(sway * 22.0 * dt * 12, 0, physics_inten * 0.2)
                        self.dance_note_cd -= dt
                        if self.dance_note_cd <= 0:
                            self.dance_note_cd = random.uniform(1.6, 2.5)
                            idle_event = idle_event or "ai_dance_note"
                    else:
                        if self.ai_state == "lofi_dance" and not music_on:
                            self.ai_state = "stand"
                        self.walk_bob += (0.0 - self.walk_bob) * min(1.0, dt * 10.0)

                    if pitch_dark and self.ai_state != "bed_nap":
                        self.ai_timer = min(self.ai_timer, 2.2)
                    elif not pitch_dark and self.ai_state == "bed_nap":
                        self.ai_state = "bed_phone"
                        self.ai_timer = random.uniform(8.0, 14.0)

                    self.ai_timer -= dt
                    if self.ai_timer <= 0:
                        self._pick_next_ai(pitch_dark, boba_busy, music_on, rain_on, aff_lvl, idle_t)
                    else:
                        self.ai_action_cd -= dt
                        if self.ai_action_cd <= 0:
                            self.ai_action_cd = random.uniform(4.2, 7.2)
                            if self.ai_state == "read_manga":
                                self.manga_turn_t = 0.45
                                self.sp["head"].kick(random.choice((-20, 20)), 12, physics_inten * 0.45)
                                idle_event = idle_event or "ai_manga_flip"
                            elif self.ai_state == "bed_phone":
                                self.sp["head"].kick(random.choice((-18, 18)), 10, physics_inten * 0.4)
                                idle_event = idle_event or "ai_phone_chuckle"
                            elif self.ai_state == "wardrobe_check":
                                self.twirl_t = 0.90
                                side = random.choice(("L", "R"))
                                sgn = -1 if side == "L" else 1
                                self.sp[f"hair{side}"].kick(sgn * 80, -35, max(0.5, physics_inten))
                                self.sp["skirt"].kick(sgn * 95, 0, max(0.5, physics_inten))
                            elif self.ai_state == "watch_window":
                                self.idle_look_t = 2.0
                                self.idle_look_vec = (random.uniform(-1.0, 1.0), -0.9)
            else:
                self.walk_bob += (0.0 - self.walk_bob) * min(1.0, dt * 10.0)

        # Smooth floor-sit drop when reading manga on the rug!
        target_floor = 46.0 if (self.ai_state == "read_manga" and not dragging and not self.air and not self.sitting) else 0.0
        self.floor_sit_y += (target_floor - self.floor_sit_y) * min(1.0, dt * 8.0)
        if abs(target_floor - self.floor_sit_y) < 0.4:
            self.floor_sit_y = target_floor

        # Lively Idle: breathing, weight-shift, micro-reactions & soft gaze attraction
        on_ground = not self.air and not dragging
        if on_ground and not interacting:
            freq = 1.65 if (pitch_dark or self.ai_state == "bed_nap") else 2.35
            amp = 2.4 if self.collar_seq_phase == 3 else 1.65
            target_b = math.sin(self.t * freq) * amp
            self.breath_y += (target_b - self.breath_y) * min(1.0, dt * 8.0)

            if self.ai_state == "stand":
                self.shift_timer -= dt
                if self.shift_timer <= 0:
                    self.shift_timer = random.uniform(7.5, 13.0)
                    self.shift_target = random.choice((-2.2, 0.0, 2.2))
                    self.sp["skirt"].kick(self.shift_target * 16, 0, physics_inten * 0.4)
                self.weight_shift_x += (self.shift_target - self.weight_shift_x) * min(1.0, dt * 2.2)
            elif self.ai_state != "lofi_dance":
                self.shift_target = 0.0
                self.weight_shift_x += (0.0 - self.weight_shift_x) * min(1.0, dt * 5.0)

            if not pitch_dark and self.ai_state in ("stand", "watch_window") and self.collar_seq_phase == 0:
                self.micro_timer -= dt
                if self.micro_timer <= 0:
                    self.micro_timer = random.uniform(6.0, 10.5)
                    roll = random.random()
                    if aff_lvl >= 4 and roll < 0.24 and self.ai_state == "stand":
                        self.wave_t = 1.25
                        self.sp["head"].kick(30, -10, max(0.6, physics_inten))
                        idle_event = idle_event or "blown_kiss"
                    elif roll < 0.62:
                        side = random.choice(("L", "R"))
                        sgn = -1 if side == "L" else 1
                        self.sp[f"hair{side}"].kick(sgn * 80, -40, max(0.6, physics_inten))
                        self.sp[f"arm{side}"].kick(sgn * 70, -65, max(0.6, physics_inten))
                        self.sp["head"].kick(-sgn * 28, 8, max(0.6, physics_inten))
                        if aff_lvl >= 3:
                            idle_event = idle_event or "hair_tuck"
                    else:
                        self.idle_look_t = random.uniform(1.2, 2.0)
                        self.idle_look_vec = (random.choice((-1.8, 1.8)), random.uniform(-0.8, 0.4))
                        self.sp["head"].kick(self.idle_look_vec[0] * 18, -6, physics_inten * 0.5)
            elif pitch_dark or self.ai_state == "bed_nap":
                nod = math.sin(self.t * 1.4)
                self.sp["head"].y += (3.5 + nod * 2.4 - self.sp["head"].y) * min(1.0, dt * 3.0)
            elif self.ai_state == "bed_phone":
                self.sp["head"].y += (2.0 - self.sp["head"].y) * min(1.0, dt * 3.5)
            elif self.ai_state == "read_manga":
                # Gently tilt head downward looking at the open manga pages!
                self.sp["head"].y += (4.4 - self.sp["head"].y) * min(1.0, dt * 4.5)

            dx_c = mx - self.rx
            dy_c = my - (self.ry - 154 + self.floor_sit_y)
            if not pitch_dark and self.ai_state != "bed_nap" and abs(dx_c) < 62 and abs(dy_c) < 48:
                self.idle_look_t = 0.0
                target_hx = clamp(dx_c * 0.055, -3.2, 3.2)
                self.sp["head"].x += (target_hx - self.sp["head"].x) * min(1.0, dt * 3.2)
        else:
            self.breath_y += (0.0 - self.breath_y) * min(1.0, dt * 10.0)
            self.weight_shift_x += (0.0 - self.weight_shift_x) * min(1.0, dt * 6.0)

        # Clamped spring sub-steps
        inv_dt = 1.0 / max(dt, 1e-4)
        cvx = (self.rx - ox) * inv_dt
        cvy = (self.ry - oy) * inv_dt
        ax = clamp((cvx - self.pvx) * inv_dt, -35000.0, 35000.0)
        ay = clamp((cvy - self.pvy) * inv_dt, -35000.0, 35000.0)
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

        # Pupil tracking
        if self.ai_state == "bed_phone" and not interacting and math.hypot(mx - self.rx, my - (self.ry - 150)) > 75:
            tx, ty = 0.7, 1.15
        elif self.ai_state == "read_manga" and not interacting and math.hypot(mx - self.rx, my - (self.ry - 110)) > 70:
            tx, ty = 0.0, 1.65
        elif self.ai_state == "watch_window" and not interacting and math.hypot(mx - self.rx, my - (self.ry - 150)) > 85:
            tx, ty = 0.0, -0.9
        elif self.idle_look_t > 0 and not interacting:
            self.idle_look_t -= dt
            tx, ty = self.idle_look_vec
        else:
            tx = clamp((mx - self.rx) / 65.0, -2.0, 2.0)
            ty = clamp((my - (self.ry - 161 + self.floor_sit_y)) / 85.0, -1.2, 1.2)
        self.pup[0] += (tx - self.pup[0]) * min(1.0, dt * 11.0)
        self.pup[1] += (ty - self.pup[1]) * min(1.0, dt * 11.0)

        self.wave_t = max(0.0, self.wave_t - dt)
        self.manga_turn_t = max(0.0, self.manga_turn_t - dt)
        self.stretch_t = max(0.0, self.stretch_t - dt)
        self.twirl_t = max(0.0, self.twirl_t - dt)
        return landed_impact, idle_event

    def twirl_scale_x(self):
        """Cute subtle horizontal turn compression during wardrobe inspection spin."""
        if self.twirl_t <= 0:
            return 1.0
        # Smooth dip from 1.0 -> 0.72 -> 1.0 like a quick playful half-turn!
        p = self.twirl_t / 0.95
        return 1.0 - 0.28 * math.sin(clamp(p, 0.0, 1.0) * math.pi)

    def compose(self, assets, outfit, accessory, emotion, dragging, grab_part, collar_relaxed=False):
        """Composite all character layers with cute face, relaxed outfits (0/1/4), floor-sit manga & stretches."""
        comp = self.comp
        comp.fill((0, 0, 0, 0))
        fy = self.floor_sit_y
        by = self.breath_y + self.walk_bob + fy
        if self.stretch_t > 0:
            by -= math.sin(clamp(self.stretch_t / 2.6, 0.0, 1.0) * math.pi) * 2.5
        wx = self.weight_shift_x
        is_sit = self.sitting and not dragging and not self.air
        is_floor = (fy > 16.0) and not dragging and not self.air and not is_sit
        use_relaxed = collar_relaxed and outfit in (0, 1, 4)
        collar_hands = (self.collar_seq_phase in (1, 2) and grab_part not in ("armL", "armR"))
        stretch_hands = ((self.stretch_t > 0 or self.collar_seq_phase == 3) and grab_part not in ("armL", "armR")
                         and not is_floor and self.wave_t <= 0)
        holding_phone = (self.ai_state == "bed_phone" and is_sit and grab_part != "armR"
                         and self.wave_t <= 0 and not collar_hands)
        holding_manga = is_floor and grab_part not in ("armL", "armR") and not collar_hands

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

        # Layer 5a: Back hair (tracks head tilt cleanly even when looking down reading manga!)
        draw_spring(assets["hair_back"], "hairB", extra_x=hx * 0.6, extra_y=hy * 0.95, angle_add=h_ang * 0.45)

        # Layer 0: Legs (air / bed-sit / floor-sit / walk / stand)
        if self.air or dragging:
            comp.blit(assets[f"legs_{outfit}_air"], (PAD, PAD))
        elif is_sit:
            dangle = math.sin(self.t * 2.4) * 2.6 if self.ai_state == "bed_phone" else 0.0
            blit_pivoted(comp, assets[f"legs_{outfit}_sit"], (OX, OY - 76),
                         (COX, COY - 76 + self.walk_bob), angle=dangle)
        elif is_floor:
            comp.blit(assets[f"legs_{outfit}_floor"], (PAD, int(round(PAD + fy))))
        else:
            walk_ang = math.sin(self.walk_phase) * 3.5 if self.ai_state == "walk" else 0.0
            if self.ai_state == "lofi_dance":
                walk_ang = math.sin(self.t * 4.71) * 2.5
            if abs(walk_ang) > 0.3:
                blit_pivoted(comp, assets[f"legs_{outfit}_stand"], (OX, OY - 74),
                             (COX, COY - 74 + self.walk_bob * 0.5), angle=walk_ang)
            else:
                comp.blit(assets[f"legs_{outfit}_stand"], (PAD, int(round(PAD + fy * 0.5))))

        # Layer 1: Skirt / shorts / hoodie hem
        draw_spring(assets[f"skirt_{outfit}"], "skirt", extra_y=self.walk_bob + fy)

        # Layer 2: Torso & shoulders (normal OR relaxed unbuttoned 1-2 buttons for outfits 0, 1 & 4!)
        torso_key = f"torso_{outfit}_relaxed" if use_relaxed else f"torso_{outfit}"
        comp.blit(assets[torso_key], (int(round(PAD + wx)), int(round(PAD + by))))

        if outfit in (0, 1, 4):
            draw_spring(assets[f"folds_{outfit}"], "folds", extra_y=by)

        # Necktie (drawn cleanly under collar hands / manga)
        if outfit == 0:
            draw_spring(assets["tie_0_relaxed" if use_relaxed else "tie"], "tie", extra_y=by)
        elif outfit == 4:
            draw_spring(assets["tie_4_relaxed" if use_relaxed else "tie_loose"], "tie", extra_y=by)

        # Layer 6: Arms (multi-phase collar / stretch / wave / floor-manga / phone / spring)
        if collar_hands:
            tug = math.sin(self.t * 16.0) * (5.5 if self.collar_seq_phase == 2 else 2.0)
            blit_pivoted(comp, assets[f"arm_l_{outfit}_collar"], PIVOTS["armL"], dp("armL", 0, by), angle=-tug)
            blit_pivoted(comp, assets[f"arm_r_{outfit}_collar"], PIVOTS["armR"], dp("armR", 0, by), angle=tug)
        elif stretch_hands:
            sw = math.sin(self.t * 3.5) * 4.5
            blit_pivoted(comp, assets[f"arm_l_{outfit}_stretch"], PIVOTS["armL"], dp("armL", 0, by), angle=-sw)
            blit_pivoted(comp, assets[f"arm_r_{outfit}_stretch"], PIVOTS["armR"], dp("armR", 0, by), angle=sw)
        elif holding_manga:
            # Reading arms + open manga are drawn cleanly in foreground AFTER hair so hands visibly grip the book!
            pass
        else:
            draw_spring(assets[f"arm_l_{outfit}"], "armL", extra_y=by)
            if self.wave_t > 0 and grab_part != "armR":
                wob = math.sin(self.t * 15) * 14.0
                blit_pivoted(comp, assets[f"arm_r_{outfit}_wave"], PIVOTS["armR"], dp("armR", 0, by), angle=wob)
            elif holding_phone:
                bob_p = math.sin(self.t * 2.6) * 1.4
                blit_pivoted(comp, assets[f"arm_r_{outfit}_phone"], PIVOTS["armR"], dp("armR", 0, by), angle=bob_p)
            else:
                draw_spring(assets[f"arm_r_{outfit}"], "armR", extra_y=by)

        # Layer 4: Head + Cute Face + Luminous 9x9 Double-Highlight Irises + Accessories
        hc = self.head_comp
        hc.fill((0, 0, 0, 0))
        hc.blit(assets["head_base"], (0, 0))
        eye_track_emos = ("normal", "blush", "smug", "surprised", "pout", "romantic", "flustered")
        if self.blinking > 0 and emotion in eye_track_emos:
            hc.blit(assets["face_blink"], (0, 0))
        else:
            hc.blit(assets[f"face_{emotion}"], (0, 0))
            if emotion in eye_track_emos:
                iris = assets["iris"]
                iw = iris.get_width() // 2
                ih = iris.get_height() // 2
                px = int(round(self.pup[0]))
                py = int(round(self.pup[1]))
                if emotion in ("blush", "flustered"):
                    px = -1 if self.pup[0] >= 0 else 1
                hc.blit(iris, (OX - 8 - iw + px, OY - 154 - ih + py))
                hc.blit(iris, (OX + 8 - iw + px, OY - 154 - ih + py))

        if accessory == 1:
            hc.blit(assets["acc_glasses"], (0, 0))

        hsx, hsy = hd.scale()
        blit_pivoted(comp, hc, PIVOTS["head"], dp("head", hx, hy), angle=h_ang, sx=hsx, sy=hsy)

        # Front side hair locks & bangs
        draw_spring(assets["hair_front_l"], "hairL", extra_x=hx, extra_y=hy, angle_add=h_ang * 0.65)
        draw_spring(assets["hair_front_r"], "hairR", extra_x=hx, extra_y=hy, angle_add=h_ang * 0.65)
        draw_spring(assets["hair_bangs"], "bangs", extra_x=hx, extra_y=hy, angle_add=h_ang * 0.85)

        if accessory == 2:
            blit_pivoted(comp, assets["acc_ears"], PIVOTS["head"], dp("head", hx, hy), angle=h_ang, sx=hsx, sy=hsy)

        # Draw open pixel manga book AND bent reading arms gripping its sides cleanly in front!
        if holding_manga:
            m_img = assets["manga_open_flip" if self.manga_turn_t > 0.10 else "manga_open"]
            comp.blit(m_img, (int(COX - 16 + wx), int(COY - 109 + by)))
            blit_pivoted(comp, assets[f"arm_l_{outfit}_manga"], PIVOTS["armL"], dp("armL", 0, by), angle=0.0)
            r_key = f"arm_r_{outfit}_manga_turn" if self.manga_turn_t > 0.10 else f"arm_r_{outfit}_manga"
            blit_pivoted(comp, assets[r_key], PIVOTS["armR"], dp("armR", 0, by), angle=0.0)

        self.mask = pygame.mask.from_surface(comp)
        return comp
