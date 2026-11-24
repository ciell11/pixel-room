# -*- coding: utf-8 -*-
"""ParticleSystem: sunbeam dust motes, lamp fireflies, romantic rose-gold sparks & soft hearts."""
import math
import random
import pygame
from constants import LAMP_POS, VW, VH, clamp


class ParticleSystem:
    def __init__(self, icons):
        self.icons = icons
        self.items = []      # interactive foreground particles (hearts, stars, dust, zzz, excl)
        self.ambient = []    # atmospheric dust motes, lamp sparkles, romantic micro-sparks & soft hearts
        self._amb_cd = 0.0

    def spawn(self, kind, x, y, count=1):
        for _ in range(count):
            if kind == "dust":
                self.items.append({
                    "k": "dust",
                    "x": x + random.uniform(-16, 16),
                    "y": y + random.uniform(-3, 2),
                    "vx": random.uniform(-42, 42),
                    "vy": random.uniform(-34, -10),
                    "grav": 115.0,
                    "life": random.uniform(0.32, 0.55),
                    "max_life": 0.55,
                    "sz": random.choice((2, 3)),
                })
            elif kind == "heart":
                self.items.append({
                    "k": "heart",
                    "x": x + random.uniform(-14, 14),
                    "y": y + random.uniform(-6, 4),
                    "vx": random.uniform(-22, 22),
                    "vy": random.uniform(-62, -36),
                    "grav": 22.0,
                    "life": random.uniform(0.95, 1.45),
                    "max_life": 1.45,
                })
            elif kind == "kiss_heart":
                # Special blown-kiss heart drifting gracefully forward & up!
                self.items.append({
                    "k": "heart",
                    "x": x + 6,
                    "y": y,
                    "vx": random.uniform(22, 38),
                    "vy": random.uniform(-36, -24),
                    "grav": -4.0,
                    "life": 1.65,
                    "max_life": 1.65,
                })
            elif kind == "star":
                self.items.append({
                    "k": "star",
                    "x": x + random.uniform(-12, 12),
                    "y": y + random.uniform(-8, 6),
                    "vx": random.uniform(-55, 55),
                    "vy": random.uniform(-95, -45),
                    "grav": 180.0,
                    "life": random.uniform(0.65, 1.15),
                    "max_life": 1.15,
                })
            else:
                self.items.append({
                    "k": kind,
                    "x": x + random.uniform(-6, 6),
                    "y": y,
                    "vx": random.uniform(-12, 16),
                    "vy": random.uniform(-48, -28),
                    "grav": 0.0,
                    "life": random.uniform(0.9, 1.4),
                    "max_life": 1.4,
                })

    def update(self, dt, sun_visible, lamp_lit, romantic_vibe=False):
        alive = []
        for p in self.items:
            p["vy"] += p["grav"] * dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vx"] *= 0.96
            p["life"] -= dt
            if p["life"] > 0:
                alive.append(p)
        self.items = alive

        self._amb_cd -= dt
        if self._amb_cd <= 0 and len(self.ambient) < 32:
            self._amb_cd = 0.20
            if romantic_vibe and random.random() < 0.62:
                # Soft glowing rose-gold sparks & semi-transparent pixel hearts!
                is_heart = random.random() < 0.28
                self.ambient.append({
                    "kind": "soft_heart" if is_heart else "rom_spark",
                    "x": random.uniform(110, VW - 90),
                    "y": random.uniform(110, VH - 40),
                    "vx": random.uniform(-6.0, 6.0),
                    "vy": random.uniform(-14.0, -7.0),
                    "phase": random.uniform(0, 6.28),
                    "life": random.uniform(2.6, 4.6),
                    "max_life": 4.6,
                    "sz": 2 if is_heart else random.choice((1, 2)),
                })
            elif sun_visible:
                y0 = random.uniform(115, 325)
                t = (y0 - 115) / 210.0
                x0 = random.uniform(265 + t * 28, 376 + t * 50)
                self.ambient.append({
                    "kind": "mote",
                    "x": x0, "y": y0,
                    "vx": random.uniform(-4.0, 6.0),
                    "vy": random.uniform(-7.0, -2.5),
                    "phase": random.uniform(0, 6.28),
                    "life": random.uniform(2.8, 5.2),
                    "max_life": 5.2,
                    "sz": random.choice((1, 2)),
                })
            elif lamp_lit:
                ang = random.uniform(0, 6.283)
                rad = random.uniform(16, 86)
                self.ambient.append({
                    "kind": "glow",
                    "x": LAMP_POS[0] + math.cos(ang) * rad,
                    "y": LAMP_POS[1] + math.sin(ang) * rad * 0.85,
                    "vx": random.uniform(-5.0, 5.0),
                    "vy": random.uniform(-9.0, -3.0),
                    "phase": random.uniform(0, 6.28),
                    "life": random.uniform(1.8, 3.6),
                    "max_life": 3.6,
                    "sz": random.choice((1, 2)),
                })

        amb_alive = []
        for a in self.ambient:
            a["phase"] += dt * 2.4
            a["x"] += (a["vx"] + math.sin(a["phase"]) * 4.5) * dt
            a["y"] += a["vy"] * dt
            a["life"] -= dt
            if a["life"] > 0:
                amb_alive.append(a)
        self.ambient = amb_alive

    def draw_ambient(self, canvas):
        for a in self.ambient:
            p = a["life"] / a["max_life"]
            fade = math.sin(clamp(p, 0.0, 1.0) * math.pi)
            twinkle = 0.65 + 0.35 * math.sin(a["phase"] * 2.1)
            alpha = int(clamp(fade * twinkle * 195, 0, 215))
            if alpha < 12:
                continue
            k = a["kind"]
            if k == "soft_heart":
                hs = self.icons["heart"].copy()
                hs.set_alpha(int(alpha * 0.58))
                canvas.blit(hs, (int(a["x"]), int(a["y"])))
            else:
                sz = a["sz"]
                s = pygame.Surface((sz, sz), pygame.SRCALPHA)
                if k == "mote":
                    s.fill((255, 250, 224, alpha))
                elif k == "rom_spark":
                    s.fill((255, 198, 222, alpha))
                else:
                    s.fill((255, 226, 148, alpha))
                canvas.blit(s, (int(a["x"]), int(a["y"])))

    def draw_foreground(self, canvas):
        for p in self.items:
            if p["k"] == "dust":
                alpha = int(clamp((p["life"] / p["max_life"]) * 185, 0, 200))
                sz = p["sz"]
                s = pygame.Surface((sz, sz), pygame.SRCALPHA)
                s.fill((236, 212, 192, alpha))
                canvas.blit(s, (int(p["x"]), int(p["y"])))
            else:
                img = self.icons[p["k"]]
                if p["k"] == "heart" and p["life"] < 0.28 and int(p["life"] * 22) % 2:
                    continue
                canvas.blit(img, (int(p["x"]) - img.get_width() // 2, int(p["y"])))

    def clear(self):
        self.items.clear()
        self.ambient.clear()
