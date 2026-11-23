# -*- coding: utf-8 -*-
"""Pixel Room (640x360 High-Bit Pixel Art) - LMB/RMB Split, Interactive Room & 8 Emotions."""
import os
import sys
import math
import random
import json
import array

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

VW, VH = 640, 360
FLOOR_Y = 336
SR = 22050
CW, CH, OX, OY = 160, 220, 80, 210
PAD = 44
COMP_W, COMP_H = CW + PAD * 2, CH + PAD * 2
COX, COY = OX + PAD, OY + PAD
LAMP_POS = (606, 162)

PILLOW_HOME = (453.0, 200.0)
BOBA_HOME = (582.0, 176.0)

TINTS = [
    (255, 255, 255),  # Day
    (255, 214, 184),  # Sunset
    (138, 126, 174),  # Evening / Night
]
LIGHT_KEYS = ["day", "sunset", "evening"]

OUT = (52, 34, 44)
WHITE = (255, 255, 255)
PINK = (244, 128, 158)
SKIN = (255, 222, 202)
SHIRT = (244, 243, 242)
TIE = (104, 110, 128)

# 8 distinct facial expressions
EMOS = ["normal", "pet", "blush", "smug", "surprised", "sleepy", "pout", "starry"]

LINES = {
    "body": ["Эй! Щекотно!", "Ой, не толкайся~", "Хи-хи, перестань!", "Хэй! Что за дела?"],
    "cheek": ["М-м? Мои щёчки!", "Эй, не тяни за щёку~", "Ой! Смущаешь..."],
    "hair": ["Эй, причёску не порти!", "Мои волосы~ они же пружинят!", "Ой, отпусти прядь!"],
    "tie": ["Эй! Галстук потянешь!", "Отпусти галстук~", "Н-ну перестань дёргать!"],
    "skirt": ["Эй! Не дёргай за одежду!", "Ой-ой, аккуратнее!", "Н-не смешно!"],
    "highfive": ["Дай пять!", "Еее! Хай-файв~", "Отлично!", "Классно!"],
    "arm_wave": ["Привет-привет~", "Ха-ха, машем вместе!", "Хай-хай!"],
    "pillow": ["Эй, подушечный бой?!", "Ой! Прямо в меня!", "Ах так?! Держись~", "Хэй, подушкой нельзя!"],
    "boba": ["Ммм, вкуснейший бабл-ти~!", "Обожаю тапиоку! Звёздочки в глазах!", "Спасибо~! Это просто космос!"],
    "pet": ["Мрр... так приятно~", "Ещё погладь, пожалуйста...", "Хе-хе, так уютно~", "М-м, хорошо..."],
    "grab": ["Ва-а! Высоко!", "Поставь меня на пол!", "Я лечу-у!"],
    "land": ["Фух, приземлилась!", "Ой-ой, не кидайся так!", "Смущаешь, вообще-то!"],
    "shake_pout": ["Хватит меня трясти!", "Хмпф! У меня голова закружится!", "Всё, я обиделась!"],
    "outfit_0": ["Классика! Школьная форма всегда в тему~", "Как тебе мой школьный образ?"],
    "outfit_1": ["Дома можно и расслабиться~", "Свободная рубашка — самое удобное!"],
    "outfit_2": ["Оверсайз худи — просто топ!", "Смотри, какая уютная кофта!"],
    "light_day": ["Доброе утро! Солнышко светит~", "Отличный ясный день!"],
    "light_sunset": ["Ого, какой красивый закат...", "Обожаю этот золотой свет~"],
    "light_eve": ["Уютный вечер с ночником~", "Включили лампу — сразу теплее!"],
    "light_dark": ["Ой, совсем стемнело...", "Выключили свет..."],
    "curtain_close": ["Прикроем шторы — так уютнее~", "Полумрак для отдыха!"],
    "curtain_open": ["Впустим немного света!", "О, так намного светлее~"],
    "sleepy_dark": ["*зевает* Темно и так хочется спать...", "М-м... ещё пять минуточек...", "Глазки слипаются..."],
    "poster_0": ["Обожаю этот тайтл! Лучший опенинг!", "Ах, мой любимый постер~"],
    "poster_1": ["Шизуку-тан! Хочу сделать этот косплей!", "Махо-сёдзё — чистый восторг!"],
    "poster_2": ["Киберпанк-эстетика! Выглядит дерзко, да?", "Эту героиню я точно закосплею!"],
    "drawer_top": ["О, мои очки для косплея!", "Тсс, там мои секретные аксессуары~"],
    "drawer_bot": ["Это новый выпуск журнала про косплей!", "Не подглядывай в мои журналы~"],
    "laundry": ["Ой! Вещи надо бы разобрать потом...", "Творческий беспорядок, хи-хи!"],
    "manga": ["О, я на самом интересном моменте остановилась!", "Эта манга просто огонь!"],
    "wave": ["Привет-привет!", "Хай-хай!", "Я тут!"],
    "idle": ["Скучновато...", "Погладь меня правой кнопкой мыши~", "Хочу бабл-ти~", "Может, сменим постер?"],
    "reset": ["Поза сброшена!", "Снова на месте~"],
    # Manual emotion button lines
    "normal": ["Уверенная полуулыбка — мой стиль~"],
    "blush": ["Н-не смотри на меня так пристально!"],
    "smug": ["Хе-хе, я же знаю, что круто выгляжу~"],
    "surprised": ["Ого! Вот это неожиданность!"],
    "sleepy": ["*зевает* Что-то меня в сон клонит..."],
    "pout": ["Хмпф! Я немного недовольна."],
    "starry": ["Вау!! Глаза прямо сияют!"],
}

PIVOTS = {
    "head":  (OX,      OY - 138),
    "bangs": (OX,      OY - 184),
    "hairL": (OX - 14, OY - 174),
    "hairR": (OX + 14, OY - 174),
    "hairB": (OX,      OY - 178),
    "tie":   (OX,      OY - 125),
    "folds": (OX,      OY - 114),
    "skirt": (OX,      OY - 93),
    "armL":  (OX - 14, OY - 126),
    "armR":  (OX + 14, OY - 126),
}


def res_dir():
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


def clamp(v, a, b):
    return a if v < a else b if v > b else v


# ------------------------------------------------------------------ lightweight retro SFX (no radio!)
def tone(f0, f1, dur, wave="sq", vol=0.26, vib=0.0, attack=0.004):
    n = int(SR * dur)
    out = array.array("h", [0]) * n
    ph = 0.0
    lp = 0.0
    for i in range(n):
        t = i / SR
        p = i / n
        f = f0 + (f1 - f0) * p
        if vib:
            f *= 1 + 0.06 * math.sin(6.283 * vib * t)
        ph += f / SR
        fr = ph % 1.0
        if wave == "sq":
            x = 1.0 if fr < 0.5 else -1.0
        elif wave == "tri":
            x = 4 * abs(fr - 0.5) - 1
        elif wave == "noise":
            lp += (random.uniform(-1, 1) - lp) * 0.25
            x = lp * 2.2
        else:
            x = math.sin(6.283 * fr)
        env = min(1.0, t / attack) * (1 - p) ** 1.6
        out[i] = int(clamp(x * env * vol, -1, 1) * 32000)
    return out


def cat(*parts):
    a = array.array("h")
    for p in parts:
        a.extend(p)
    return a


class Sfx:
    def __init__(self):
        self.ok = pygame.mixer.get_init() is not None
        self.s = {}
        if not self.ok:
            return
        mk = lambda a: pygame.mixer.Sound(buffer=a.tobytes())
        self.s["click"] = mk(tone(1300, 900, 0.035, "sq", 0.16))
        self.s["pop"] = mk(tone(760, 260, 0.09, "sq", 0.20))
        self.s["boing"] = mk(tone(180, 580, 0.20, "tri", 0.42, vib=18))
        self.s["snap"] = mk(tone(260, 680, 0.14, "tri", 0.34, vib=22))
        self.s["pillow"] = mk(cat(tone(140, 75, 0.11, "tri", 0.52), tone(0, 0, 0.06, "noise", 0.20)))
        self.s["sip"] = mk(cat(tone(520, 880, 0.09, "tri", 0.24), tone(660, 1080, 0.11, "tri", 0.26)))
        self.s["heart"] = mk(cat(tone(1046, 1046, 0.05, "tri", 0.30), tone(1568, 1568, 0.09, "tri", 0.30)))
        self.s["whoosh"] = mk(tone(0, 0, 0.22, "noise", 0.40, attack=0.06))
        self.s["curtain"] = mk(tone(0, 0, 0.18, "noise", 0.28, attack=0.05))
        self.s["drawer"] = mk(cat(tone(210, 140, 0.07, "tri", 0.32), tone(0, 0, 0.06, "noise", 0.18)))
        self.s["page"] = mk(tone(0, 0, 0.08, "noise", 0.25, attack=0.01))
        self.s["lamp"] = mk(cat(tone(2200, 1500, 0.012, "sq", 0.14), tone(320, 300, 0.06, "sq", 0.09)))
        self.s["land"] = mk(tone(170, 55, 0.11, "tri", 0.52))
        self.s["sparkle"] = mk(cat(tone(1318, 1318, 0.04, "tri", 0.28),
                                   tone(1760, 1760, 0.04, "tri", 0.28),
                                   tone(2093, 2093, 0.08, "tri", 0.28)))
        self.blips = [mk(tone(f, f * 1.08, 0.032, "sq", 0.08)) for f in (520, 590, 660, 740, 820)]

    def volume(self, v):
        for snd in list(self.s.values()) + getattr(self, "blips", []):
            snd.set_volume(v)

    def play(self, name):
        if self.ok and name in self.s:
            self.s[name].play()

    def blip(self):
        if self.ok:
            random.choice(self.blips).play()


