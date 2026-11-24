# -*- coding: utf-8 -*-
"""Pixel Room — Marin Kitagawa (v0.2-beta)
Clean modular architecture: SaveManager, AudioEngine, ParticleSystem,
CharacterPhysics, RoomObjects, and UIManager.
"""
import os
import sys
import math
import random

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

from constants import (
    VERSION, VW, VH, FLOOR_Y, SR, OX, OY, COX, COY,
    EMOS, LINES, PIVOTS, OUTFIT_COUNT, ACC_COUNT,
    PINK, WHITE, res_dir, clamp,
)
from save_manager import SaveManager
from audio_engine import AudioEngine
from particles import ParticleSystem
from physics import CharacterPhysics, blit_pivoted, MAX_BODY_VEL
from room_objects import RoomObjects, MAX_PILLOW_VEL
from ui_manager import UIManager, pattern_surface, HEART_P


class Game:
    def __init__(self):
        pygame.mixer.pre_init(SR, -16, 1, 256)
        pygame.init()
        try:
            pygame.mixer.init(SR, -16, 1, 256)
        except pygame.error:
            pass

        self.saves = SaveManager()
        cfg = self.saves.data

        info = pygame.display.Info()
        self.max_scale = int(max(1, min((info.current_w * 0.94) // VW, (info.current_h * 0.90) // VH)))
        if not cfg["scale"] or cfg["scale"] > self.max_scale:
            cfg["scale"] = min(self.max_scale, 2)
        cfg["scale"] = int(clamp(cfg["scale"], 1, self.max_scale))

        pygame.display.set_caption(f"Pixel Room — Marin Kitagawa ({VERSION})")
        pygame.display.set_icon(pattern_surface(HEART_P, {"#": PINK, "+": WHITE}, scale=4))
        self.apply_window()

        self.canvas = pygame.Surface((VW, VH))
        self.assets = self._load_assets()

        # Modular subsystems
        self.audio = AudioEngine(cfg["volume"])
        self.ui = UIManager()
        self.particles = ParticleSystem(self.ui.icons)
        self.phys = CharacterPhysics()
        self.room = RoomObjects(cfg)

        # Character state synced with SaveManager
        self.outfit = cfg["outfit"]
        self.accessory = cfg["accessory"]
        self.mood = cfg["mood"]
        self.rps_wins = cfg["rps_wins"]

        self.emotion, self.emo_t = self.base_emotion(), 0.0
        self.speech, self.speech_t, self.speech_shown = "", 0.0, 0.0

        # Input & interaction state
        self.mode = None          # LMB: press|drag|spring_grab|arm_grab|pillow|boba|glasses_item|camera_item
        self.rmb_petting = False  # RMB: headpat
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
        self.idle_t = 0.0
        self.sleepy_cd = 2.0
        self.hint_t = 10.0
        self.emo_idx = 0
        self.mouse = (320.0, 180.0)
        self.hover_curtains = False
        self.cursor = None

    @staticmethod
    def _load_assets():
        adir = os.path.join(res_dir(), "assets")
        out = {}
        for fn in os.listdir(adir):
            if fn.endswith(".png"):
                out[fn[:-4]] = pygame.image.load(os.path.join(adir, fn)).convert_alpha()
        return out

    # ------------------------------------------------ window & persistence
    def apply_window(self):
        s = self.saves.data["scale"]
        self.screen = pygame.display.set_mode((VW * s, VH * s))
        self.apply_topmost()

    def apply_topmost(self):
        if sys.platform != "win32":
            return
        try:
            import ctypes
            hwnd = pygame.display.get_wm_info().get("window")
            if hwnd:
                flag = -1 if self.saves.data["topmost"] else -2
                ctypes.windll.user32.SetWindowPos(hwnd, flag, 0, 0, 0, 0, 0x0013)
        except Exception:
            pass

    def persist(self):
        d = self.saves.data
        d["outfit"] = self.outfit
        d["accessory"] = self.accessory
        d["mood"] = round(self.mood, 1)
        d["light"] = self.room.light
        d["lamp_on"] = self.room.lamp_on
        d["curtains_closed"] = self.room.curtains_closed
        d["poster_idx"] = self.room.poster_idx
        d["rps_wins"] = self.rps_wins
        self.saves.save()

    def reset_pose(self):
        self.phys.reset()
        self.room.reset_props()
        self.mode = None
        self.rmb_petting = False
        self.grab_part = None
        self.shake_acc = 0.0
        self.emote("normal", 0.0)
        self.say("reset")
        self.audio.play("sparkle")

    def reset_all_progress(self):
        sc = self.saves.data["scale"]
        d = self.saves.reset_defaults(keep_scale=sc)
        self.outfit = d["outfit"]
        self.accessory = d["accessory"]
        self.mood = d["mood"]
        self.rps_wins = d["rps_wins"]
        self.room.sync_from_save(d)
        self.room.reset_props()
        self.phys.reset()
        self.particles.clear()
        self.audio.set_volume(d["volume"])
        self.apply_topmost()
        self.ui.close_rps()
        self.ui.settings = False
        self.ui.confirm_reset = False
        self.emote("normal", 0.0)
        self.say("reset_all")
        self.audio.play("sparkle")

    # ------------------------------------------------ reactions
    def say(self, key_or_text, raw=False):
        self.speech = key_or_text if raw else random.choice(LINES[key_or_text])
        self.speech_t = 2.4 + len(self.speech) * 0.042
        self.speech_shown = 0.0
        self.idle_t = 0.0

    def emote(self, e, dur=2.0):
        self.emotion, self.emo_t = e, dur

    def base_emotion(self):
        return "sleepy" if self.room.is_pitch_dark() else "normal"

    def cycle_light(self):
        if self.room.light == 0:
            self.room.light, self.room.lamp_on = 1, False
            self.say("light_sunset")
            self.emote("smug", 1.8)
        elif self.room.light == 1:
            self.room.light, self.room.lamp_on = 2, True
            self.say("light_eve")
            self.emote("normal", 1.5)
        elif self.room.light == 2 and self.room.lamp_on:
            self.room.lamp_on = False
            if self.room.is_pitch_dark():
                self.say("sleepy_dark")
                self.emote("sleepy", 3.5)
            else:
                self.say("light_dark")
        else:
            self.room.light, self.room.lamp_on = 0, False
            self.say("light_day")
            self.emote("pet", 1.4)
        self.audio.play("lamp")
        self.persist()

    def toggle_lamp(self):
        self.audio.play("lamp")
        if self.room.light != 2:
            self.room.light, self.room.lamp_on = 2, True
            self.say("light_eve")
        else:
            self.room.lamp_on = not self.room.lamp_on
            if self.room.lamp_on:
                self.say("light_eve")
                self.emote("normal", 1.5)
            elif self.room.is_pitch_dark():
                self.say("sleepy_dark")
                self.emote("sleepy", 3.5)
            else:
                self.say("light_dark")
        self.persist()

    def toggle_curtains(self):
        self.room.curtains_closed = not self.room.curtains_closed
        self.audio.play("curtain")
        if self.room.is_pitch_dark():
            self.say("sleepy_dark")
            self.emote("sleepy", 3.5)
        elif self.room.curtains_closed:
            self.say("curtain_close")
        else:
            self.say("curtain_open")
        self.persist()

    def cycle_accessory(self):
        self.accessory = (self.accessory + 1) % ACC_COUNT
        self.audio.play("sparkle")
        self.particles.spawn("star", self.phys.rx, self.phys.ry - 172, 6)
        self.phys.sp["head"].kick(random.choice((-65, 65)), -25, self.saves.data["physics"])
        self.emote("smug" if self.accessory == 1 else ("starry" if self.accessory == 2 else "normal"), 2.2)
        self.say(f"acc_{self.accessory}")
        self.persist()

    def start_wardrobe(self):
        if self.room.ward_t < 0:
            self.room.ward_t, self.room.ward_swapped = 0.0, False
            self.audio.play("wardrobe")

    # ------------------------------------------------ mouse input
    def on_rmb_down(self, mx, my):
        if self.ui.settings:
            return
        if self.phys.head_rmb_hit(mx, my):
            self.rmb_petting = True
            self.pet_acc = 0.0
            self.pet_hearts = 0
            self.emote("pet", 1.8)

    def on_rmb_up(self):
        if self.rmb_petting:
            if self.pet_hearts == 0:
                self.particles.spawn("heart", self.phys.rx, self.phys.ry - 188, 1)
                self.audio.play("headpat")
                self.mood = min(100.0, self.mood + 1.5)
                self.say("pet")
            self.rmb_petting = False
            self.phys.sp["head"].pulled = False
            self.phys.sp["head"].tx = self.phys.sp["head"].ty = 0.0
            self.persist()

    def on_lmb_down(self, mx, my):
        p = (mx, my)
        # 1. Settings modal
        if self.ui.settings:
            R = self.ui.panel_rects()
            if self.ui.inr(p, R["close"]) or not self.ui.inr(p, R["panel"]):
                self.ui.settings = False
                self.ui.confirm_reset = False
                self.persist()
                self.audio.play("click")
            elif self.ui.inr(p, (R["physics"][0] - 6, R["physics"][1] - 6, 174, 26)):
                self.ui.slider = "physics"
                self._set_slider(mx)
            elif self.ui.inr(p, (R["volume"][0] - 6, R["volume"][1] - 6, 174, 26)):
                self.ui.slider = "volume"
                self._set_slider(mx)
            elif self.ui.inr(p, (166, R["topmost"][1] - 4, 308, 26)):
                self.saves.data["topmost"] = not self.saves.data["topmost"]
                self.apply_topmost()
                self.audio.play("click")
                self.persist()
            elif self.ui.inr(p, R["scale"]):
                sc = self.saves.data["scale"] + 1
                self.saves.data["scale"] = 1 if sc > self.max_scale else sc
                self.apply_window()
                self.audio.play("click")
                self.persist()
            elif self.ui.inr(p, R["reset"]):
                self.reset_pose()
                self.ui.settings = False
                self.ui.confirm_reset = False
            elif self.ui.inr(p, R["reset_all"]):
                if self.ui.confirm_reset:
                    self.reset_all_progress()
                else:
                    self.ui.confirm_reset = True
                    self.audio.play("click")
            elif self.ui.inr(p, R["quit"]):
                self.persist()
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            else:
                self.ui.confirm_reset = False
            return

        # 2. RPS minigame buttons
        if self.ui.rps_phase is not None:
            RR = self.ui.rps_rects()
            if self.ui.inr(p, RR["close"]):
                self.ui.close_rps()
                self.audio.play("click")
                return
            if self.ui.rps_phase in ("choose", "result"):
                for key in ("rock", "scissors", "paper"):
                    if self.ui.inr(p, RR[key]):
                        self.ui.pick_rps(key)
                        self.audio.play("rps_tick")
                        self.phys.kick_all(random.choice((-1, 1)), 0.45, self.saves.data["physics"])
                        self.emote("smug", 1.3)
                        return

        # 3. Corner HUD buttons
        b = self.ui.ui_hit(mx, my)
        if b:
            self.audio.play("click")
            if b == "gear":
                self.ui.settings = True
                self.ui.confirm_reset = False
            elif b == "shirt":
                self.start_wardrobe()
            elif b == "acc":
                self.cycle_accessory()
            elif b == "bulb":
                self.cycle_light()
            elif b == "game":
                if self.ui.rps_phase is None:
                    self.ui.start_rps()
                    self.emote("smug", 2.4)
                    self.say("rps_start")
                else:
                    self.ui.close_rps()
            elif b == "smile":
                e = EMOS[self.emo_idx % len(EMOS)]
                self.emo_idx += 1
                self.emote(e, 3.0)
                self.say(e)
                self.phys.kick_all(random.choice((-1, 1)), 0.45, self.saves.data["physics"])
            elif b == "hand":
                self.phys.wave_t = 1.8
                self.say("wave")
                self.emote("smug", 1.8)
                self.mood = min(100.0, self.mood + 3.0)
                self.persist()
            return

        # 4. Movable interactive props (drawer items -> boba -> pillow)
        if self.room.glasses_item_hit(mx, my):
            self.mode = "glasses_item"
            self.room.glasses_item["returning"] = False
            self.audio.play("click")
            return
        if self.room.camera_item_hit(mx, my):
            self.mode = "camera_item"
            self.room.camera_item["returning"] = False
            self.audio.play("click")
            return
        if self.room.boba_hit(mx, my):
            self.mode = "boba"
            self.room.boba["returning"] = False
            self.audio.play("click")
            return
        if self.room.pillow_hit(mx, my):
            self.mode = "pillow"
            self.room.pillow["on_bed"] = False
            self.room.pillow["vx"] = self.room.pillow["vy"] = self.room.pillow["vang"] = 0.0
            self.audio.play("click")
            return

        # 5. Character LMB interaction
        zone = self.phys.hit_zone(mx, my, self.outfit)
        if zone:
            self.mode = "press"
            self.press = (mx, my)
            self.press_zone = zone
            self.arm_wave_acc = 0.0
            self.arm_wave_said = False
            self.shake_acc = 0.0
            return

        # 6. Static clickable room furniture
        if self.room.curtains_hit(mx, my):
            self.toggle_curtains()
        elif self.ui.inr(p, (176, 72, 48, 66)):
            self.room.poster_idx = (self.room.poster_idx + 1) % 3
            self.audio.play("pop")
            self.emote("smug", 2.4)
            self.say(f"poster_{self.room.poster_idx}")
            self.persist()
        elif self.ui.inr(p, (580, 144, 54, 48)):
            self.toggle_lamp()
        elif self.ui.inr(p, (576, 202, 60, 34)):
            self.room.drawer_top = not self.room.drawer_top
            self.audio.play("drawer")
            if self.room.drawer_top:
                self.emote("smug", 2.2)
                self.say("drawer_top")
        elif self.ui.inr(p, (576, 238, 60, 34)):
            self.room.drawer_bot = not self.room.drawer_bot
            self.audio.play("drawer")
            if self.room.drawer_bot:
                self.emote("starry", 2.2)
                self.say("drawer_bot")
        elif self.ui.inr(p, (160, 216, 50, 48)):
            self.room.laundry_hop = 1.0
            self.audio.play("pop")
            self.emote("blush", 1.8)
            self.say("laundry")
        elif self.ui.inr(p, (214, 270, 34, 20)):
            self.room.manga_flip = 1.0
            self.audio.play("page")
            self.emote("starry", 2.0)
            self.say("manga")
        elif self.ui.inr(p, (26, 38, 128, 226)):
            self.start_wardrobe()

    def _set_slider(self, mx):
        R = self.ui.panel_rects()[self.ui.slider]
        f = clamp((mx - R[0]) / R[2], 0.0, 1.0)
        if self.ui.slider == "physics":
            self.saves.data["physics"] = round(f * 1.5, 2)
        else:
            self.saves.data["volume"] = round(f, 2)
            self.audio.set_volume(self.saves.data["volume"])

    def on_motion(self, mx, my, dx, dy):
        if self.ui.slider:
            self._set_slider(mx)
            return

        phys_k = self.saves.data["physics"]

        # RMB Headpat
        if self.rmb_petting and self.phys.head_rmb_hit(mx, my):
            hx = self.phys.rx + self.phys.sp["head"].x
            hy = self.phys.ry - 166
            self.phys.sp["head"].pulled = True
            self.phys.sp["head"].tx = clamp((mx - self.phys.rx) * 0.28, -7.0, 7.0)
            self.phys.sp["head"].ty = clamp((my - hy) * 0.14, -3.0, 4.0)
            self.phys.sp["bangs"].kick(dx * 12, 0, phys_k)
            self.phys.sp["hairL"].kick(dx * 14, 0, phys_k)
            self.phys.sp["hairR"].kick(dx * 14, 0, phys_k)
            self.emote("pet", 1.8)
            self.pet_acc += abs(dx) + abs(dy) * 0.5
            if self.pet_acc > 22:
                self.pet_acc = 0.0
                self.pet_hearts += 1
                self.particles.spawn("heart", hx, self.phys.ry - 190, 1)
                self.mood = min(100.0, self.mood + 2.8)
                if self.pet_hearts % 2 == 1:
                    self.audio.play("headpat")
                if self.pet_hearts == 2:
                    self.say("pet")
            self.idle_t = 0.0
            return

        # Draggable Cosplay Glasses -> bring to Marin's face to wear/toggle!
        if self.mode == "glasses_item":
            gi = self.room.glasses_item
            gi["x"], gi["y"] = clamp(mx, 18, VW - 18), clamp(my, 16, FLOOR_Y - 10)
            if math.hypot(gi["x"] - self.phys.rx, gi["y"] - (self.phys.ry - 161)) < 34:
                self.mode = None
                gi["returning"] = True
                self.accessory = 0 if self.accessory == 1 else 1
                self.audio.play("sparkle")
                self.particles.spawn("star", self.phys.rx, self.phys.ry - 165, 7)
                self.emote("smug" if self.accessory == 1 else "normal", 2.5)
                self.say(f"acc_{self.accessory}")
                self.mood = min(100.0, self.mood + 4.0)
                self.persist()
            return

        # Draggable Retro Camera -> bring near Marin for a Selfie Flash!
        if self.mode == "camera_item":
            ci = self.room.camera_item
            ci["x"], ci["y"] = clamp(mx, 18, VW - 18), clamp(my, 16, FLOOR_Y - 12)
            if math.hypot(ci["x"] - self.phys.rx, ci["y"] - (self.phys.ry - 135)) < 46:
                self.mode = None
                ci["returning"] = True
                self.room.trigger_flash()
                self.audio.play("shutter")
                self.phys.wave_t = 1.6
                self.phys.kick_all(random.choice((-1, 1)), 0.75, phys_k)
                self.particles.spawn("star", self.phys.rx, self.phys.ry - 165, 9)
                self.particles.spawn("heart", self.phys.rx, self.phys.ry - 188, 2)
                self.emote("starry", 2.6)
                self.say("selfie")
                self.mood = min(100.0, self.mood + 6.0)
                self.persist()
            return

        if self.mode == "pillow":
            pl = self.room.pillow
            pl["x"] = clamp(mx, 24, VW - 24)
            pl["y"] = clamp(my, 20, FLOOR_Y - 8)
            pl["vx"] = clamp(dx * 44.0, -MAX_PILLOW_VEL, MAX_PILLOW_VEL)
            pl["vy"] = clamp(dy * 44.0, -MAX_PILLOW_VEL, MAX_PILLOW_VEL)
            pl["vang"] = clamp(dx * 14.0, -280, 280)
            return

        if self.mode == "boba":
            bb = self.room.boba
            bb["x"] = clamp(mx, 14, VW - 14)
            bb["y"] = clamp(my, 16, FLOOR_Y - 12)
            if math.hypot(bb["x"] - self.phys.rx, bb["y"] - (self.phys.ry - 150)) < 36:
                self.mode = None
                bb["drink_t"] = 2.3
                bb["returning"] = False
                self.emote("starry", 2.5)
                self.mood = min(100.0, self.mood + 12.0)
                self.say("boba")
                self.audio.play("sip")
                self.particles.spawn("heart", self.phys.rx, self.phys.ry - 188, 3)
                self.particles.spawn("star", self.phys.rx, self.phys.ry - 178, 3)
                self.persist()
            return

        # Subtle spring ripple when sweeping cursor across Marin
        if self.mode is None and (abs(dx) + abs(dy)) > 5 and self.phys.hit_zone(mx, my, self.outfit):
            k = phys_k * 0.20
            self.phys.sp["hairL"].kick(dx * 4.5, dy * 1.8, k)
            self.phys.sp["hairR"].kick(dx * 4.5, dy * 1.8, k)
            self.phys.sp["tie"].kick(dx * 5.0, dy * 1.5, k)
            self.phys.sp["bangs"].kick(dx * 3.0, 0, k)

        if self.mode == "press" and math.hypot(mx - self.press[0], my - self.press[1]) > 5:
            if self.press_zone in ("armL", "armR"):
                self.mode = "arm_grab"
                self.grab_part = self.press_zone
                self.phys.sp[self.grab_part].pulled = True
            elif self.press_zone in ("cheek", "hairL", "hairR", "tie", "skirt"):
                part = "head" if self.press_zone == "cheek" else self.press_zone
                self.mode = "spring_grab"
                self.grab_part = part
                self.grab_anchor = (mx, my)
                self.phys.sp[part].pulled = True
            else:
                self.mode = "drag"
                self.grab = (self.phys.rx - mx, self.phys.ry - my)
                self.phys.air = True
                self.drag_said = False

        elif self.mode == "drag":
            self.shake_acc += abs(dx) + abs(dy)
            if self.shake_acc > 340:
                self.shake_acc = 0.0
                self.emote("pout", 2.8)
                self.say("shake_pout")

        elif self.mode == "arm_grab" and self.grab_part:
            part = self.grab_part
            sp = self.phys.sp[part]
            px_loc, py_loc = PIVOTS[part]
            sh_x = self.phys.rx + (px_loc - OX)
            sh_y = self.phys.ry + (py_loc - OY) + self.phys.breath_y
            vx, vy = mx - sh_x, my - sh_y
            dist = max(1.0, math.hypot(vx, vy))
            ang = math.degrees(math.atan2(vx, vy))
            ang = clamp(ang, -82.0, 26.0) if part == "armL" else clamp(ang, -26.0, 82.0)
            sp.override_angle = ang
            sp.override_stretch = clamp((dist - 44.0) / 145.0, -0.04, 0.12)
            sp.x = clamp(vx * 0.22, -sp.cx, sp.cx)
            sp.y = clamp((vy - 40.0) * 0.16, -sp.cy, sp.cy)
            self.phys.sp["head"].tx = clamp(vx * 0.11, -7.0, 7.0)
            self.phys.sp["head"].pulled = True
            self.phys.rx = clamp(self.phys.rx + clamp(vx * 0.012, -1.1, 1.1), 42, VW - 42)

            self.arm_wave_acc += abs(dx)
            if self.arm_wave_acc > 68 and not self.arm_wave_said:
                self.arm_wave_said = True
                self.emote("pet", 2.0)
                self.say("arm_wave")
                self.mood = min(100.0, self.mood + 4.0)
                self.particles.spawn("star", mx, my - 10, 3)
                self.audio.play("headpat")

        elif self.mode == "spring_grab" and self.grab_part:
            sp = self.phys.sp[self.grab_part]
            px = clamp((mx - self.grab_anchor[0]) * 0.62, -sp.cx * 1.65, sp.cx * 1.65)
            py = clamp((my - self.grab_anchor[1]) * 0.52, -sp.cy * 1.55, sp.cy * 1.55)
            sp.tx, sp.ty = px, py
            self.shake_acc += abs(dx) + abs(dy)
            if self.shake_acc > 280:
                self.shake_acc = 0.0
                self.emote("pout", 2.6)
                self.say("shake_pout")
            elif self.grab_part in ("tie", "skirt"):
                self.emote("blush", 1.4)
            if self.grab_part == "head":
                self.phys.rx = clamp(self.phys.rx + px * 0.035, 42, VW - 42)
                self.phys.sp["hairL"].kick(dx * 3.5, dy * 1.8, phys_k * 0.4)
                self.phys.sp["hairR"].kick(dx * 3.5, dy * 1.8, phys_k * 0.4)
                self.phys.sp["bangs"].tx = px * 0.5

    def on_lmb_up(self, mx, my):
        if self.ui.slider:
            self.ui.slider = None
            self.persist()
            return
        if self.mode == "pillow":
            self.mode = None
            return
        if self.mode == "boba":
            self.room.boba["returning"] = True
            self.mode = None
            return
        if self.mode == "glasses_item":
            self.room.glasses_item["returning"] = True
            self.mode = None
            return
        if self.mode == "camera_item":
            self.room.camera_item["returning"] = True
            self.mode = None
            return

        phys_k = self.saves.data["physics"]

        if self.mode == "arm_grab" and self.grab_part:
            sp = self.phys.sp[self.grab_part]
            ang = sp.override_angle or 0.0
            sp.override_angle = None
            sp.override_stretch = 0.0
            sp.pulled = False
            sp.x = clamp(ang / sp.rot_scale, -sp.cx, sp.cx)
            sp.vx = clamp(-sp.x * 10.5, -400, 400)
            self.phys.sp["head"].pulled = False
            self.phys.sp["head"].tx = 0.0
            self.audio.play("snap")
            self.grab_part = None

        elif self.mode == "spring_grab" and self.grab_part:
            part = self.grab_part
            sp = self.phys.sp[part]
            sp.pulled = False
            sp.vx = clamp(sp.vx - sp.x * 15.0, -450, 450)
            sp.vy = clamp(sp.vy - sp.y * 13.0, -450, 450)
            sp.tx = sp.ty = 0.0
            self.audio.play("snap")
            if part == "head":
                self.say("cheek")
                self.emote("blush", 2.0)
                self.phys.kick_all(1 if sp.x < 0 else -1, 0.65, phys_k)
            elif part in ("hairL", "hairR"):
                self.say("hair")
                self.emote("pout", 1.8)
                self.phys.sp["hairB"].kick(-sp.x * 12, -35, phys_k)
            elif part == "tie":
                self.say("tie")
                self.emote("blush", 2.2)
            elif part == "skirt":
                self.say("skirt")
                self.emote("blush", 2.4)
            self.grab_part = None

        elif self.mode == "drag":
            self.phys.vx = clamp(self.phys.vx, -MAX_BODY_VEL, MAX_BODY_VEL)
            self.phys.vy = clamp(self.phys.vy, -MAX_BODY_VEL, MAX_BODY_VEL)
            self.emote("surprised", 1.1)

        elif self.mode == "press":
            d = 1 if self.phys.rx > mx else -1
            z = self.press_zone
            if z in ("armL", "armR"):
                self.phys.sp[z].kick((-1 if z == "armL" else 1) * 240, -130, phys_k)
                self.phys.sp["hairL"].kick(d * 95, -35, phys_k)
                self.phys.sp["hairR"].kick(d * 95, -35, phys_k)
                self.emote("starry", 2.0)
                self.mood = min(100.0, self.mood + 5.0)
                self.say("highfive")
                self.particles.spawn("star", mx, my - 8, 5)
                self.audio.play("sparkle")
                self.persist()
            elif z == "cheek":
                self.phys.sp["head"].kick(d * 200, -50, phys_k)
                self.phys.kick_all(d, 0.65, phys_k)
                self.emote("blush", 2.0)
                self.say("cheek")
                self.audio.play("pop")
            elif z in ("hairL", "hairR"):
                self.phys.sp[z].kick((-1 if z == "hairL" else 1) * 250, -100, phys_k)
                self.phys.sp["hairB"].kick(d * 165, -55, phys_k)
                self.phys.sp["head"].kick(d * 100, -28, phys_k)
                self.emote("pout", 1.8)
                self.say("hair")
                self.audio.play("pop")
            elif z == "tie":
                self.phys.sp["tie"].kick(d * 300, -75, phys_k)
                self.phys.sp["folds"].kick(d * 80, 35, phys_k)
                self.emote("blush", 2.0)
                self.say("tie")
                self.audio.play("pop")
            elif z == "skirt":
                self.phys.sp["skirt"].kick(d * 240, -65, phys_k)
                self.emote("blush", 2.2)
                self.say("skirt")
                self.audio.play("pop")
            else:
                self.phys.kick_all(d, 1.05, phys_k)
                self.phys.land_sq.kick(-0.95)
                if not self.phys.air:
                    self.phys.vy, self.phys.air = -150, True
                self.emote("blush", 1.8)
                self.say("body")
                self.particles.spawn("excl", self.phys.rx + 22, self.phys.ry - 190, 1)
                self.audio.play("pop")

        self.mode = None

    # ------------------------------------------------ main update
    def update(self, dt):
        mx, my = self.mouse
        phys_k = self.saves.data["physics"]
        interacting = (self.mode is not None or self.rmb_petting or self.ui.rps_phase is not None)

        # 1. Character kinematics & springs
        land_imp = self.phys.update(
            dt, self.mouse, self.mode == "drag", self.grab,
            phys_k, self.room.is_pitch_dark(), interacting
        )
        if self.mode == "drag":
            if self.emotion != "pout":
                self.emote("surprised", 0.5)
            if not self.drag_said and self.phys.ry < FLOOR_Y - 22:
                self.drag_said = True
                self.say("grab")
                self.audio.play("boing")
        if land_imp > 155:
            self.audio.play("land")
            self.particles.spawn("dust", self.phys.rx, FLOOR_Y - 2, 6)
            if land_imp > 500:
                self.emote("blush", 2.4)
                self.say("land")

        # 2. Room Lerp, pillow collision, boba & drawer items
        ev = self.room.update(dt, self.mode, self.phys, self.particles, self.audio, phys_k)
        if ev.get("wardrobe_swap"):
            self.outfit = (self.outfit + 1) % OUTFIT_COUNT
            self.particles.spawn("star", self.phys.rx, self.phys.ry - 98, 12)
            self.audio.play("sparkle")
            self.say(f"outfit_{self.outfit}")
            self.emote("smug", 2.2)
            self.phys.kick_all(1, 0.8, phys_k)
            self.phys.land_sq.kick(-0.85)
            self.persist()
        if ev.get("pillow_hit"):
            self.emote("surprised", 2.0)
            self.say("pillow")
            self.particles.spawn("excl", self.phys.rx + 22, self.phys.ry - 190, 1)
            self.audio.play("pillow")

        # 3. RPS Minigame update
        rps_ev = self.ui.update_rps(dt)
        if rps_ev == "tick":
            self.audio.play("rps_tick")
            self.phys.land_sq.kick(-0.55)
            self.phys.sp["head"].kick(random.choice((-45, 45)), -15, phys_k)
        elif rps_ev in ("win", "lose", "draw"):
            if rps_ev == "win":
                self.rps_wins += 1
                self.mood = min(100.0, self.mood + 10.0)
                self.emote("starry", 2.6)
                self.say("rps_win")
                self.particles.spawn("star", self.phys.rx, self.phys.ry - 175, 8)
                self.audio.play("rps_win")
            elif rps_ev == "lose":
                self.mood = min(100.0, self.mood + 5.0)
                self.emote("smug", 2.6)
                self.say("rps_lose")
                self.audio.play("rps_lose")
            else:
                self.mood = min(100.0, self.mood + 6.0)
                self.emote("pet", 2.4)
                self.say("rps_draw")
                self.particles.spawn("heart", self.phys.rx, self.phys.ry - 185, 2)
                self.audio.play("headpat")
            self.phys.kick_all(1, 0.6, phys_k)
            self.persist()

        # 4. Atmospheric & interactive particles
        sun_vis = self.room.cur_sun_alpha > 15.0
        lamp_vis = self.room.cur_lamp_alpha > 80.0
        self.particles.update(dt, sun_vis, lamp_vis)

        # 5. Sleepy dark-room Zzz particles
        if self.room.is_pitch_dark() and not self.phys.air and not interacting:
            self.sleepy_cd -= dt
            if self.sleepy_cd <= 0:
                self.sleepy_cd = random.uniform(4.5, 7.5)
                self.particles.spawn("zzz", self.phys.rx + 18, self.phys.ry - 192, 1)
                if random.random() < 0.42:
                    self.say("sleepy_dark")

        # 6. Emotion / speech / idle timers
        self.emo_t -= dt
        if self.emo_t <= 0:
            self.emotion = self.base_emotion()

        if self.speech_t > 0:
            self.speech_t -= dt
            prev = int(self.speech_shown)
            self.speech_shown = min(len(self.speech), self.speech_shown + dt * 28)
            if int(self.speech_shown) != prev and prev % 2 == 0 and prev < len(self.speech):
                self.audio.blip()

        self.mood += (55.0 - self.mood) * 0.004 * dt
        self.idle_t += dt
        if self.idle_t > 24 and not interacting:
            self.say("sleepy_dark" if self.room.is_pitch_dark() else "idle")
        self.hint_t -= dt

        # 7. Hover & cursor feedback
        p = (mx, my)
        self.hover_curtains = (
            not self.ui.settings and self.mode is None
            and not self.phys.hit_zone(mx, my, self.outfit)
            and self.room.curtains_hit(mx, my)
        )
        hv = None
        if self.mode in ("drag", "spring_grab", "arm_grab", "pillow", "boba", "glasses_item", "camera_item"):
            hv = pygame.SYSTEM_CURSOR_SIZEALL
        elif (self.ui.settings or self.ui.ui_hit(mx, my) or self.room.pillow_hit(mx, my)
              or self.room.boba_hit(mx, my) or self.room.glasses_item_hit(mx, my)
              or self.room.camera_item_hit(mx, my) or self.hover_curtains
              or self.phys.hit_zone(mx, my, self.outfit)
              or self.ui.inr(p, (176, 72, 48, 66)) or self.ui.inr(p, (580, 144, 54, 48))
              or self.ui.inr(p, (576, 202, 60, 70)) or self.ui.inr(p, (160, 216, 50, 48))
              or self.ui.inr(p, (214, 270, 34, 20)) or self.ui.inr(p, (26, 38, 128, 226))):
            hv = pygame.SYSTEM_CURSOR_HAND
        hv = hv or pygame.SYSTEM_CURSOR_ARROW
        if hv != self.cursor:
            self.cursor = hv
            try:
                pygame.mouse.set_cursor(hv)
            except Exception:
                pass
        self.ui.hover = self.ui.ui_hit(mx, my) if not self.ui.settings else None

    # ------------------------------------------------ rendering
    def draw(self):
        c = self.canvas
        # 1. Room background + smooth Lerp sky/curtains/lighting
        self.room.draw_background(c, self.assets, self.hover_curtains)
        # 2. Atmospheric particles (sunbeam dust motes & warm lamp micro-sparkles)
        self.particles.draw_ambient(c)
        # 3. Dynamic floor shadow under Marin
        self.room.draw_floor_shadow(
            c, self.phys.rx, FLOOR_Y - self.phys.ry,
            base_w=54, base_h=10, max_alpha=95, squash=self.phys.land_sq.val
        )
        # 4. Character composited & smoothly tinted to room lighting
        comp = self.phys.compose(
            self.assets, self.outfit, self.accessory, self.emotion,
            self.mode == "drag", self.grab_part
        )
        lit = self.room.tint_surface(comp, self.phys.rx, self.phys.ry - 100)
        sq = self.phys.land_sq.val
        blit_pivoted(c, lit, (COX, COY), (self.phys.rx, self.phys.ry),
                     angle=0.0, sx=1.0 - sq * 0.85, sy=1.0 + sq)
        # 5. Dynamic room props (pillow, boba, drawer glasses & retro camera)
        self.room.draw_props(c, self.assets, self.mode)
        # 6. Foreground interactive particles (hearts, stars, landing dust, zzz, excl)
        self.particles.draw_foreground(c)
        # 7. Camera selfie flash overlay
        self.room.draw_flash(c)
        # 8. Speech bubble, HUD, RPS minigame & Settings modal
        if self.speech_t > 0:
            self.ui.draw_speech(c, self.phys.rx, self.phys.ry, self.speech, self.speech_shown)
        self.ui.draw_hud(c, self.mood, self.rps_wins, self.hint_t, self.assets, self.phys.rx, self.phys.ry)
        if self.ui.settings:
            self.ui.draw_settings(c, self.saves.data)

        # Crisp Nearest-Neighbor upscale to window (2x / 3x)
        pygame.transform.scale(c, self.screen.get_size(), self.screen)
        pygame.display.flip()

    # ------------------------------------------------ main loop
    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            dt = min(clock.tick(60) / 1000.0, 1 / 30)
            sc = self.saves.data["scale"]
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    if self.ui.settings:
                        self.ui.settings = False
                        self.ui.confirm_reset = False
                        self.persist()
                    elif self.ui.rps_phase is not None:
                        self.ui.close_rps()
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
        self.persist()
        pygame.quit()


def main():
    Game().run()


if __name__ == "__main__":
    main()
