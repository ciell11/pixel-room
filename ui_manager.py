# -*- coding: utf-8 -*-
"""UIManager: Corner HUD, Offline Chat Bar + Quick Chips, Polaroid Selfie Frame, Smooth Settings Modal, RPS & Pixel Cursors."""
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
RAIN_P = ["...####...", ".########.", "##########", ".########.", "..........",
          "..+..+..+.", ".+..+..+.."]
CHAT_P = [".########.", "##########", "##++##++##", "##########", ".########.",
          "..###.....", ".##......."]
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

QUICK_CHIPS = [
    ("Привет!", "Привет!"),
    ("Комплимент", "Ты очень красивая и милая!"),
    ("Как дела?", "Как дела?"),
    ("Пофлиртовать", "Я тебя люблю, поцелуй!"),
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
    """Manages HUD, Chat UI + Quick Chips, Polaroid Selfie Frame, Smooth Settings Modal, RPS & Pixel Cursors."""

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
            "rain":  pattern_surface(RAIN_P,  {"#": (184, 214, 246), "+": (122, 198, 255)}, scale=2),
            "game":  pattern_surface(GAME_P,  {"#": MINT, "+": WHITE}, scale=2),
            "chat":  pattern_surface(CHAT_P,  {"#": (255, 242, 248), "+": PINK}, scale=2),
            "hand":  pattern_surface(HAND_P,  {"#": SKIN}, scale=2),
            "smile": pattern_surface(SMILE_P, {"#": (255, 214, 96)}, scale=2),
            "star":  pattern_surface(STAR_P,  {"#": (255, 246, 174)}, scale=2),
            "excl":  pattern_surface(EXCL_P,  {"#": (255, 96, 102)}, scale=2),
            "zzz":   pattern_surface(ZZZ_P,   {"#": (176, 198, 255)}, scale=2),
            "note":  pattern_surface(NOTE_P,  {"#": (255, 214, 146)}, scale=1),
        }

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
            "rain":  (180, 10),
            "game":  (214, 10),
            "chat":  (532, 320),
            "smile": (566, 320),
            "hand":  (600, 320),
        }
        self.tips = {
            "gear":  "Настройки",
            "shirt": "Наряд (5)",
            "acc":   "Аксессуар (Очки / Ушки)",
            "bulb":  "Свет / Romantic Glow",
            "music": "16-bit Lo-Fi музыка",
            "rain":  "Погода: Дождь / Ясно",
            "game":  "Камень-Ножницы-Бумага",
            "chat":  "Чат с Марин (Enter / T)",
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

        # Chat UI state
        self.chat_open = False
        self.chat_text = ""
        self.chat_blink = 0.0

        # Polaroid Selfie popup state
        self.polaroid_t = 0.0
        self.polaroid_max = 3.4
        self.polaroid_card = None

        # Rock-Paper-Scissors minigame state
        self.rps_phase = None
        self.rps_player = None
        self.rps_marin = None
        self.rps_timer = 0.0
        self.rps_step = 0
        self.rps_outcome = None

    def panel_rects(self):
        return {
            "panel":          (134, 16, 372, 330),
            "close":          (482, 24, 16, 16),
            "physics":        (316, 56, 166, 14),
            "volume":         (316, 86, 166, 14),
            "topmost":        (464, 114, 18, 18),
            "free_life":      (464, 140, 18, 18),
            "weather_rain":   (464, 166, 18, 18),
            "real_time_sync": (464, 192, 18, 18),
            "scale":          (398, 220, 84, 22),
            "reset":          (156, 274, 146, 22),
            "quit":           (398, 274, 84, 22),
            "reset_all":      (156, 306, 326, 24),
        }

    def chat_rects(self):
        rects = {
            "bar":   (104, 320, 374, 26),
            "send":  (484, 320, 40, 26),
            "chips": [],
        }
        cx = 104
        for label, payload in QUICK_CHIPS:
            w = self.font_sm.size(label)[0] + 14
            rects["chips"].append(((cx, 294, w, 20), label, payload))
            cx += w + 6
        return rects

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

    def open_chat(self):
        self.chat_open = True
        self.rps_phase = None
        self.chat_blink = 0.0
        try:
            pygame.key.start_text_input()
        except Exception:
            pass

    def close_chat(self):
        self.chat_open = False
        try:
            pygame.key.stop_text_input()
        except Exception:
            pass

    def trigger_polaroid(self, portrait_surf, label="Marin!"):
        """Build a crisp 16-bit Polaroid card with Marin's snapped portrait and start slide-in."""
        cw, ch = 78, 96
        card = pygame.Surface((cw, ch), pygame.SRCALPHA)
        pygame.draw.rect(card, OUT, (0, 0, cw, ch))
        pygame.draw.rect(card, (250, 246, 240), (2, 2, cw - 4, ch - 4))
        # Inner photo frame (66x66)
        pygame.draw.rect(card, OUT, (5, 5, 68, 68))
        photo = pygame.transform.scale(portrait_surf, (66, 66))
        card.blit(photo, (6, 6))
        # Subtle warm glossy reflection line across photo corner
        pygame.draw.line(card, (255, 255, 255), (9, 9), (19, 9), 1)
        pygame.draw.line(card, (255, 255, 255), (9, 9), (9, 17), 1)
        # Handwritten-style caption & tiny heart cleanly centered in bottom white margin
        txt = self.font_sm.render(label, False, (86, 56, 74))
        h_ic = pattern_surface(HEART_P, {"#": PINK, "+": WHITE}, scale=1)
        tot_w = txt.get_width() + 4 + h_ic.get_width()
        x0 = (cw - tot_w) // 2
        card.blit(txt, (x0, 78))
        card.blit(h_ic, (x0 + txt.get_width() + 4, 79))
        self.polaroid_card = pygame.transform.rotate(card, 4.0)
        self.polaroid_t = self.polaroid_max

    def update_ui(self, dt):
        target = 1.0 if self.settings else 0.0
        self.settings_alpha += (target - self.settings_alpha) * min(1.0, dt * 14.0)
        if abs(target - self.settings_alpha) < 0.01:
            self.settings_alpha = target
        self.chat_blink += dt
        if self.polaroid_t > 0:
            self.polaroid_t = max(0.0, self.polaroid_t - dt)

    # ------------------------------------------------ RPS logic
    def start_rps(self):
        self.close_chat()
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

    def _wrap_text(self, text, max_w=296):
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
        return lines[:3] if lines else [""]

    def draw_speech(self, canvas, rx, ry, speech, shown_len, head_offset_y=0.0):
        if not speech or self.settings:
            return
        lines = self._wrap_text(speech, max_w=296)
        line_h = self.font.get_height() + 2
        tw = max(self.font.size(ln)[0] for ln in lines)
        bw, bh = tw + 18, len(lines) * line_h + 10
        bx = int(clamp(rx - bw // 2, 8, VW - bw - 8))
        by = int(clamp(ry - 208 + head_offset_y - bh, 44, VH - bh - 56))
        self.frame(canvas, (bx, by, bw, bh), WHITE)
        tx = int(clamp(rx, bx + 10, bx + bw - 10))
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

    def draw_polaroid(self, canvas):
        """Smoothly slide-in/fade-out Polaroid selfie card in the left corner."""
        if self.polaroid_t <= 0 or self.polaroid_card is None:
            return
        elapsed = self.polaroid_max - self.polaroid_t
        if elapsed < 0.32:
            p = elapsed / 0.32
            ease = 1.0 - (1.0 - p) ** 3
            px = int(-90 + ease * 104)
            alpha = int(clamp(ease * 255, 0, 255))
        elif self.polaroid_t < 0.45:
            p = self.polaroid_t / 0.45
            ease = p * p
            px = int(-90 + ease * 104)
            alpha = int(clamp(ease * 255, 0, 255))
        else:
            px, alpha = 14, 255
        card = self.polaroid_card.copy()
        card.set_alpha(alpha)
        canvas.blit(card, (px, 52))

    def draw_chat_bar(self, canvas, mouse_pos):
        """Draw compact Quick Reply chips + Cyrillic pixel input bar at bottom of screen."""
        if not self.chat_open or self.settings:
            return
        cr = self.chat_rects()
        # 1. Quick-reply chips
        for rect, label, _ in cr["chips"]:
            hov = self.inr(mouse_pos, rect)
            bg = (88, 62, 108) if hov else (44, 34, 62)
            self.frame(canvas, rect, bg)
            self.text(canvas, label, rect[0] + rect[2] // 2, rect[1] + 4, (255, 232, 244), center=True, small=True)

        # 2. Text input field
        bx, by, bw, bh = cr["bar"]
        self.frame(canvas, (bx, by, bw, bh), (28, 22, 42))
        if self.chat_text:
            # Clip left if user types a long message so caret always stays visible!
            disp = self.chat_text
            while self.font.size(disp)[0] > bw - 20 and len(disp) > 1:
                disp = disp[1:]
            self.text(canvas, disp, bx + 8, by + 6, WHITE, shadow=False)
            if int(self.chat_blink * 2.2) % 2 == 0:
                cx = bx + 9 + self.font.size(disp)[0]
                canvas.fill(PINK, (cx, by + 5, 2, 15))
        else:
            self.text(canvas, "Напиши Марин... (Enter — отправить, Esc — закрыть)",
                      bx + 8, by + 7, (148, 134, 168), shadow=False, small=True)
            if int(self.chat_blink * 2.2) % 2 == 0:
                canvas.fill(PINK, (bx + 7, by + 5, 2, 15))

        # 3. Send button
        sr = cr["send"]
        hov_s = self.inr(mouse_pos, sr)
        self.frame(canvas, sr, (226, 98, 146) if hov_s else (178, 72, 114))
        self.text(canvas, "OK", sr[0] + sr[2] // 2, sr[1] + 6, WHITE, center=True, small=True)

    def draw_hud(self, canvas, mood, aff_lvl, aff_xp, rps_wins, hint_t, assets, rx, ry,
                 music_on=False, rain_on=False, mouse_pos=(0, 0)):
        # Corner buttons
        for name, (x, y) in self.buttons.items():
            hov = self.hover == name
            active_rps = (name == "game" and self.rps_phase is not None)
            active_mus = (name == "music" and music_on)
            active_rain = (name == "rain" and rain_on)
            active_chat = (name == "chat" and self.chat_open)
            if active_rps:
                bg = (52, 86, 80)
            elif active_mus:
                bg = (96, 54, 88)
            elif active_rain:
                bg = (52, 74, 108)
            elif active_chat:
                bg = (118, 58, 92)
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
        for x_tick in range(508, 616, 16):
            canvas.fill((22, 16, 28), (x_tick, 16, 1, 10))
        extra = f" • КНБ: {rps_wins}" if rps_wins > 0 else ""
        self.text(canvas, f"Affinity Lv.{aff_lvl}{extra}", 547, 34, (255, 224, 238), center=True, small=True)

        # Polaroid Selfie card
        self.draw_polaroid(canvas)

        # Bottom overlays (Chat OR RPS OR brief hint)
        if self.chat_open and not self.settings:
            self.draw_chat_bar(canvas, mouse_pos)
        elif self.rps_phase and not self.settings:
            self._draw_rps(canvas, assets, rx, ry)
        elif hint_t > 0 and not self.settings:
            self.text(
                canvas,
                "ЛКМ — тяни/кровать/окно (дождь) • ПКМ — погладить • Enter / T — чат с Марин",
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
        surf.fill((12, 8, 22, int(148 * self.settings_alpha)))

        R = self.panel_rects()
        self.frame(surf, R["panel"], (42, 34, 58))
        self.frame(surf, R["close"], (156, 62, 82))
        x, y, w, h = R["close"]
        pygame.draw.line(surf, WHITE, (x + 4, y + 4), (x + w - 5, y + h - 5), 2)
        pygame.draw.line(surf, WHITE, (x + w - 5, y + 4), (x + 4, y + h - 5), 2)

        self.text(surf, f"Настройки ({VERSION})", 320, 26, GOLD, center=True)

        for key, label, vmax in (("physics", "Физика", 1.5), ("volume", "Громкость", 1.0)):
            sx, sy, sw, sh = R[key]
            v = cfg[key]
            frac = clamp(v / vmax, 0.0, 1.0)
            self.text(surf, label, 156, sy - 2)
            self.text(surf, f"{int(round(v * 100))}%", 258, sy - 2, (210, 206, 228))
            surf.fill(OUT, (sx - 2, sy + 4, sw + 4, 6))
            surf.fill((24, 18, 32), (sx, sy + 5, sw, 4))
            surf.fill((236, 98, 148), (sx, sy + 5, int(sw * frac), 4))
            kx = sx + int(sw * frac) - 4
            self.frame(surf, (kx, sy, 8, 14), (252, 224, 234))

        # 4 Settings checkboxes
        for key, label in (
            ("topmost",        "Поверх всех окон (Always on Top)"),
            ("free_life",      "Свободная жизнь в комнате (ИИ)"),
            ("weather_rain",   "Погода за окном: Уютный дождь"),
            ("real_time_sync", "Свет по реальному времени ПК"),
        ):
            tx, ty, tw, th = R[key]
            self.text(surf, label, 156, ty + 1)
            self.frame(surf, (tx, ty, tw, th), (24, 18, 32))
            if cfg.get(key, False):
                surf.fill((120, 232, 146), (tx + 3, ty + 3, tw - 6, th - 6))

        self.text(surf, "Масштаб окна", 156, R["scale"][1] + 4)
        self.frame(surf, R["scale"], (72, 62, 104))
        self.text(surf, f"x{cfg['scale']} ({VH * cfg['scale']}p)",
                  R["scale"][0] + 42, R["scale"][1] + 4, center=True, small=True)

        # Mini-Statistics bar!
        stats_txt = (
            f"Поглаж.: {cfg.get('stat_pets', 0)}  •  КНБ: {cfg.get('rps_wins', 0)}  •  "
            f"Селфи: {cfg.get('stat_selfies', 0)}  •  Чат: {cfg.get('stat_chats', 0)}"
        )
        self.frame(surf, (156, 248, 326, 18), (30, 24, 44))
        self.text(surf, stats_txt, 319, 251, (255, 224, 238), center=True, small=True)

        self.frame(surf, R["reset"], (68, 86, 118))
        self.text(surf, "Сбросить позу", R["reset"][0] + 73, R["reset"][1] + 4, center=True)

        self.frame(surf, R["quit"], (122, 52, 68))
        self.text(surf, "Выход", R["quit"][0] + 42, R["quit"][1] + 4, center=True)

        ra = R["reset_all"]
        self.frame(surf, ra, (164, 52, 64) if self.confirm_reset else (78, 46, 66))
        msg = "Точно сбросить save.json? Нажми ещё раз!" if self.confirm_reset else "Сбросить прогресс и комнату"
        self.text(surf, msg, ra[0] + ra[2] // 2, ra[1] + 5,
                  (255, 238, 176) if self.confirm_reset else WHITE, center=True, small=True)

        surf.set_alpha(int(clamp(self.settings_alpha * 255, 0, 255)))
        canvas.blit(surf, (0, 0))

    def draw_cursor(self, canvas, pos, state="arrow"):
        surf, (hx, hy) = self.cursors.get(state, self.cursors["arrow"])
        x, y = int(round(pos[0])) - hx, int(round(pos[1])) - hy
        if -16 <= x <= VW + 4 and -16 <= y <= VH + 4:
            canvas.blit(surf, (x, y))
