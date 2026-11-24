# -*- coding: utf-8 -*-
"""UIManager: Corner HUD, Lo-Fi Note button, Smooth Settings Modal, RPS Minigame, and Custom 16-bit Pixel Cursors."""
import random
import pygame
from constants import VERSION, VW, VH, OUT, WHITE, PINK, MINT, SKIN, SHIRT, TIE, GOLD, clamp

# ------------------------------------------------------------------ pixel UI icon bitmaps
HEART_P = [".##.##.", "#######", "#++####", ".#####.", "..###..", "...#..."]
GEAR_P = ["...#..#...", "..######..", ".########.", "####..####", "###....###",
          "###....###", "####..####", ".########.", "..######..", "...#..#..."]
SHIRT_P = ["...##..##...", ".###+..+###.", "####+..+####", "####.++.####", "###.####.###",
           "...######...", "...######...", "...######...", "...######..."]
ACC_P = ["..##....##..", ".####..####.", ".#++####++#.", ".##########.", "............",
         ".####..####.", ".#++####++#.", ".####..####."]
BULB_P = ["..####..", ".##++##.", "##+#####", "########", "########", ".######.",
          "..####..", "..====..", "..====..", "...==..."]
NOTE_P = ["....######", "...#######", "...##...##", "...##...##", "...##...##",
          "..###..###", ".####.####", ".###...###"]
GAME_P = ["..########..", ".##########.", "##+##++##+##", "#####++#####", "###+####+###",
          "############", ".###....###.", "..##....##.."]
HAND_P = ["....#.....", "..#.#.#...", "..#.#.#.#.", "..#.#.#.#.", "..#######.", "#.#######.",
          "##.######.", ".########.", "..#######.", "...#####..", "...#####.."]
SMILE_P = [".######.", "##.##.##", "########", "#.####.#", "##....##", ".######."]
STAR_P = ["..#..", ".###.", "#####", ".###.", "..#.."]
EXCL_P = ["##", "##", "##", "##", "..", "##"]
ZZZ_P  = ["#####", "...#.", "..#..", ".#...", "#####"]

# ------------------------------------------------------------------ custom 16-bit pixel cursors (1x native grid)
CUR_ARROW_P = [
    "#........",
    "##.......",
    "#+#......",
    "#++#.....",
    "#+++#....",
    "#++++#...",
    "#+++++#..",
    "#++++++#.",
    "#+++####.",
    "#++#.#...",
    "##...#...",
    "......#..",
]
CUR_HAND_OPEN_P = [
    "....##.....",
    "..#.##.#...",
    "..#.##.##..",
    "..#.##.##..",
    "#.#.##.##..",
    "#.#######..",
    ".########..",
    ".########..",
    "..#######..",
    "...#####...",
    "...#####...",
]
CUR_HAND_GRAB_P = [
    "...........",
    "..##.##.##.",
    ".#########.",
    "##########.",
    "##########.",
    ".#########.",
    ".########..",
    "..#######..",
    "...#####...",
    "...#####...",
]
CUR_HAND_HEART_P = [
    "....##.##..",
    "...#######.",
    "....#####..",
    "..#..###...",
    "#.#.##.#...",
    "#.#######..",
    ".########..",
    ".########..",
    "..#######..",
    "...#####...",
]


def pattern_surface(rows, colors, scale=2):
    h, w = len(rows), max(len(r) for r in rows)
    s = pygame.Surface((w + 2, h + 2), pygame.SRCALPHA)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in colors:
                s.set_at((x + 1, y + 1), colors[ch])
    m = pygame.mask.from_surface(s)
    sil = m.to_surface(setcolor=OUT + (255,), unsetcolor=(0, 0, 0, 0))
    o = pygame.Surface(s.get_size(), pygame.SRCALPHA)
    for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        o.blit(sil, d)
    o.blit(s, (0, 0))
    return pygame.transform.scale_by(o, scale) if scale > 1 else o