# ------------------------------------------------------------------ bouncy elastic spring-damper
class Spring2D:
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
        if self.pulled:
            pk, pc = self.k * 2.4, self.c * 2.5
            self.vx += (pk * (self.tx - self.x) - pc * self.vx) * dt
            self.vy += (pk * (self.ty - self.y) - pc * self.vy) * dt
        else:
            self.vx += (-self.k * self.x - self.c * self.vx - self.inertia * ax * inten) * dt
            self.vy += (-self.k * self.y - self.c * self.vy - self.inertia * ay * inten) * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        lim_x = self.cx * (2.2 if self.pulled else 1.0)
        lim_y = self.cy * (2.2 if self.pulled else 1.0)
        if abs(self.x) > lim_x:
            self.x = math.copysign(lim_x, self.x)
            self.vx *= -0.42
        if abs(self.y) > lim_y:
            self.y = math.copysign(lim_y, self.y)
            self.vy *= -0.42

    def kick(self, vx, vy, inten):
        self.vx += vx * inten
        self.vy += vy * inten

    def reset(self):
        self.x = self.y = self.vx = self.vy = self.tx = self.ty = 0.0
        self.pulled = False
        self.override_angle = None
        self.override_stretch = 0.0

    def angle(self):
        if self.override_angle is not None:
            return self.override_angle
        return clamp(self.x * self.rot_scale, -42.0, 42.0)

    def scale(self):
        st = self.override_stretch if self.override_angle is not None else clamp(
            (abs(self.x) * 0.6 + self.y) * self.stretch_scale, -0.10, 0.14
        )
        return 1.0 - st * 0.45, 1.0 + st


class Spring1D:
    def __init__(self, k=260.0, c=10.5):
        self.k, self.c = k, c
        self.val = self.vel = 0.0

    def update(self, dt):
        self.vel += (-self.k * self.val - self.c * self.vel) * dt
        self.val = clamp(self.val + self.vel * dt, -0.18, 0.18)

    def kick(self, v):
        self.vel += v

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


# ------------------------------------------------------------------ tiny pixel UI icons
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


HEART_P = [".##.##.", "#######", "#++####", ".#####.", "..###..", "...#..."]
GEAR_P = ["...#..#...", "..######..", ".########.", "####..####", "###....###",
          "###....###", "####..####", ".########.", "..######..", "...#..#..."]
SHIRT_P = ["...##..##...", ".###+..+###.", "####+..+####", "####.++.####", "###.####.###",
           "...######...", "...######...", "...######...", "...######..."]
BULB_P = ["..####..", ".##++##.", "##+#####", "########", "########", ".######.",
          "..####..", "..====..", "..====..", "...==..."]
HAND_P = ["....#.....", "..#.#.#...", "..#.#.#.#.", "..#.#.#.#.", "..#######.", "#.#######.",
          "##.######.", ".########.", "..#######.", "...#####..", "...#####.."]
SMILE_P = [".######.", "##.##.##", "########", "#.####.#", "##....##", ".######."]
STAR_P = ["..#..", ".###.", "#####", ".###.", "..#.."]
EXCL_P = ["##", "##", "##", "##", "..", "##"]
ZZZ_P  = ["#####", "...#.", "..#..", ".#...", "#####"]


# ------------------------------------------------------------------ main game
class Game:
    def __init__(self):
        pygame.mixer.pre_init(SR, -16, 1, 256)
        pygame.init()
        try:
            pygame.mixer.init(SR, -16, 1, 256)
        except pygame.error:
            pass

        self.cfg_path = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), "PixelRoom", "settings.json")
        self.cfg = {"physics": 1.0, "volume": 0.6, "topmost": False, "scale": 0}
        try:
            with open(self.cfg_path, "r", encoding="utf-8") as f:
                self.cfg.update(json.load(f))
        except Exception:
            pass

        self.cfg["physics"] = clamp(float(self.cfg.get("physics", 1.0)), 0.0, 1.5)
        self.cfg["volume"] = clamp(float(self.cfg.get("volume", 0.6)), 0.0, 1.0)

        info = pygame.display.Info()
        self.max_scale = int(max(1, min((info.current_w * 0.94) // VW, (info.current_h * 0.90) // VH)))
        if not self.cfg["scale"] or self.cfg["scale"] > self.max_scale:
            self.cfg["scale"] = min(self.max_scale, 2)
        self.cfg["scale"] = int(clamp(self.cfg["scale"], 1, self.max_scale))

        pygame.display.set_caption("Pixel Room")
        pygame.display.set_icon(pattern_surface(HEART_P, {"#": PINK, "+": WHITE}, scale=4))
        self.apply_window()

        self.canvas = pygame.Surface((VW, VH))
        self.char_comp = pygame.Surface((COMP_W, COMP_H), pygame.SRCALPHA)
        self.head_comp = pygame.Surface((CW, CH), pygame.SRCALPHA)
        self.char_mask = pygame.mask.from_surface(self.char_comp)
        self.font = pygame.font.Font(None, 18)
        self.font_sm = pygame.font.Font(None, 15)

        self.sfx = Sfx()
        self.sfx.volume(self.cfg["volume"])

        self.assets = {}
        self.load_assets()

        self.ic = {
            "heart": pattern_surface(HEART_P, {"#": PINK, "+": WHITE}, scale=2),
            "gear": pattern_surface(GEAR_P, {"#": (204, 206, 222)}, scale=2),
            "shirt": pattern_surface(SHIRT_P, {"#": SHIRT, "+": TIE}, scale=2),
            "bulb": pattern_surface(BULB_P, {"#": (255, 228, 126), "+": WHITE, "=": (154, 154, 170)}, scale=2),
            "hand": pattern_surface(HAND_P, {"#": SKIN}, scale=2),
            "smile": pattern_surface(SMILE_P, {"#": (255, 214, 96)}, scale=2),
            "star": pattern_surface(STAR_P, {"#": (255, 246, 174)}, scale=2),
            "excl": pattern_surface(EXCL_P, {"#": (255, 96, 102)}, scale=2),
            "zzz":  pattern_surface(ZZZ_P,  {"#": (176, 198, 255)}, scale=2),
        }

        # Clean top-left bar: Settings, Wardrobe, Light (NO radio!)
        self.buttons = {
            "gear": (10, 10),
            "shirt": (44, 10),
            "bulb": (78, 10),
            "smile": (566, 320),
            "hand": (600, 320),
        }
        self.tips = {
            "gear": "Настройки",
            "shirt": "Сменить наряд (3)",
            "bulb": "Время суток / Свет",
            "smile": "Эмоции (8)",
            "hand": "Помахать",
        }

        # Room state
        self.light = 2          # 0=day, 1=sunset, 2=evening/night
        self.lamp_on = True     # table lamp toggle
        self.curtains_closed = False
        self.curtain_prog = 0.0  # 0.0 open -> 1.0 closed
        self.poster_idx = 0
        self.drawer_top = False
        self.drawer_bot = False
        self.laundry_hop = 0.0
        self.manga_flip = 0.0
        self.outfit = 0

        self.rx, self.ry = 320.0, float(FLOOR_Y)
        self.vx = self.vy = 0.0
        self.pvx = self.pvy = 0.0
        self.air = False

        # Bouncy underdamped springs
        self.sp = {
            "head":  Spring2D(170, 6.2, 0.12, 10,  7, rot_scale=-1.45, stretch_scale=0.005),
            "bangs": Spring2D(130, 4.8, 0.18,  8,  5, rot_scale=1.50,  stretch_scale=0.007),
            "hairL": Spring2D(68,  2.9, 0.34, 18, 12, rot_scale=1.85,  stretch_scale=0.009),
            "hairR": Spring2D(72,  3.1, 0.34, 18, 12, rot_scale=1.85,  stretch_scale=0.009),
            "hairB": Spring2D(54,  2.6, 0.38, 20, 12, rot_scale=1.40,  stretch_scale=0.008),
            "tie":   Spring2D(92,  3.4, 0.32, 18,  9, rot_scale=2.20,  stretch_scale=0.009),
            "folds": Spring2D(150, 5.2, 0.16,  5,  4, rot_scale=0.80,  stretch_scale=0.012),
            "skirt": Spring2D(120, 4.4, 0.22, 12,  7, rot_scale=1.35,  stretch_scale=0.010),
            "armL":  Spring2D(94,  3.8, 0.26, 16, 12, rot_scale=2.20,  stretch_scale=0.007),
            "armR":  Spring2D(98,  4.0, 0.26, 16, 12, rot_scale=2.20,  stretch_scale=0.007),
        }
        self.land_sq = Spring1D(k=260.0, c=10.0)

        self.pillow = {
            "x": PILLOW_HOME[0], "y": PILLOW_HOME[1],
            "vx": 0.0, "vy": 0.0, "ang": 0.0, "vang": 0.0,
            "on_bed": True, "hit_cd": 0.0
        }
        self.boba = {
            "x": BOBA_HOME[0], "y": BOBA_HOME[1],
            "returning": False, "drink_t": 0.0
        }

        self.t = 0.0
        self.breath_y = 0.0
        self.blink_t, self.blinking = random.uniform(2.2, 4.5), 0.0
        self.pup = [0.0, 0.0]
        self.emotion, self.emo_t = "normal", 0.0
        self.mood = 65.0
        self.speech, self.speech_t, self.speech_shown = "", 0.0, 0.0
        self.parts = []

        # LMB / RMB interaction state
        self.mode = None          # LMB: "press" | "drag" | "spring_grab" | "arm_grab" | "pillow" | "boba"
        self.rmb_petting = False  # RMB: headpat!
        self.press = (0.0, 0.0)
        self.press_zone = None
        self.grab = (0.0, 0.0)
        self.grab_part = None
        self.grab_anchor = (0.0, 0.0)
        self.shake_acc = 0.0
        self.arm_wave_acc = 0.0
        self.arm_wave_said = False
        self.pet_acc = 0.0
        self.pet_hearts = 0
        self.drag_said = False
        self.wave_t = 0.0
        self.ward_t = -1.0
        self.ward_swapped = False
        self.idle_t = 0.0
        self.sleepy_cd = 0.0
        self.settings = False
        self.slider = None
        self.hint_t = 11.0
        self.emo_idx = 0
        self.mouse = (320.0, 180.0)
        self.hover = None
        self.hover_curtains = False
        self.cursor = None

    def load_assets(self):
        adir = os.path.join(res_dir(), "assets")
        for fn in os.listdir(adir):
            if fn.endswith(".png"):
                self.assets[fn[:-4]] = pygame.image.load(os.path.join(adir, fn)).convert_alpha()

    def is_pitch_dark(self):
        return self.light == 2 and self.curtains_closed and not self.lamp_on

    # ------------------------------------------------ window / settings
    def apply_window(self):
        s = self.cfg["scale"]
        self.screen = pygame.display.set_mode((VW * s, VH * s))
        self.apply_topmost()

    def apply_topmost(self):
        if sys.platform != "win32":
            return
        try:
            import ctypes
            hwnd = pygame.display.get_wm_info().get("window")
            if hwnd:
                ctypes.windll.user32.SetWindowPos(hwnd, -1 if self.cfg["topmost"] else -2, 0, 0, 0, 0, 0x0013)
        except Exception:
            pass

    def save_cfg(self):
        try:
            os.makedirs(os.path.dirname(self.cfg_path), exist_ok=True)
            with open(self.cfg_path, "w", encoding="utf-8") as f:
                json.dump(self.cfg, f)
        except Exception:
            pass

    def reset_pose(self):
        self.rx, self.ry = 320.0, float(FLOOR_Y)
        self.vx = self.vy = self.pvx = self.pvy = 0.0
        self.air = False
        self.mode = None
        self.rmb_petting = False
        self.grab_part = None
        self.wave_t = 0.0
        self.shake_acc = 0.0
        for s in self.sp.values():
            s.reset()
        self.land_sq.reset()
        self.pillow.update({"x": PILLOW_HOME[0], "y": PILLOW_HOME[1], "vx": 0.0, "vy": 0.0,
                            "ang": 0.0, "vang": 0.0, "on_bed": True, "hit_cd": 0.0})
        self.boba.update({"x": BOBA_HOME[0], "y": BOBA_HOME[1], "returning": False, "drink_t": 0.0})
        self.emote("normal", 0.0)
        self.say("reset")
        self.sfx.play("sparkle")

    # ------------------------------------------------ reactions
    def say(self, key_or_text, raw=False):
        self.speech = key_or_text if raw else random.choice(LINES[key_or_text])
        self.speech_t = 2.4 + len(self.speech) * 0.042
        self.speech_shown = 0.0
        self.idle_t = 0.0

    def emote(self, e, dur=2.0):
        self.emotion, self.emo_t = e, dur

    def base_emotion(self):
        return "sleepy" if self.is_pitch_dark() else "normal"

    def kick_all(self, dx, strength=1.0):
        k = self.cfg["physics"] * strength
        self.sp["head"].kick(dx * 110, -45, k)
        self.sp["bangs"].kick(dx * 130, -35, k)
        self.sp["hairL"].kick(dx * 240, -100, k)
        self.sp["hairR"].kick(dx * 240, -100, k)
        self.sp["hairB"].kick(dx * 210, -80, k)
        self.sp["tie"].kick(dx * 280, -50, k)
        self.sp["folds"].kick(dx * 90, 40, k)
        self.sp["skirt"].kick(dx * 190, 55, k)
        self.sp["armL"].kick(dx * 185, -45, k)
        self.sp["armR"].kick(dx * 185, -45, k)

    def spawn(self, kind, x, y, n=1):
        for _ in range(n):
            self.parts.append({
                "k": kind,
                "x": x + random.uniform(-10, 10),
                "y": y + random.uniform(-4, 4),
                "vx": random.uniform(-22, 22),
                "vy": random.uniform(-70, -38),
                "life": random.uniform(0.95, 1.5),
            })

    def cycle_light(self):
        # Day -> Sunset -> Evening (Lamp ON) -> Night (Lamp OFF)
        if self.light == 0:
            self.light, self.lamp_on = 1, False
            self.say("light_sunset")
            self.emote("smug", 1.8)
        elif self.light == 1:
            self.light, self.lamp_on = 2, True
            self.say("light_eve")
            self.emote("normal", 1.5)
        elif self.light == 2 and self.lamp_on:
            self.lamp_on = False
            if self.is_pitch_dark():
                self.say("sleepy_dark")
                self.emote("sleepy", 3.5)
            else:
                self.say("light_dark")
        else:
            self.light, self.lamp_on = 0, False
            self.say("light_day")
            self.emote("pet", 1.4)
        self.sfx.play("lamp")

    def toggle_lamp(self):
        self.sfx.play("lamp")
        if self.light != 2:
            self.light, self.lamp_on = 2, True
            self.say("light_eve")
        else:
            self.lamp_on = not self.lamp_on
            if self.lamp_on:
                self.say("light_eve")
                self.emote("normal", 1.5)
            elif self.is_pitch_dark():
                self.say("sleepy_dark")
                self.emote("sleepy", 3.5)
            else:
                self.say("light_dark")

    def toggle_curtains(self):
        self.curtains_closed = not self.curtains_closed
        self.sfx.play("curtain")
        if self.is_pitch_dark():
            self.say("sleepy_dark")
            self.emote("sleepy", 3.5)
        elif self.curtains_closed:
            self.say("curtain_close")
        else:
            self.say("curtain_open")

    def start_wardrobe(self):
        if self.ward_t < 0:
            self.ward_t, self.ward_swapped = 0.0, False
            self.sfx.play("whoosh")

    # ------------------------------------------------ hitboxes
    def pillow_hit(self, mx, my):
        return abs(mx - self.pillow["x"]) <= 24 and abs(my - self.pillow["y"]) <= 14

    def boba_hit(self, mx, my):
        return self.boba["drink_t"] <= 0 and abs(mx - self.boba["x"]) <= 13 and abs(my - self.boba["y"]) <= 16

    def curtains_hit(self, mx, my):
        return 228 <= mx <= 412 and 50 <= my <= 184

    def head_rmb_hit(self, mx, my):
        hx = self.rx + self.sp["head"].x
        hy = self.ry - 166 + self.sp["head"].y
        return abs(mx - hx) <= 28 and abs(my - hy) <= 32

    def char_hit(self, mx, my):
        lx, ly = int(mx - self.rx + COX), int(my - self.ry + COY)
        if 0 <= lx < COMP_W and 0 <= ly < COMP_H and self.char_mask.get_at((lx, ly)):
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
            if self.outfit == 0 and abs(rel_x) <= 6 and -128 < rel_y < -92:
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

    def ui_hit(self, mx, my):
        for name, (x, y) in self.buttons.items():
            if x <= mx < x + 28 and y <= my < y + 28:
                return name
        return None

    def panel_rects(self):
        return {
            "panel":   (150, 56, 340, 248),
            "close":   (466, 64, 16, 16),
            "physics": (308, 106, 160, 14),
            "volume":  (308, 144, 160, 14),
            "topmost": (450, 178, 18, 18),
            "scale":   (388, 212, 80, 22),
            "reset":   (174, 256, 134, 24),
            "quit":    (388, 256, 80, 24),
        }

    @staticmethod
    def inr(p, r):
        return r[0] <= p[0] < r[0] + r[2] and r[1] <= p[1] < r[1] + r[3]

    # ------------------------------------------------ mouse input (LMB vs RMB)
    def on_rmb_down(self, mx, my):
        if self.settings:
            return
        if self.head_rmb_hit(mx, my):
            self.rmb_petting = True
            self.pet_acc = 0.0
            self.pet_hearts = 0
            self.emote("pet", 1.8)

    def on_rmb_up(self):
        if self.rmb_petting:
            if self.pet_hearts == 0:
                self.spawn("heart", self.rx, self.ry - 188)
                self.sfx.play("heart")
                self.mood = min(100, self.mood + 1.5)
                self.say("pet")
            self.rmb_petting = False
            self.sp["head"].pulled = False
            self.sp["head"].tx = self.sp["head"].ty = 0.0

    def on_lmb_down(self, mx, my):
        if self.settings:
            R = self.panel_rects()
            p = (mx, my)
            if self.inr(p, R["close"]) or not self.inr(p, R["panel"]):
                self.settings = False
                self.save_cfg()
                self.sfx.play("click")
            elif self.inr(p, (R["physics"][0] - 6, R["physics"][1] - 6, 172, 26)):
                self.slider = "physics"
                self.set_slider(mx)
            elif self.inr(p, (R["volume"][0] - 6, R["volume"][1] - 6, 172, 26)):
                self.slider = "volume"
                self.set_slider(mx)
            elif self.inr(p, (170, R["topmost"][1] - 4, 304, 26)):
                self.cfg["topmost"] = not self.cfg["topmost"]
                self.apply_topmost()
                self.sfx.play("click")
            elif self.inr(p, R["scale"]):
                sc = self.cfg["scale"] + 1
                self.cfg["scale"] = 1 if sc > self.max_scale else sc
                self.apply_window()
                self.sfx.play("click")
            elif self.inr(p, R["reset"]):
                self.reset_pose()
                self.settings = False
            elif self.inr(p, R["quit"]):
                self.save_cfg()
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            return

        b = self.ui_hit(mx, my)
        if b:
            self.sfx.play("click")
            if b == "gear":
                self.settings = True
            elif b == "shirt":
                self.start_wardrobe()
            elif b == "bulb":
                self.cycle_light()
            elif b == "smile":
                e = EMOS[self.emo_idx % len(EMOS)]
                self.emo_idx += 1
                self.emote(e, 3.0)
                self.say(e)
                self.kick_all(random.choice((-1, 1)), 0.5)
            elif b == "hand":
                self.wave_t = 1.8
                self.say("wave")
                self.emote("smug", 1.8)
                self.mood = min(100, self.mood + 3)
            return

        # Interactive movable props first
        if self.boba_hit(mx, my):
            self.mode = "boba"
            self.boba["returning"] = False
            self.sfx.play("click")
            return
        if self.pillow_hit(mx, my):
            self.mode = "pillow"
            self.pillow["on_bed"] = False
            self.pillow["vx"] = self.pillow["vy"] = self.pillow["vang"] = 0.0
            self.sfx.play("click")
            return

        # Character LMB interaction (drag / pull / click — petting is on RMB!)
        zone = self.char_hit(mx, my)
        if zone:
            self.mode = "press"
            self.press = (mx, my)
            self.press_zone = zone
            self.arm_wave_acc = 0.0
            self.arm_wave_said = False
            self.shake_acc = 0.0
            return

        # Interactive room interior objects!
        p = (mx, my)
        if self.curtains_hit(mx, my):
            self.toggle_curtains()
        elif self.inr(p, (176, 72, 48, 66)):  # Wall poster (3 anime/cosplay posters)
            self.poster_idx = (self.poster_idx + 1) % 3
            self.sfx.play("pop")
            self.emote("smug", 2.4)
            self.say(f"poster_{self.poster_idx}")
        elif self.inr(p, (580, 144, 54, 48)):  # Table lamp
            self.toggle_lamp()
        elif self.inr(p, (576, 202, 60, 34)):  # Top nightstand drawer (cosplay glasses)
            self.drawer_top = not self.drawer_top
            self.sfx.play("drawer")
            if self.drawer_top:
                self.emote("smug", 2.2)
                self.say("drawer_top")
        elif self.inr(p, (576, 238, 60, 34)):  # Bottom nightstand drawer (magazine)
            self.drawer_bot = not self.drawer_bot
            self.sfx.play("drawer")
            if self.drawer_bot:
                self.emote("blush", 2.0)
                self.say("drawer_bot")
        elif self.inr(p, (160, 216, 50, 48)):  # Laundry basket
            self.laundry_hop = 1.0
            self.sfx.play("pop")
            self.emote("blush", 1.8)
            self.say("laundry")
        elif self.inr(p, (214, 270, 34, 20)):  # Floor manga/book
            self.manga_flip = 1.0
            self.sfx.play("page")
            self.emote("starry", 2.0)
            self.say("manga")
        elif self.inr(p, (26, 38, 128, 226)):  # Wardrobe
            self.start_wardrobe()

    def set_slider(self, mx):
        R = self.panel_rects()[self.slider]
        f = clamp((mx - R[0]) / R[2], 0.0, 1.0)
        if self.slider == "physics":
            self.cfg["physics"] = round(f * 1.5, 2)
        else:
            self.cfg["volume"] = round(f, 2)
            self.sfx.volume(self.cfg["volume"])

    def on_motion(self, mx, my, dx, dy):
        if self.slider:
            self.set_slider(mx)
            return

        # RMB Headpat! Head gently tilts toward cursor on neck spring!
        if self.rmb_petting and self.head_rmb_hit(mx, my):
            hx = self.rx + self.sp["head"].x
            hy = self.ry - 166
            # Lean head warmly into the user's hand
            self.sp["head"].pulled = True
            self.sp["head"].tx = clamp((mx - self.rx) * 0.28, -7.0, 7.0)
            self.sp["head"].ty = clamp((my - hy) * 0.14, -3.0, 4.0)
            k = self.cfg["physics"]
            self.sp["bangs"].kick(dx * 14, 0, k)
            self.sp["hairL"].kick(dx * 16, 0, k)
            self.sp["hairR"].kick(dx * 16, 0, k)
            self.emote("pet", 1.8)
            self.pet_acc += abs(dx) + abs(dy) * 0.5
            if self.pet_acc > 22:
                self.pet_acc = 0.0
                self.pet_hearts += 1
                self.spawn("heart", hx, self.ry - 190)
                self.mood = min(100, self.mood + 2.8)
                if self.pet_hearts % 2 == 1:
                    self.sfx.play("heart")
                if self.pet_hearts == 2:
                    self.say("pet")
            self.idle_t = 0.0
            return

        if self.mode == "pillow":
            self.pillow["x"] = clamp(mx, 24, VW - 24)
            self.pillow["y"] = clamp(my, 20, FLOOR_Y - 8)
            self.pillow["vx"] = clamp(dx * 48.0, -900, 900)
            self.pillow["vy"] = clamp(dy * 48.0, -900, 900)
            self.pillow["vang"] = clamp(dx * 16.0, -320, 320)
            return

        if self.mode == "boba":
            self.boba["x"] = clamp(mx, 14, VW - 14)
            self.boba["y"] = clamp(my, 16, FLOOR_Y - 12)
            if math.hypot(self.boba["x"] - self.rx, self.boba["y"] - (self.ry - 150)) < 36:
                self.mode = None
                self.boba["drink_t"] = 2.3
                self.boba["returning"] = False
                self.emote("starry", 2.5)  # Starry-eyed delight when drinking bubble tea!
                self.mood = min(100, self.mood + 12)
                self.say("boba")
                self.sfx.play("sip")
                self.spawn("heart", self.rx, self.ry - 188, 3)
                self.spawn("star", self.rx, self.ry - 178, 3)
            return

        # Subtle spring ripple when sweeping cursor across Marin
        if self.mode is None and (abs(dx) + abs(dy)) > 5 and self.char_hit(mx, my):
            k = self.cfg["physics"] * 0.22
            self.sp["hairL"].kick(dx * 5.0, dy * 2.0, k)
            self.sp["hairR"].kick(dx * 5.0, dy * 2.0, k)
            self.sp["tie"].kick(dx * 6.0, dy * 1.5, k)
            self.sp["bangs"].kick(dx * 3.5, 0, k)

        if self.mode == "press" and math.hypot(mx - self.press[0], my - self.press[1]) > 5:
            if self.press_zone in ("armL", "armR"):
                self.mode = "arm_grab"
                self.grab_part = self.press_zone
                self.sp[self.grab_part].pulled = True
            elif self.press_zone in ("cheek", "hairL", "hairR", "tie", "skirt"):
                part = "head" if self.press_zone == "cheek" else self.press_zone
                self.mode = "spring_grab"
                self.grab_part = part
                self.grab_anchor = (mx, my)
                self.sp[part].pulled = True
            else:
                self.mode = "drag"
                self.grab = (self.rx - mx, self.ry - my)
                self.air = True
                self.drag_said = False

        elif self.mode == "drag":
            # Detect prolonged shaking -> Marin pouts!
            self.shake_acc += abs(dx) + abs(dy)
            if self.shake_acc > 340:
                self.shake_acc = 0.0
                self.emote("pout", 2.8)
                self.say("shake_pout")

        elif self.mode == "arm_grab" and self.grab_part:
            part = self.grab_part
            sp = self.sp[part]
            px_loc, py_loc = PIVOTS[part]
            sh_x = self.rx + (px_loc - OX)
            sh_y = self.ry + (py_loc - OY) + self.breath_y
            vx, vy = mx - sh_x, my - sh_y
            dist = max(1.0, math.hypot(vx, vy))
            ang = math.degrees(math.atan2(vx, vy))
            ang = clamp(ang, -85.0, 28.0) if part == "armL" else clamp(ang, -28.0, 85.0)
            sp.override_angle = ang
            sp.override_stretch = clamp((dist - 44.0) / 140.0, -0.04, 0.14)
            sp.x = clamp(vx * 0.25, -sp.cx, sp.cx)
            sp.y = clamp((vy - 40.0) * 0.18, -sp.cy, sp.cy)
            self.sp["head"].tx = clamp(vx * 0.12, -8.0, 8.0)
            self.sp["head"].pulled = True
            self.rx = clamp(self.rx + clamp(vx * 0.012, -1.2, 1.2), 40, VW - 40)

            self.arm_wave_acc += abs(dx)
            if self.arm_wave_acc > 68 and not self.arm_wave_said:
                self.arm_wave_said = True
                self.emote("pet", 2.0)
                self.say("arm_wave")
                self.mood = min(100, self.mood + 4)
                self.spawn("star", mx, my - 10, 3)
                self.sfx.play("heart")

        elif self.mode == "spring_grab" and self.grab_part:
            sp = self.sp[self.grab_part]
            px = clamp((mx - self.grab_anchor[0]) * 0.65, -sp.cx * 1.7, sp.cx * 1.7)
            py = clamp((my - self.grab_anchor[1]) * 0.55, -sp.cy * 1.6, sp.cy * 1.6)
            sp.tx, sp.ty = px, py
            self.shake_acc += abs(dx) + abs(dy)
            if self.shake_acc > 280:
                self.shake_acc = 0.0
                self.emote("pout", 2.6)
                self.say("shake_pout")
            elif self.grab_part in ("tie", "skirt"):
                self.emote("blush", 1.4)
            if self.grab_part == "head":
                self.rx = clamp(self.rx + px * 0.04, 40, VW - 40)
                self.sp["hairL"].kick(dx * 4, dy * 2, self.cfg["physics"] * 0.4)
                self.sp["hairR"].kick(dx * 4, dy * 2, self.cfg["physics"] * 0.4)
                self.sp["bangs"].tx = px * 0.5

    def on_lmb_up(self, mx, my):
        if self.slider:
            self.slider = None
            self.save_cfg()
            return
        if self.mode == "pillow":
            self.mode = None
            return
        if self.mode == "boba":
            self.boba["returning"] = True
            self.mode = None
            return

        if self.mode == "arm_grab" and self.grab_part:
            sp = self.sp[self.grab_part]
            ang = sp.override_angle or 0.0
            sp.override_angle = None
            sp.override_stretch = 0.0
            sp.pulled = False
            sp.x = clamp(ang / sp.rot_scale, -sp.cx, sp.cx)
            sp.vx = -sp.x * 11.0
            self.sp["head"].pulled = False
            self.sp["head"].tx = 0.0
            self.sfx.play("snap")
            self.grab_part = None

        elif self.mode == "spring_grab" and self.grab_part:
            part = self.grab_part
            sp = self.sp[part]
            sp.pulled = False
            sp.vx -= sp.x * 16.0
            sp.vy -= sp.y * 14.0
            sp.tx = sp.ty = 0.0
            self.sfx.play("snap")
            if part == "head":
                self.say("cheek")
                self.emote("blush", 2.0)
                self.kick_all(1 if sp.x < 0 else -1, 0.7)
            elif part in ("hairL", "hairR"):
                self.say("hair")
                self.emote("pout", 1.8)
                self.sp["hairB"].kick(-sp.x * 14, -40, self.cfg["physics"])
            elif part == "tie":
                self.say("tie")
                self.emote("blush", 2.2)
            elif part == "skirt":
                self.say("skirt")
                self.emote("blush", 2.4)
            self.grab_part = None

        elif self.mode == "drag":
            self.vx = clamp(self.vx, -1250, 1250)
            self.vy = clamp(self.vy, -1250, 1250)
            self.emote("surprised", 1.1)

        elif self.mode == "press":
            d = 1 if self.rx > mx else -1
            k = self.cfg["physics"]
            z = self.press_zone
            if z in ("armL", "armR"):
                self.sp[z].kick((-1 if z == "armL" else 1) * 260, -140, k)
                self.sp["hairL"].kick(d * 100, -40, k)
                self.sp["hairR"].kick(d * 100, -40, k)
                self.emote("starry", 2.0)
                self.mood = min(100, self.mood + 5)
                self.say("highfive")
                self.spawn("star", mx, my - 8, 5)
                self.sfx.play("sparkle")
            elif z == "cheek":
                self.sp["head"].kick(d * 220, -55, k)
                self.kick_all(d, 0.7)
                self.emote("blush", 2.0)
                self.say("cheek")
                self.sfx.play("pop")
            elif z in ("hairL", "hairR"):
                self.sp[z].kick((-1 if z == "hairL" else 1) * 280, -110, k)
                self.sp["hairB"].kick(d * 180, -60, k)
                self.sp["head"].kick(d * 110, -30, k)
                self.emote("pout", 1.8)
                self.say("hair")
                self.sfx.play("pop")
            elif z == "tie":
                self.sp["tie"].kick(d * 340, -80, k)
                self.sp["folds"].kick(d * 90, 40, k)
                self.emote("blush", 2.0)
                self.say("tie")
                self.sfx.play("pop")
            elif z == "skirt":
                self.sp["skirt"].kick(d * 260, -70, k)
                self.emote("blush", 2.2)
                self.say("skirt")
                self.sfx.play("pop")
            else:
                self.kick_all(d, 1.1)
                self.land_sq.kick(-1.0)
                if not self.air:
                    self.vy, self.air = -155, True
                self.emote("blush", 1.8)
                self.say("body")
                self.spawn("excl", self.rx + 22, self.ry - 190)
                self.sfx.play("pop")

        self.mode = None

    # ------------------------------------------------ simulation
    def update(self, dt):
        self.t += dt
        mx, my = self.mouse
        ox, oy = self.rx, self.ry

        # Smooth curtain slide animation
        target_c = 1.0 if self.curtains_closed else 0.0
        self.curtain_prog += (target_c - self.curtain_prog) * min(1.0, dt * 8.0)

        # Interior prop micro-animations
        self.laundry_hop = max(0.0, self.laundry_hop - dt * 2.8)
        self.manga_flip = max(0.0, self.manga_flip - dt * 3.0)

        if self.mode == "drag":
            nx = clamp(mx + self.grab[0], 40, VW - 40)
            ny = clamp(my + self.grab[1], 200, FLOOR_Y)
            self.rx, self.ry = nx, ny
            self.vx += ((nx - ox) / dt - self.vx) * 0.55
            self.vy += ((ny - oy) / dt - self.vy) * 0.55
            if self.emotion != "pout":
                self.emote("surprised", 0.5)
            if not self.drag_said and self.ry < FLOOR_Y - 22:
                self.drag_said = True
                self.say("grab")
                self.sfx.play("boing")
        elif self.air:
            self.vy += 1550 * dt
            self.rx += self.vx * dt
            self.ry += self.vy * dt
            if self.rx < 40 or self.rx > VW - 40:
                self.rx = clamp(self.rx, 40, VW - 40)
                self.vx *= -0.55
            if self.ry < 200:
                self.ry, self.vy = 200, abs(self.vy) * 0.35
            if self.ry >= FLOOR_Y:
                self.ry = FLOOR_Y
                impact = self.vy
                if impact > 160:
                    self.vy = -impact * 0.30
                    self.sfx.play("land")
                    sq_imp = min(2.4, impact / 320.0) * max(0.5, self.cfg["physics"])
                    self.land_sq.kick(-sq_imp)
                    self.kick_all(1 if self.vx >= 0 else -1, min(1.5, impact / 500.0))
                    if impact > 520:
                        self.emote("blush", 2.4)
                        self.say("land")
                else:
                    self.vy, self.air = 0.0, False
                self.vx *= 0.62
        else:
            self.vx *= math.exp(-8.5 * dt)
            self.rx = clamp(self.rx + self.vx * dt, 40, VW - 40)

        # Throwable Pillow physics & collision
        pl = self.pillow
        pl["hit_cd"] = max(0.0, pl["hit_cd"] - dt)
        if self.mode != "pillow" and not pl["on_bed"]:
            pl["vy"] += 1150 * dt
            pl["x"] += pl["vx"] * dt
            pl["y"] += pl["vy"] * dt
            pl["ang"] += pl["vang"] * dt
            if pl["x"] < 24 or pl["x"] > VW - 24:
                pl["x"] = clamp(pl["x"], 24, VW - 24)
                pl["vx"] *= -0.62
                pl["vang"] *= -0.7
            if pl["y"] < 18:
                pl["y"], pl["vy"] = 18, abs(pl["vy"]) * 0.4
            if pl["y"] >= FLOOR_Y - 6:
                pl["y"] = FLOOR_Y - 6
                if abs(pl["vy"]) > 110:
                    pl["vy"] *= -0.36
                    pl["vx"] *= 0.72
                    pl["vang"] *= 0.65
                else:
                    pl["vy"] = 0.0
                    pl["vx"] *= math.exp(-6.0 * dt)
                    pl["vang"] *= math.exp(-8.0 * dt)
                    pl["ang"] += (0.0 - pl["ang"]) * min(1.0, dt * 6)
            spd = math.hypot(pl["vx"], pl["vy"])
            if pl["hit_cd"] <= 0 and spd > 95:
                if abs(pl["x"] - self.rx) < 34 and (self.ry - 188) < pl["y"] < (self.ry - 40):
                    pl["hit_cd"] = 0.45
                    dx_dir = 1 if pl["vx"] >= 0 else -1
                    pl["vx"] = -pl["vx"] * 0.52 - dx_dir * 70
                    pl["vy"] = min(-160.0, -abs(pl["vy"]) * 0.45)
                    pl["vang"] = -dx_dir * 260
                    self.vx += dx_dir * 135
                    self.kick_all(dx_dir, 1.45)
                    self.land_sq.kick(-1.35)
                    self.emote("surprised", 2.0)
                    self.say("pillow")
                    self.spawn("excl", self.rx + 22, self.ry - 190)
                    self.sfx.play("pillow")

        # Bubble tea drinking & smooth return
        bb = self.boba
        if bb["drink_t"] > 0:
            bb["drink_t"] -= dt
            bb["x"] += (self.rx + 10 - bb["x"]) * min(1.0, dt * 12)
            bb["y"] += (self.ry - 144 - bb["y"]) * min(1.0, dt * 12)
            if int(bb["drink_t"] * 4) != int((bb["drink_t"] + dt) * 4):
                self.spawn("heart", self.rx, self.ry - 186, 1)
            if bb["drink_t"] <= 0:
                bb["returning"] = True
        elif bb["returning"]:
            bb["x"] += (BOBA_HOME[0] - bb["x"]) * min(1.0, dt * 9)
            bb["y"] += (BOBA_HOME[1] - bb["y"]) * min(1.0, dt * 9)
            if math.hypot(bb["x"] - BOBA_HOME[0], bb["y"] - BOBA_HOME[1]) < 1.5:
                bb["x"], bb["y"] = BOBA_HOME
                bb["returning"] = False

        # Sleepy head-nodding in pitch-dark room (night + curtains closed + lamp off!)
        on_ground = not self.air and self.mode is None and not self.rmb_petting
        if self.is_pitch_dark() and on_ground:
            # Gentle drowsy nod ("клевать носом")
            nod = math.sin(self.t * 1.4)
            self.sp["head"].y += (3.5 + nod * 2.5 - self.sp["head"].y) * min(1.0, dt * 3)
            self.sleepy_cd -= dt
            if self.sleepy_cd <= 0:
                self.sleepy_cd = random.uniform(4.5, 7.5)
                self.spawn("zzz", self.rx + 18, self.ry - 192, 1)
                if random.random() < 0.45:
                    self.say("sleepy_dark")

        # Idle breathing
        target_b = math.sin(self.t * (1.7 if self.is_pitch_dark() else 2.4)) * 1.5 if on_ground else 0.0
        self.breath_y += (target_b - self.breath_y) * min(1.0, dt * 10)

        # Root acceleration drives springs
        cvx = (self.rx - ox) / dt
        cvy = (self.ry - oy) / dt
        ax = clamp((cvx - self.pvx) / dt, -55000, 55000)
        ay = clamp((cvy - self.pvy) / dt, -55000, 55000)
        self.pvx, self.pvy = cvx, cvy

        inten = self.cfg["physics"]
        for _ in range(3):
            sdt = dt / 3.0
            for s in self.sp.values():
                s.update(sdt, ax, ay, inten)
            self.land_sq.update(sdt)

        # Blinking
        self.blink_t -= dt
        if self.blink_t <= 0:
            self.blinking, self.blink_t = 0.14, random.uniform(2.2, 5.0)
        self.blinking = max(0.0, self.blinking - dt)

        # Smooth mouse-tracking pupils
        dxm = mx - self.rx
        dym = my - (self.ry - 161)
        tx = clamp(dxm / 65.0, -2.0, 2.0)
        ty = clamp(dym / 85.0, -1.2, 1.2)
        self.pup[0] += (tx - self.pup[0]) * min(1.0, dt * 11)
        self.pup[1] += (ty - self.pup[1]) * min(1.0, dt * 11)

        # Emotion returns cleanly to base_emotion (normal smirk or sleepy in pitch dark)
        self.emo_t -= dt
        if self.emo_t <= 0:
            self.emotion = self.base_emotion()

        if self.speech_t > 0:
            self.speech_t -= dt
            prev = int(self.speech_shown)
            self.speech_shown = min(len(self.speech), self.speech_shown + dt * 28)
            if int(self.speech_shown) != prev and prev % 2 == 0 and prev < len(self.speech):
                self.sfx.blip()

        self.mood += (55.0 - self.mood) * 0.005 * dt
        self.idle_t += dt
        if self.idle_t > 24:
            self.say("sleepy_dark" if self.is_pitch_dark() else "idle")

        self.wave_t = max(0.0, self.wave_t - dt)
        self.hint_t -= dt

        # Wardrobe cycles through 3 outfits with door-open animation!
        if self.ward_t >= 0:
            self.ward_t += dt
            if self.ward_t > 0.42 and not self.ward_swapped:
                self.ward_swapped = True
                self.outfit = (self.outfit + 1) % 3
                self.spawn("star", self.rx, self.ry - 98, 12)
                self.sfx.play("sparkle")
                self.say(f"outfit_{self.outfit}")
                self.emote("smug", 2.2)
                self.kick_all(1, 0.85)
                self.land_sq.kick(-0.9)
            if self.ward_t > 0.88:
                self.ward_t = -1.0

        # Particles
        for p in self.parts:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vx"] *= 0.97
            if p["k"] == "star":
                p["vy"] += 110 * dt
            p["life"] -= dt
        self.parts = [p for p in self.parts if p["life"] > 0]

        # Hover & cursor feedback
        p = (mx, my)
        self.hover_curtains = (not self.settings and self.mode is None and not self.char_hit(mx, my)
                               and self.curtains_hit(mx, my))
        hv = None
        if self.mode in ("drag", "spring_grab", "arm_grab", "pillow", "boba"):
            hv = pygame.SYSTEM_CURSOR_SIZEALL
        elif (self.settings or self.ui_hit(mx, my) or self.pillow_hit(mx, my) or self.boba_hit(mx, my)
              or self.hover_curtains or self.char_hit(mx, my)
              or self.inr(p, (176, 72, 48, 66)) or self.inr(p, (580, 144, 54, 48))
              or self.inr(p, (576, 202, 60, 70)) or self.inr(p, (160, 216, 50, 48))
              or self.inr(p, (214, 270, 34, 20)) or self.inr(p, (26, 38, 128, 226))):
            hv = pygame.SYSTEM_CURSOR_HAND
        hv = hv or pygame.SYSTEM_CURSOR_ARROW
        if hv != self.cursor:
            self.cursor = hv
            try:
                pygame.mouse.set_cursor(hv)
            except Exception:
                pass
        self.hover = self.ui_hit(mx, my) if not self.settings else None

    # ------------------------------------------------ character compositing
    def compose_char(self):
        comp = self.char_comp
        comp.fill((0, 0, 0, 0))
        A = self.assets
        o = self.outfit
        by = self.breath_y

        def dp(name, extra_x=0.0, extra_y=0.0):
            px, py = PIVOTS[name]
            return (px + PAD + extra_x, py + PAD + extra_y)

        def draw_spring(surf, sp_name, extra_x=0.0, extra_y=0.0, angle_add=0.0):
            sp = self.sp[sp_name]
            sx, sy = sp.scale()
            ox_s = 0.0 if sp.override_angle is not None else sp.x * 0.55
            oy_s = 0.0 if sp.override_angle is not None else sp.y * 0.55
            blit_pivoted(
                comp, surf, PIVOTS[sp_name],
                dp(sp_name, ox_s + extra_x, oy_s + extra_y),
                angle=sp.angle() + angle_add, sx=sx, sy=sy
            )

        hd = self.sp["head"]
        h_ang = hd.angle()
        hx, hy = hd.x * 0.5, hd.y * 0.5 + by

        draw_spring(A["hair_back"], "hairB", extra_x=hx * 0.6, extra_y=hy * 0.6, angle_add=h_ang * 0.45)

        legs_key = f"legs_{o}_air" if (self.air or self.mode == "drag") else f"legs_{o}_stand"
        comp.blit(A[legs_key], (PAD, PAD))

        draw_spring(A[f"skirt_{o}"], "skirt")
        comp.blit(A[f"torso_{o}"], (PAD, int(round(PAD + by))))

        if o in (0, 1):
            draw_spring(A[f"folds_{o}"], "folds", extra_y=by)

        draw_spring(A[f"arm_l_{o}"], "armL", extra_y=by)
        if self.wave_t > 0 and self.grab_part != "armR":
            wob = math.sin(self.t * 15) * 14.0
            blit_pivoted(comp, A[f"arm_r_{o}_wave"], PIVOTS["armR"], dp("armR", 0, by), angle=wob)
        else:
            draw_spring(A[f"arm_r_{o}"], "armR", extra_y=by)

        if o == 0:
            draw_spring(A["tie"], "tie", extra_y=by)

        # Layer 4: Head + 8 Emotions + Tracking Irises
        hc = self.head_comp
        hc.fill((0, 0, 0, 0))
        hc.blit(A["head_base"], (0, 0))
        emo = self.emotion
        eye_track_emos = ("normal", "blush", "smug", "surprised", "pout")
        if self.blinking > 0 and emo in eye_track_emos:
            hc.blit(A["face_blink"], (0, 0))
        else:
            hc.blit(A[f"face_{emo}"], (0, 0))
            if emo in eye_track_emos:
                iris = A["iris"]
                px = int(round(self.pup[0]))
                py = int(round(self.pup[1]))
                if emo == "blush":
                    px = -1 if self.pup[0] >= 0 else 1  # shy glance
                hc.blit(iris, (OX - 8 - 4 + px, OY - 161 - 4 + py))
                hc.blit(iris, (OX + 8 - 4 + px, OY - 161 - 4 + py))
        hsx, hsy = hd.scale()
        blit_pivoted(comp, hc, PIVOTS["head"], dp("head", hx, hy), angle=h_ang, sx=hsx, sy=hsy)

        draw_spring(A["hair_front_l"], "hairL", extra_x=hx, extra_y=hy, angle_add=h_ang * 0.65)
        draw_spring(A["hair_front_r"], "hairR", extra_x=hx, extra_y=hy, angle_add=h_ang * 0.65)
        draw_spring(A["hair_bangs"], "bangs", extra_x=hx, extra_y=hy, angle_add=h_ang * 0.85)

        self.char_mask = pygame.mask.from_surface(comp)

    # ------------------------------------------------ rendering
    def tint_prop(self, surf, x, y):
        lit = surf.copy()
        tint = TINTS[self.light]
        if self.light in (0, 1) and self.curtain_prog > 0.1:
            dim = 1.0 - self.curtain_prog * 0.28
            tint = tuple(int(v * dim) for v in tint)
        elif self.is_pitch_dark():
            tint = (92, 84, 128)
        lit.fill(tint, special_flags=pygame.BLEND_RGB_MULT)
        if self.light == 2 and self.lamp_on:
            d = math.hypot(x - LAMP_POS[0], y - LAMP_POS[1])
            f = max(0.0, 1.0 - d / 340.0) ** 1.5
            lit.fill((int(115 * f), int(80 * f), int(36 * f)), special_flags=pygame.BLEND_RGB_ADD)
        return lit

    def text(self, txt, x, y, col=WHITE, center=False, shadow=True, small=False):
        f = self.font_sm if small else self.font
        img = f.render(txt, False, col)
        px, py = int(x), int(y)
        if center:
            px -= img.get_width() // 2
        if shadow:
            self.canvas.blit(f.render(txt, False, (28, 18, 28)), (px + 1, py + 1))
        self.canvas.blit(img, (px, py))

    def frame(self, r, fill=(36, 30, 48)):
        x, y, w, h = r
        c = self.canvas
        c.fill(OUT, (x - 2, y, w + 4, h))
        c.fill(OUT, (x, y - 2, w, h + 4))
        c.fill(OUT, (x - 1, y - 1, w + 2, h + 2))
        c.fill(fill, (x, y, w, h))
        c.fill(tuple(min(255, v + 28) for v in fill), (x, y, w, 2))

    def draw(self):
        c = self.canvas
        ward_open = 0.08 < self.ward_t < 0.78
        bg_key = f"room_{LIGHT_KEYS[self.light]}" + ("_open" if ward_open else "")
        c.blit(self.assets[bg_key], (0, 0))

        # Dynamic wall poster (3 styles, tinted to room light)
        poster_surf = self.tint_prop(self.assets[f"poster_{self.poster_idx}"], 200, 105)
        c.blit(poster_surf, (176, 72))

        # Dynamic sliding curtains! (36px open -> 86px closed, meeting cleanly at x=320)
        cw = int(round(36 + self.curtain_prog * 51))
        cp = self.tint_prop(pygame.transform.scale(self.assets["curtain_panel"], (cw, 132)), 320, 116)
        c.blit(cp, (234, 52))
        c.blit(cp, (406 - cw, 52))
        if self.hover_curtains:
            pygame.draw.rect(c, (255, 240, 190), (233, 51, cw + 2, 134), 1)
            pygame.draw.rect(c, (255, 240, 190), (405 - cw, 51, cw + 2, 134), 1)

        # Open nightstand drawers (with cosplay glasses / magazine inside!)
        if self.drawer_top:
            c.blit(self.tint_prop(self.assets["drawer_top_open"], 604, 218), (576, 200))
        if self.drawer_bot:
            c.blit(self.tint_prop(self.assets["drawer_bot_open"], 604, 254), (576, 236))

        # Laundry basket bounce micro-animation
        if self.laundry_hop > 0:
            dy = int(round(math.sin(self.laundry_hop * math.pi) * 10))
            pygame.draw.ellipse(c, (92, 116, 152), (166, 218 - dy, 20, 12))
            pygame.draw.ellipse(c, (238, 162, 184), (180, 216 - dy, 22, 12))

        # Floor manga page-flip micro-animation
        if self.manga_flip > 0:
            fy = int(round(math.sin(self.manga_flip * math.pi) * 8))
            pygame.draw.polygon(c, WHITE, [(228, 282), (242, 276 - fy), (228, 272 - fy)])

        # Dynamic room lighting overlays (sunlight shaft / closed-curtain dim / evening lamp glow)
        if self.light in (0, 1):
            if self.curtain_prog < 0.85:
                sun = pygame.Surface((VW, VH), pygame.SRCALPHA)
                alpha = int((38 if self.light == 0 else 48) * (1.0 - self.curtain_prog))
                col = (255, 248, 220, alpha) if self.light == 0 else (255, 190, 110, alpha)
                pygame.draw.polygon(sun, col, [(266, 240), (374, 240), (434, 360), (296, 360)])
                c.blit(sun, (0, 0))
            if self.curtain_prog > 0.05:
                dim = pygame.Surface((VW, VH), pygame.SRCALPHA)
                dim.fill((26, 20, 44, int(self.curtain_prog * 76)))
                c.blit(dim, (0, 0))
        else:
            if self.lamp_on:
                c.blit(self.assets["lamp_glow"], (0, 0))
                # Bright lit lampshade on top of glow
                pygame.draw.polygon(c, (255, 246, 196), [(590, 146), (622, 146), (630, 172), (582, 172)])
                pygame.draw.polygon(c, OUT, [(590, 146), (622, 146), (630, 172), (582, 172)], 1)
                pygame.draw.line(c, (255, 255, 236), (586, 170), (626, 170), 2)
            elif self.curtain_prog > 0.05:
                # Pitch-dark cozy night when curtains closed & lamp OFF!
                dark = pygame.Surface((VW, VH), pygame.SRCALPHA)
                dark.fill((10, 8, 24, int(self.curtain_prog * 112)))
                c.blit(dark, (0, 0))

        # Ground shadow under Marin
        h_air = FLOOR_Y - self.ry
        sq = self.land_sq.val
        sw = int(54 * (1.0 - min(0.6, h_air / 210.0)) * (1.0 - sq * 0.7))
        sh = pygame.Surface((max(8, sw), 10), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (30, 16, 22, 95), (0, 0, max(8, sw), 10))
        c.blit(sh, (int(self.rx) - sw // 2, FLOOR_Y - 5))

        # Character
        self.compose_char()
        lit = self.tint_prop(self.char_comp, self.rx, self.ry - 100)
        if self.light == 1 and not self.curtains_closed:
            lit.fill((18, 8, 0), special_flags=pygame.BLEND_RGB_ADD)
        sy_body = 1.0 + sq
        sx_body = 1.0 - sq * 0.85
        blit_pivoted(c, lit, (COX, COY), (self.rx, self.ry), angle=0.0, sx=sx_body, sy=sy_body)

        # Throwable Pillow
        pl = self.pillow
        if not pl["on_bed"]:
            psh = pygame.Surface((40, 8), pygame.SRCALPHA)
            pygame.draw.ellipse(psh, (30, 16, 22, 75), (0, 0, 40, 8))
            c.blit(psh, (int(pl["x"]) - 20, FLOOR_Y - 3))
        blit_pivoted(c, self.tint_prop(self.assets["pillow"], pl["x"], pl["y"]), (24, 13), (pl["x"], pl["y"]), angle=pl["ang"])

        # Bubble Tea
        bb = self.boba
        b_ang = -14.0 if bb["drink_t"] > 0 else 0.0
        blit_pivoted(c, self.tint_prop(self.assets["boba"], bb["x"], bb["y"]), (11, 15), (bb["x"], bb["y"]), angle=b_ang)

        # Particles
        for p in self.parts:
            img = self.ic[p["k"]]
            if p["k"] == "heart" and p["life"] < 0.3 and int(p["life"] * 20) % 2:
                continue
            c.blit(img, (int(p["x"]) - img.get_width() // 2, int(p["y"])))

        # Pixel speech bubble
        if self.speech_t > 0 and self.speech and not self.settings:
            shown = self.speech[:int(self.speech_shown)]
            tw, th = self.font.size(self.speech)
            bw, bh = tw + 18, th + 12
            bx = int(clamp(self.rx - bw // 2, 8, VW - bw - 8))
            by = int(max(8, self.ry - 202 - bh))
            self.frame((bx, by, bw, bh), WHITE)
            tx = int(clamp(self.rx, bx + 8, bx + bw - 10))
            pygame.draw.polygon(c, WHITE, [(tx - 4, by + bh), (tx + 4, by + bh), (tx, by + bh + 6)])
            pygame.draw.line(c, OUT, (tx - 5, by + bh), (tx, by + bh + 6), 2)
            pygame.draw.line(c, OUT, (tx + 5, by + bh), (tx, by + bh + 6), 2)
            self.text(shown, bx + 9, by + 6, (56, 38, 58), shadow=False)

        # Corner UI buttons (Settings, Wardrobe, Light, Emotion, Wave)
        for name, (x, y) in self.buttons.items():
            hov = self.hover == name
            self.frame((x, y, 28, 28), (64, 52, 86) if hov else (36, 30, 48))
            img = self.ic[name]
            c.blit(img, (x + 14 - img.get_width() // 2, y + 14 - img.get_height() // 2))

        if self.hover:
            x, y = self.buttons[self.hover]
            tip = self.tips[self.hover]
            tw, th = self.font_sm.size(tip)
            tx = int(clamp(x + 14 - tw // 2, 6, VW - tw - 14))
            ty = y + 34 if y < 180 else y - 22
            self.frame((tx, ty, tw + 10, th + 6), (36, 30, 48))
            self.text(tip, tx + 5, ty + 3, small=True)

        # Mood bar
        self.frame((472, 10, 156, 22))
        c.blit(self.ic["heart"], (476, 13))
        c.fill((22, 16, 28), (498, 16, 122, 10))
        fw = int(122 * self.mood / 100.0)
        c.fill((236, 98, 148), (498, 16, fw, 10))
        c.fill((255, 174, 204), (498, 16, fw, 2))
        for i in range(498, 620, 15):
            c.fill((22, 16, 28), (i + 13, 16, 2, 10))
        self.text("Настроение", 550, 35, (255, 224, 238), center=True, small=True)

        if self.hint_t > 0 and not self.settings:
            self.text("ЛКМ — тяни/кидай и кликай интерьер (шторы, постер, ящики) • ПКМ по голове — погладить",
                      320, 342, (255, 242, 224), center=True, small=True)

        if self.settings:
            self.draw_settings()

        pygame.transform.scale(c, self.screen.get_size(), self.screen)
        pygame.display.flip()

    def draw_settings(self):
        c = self.canvas
        dim = pygame.Surface((VW, VH), pygame.SRCALPHA)
        dim.fill((12, 8, 22, 135))
        c.blit(dim, (0, 0))
        R = self.panel_rects()
        self.frame(R["panel"], (42, 34, 58))
        self.frame(R["close"], (156, 62, 82))
        x, y, w, h = R["close"]
        pygame.draw.line(c, WHITE, (x + 4, y + 4), (x + w - 5, y + h - 5), 2)
        pygame.draw.line(c, WHITE, (x + w - 5, y + 4), (x + 4, y + h - 5), 2)

        self.text("Настройки", 320, 68, (255, 224, 132), center=True)

        for key, label, vmax in (("physics", "Физика", 1.5), ("volume", "Громкость", 1.0)):
            sx, sy, sw, sh = R[key]
            v = self.cfg[key]
            frac = clamp(v / vmax, 0.0, 1.0)
            self.text(label, 174, sy - 2)
            self.text(f"{int(round(v * 100))}%", 262, sy - 2, (210, 206, 228))
            c.fill(OUT, (sx - 2, sy + 4, sw + 4, 6))
            c.fill((24, 18, 32), (sx, sy + 5, sw, 4))
            c.fill((236, 98, 148), (sx, sy + 5, int(sw * frac), 4))
            kx = sx + int(sw * frac) - 4
            self.frame((kx, sy, 8, 14), (252, 224, 234))

        tx, ty, tw, th = R["topmost"]
        self.text("Поверх всех окон (Always on Top)", 174, ty + 1)
        self.frame((tx, ty, tw, th), (24, 18, 32))
        if self.cfg["topmost"]:
            c.fill((120, 232, 146), (tx + 3, ty + 3, tw - 6, th - 6))

        self.text("Масштаб окна", 174, R["scale"][1] + 4)
        self.frame(R["scale"], (72, 62, 104))
        self.text(f"x{self.cfg['scale']} ({VH * self.cfg['scale']}p)", R["scale"][0] + 40, R["scale"][1] + 4,
                  center=True, small=True)

        self.frame(R["reset"], (68, 86, 118))
        self.text("Сбросить позу", R["reset"][0] + 67, R["reset"][1] + 5, center=True)
        self.frame(R["quit"], (122, 52, 68))
        self.text("Выход", R["quit"][0] + 40, R["quit"][1] + 5, center=True)

    # ------------------------------------------------ main loop
    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            dt = min(clock.tick(60) / 1000.0, 1 / 30)
            sc = self.cfg["scale"]
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    if self.settings:
                        self.settings = False
                        self.save_cfg()
                elif ev.type == pygame.MOUSEBUTTONDOWN:
                    if ev.button == 1:
                        self.on_lmb_down(ev.pos[0] / sc, ev.pos[1] / sc)
                    elif ev.button == 3:
                        self.on_rmb_down(ev.pos[0] / sc, ev.pos[1] / sc)
                elif ev.type == pygame.MOUSEMOTION:
                    self.mouse = (ev.pos[0] / sc, ev.pos[1] / sc)
                    self.on_motion(*self.mouse, ev.rel[0] / sc, ev.rel[1] / sc)
                elif ev.type == pygame.MOUSEBUTTONUP:
                    if ev.button == 1:
                        self.on_lmb_up(ev.pos[0] / sc, ev.pos[1] / sc)
                    elif ev.button == 3:
                        self.on_rmb_up()
            self.update(dt)
            self.draw()
        self.save_cfg()
        pygame.quit()


def main():
    Game().run()


if __name__ == "__main__":
    main()