class UIManager:
    """Manages HUD buttons, tooltips, speech bubble, smooth Settings modal, RPS Minigame & Pixel Cursors."""

    def __init__(self):
        self.font = pygame.font.Font(None, 18)
        self.font_sm = pygame.font.Font(None, 15)
        self.icons = {
            "heart": pattern_surface(HEART_P, {"#": PINK, "+": WHITE}, scale=2),
            "gear":  pattern_surface(GEAR_P,  {"#": (204, 206, 222)}, scale=2),
            "shirt": pattern_surface(SHIRT_P, {"#": SHIRT, "+": TIE}, scale=2),
            "acc":   pattern_surface(ACC_P,   {"#": PINK, "+": WHITE}, scale=2),
            "bulb":  pattern_surface(BULB_P,  {"#": (255, 228, 126), "+": WHITE, "=": (154, 154, 170)}, scale=2),
            "music": pattern_surface(NOTE_P,  {"#": (255, 174, 212)}, scale=2),
            "game":  pattern_surface(GAME_P,  {"#": MINT, "+": WHITE}, scale=2),
            "hand":  pattern_surface(HAND_P,  {"#": SKIN}, scale=2),
            "smile": pattern_surface(SMILE_P, {"#": (255, 214, 96)}, scale=2),
            "star":  pattern_surface(STAR_P,  {"#": (255, 246, 174)}, scale=2),
            "excl":  pattern_surface(EXCL_P,  {"#": (255, 96, 102)}, scale=2),
            "zzz":   pattern_surface(ZZZ_P,   {"#": (176, 198, 255)}, scale=2),
        }

        # Custom 16-bit pixel cursors (rendered natively on the 640x360 canvas)
        self.cursors = {
            "arrow":      (pattern_surface(CUR_ARROW_P,      {"#": (255, 236, 244), "+": WHITE}, scale=1), (1, 1)),
            "hand_open":  (pattern_surface(CUR_HAND_OPEN_P,  {"#": SKIN}, scale=1), (5, 2)),
            "hand_grab":  (pattern_surface(CUR_HAND_GRAB_P,  {"#": (255, 208, 188)}, scale=1), (5, 4)),
            "hand_heart": (pattern_surface(CUR_HAND_HEART_P, {"#": PINK}, scale=1), (5, 4)),
        }

        self.buttons = {
            "gear":  (10, 10),
            "shirt": (44, 10),
            "acc":   (78, 10),
            "bulb":  (112, 10),
            "music": (146, 10),
            "game":  (180, 10),
            "smile": (566, 320),
            "hand":  (600, 320),
        }
        self.tips = {
            "gear":  "Настройки",
            "shirt": "Наряд (5)",
            "acc":   "Аксессуар (Очки / Ушки)",
            "bulb":  "Свет / Romantic Glow",
            "music": "16-bit Lo-Fi музыка",
            "game":  "Камень-Ножницы-Бумага",
            "smile": "Эмоции (10)",
            "hand":  "Помахать",
        }

        # Settings modal state + smooth alpha easing
        self.settings = False
        self.settings_alpha = 0.0
        self._modal_surf = pygame.Surface((VW, VH), pygame.SRCALPHA)
        self.slider = None
        self.confirm_reset = False
        self.hover = None

        # Rock-Paper-Scissors minigame state
        self.rps_phase = None
        self.rps_player = None
        self.rps_marin = None
        self.rps_timer = 0.0
        self.rps_step = 0
        self.rps_outcome = None

    def panel_rects(self):
        return {
            "panel":     (146, 32, 348, 296),
            "close":     (470, 40, 16, 16),
            "physics":   (308, 78, 162, 14),
            "volume":    (308, 112, 162, 14),
            "topmost":   (452, 144, 18, 18),
            "free_life": (452, 174, 18, 18),
            "scale":     (386, 206, 84, 22),
            "reset":     (168, 246, 138, 24),
            "quit":      (386, 246, 84, 24),
            "reset_all": (168, 284, 302, 24),
        }

    def rps_rects(self):
        return {
            "rock":     (222, 294, 58, 42),
            "scissors": (291, 294, 58, 42),
            "paper":    (360, 294, 58, 42),
            "close":    (426, 294, 22, 22),
        }

    @staticmethod
    def inr(p, r):
        return r[0] <= p[0] < r[0] + r[2] and r[1] <= p[1] < r[1] + r[3]

    def ui_hit(self, mx, my):
        for name, (x, y) in self.buttons.items():
            if x <= mx < x + 28 and y <= my < y + 28:
                return name
        return None

    def update_ui(self, dt):
        target = 1.0 if self.settings else 0.0
        self.settings_alpha += (target - self.settings_alpha) * min(1.0, dt * 14.0)
        if abs(target - self.settings_alpha) < 0.01:
            self.settings_alpha = target

    # ------------------------------------------------ RPS logic
    def start_rps(self):
        self.rps_phase = "choose"
        self.rps_player = None
        self.rps_marin = None
        self.rps_outcome = None

    def close_rps(self):
        self.rps_phase = None

    def pick_rps(self, choice):
        self.rps_player = choice
        self.rps_marin = random.choice(("rock", "scissors", "paper"))
        self.rps_phase = "countdown"
        self.rps_timer = 1.25
        self.rps_step = 3

    def update_rps(self, dt):
        if self.rps_phase == "countdown":
            prev_step = int(self.rps_timer / 0.4)
            self.rps_timer -= dt
            cur_step = int(max(0.0, self.rps_timer) / 0.4)
            if self.rps_timer <= 0:
                self.rps_phase = "result"
                self.rps_timer = 2.6
                p, m = self.rps_player, self.rps_marin
                if p == m:
                    self.rps_outcome = "draw"
                elif (p == "rock" and m == "scissors") or (p == "scissors" and m == "paper") or (p == "paper" and m == "rock"):
                    self.rps_outcome = "win"
                else:
                    self.rps_outcome = "lose"
                return self.rps_outcome
            elif cur_step != prev_step:
                self.rps_step = cur_step + 1
                return "tick"
        elif self.rps_phase == "result":
            self.rps_timer -= dt
            if self.rps_timer <= 0:
                self.rps_phase = "choose"
        return None

    # ------------------------------------------------ drawing helpers
    def text(self, canvas, txt, x, y, col=WHITE, center=False, shadow=True, small=False):
        f = self.font_sm if small else self.font
        img = f.render(txt, False, col)
        px, py = int(x), int(y)
        if center:
            px -= img.get_width() // 2
        if shadow:
            canvas.blit(f.render(txt, False, (28, 18, 28)), (px + 1, py + 1))
        canvas.blit(img, (px, py))

    @staticmethod
    def frame(canvas, r, fill=(36, 30, 48)):
        x, y, w, h = r
        canvas.fill(OUT, (x - 2, y, w + 4, h))
        canvas.fill(OUT, (x, y - 2, w, h + 4))
        canvas.fill(OUT, (x - 1, y - 1, w + 2, h + 2))
        canvas.fill(fill, (x, y, w, h))
        canvas.fill(tuple(min(255, v + 28) for v in fill), (x, y, w, 2))

    def _wrap_text(self, text, max_w=310):
        words = text.split(" ")
        lines, cur = [], ""
        for w in words:
            cand = f"{cur} {w}".strip()
            if cur and self.font.size(cand)[0] > max_w:
                lines.append(cur)
                cur = w
            else:
                cur = cand
        if cur:
            lines.append(cur)
        return lines or [""]

    def draw_speech(self, canvas, rx, ry, speech, shown_len):
        if not speech or self.settings:
            return
        lines = self._wrap_text(speech, max_w=310)
        line_h = self.font.get_height() + 2
        tw = max(self.font.size(ln)[0] for ln in lines)
        bw, bh = tw + 18, len(lines) * line_h + 10
        bx = int(clamp(rx - bw // 2, 8, VW - bw - 8))
        by = int(max(8, ry - 208 - bh))
        self.frame(canvas, (bx, by, bw, bh), WHITE)
        tx = int(clamp(rx, bx + 8, bx + bw - 10))
        pygame.draw.polygon(canvas, WHITE, [(tx - 4, by + bh), (tx + 4, by + bh), (tx, by + bh + 6)])
        pygame.draw.line(canvas, OUT, (tx - 5, by + bh), (tx, by + bh + 6), 2)
        pygame.draw.line(canvas, OUT, (tx + 5, by + bh), (tx, by + bh + 6), 2)
        rem = int(shown_len)
        for idx, ln in enumerate(lines):
            if rem <= 0:
                break
            part = ln[:rem]
            rem -= len(ln) + 1
            self.text(canvas, part, bx + 9, by + 6 + idx * line_h, (56, 38, 58), shadow=False)

    def draw_hud(self, canvas, mood, aff_lvl, aff_xp, rps_wins, hint_t, assets, rx, ry, music_on=False):
        # Corner buttons
        for name, (x, y) in self.buttons.items():
            hov = self.hover == name
            active_rps = (name == "game" and self.rps_phase is not None)
            active_mus = (name == "music" and music_on)
            if active_rps:
                bg = (52, 86, 80)
            elif active_mus:
                bg = (96, 54, 88)
            elif hov:
                bg = (64, 52, 86)
            else:
                bg = (36, 30, 48)
            self.frame(canvas, (x, y, 28, 28), bg)
            img = self.icons[name]
            canvas.blit(img, (x + 14 - img.get_width() // 2, y + 14 - img.get_height() // 2))

        if self.hover and not self.settings:
            x, y = self.buttons[self.hover]
            tip = self.tips[self.hover]
            tw, th = self.font_sm.size(tip)
            tx = int(clamp(x + 14 - tw // 2, 6, VW - tw - 14))
            ty = y + 34 if y < 180 else y - 22
            self.frame(canvas, (tx, ty, tw + 10, th + 6), (36, 30, 48))
            self.text(canvas, tip, tx + 5, ty + 3, small=True)

        # Clean Mood & Affinity bar (top-right, strictly above FAIRY_POS y=48!)
        self.frame(canvas, (466, 10, 162, 22))
        canvas.blit(self.icons["heart"], (470, 13))
        canvas.fill((22, 16, 28), (492, 16, 128, 10))
        fw = int(128 * clamp(mood, 0, 100) / 100.0)
        canvas.fill((236, 98, 148), (492, 16, fw, 10))
        canvas.fill((255, 174, 204), (492, 16, fw, 2))
        # Strictly internal segment ticks (never outside right edge 620!)
        for x_tick in range(508, 616, 16):
            canvas.fill((22, 16, 28), (x_tick, 16, 1, 10))
        extra = f" • КНБ: {rps_wins}" if rps_wins > 0 else ""
        self.text(canvas, f"Affinity Lv.{aff_lvl}{extra}", 547, 34, (255, 224, 238), center=True, small=True)

        # RPS Minigame overlay (when open & settings closed)
        if self.rps_phase and not self.settings:
            self._draw_rps(canvas, assets, rx, ry)
        elif hint_t > 0 and not self.settings:
            self.text(
                canvas,
                "ЛКМ — тяни/пересади на кровать, подушка, гирлянда, ящики • ПКМ по голове — погладить",
                320, 342, (255, 242, 224), center=True, small=True
            )

    def _draw_rps(self, canvas, assets, rx, ry):
        R = self.rps_rects()
        bx = int(clamp(rx + 42, 24, VW - 68))
        by = int(clamp(ry - 146, 56, VH - 90))
        if self.rps_phase == "countdown":
            self.frame(canvas, (bx, by, 44, 44), (48, 38, 68))
            words = {3: "Камень", 2: "Ножн.", 1: "Бумага"}
            self.text(canvas, str(self.rps_step), bx + 22, by + 6, GOLD, center=True)
            self.text(canvas, words.get(self.rps_step, "..."), bx + 22, by + 24, WHITE, center=True, small=True)
        elif self.rps_phase == "result" and self.rps_marin:
            col = (56, 104, 78) if self.rps_outcome == "win" else ((114, 54, 72) if self.rps_outcome == "lose" else (68, 64, 96))
            self.frame(canvas, (bx, by, 44, 44), col)
            ic = assets[f"rps_{self.rps_marin}"]
            canvas.blit(ic, (bx + 22 - ic.get_width() // 2, by + 22 - ic.get_height() // 2))

        labels = {"rock": "Камень", "scissors": "Ножницы", "paper": "Бумага"}
        for key in ("rock", "scissors", "paper"):
            r = R[key]
            sel = (self.rps_player == key and self.rps_phase != "choose")
            self.frame(canvas, r, (78, 64, 114) if sel else (40, 32, 56))
            ic = assets[f"rps_{key}"]
            canvas.blit(ic, (r[0] + r[2] // 2 - ic.get_width() // 2, r[1] + 2))
            self.text(canvas, labels[key], r[0] + r[2] // 2, r[1] + 29, WHITE, center=True, small=True)

        cr = R["close"]
        self.frame(canvas, cr, (142, 56, 74))
        pygame.draw.line(canvas, WHITE, (cr[0] + 6, cr[1] + 6), (cr[0] + 15, cr[1] + 15), 2)
        pygame.draw.line(canvas, WHITE, (cr[0] + 15, cr[1] + 6), (cr[0] + 6, cr[1] + 15), 2)

    def draw_settings(self, canvas, cfg):
        if self.settings_alpha <= 0.02:
            return
        surf = self._modal_surf
        surf.fill((0, 0, 0, 0))
        surf.fill((12, 8, 22, int(144 * self.settings_alpha)))

        R = self.panel_rects()
        self.frame(surf, R["panel"], (42, 34, 58))
        self.frame(surf, R["close"], (156, 62, 82))
        x, y, w, h = R["close"]
        pygame.draw.line(surf, WHITE, (x + 4, y + 4), (x + w - 5, y + h - 5), 2)
        pygame.draw.line(surf, WHITE, (x + w - 5, y + 4), (x + 4, y + h - 5), 2)

        self.text(surf, f"Настройки ({VERSION})", 320, 42, GOLD, center=True)

        for key, label, vmax in (("physics", "Физика", 1.5), ("volume", "Громкость", 1.0)):
            sx, sy, sw, sh = R[key]
            v = cfg[key]
            frac = clamp(v / vmax, 0.0, 1.0)
            self.text(surf, label, 168, sy - 2)
            self.text(surf, f"{int(round(v * 100))}%", 258, sy - 2, (210, 206, 228))
            surf.fill(OUT, (sx - 2, sy + 4, sw + 4, 6))
            surf.fill((24, 18, 32), (sx, sy + 5, sw, 4))
            surf.fill((236, 98, 148), (sx, sy + 5, int(sw * frac), 4))
            kx = sx + int(sw * frac) - 4
            self.frame(surf, (kx, sy, 8, 14), (252, 224, 234))

        # Checkboxes: Always on Top & Free Life AI
        for key, label in (("topmost", "Поверх всех окон (Always on Top)"),
                           ("free_life", "Свободная жизнь в комнате (ИИ)")):
            tx, ty, tw, th = R[key]
            self.text(surf, label, 168, ty + 1)
            self.frame(surf, (tx, ty, tw, th), (24, 18, 32))
            if cfg.get(key, False):
                surf.fill((120, 232, 146), (tx + 3, ty + 3, tw - 6, th - 6))

        self.text(surf, "Масштаб окна", 168, R["scale"][1] + 4)
        self.frame(surf, R["scale"], (72, 62, 104))
        self.text(surf, f"x{cfg['scale']} ({VH * cfg['scale']}p)",
                  R["scale"][0] + 42, R["scale"][1] + 4, center=True, small=True)

        self.frame(surf, R["reset"], (68, 86, 118))
        self.text(surf, "Сбросить позу", R["reset"][0] + 69, R["reset"][1] + 5, center=True)

        self.frame(surf, R["quit"], (122, 52, 68))
        self.text(surf, "Выход", R["quit"][0] + 42, R["quit"][1] + 5, center=True)

        ra = R["reset_all"]
        self.frame(surf, ra, (164, 52, 64) if self.confirm_reset else (78, 46, 66))
        msg = "Точно сбросить save.json? Нажми ещё раз!" if self.confirm_reset else "Сбросить прогресс и комнату"
        self.text(surf, msg, ra[0] + ra[2] // 2, ra[1] + 5,
                  (255, 238, 176) if self.confirm_reset else WHITE, center=True, small=True)

        surf.set_alpha(int(clamp(self.settings_alpha * 255, 0, 255)))
        canvas.blit(surf, (0, 0))

    def draw_cursor(self, canvas, pos, state="arrow"):
        """Render the custom 16-bit pixel cursor directly on the native 640x360 canvas."""
        surf, (hx, hy) = self.cursors.get(state, self.cursors["arrow"])
        x, y = int(round(pos[0])) - hx, int(round(pos[1])) - hy
        if -16 <= x <= VW + 4 and -16 <= y <= VH + 4:
            canvas.blit(surf, (x, y))
