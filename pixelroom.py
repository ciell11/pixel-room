# -*- coding: utf-8 -*-
"""Pixel Room — Marin Kitagawa (v0.5-beta: Alive, Cute & Chat Update)."""
import os
import sys
import math
import random
import datetime

# Set Windows DPI awareness BEFORE pygame.init() for crisp 1:1 Nearest-Neighbor scaling & zero black strips!
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

from constants import (
    VERSION, VW, VH, FLOOR_Y, SR, OX, OY, COX, COY,
    EMOS, LINES, PIVOTS, OUTFIT_COUNT, ACC_COUNT,
    PINK, WHITE, affinity_level, res_dir, clamp,
)
from save_manager import SaveManager
from audio_engine import AudioEngine
from particles import ParticleSystem
from physics import CharacterPhysics, blit_pivoted, MAX_BODY_VEL
from room_objects import RoomObjects, MAX_PILLOW_VEL
from ui_manager import UIManager, pattern_surface, HEART_P
from chat_engine import ChatEngine


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
        try:
            pygame.mouse.set_visible(False)
            pygame.key.stop_text_input()
        except Exception:
            pass

        self.canvas = pygame.Surface((VW, VH))
        self.assets = self._load_assets()
        self._phone_halo = self._build_phone_halo()

        # Modular subsystems
        self.audio = AudioEngine(cfg["volume"])
        self.music_on = bool(cfg.get("music_on", False))
        self.audio.set_music(self.music_on)
        self.ui = UIManager()
        self.particles = ParticleSystem(self.ui.icons)
        self.phys = CharacterPhysics()
        self.room = RoomObjects(cfg)
        self.chat = ChatEngine()
        self.audio.set_rain(self.room.weather_rain)

        # Persistent character state & stats
        self.outfit = cfg["outfit"]
        self.accessory = cfg["accessory"]
        self.mood = cfg["mood"]
        self.affinity_xp = cfg["affinity_xp"]
        self.rps_wins = cfg["rps_wins"]
        self.collar_relaxed = bool(cfg.get("collar_relaxed", False))
        self.player_name = cfg.get("player_name", "")
        self.stat_pets = cfg.get("stat_pets", 0)
        self.stat_selfies = cfg.get("stat_selfies", 0)
        self.stat_chats = cfg.get("stat_chats", 0)

        if cfg.get("real_time_sync", False):
            self.sync_real_time_light(silent=True)

        self.emotion, self.emo_t = self.base_emotion(), 0.0
        self.speech, self.speech_t, self.speech_shown = "", 0.0, 0.0

        # Input & dynamic interaction state
        self.mode = None
        self.rmb_petting = False
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
        self.near_hover_t = 0.0
        self.near_cd = 0.0
        self.tease_score = 0.0
        self.collar_check_cd = 5.0
        self.rt_sync_cd = 30.0
        self.hint_t = 10.0
        self.emo_idx = 0
        self.mouse = (320.0, 180.0)
        self.mouse_in_window = True
        self.hover_obj = None
        self.cursor_state = "arrow"
        self._skip_next_textinput = False
        self._snap_polaroid_next = False

    @staticmethod
    def _build_phone_halo():
        """Precompute a 16-bit 4x4 Bayer-dithered soft cyan smartphone glow halo (zero numpy at runtime)."""
        bayer = (
            (0, 8, 2, 10),
            (12, 4, 14, 6),
            (3, 11, 1, 9),
            (15, 7, 13, 5),
        )
        w, h = 64, 72
        s = pygame.Surface((w, h))
        s.fill((0, 0, 0))
        cx, cy = 36.0, 44.0
        for y in range(h):
            by = bayer[y & 3]
            for x in range(w):
                d = math.hypot((x - cx) * 1.05, (y - cy) * 0.85)
                f = max(0.0, 1.0 - d / 36.0) ** 1.65
                q = f * 5.0
                lvl = int(q) + (1 if (q - int(q)) > (by[x & 3] / 16.0) else 0)
                v = min(1.0, lvl / 5.0)
                if v > 0:
                    s.set_at((x, y), (int(34 * v), int(68 * v), int(92 * v)))
        return s

    @staticmethod
    def _load_assets():
        adir = os.path.join(res_dir(), "assets")
        out = {}
        for fn in os.listdir(adir):
            if fn.endswith(".png"):
                out[fn[:-4]] = pygame.image.load(os.path.join(adir, fn)).convert_alpha()
        return out

    @property
    def aff_lvl(self):
        return affinity_level(self.affinity_xp)

    def add_affinity(self, pts):
        if pts <= 0:
            return
        old_lvl = self.aff_lvl
        self.affinity_xp += int(pts)
        new_lvl = self.aff_lvl
        if new_lvl > old_lvl:
            self.audio.play("level_up")
            self.particles.spawn("heart", self.phys.rx, self.phys.ry - 188 + self.phys.floor_sit_y, 6)
            self.particles.spawn("star", self.phys.rx, self.phys.ry - 170 + self.phys.floor_sit_y, 8)
            self.emote("romantic", 3.4)
            msg = random.choice(LINES["level_up"]).format(lvl=new_lvl)
            self.say(msg, raw=True)

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

    def sync_real_time_light(self, silent=False):
        """Map system clock hour cleanly to Day / Sunset / Evening Lamp / Night."""
        hour = datetime.datetime.now().hour
        if 6 <= hour < 17:
            self.room.light, self.room.lamp_on = 0, False
        elif 17 <= hour < 20:
            self.room.light, self.room.lamp_on = 1, False
        elif 20 <= hour < 23:
            self.room.light, self.room.lamp_on = 2, True
        else:
            self.room.light, self.room.lamp_on = 2, False
            self.room.fairy_on = True
        if not silent:
            self.audio.play("lamp")

    def persist(self):
        d = self.saves.data
        d["outfit"] = self.outfit
        d["accessory"] = self.accessory
        d["mood"] = round(self.mood, 1)
        d["affinity_xp"] = self.affinity_xp
        d["light"] = self.room.light
        d["lamp_on"] = self.room.lamp_on
        d["fairy_on"] = self.room.fairy_on
        d["curtains_closed"] = self.room.curtains_closed
        d["poster_idx"] = self.room.poster_idx
        d["weather_rain"] = self.room.weather_rain
        d["rps_wins"] = self.rps_wins
        d["music_on"] = self.music_on
        d["collar_relaxed"] = self.collar_relaxed
        d["player_name"] = self.player_name
        d["stat_pets"] = self.stat_pets
        d["stat_selfies"] = self.stat_selfies
        d["stat_chats"] = self.stat_chats
        self.saves.save()

    def reset_pose(self):
        self.phys.reset()
        self.room.reset_props()
        self.mode = None
        self.rmb_petting = False
        self.grab_part = None
        self.shake_acc = 0.0
        self.tease_score = 0.0
        self.emote("normal", 0.0)
        self.say("reset")
        self.audio.play("sparkle")

    def reset_all_progress(self):
        sc = self.saves.data["scale"]
        d = self.saves.reset_defaults(keep_scale=sc)
        self.outfit = d["outfit"]
        self.accessory = d["accessory"]
        self.mood = d["mood"]
        self.affinity_xp = d["affinity_xp"]
        self.rps_wins = d["rps_wins"]
        self.music_on = d["music_on"]
        self.collar_relaxed = d["collar_relaxed"]
        self.player_name = d["player_name"]
        self.stat_pets = d["stat_pets"]
        self.stat_selfies = d["stat_selfies"]
        self.stat_chats = d["stat_chats"]
        self.tease_score = 0.0
        self.audio.set_music(self.music_on)
        self.room.sync_from_save(d)
        self.audio.set_rain(self.room.weather_rain)
        self.room.reset_props()
        self.phys.reset()
        self.particles.clear()
        self.audio.set_volume(d["volume"])
        self.apply_topmost()
        self.ui.close_rps()
        self.ui.close_chat()
        self.ui.settings = False
        self.ui.confirm_reset = False
        self.emote("normal", 0.0)
        self.say("reset_all")
        self.audio.play("sparkle")

    # ------------------------------------------------ reactions, chat & weather
    def say(self, key_or_text, raw=False):
        self.speech = key_or_text if raw else random.choice(LINES[key_or_text])
        self.speech_t = 2.8 + len(self.speech) * 0.044
        self.speech_shown = 0.0
        self.idle_t = 0.0

    def emote(self, e, dur=2.0):
        self.emotion, self.emo_t = e, dur

    def base_emotion(self):
        if self.room.is_pitch_dark() or self.phys.ai_state == "bed_nap":
            return "sleepy"
        return "normal"

    def toggle_rain(self, force_state=None, silent=False):
        new_state = (not self.room.weather_rain) if force_state is None else bool(force_state)
        self.room.weather_rain = new_state
        self.saves.data["weather_rain"] = new_state
        self.audio.set_rain(new_state)
        if not silent:
            self.audio.play("fairy" if new_state else "click")
            self.say("rain_on" if new_state else "rain_off")
            self.emote("romantic" if new_state else "pet", 2.4)
        self.persist()

    def submit_chat(self, text):
        msg = text.strip()
        if not msg:
            return
        ctx = {
            "aff_lvl": self.aff_lvl,
            "mood": self.mood,
            "outfit": self.outfit,
            "collar_relaxed": self.collar_relaxed,
            "music_on": self.music_on,
            "rain_on": self.room.weather_rain,
            "light": self.room.light,
            "player_name": self.player_name,
        }
        res = self.chat.respond(msg, ctx)
        if not res:
            return

        self.stat_chats += 1
        self.idle_t = 0.0
        if res["set_name"]:
            self.player_name = res["set_name"]
        self.mood = clamp(self.mood + res["mood_delta"], 0.0, 100.0)
        self.tease_score = max(0.0, self.tease_score + res["tease_delta"])
        if res["aff_delta"]:
            self.add_affinity(res["aff_delta"])

        self.emote(res["emote"], 3.0)
        self.say(res["reply"], raw=True)

        pt = res["particle"]
        py_top = self.phys.ry - 186 + self.phys.floor_sit_y
        if pt == "kiss_heart":
            self.phys.wave_t = 1.25
            self.particles.spawn("kiss_heart", self.phys.rx + 12, self.phys.ry - 154 + self.phys.floor_sit_y, 1)
            self.particles.spawn("heart", self.phys.rx, py_top, 3)
            self.audio.play("headpat")
        elif pt == "heart":
            self.particles.spawn("heart", self.phys.rx, py_top, 3)
            self.audio.play("headpat")
        elif pt == "star":
            self.particles.spawn("star", self.phys.rx, py_top + 12, 5)
            self.audio.play("sparkle")
        elif pt == "excl":
            self.particles.spawn("excl", self.phys.rx + 22, py_top, 1)
            self.audio.play("pop")

        # Execute live room / character action if requested via chat!
        act = res["action"]
        if act == "music_on":
            self.music_on = True
            self.audio.set_music(True)
        elif act == "music_off":
            self.music_on = False
            self.audio.set_music(False)
        elif act == "rain_on":
            self.toggle_rain(True, silent=True)
        elif act == "rain_off":
            self.toggle_rain(False, silent=True)
        elif act == "light_off":
            self.room.light, self.room.lamp_on = 2, False
            self.audio.play("lamp")
        elif act == "light_on":
            self.room.light, self.room.lamp_on = 0, False
            self.room.curtains_closed = False
            self.audio.play("lamp")
        elif act == "romantic":
            self.room.light = 3
            self.room.fairy_on = True
            self.audio.play("fairy")
        elif act == "wardrobe":
            self.start_wardrobe()
        elif act == "accessory":
            self.accessory = (self.accessory + 1) % ACC_COUNT
            self.audio.play("sparkle")
            self.particles.spawn("star", self.phys.rx, py_top + 12, 6)
        elif act == "sit_bed":
            self.phys.go_to_activity("bed_phone")
        elif act == "read_manga":
            self.phys.go_to_activity("read_manga")
        elif act == "start_rps":
            self.ui.start_rps()
        elif act == "dance":
            if not self.music_on:
                self.music_on = True
                self.audio.set_music(True)
            self.phys.go_to_activity("lofi_dance")
        elif act == "stretch":
            self.phys.go_to_activity("stretch")
        elif act == "wave":
            self.phys.wave_t = 1.9
        elif act == "collar_relax" and self.outfit in (0, 1, 4):
            self.phys.start_collar_anim(True)
        elif act == "collar_button" and self.outfit in (0, 1, 4):
            self.phys.start_collar_anim(False)
        elif act == "throw_pillow":
            pl = self.room.pillow
            pl["on_bed"] = False
            pl["x"], pl["y"] = self.phys.rx, self.phys.ry - 125
            tx, ty = self.mouse[0] - pl["x"], self.mouse[1] - pl["y"]
            dist = max(20.0, math.hypot(tx, ty))
            pl["vx"] = clamp((tx / dist) * 480.0, -MAX_PILLOW_VEL, MAX_PILLOW_VEL)
            pl["vy"] = clamp((ty / dist) * 320.0 - 200.0, -MAX_PILLOW_VEL, MAX_PILLOW_VEL)
            pl["vang"] = 360.0 if pl["vx"] >= 0 else -360.0
            self.phys.wave_t = 0.8
            self.audio.play("boing")

        self.persist()

    def _check_reading_light_reaction(self, was_dim):
        if self.phys.ai_state != "read_manga":
            return False
        is_dim = self.room.is_dim_or_dark() and not self.room.lamp_on
        if not was_dim and is_dim:
            self.tease_score += 1.8
            self.emote("pout", 2.8)
            self.say("tease_dark_read")
            self.particles.spawn("excl", self.phys.rx + 20, self.phys.ry - 186 + self.phys.floor_sit_y, 1)
            return True
        if was_dim and not is_dim:
            self.tease_score = max(0.0, self.tease_score - 2.0)
            self.mood = min(100.0, self.mood + 8.0)
            self.add_affinity(10)
            self.emote("romantic", 2.6)
            self.say("care_light_read")
            self.particles.spawn("heart", self.phys.rx, self.phys.ry - 184 + self.phys.floor_sit_y, 3)
            return True
        return False

    def cycle_light(self):
        was_dim = self.room.is_dim_or_dark() and not self.room.lamp_on
        if self.room.light == 0:
            self.room.light, self.room.lamp_on = 1, False
            if not self._check_reading_light_reaction(was_dim):
                self.say("light_sunset")
                self.emote("smug", 1.8)
        elif self.room.light == 1:
            self.room.light, self.room.lamp_on = 2, True
            if not self._check_reading_light_reaction(was_dim):
                self.say("light_eve")
                self.emote("normal", 1.5)
        elif self.room.light == 2 and self.room.lamp_on:
            self.room.lamp_on = False
            if not self._check_reading_light_reaction(was_dim):
                if self.room.is_pitch_dark():
                    self.say("sleepy_dark")
                    self.emote("sleepy", 3.5)
                else:
                    self.say("light_dark")
        elif self.room.light == 2 and not self.room.lamp_on:
            self.room.light = 3
            self.room.fairy_on = True
            if not self._check_reading_light_reaction(was_dim):
                self.say("light_romantic")
                self.emote("romantic", 2.8)
            self.audio.play("fairy")
            self.persist()
            return
        else:
            self.room.light, self.room.lamp_on = 0, False
            if not self._check_reading_light_reaction(was_dim):
                self.say("light_day")
                self.emote("pet", 1.4)
        self.audio.play("lamp")
        self.persist()

    def toggle_lamp(self):
        was_dim = self.room.is_dim_or_dark() and not self.room.lamp_on
        self.audio.play("lamp")
        if self.room.light != 2:
            self.room.light, self.room.lamp_on = 2, True
            if not self._check_reading_light_reaction(was_dim):
                self.say("light_eve")
        else:
            self.room.lamp_on = not self.room.lamp_on
            if not self._check_reading_light_reaction(was_dim):
                if self.room.lamp_on:
                    self.say("light_eve")
                    self.emote("normal", 1.5)
                elif self.room.is_pitch_dark():
                    self.say("sleepy_dark")
                    self.emote("sleepy", 3.5)
                else:
                    self.say("light_dark")
        self.persist()

    def toggle_fairy(self):
        self.room.fairy_on = not self.room.fairy_on
        self.audio.play("fairy" if self.room.fairy_on else "click")
        self.say("fairy_on" if self.room.fairy_on else "fairy_off")
        if self.room.fairy_on:
            self.emote("romantic", 2.2)
        self.persist()

    def toggle_music(self):
        self.music_on = not self.music_on
        self.audio.set_music(self.music_on)
        self.say("music_on" if self.music_on else "music_off")
        if self.music_on:
            self.emote("pet", 1.8)
            self.particles.spawn("note", self.phys.rx, self.phys.ry - 184 + self.phys.floor_sit_y, 2)
        self.persist()

    def toggle_curtains(self):
        was_dim = self.room.is_dim_or_dark() and not self.room.lamp_on
        self.room.curtains_closed = not self.room.curtains_closed
        self.audio.play("curtain")
        if not self._check_reading_light_reaction(was_dim):
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
        self.particles.spawn("star", self.phys.rx, self.phys.ry - 172 + self.phys.floor_sit_y, 6)
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
            dur = 2.0 + self.aff_lvl * 0.35
            self.emote("pet", dur)

    def on_rmb_up(self):
        if self.rmb_petting:
            if self.pet_hearts == 0:
                self.stat_pets += 1
                self.particles.spawn("heart", self.phys.rx, self.phys.ry - 188 + self.phys.floor_sit_y, 1)
                self.audio.play("headpat")
                self.mood = min(100.0, self.mood + 1.5)
                self.tease_score = max(0.0, self.tease_score - 0.8)
                self.add_affinity(2)
                self.say("pet_high" if self.aff_lvl >= 3 else "pet_low")
            elif self.aff_lvl >= 3:
                self.emote("romantic", 2.2)
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
            elif self.ui.inr(p, (R["physics"][0] - 6, R["physics"][1] - 6, 178, 26)):
                self.ui.slider = "physics"
                self._set_slider(mx)
            elif self.ui.inr(p, (R["volume"][0] - 6, R["volume"][1] - 6, 178, 26)):
                self.ui.slider = "volume"
                self._set_slider(mx)
            elif self.ui.inr(p, (154, R["topmost"][1] - 3, 330, 24)):
                self.saves.data["topmost"] = not self.saves.data["topmost"]
                self.apply_topmost()
                self.audio.play("click")
                self.persist()
            elif self.ui.inr(p, (154, R["free_life"][1] - 3, 330, 24)):
                self.saves.data["free_life"] = not self.saves.data["free_life"]
                self.audio.play("click")
                self.persist()
            elif self.ui.inr(p, (154, R["weather_rain"][1] - 3, 330, 24)):
                self.toggle_rain(silent=True)
                self.audio.play("click")
            elif self.ui.inr(p, (154, R["real_time_sync"][1] - 3, 330, 24)):
                self.saves.data["real_time_sync"] = not self.saves.data["real_time_sync"]
                if self.saves.data["real_time_sync"]:
                    self.sync_real_time_light(silent=True)
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

        # 2. Chat bar & quick-reply chips
        if self.ui.chat_open:
            cr = self.ui.chat_rects()
            for rect, _, payload in cr["chips"]:
                if self.ui.inr(p, rect):
                    self.audio.play("click")
                    self.submit_chat(payload)
                    return
            if self.ui.inr(p, cr["send"]):
                self.audio.play("click")
                if self.ui.chat_text.strip():
                    txt = self.ui.chat_text
                    self.ui.chat_text = ""
                    self.submit_chat(txt)
                return
            if self.ui.inr(p, cr["bar"]):
                return

        # 3. RPS minigame buttons
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

        # 4. Corner HUD buttons
        b = self.ui.ui_hit(mx, my)
        if b:
            self.audio.play("click")
            if b == "gear":
                self.ui.close_chat()
                self.ui.settings = True
                self.ui.confirm_reset = False
            elif b == "shirt":
                self.start_wardrobe()
            elif b == "acc":
                self.cycle_accessory()
            elif b == "bulb":
                self.cycle_light()
            elif b == "music":
                self.toggle_music()
            elif b == "rain":
                self.toggle_rain()
            elif b == "chat":
                if self.ui.chat_open:
                    self.ui.close_chat()
                else:
                    self.ui.open_chat()
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
                self.emote("romantic" if self.aff_lvl >= 3 else "smug", 1.8)
                self.mood = min(100.0, self.mood + 3.0)
                self.persist()
            return

        # 5. Movable interactive props
        if self.room.gift_item_hit(mx, my):
            self.mode = "gift_item"
            self.room.gift_item["returning"] = False
            self.audio.play("click")
            return
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

        # 6. Character LMB interaction
        zone = self.phys.hit_zone(mx, my, self.outfit)
        if zone:
            self.mode = "press"
            self.press = (mx, my)
            self.press_zone = zone
            self.arm_wave_acc = 0.0
            self.arm_wave_said = False
            self.shake_acc = 0.0
            return

        # 7. Clickable room decor & furniture
        if self.room.fairy_hit(mx, my):
            self.toggle_fairy()
        elif self.room.window_glass_hit(mx, my):
            self.toggle_rain()
        elif self.room.curtains_hit(mx, my):
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
            self.emote("flustered", 1.8)
            self.say("laundry")
        elif self.ui.inr(p, (214, 270, 34, 20)):
            if not self.phys.is_floor_manga:
                self.room.manga_flip = 1.0
                self.audio.play("page")
                self.phys.go_to_activity("read_manga")
                self.emote("starry", 2.2)
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
            hy = self.phys.ry - 166 + self.phys.floor_sit_y
            self.phys.sp["head"].pulled = True
            self.phys.sp["head"].tx = clamp((mx - self.phys.rx) * 0.28, -7.0, 7.0)
            self.phys.sp["head"].ty = clamp((my - hy) * 0.14, -3.0, 4.0)
            self.phys.sp["bangs"].kick(dx * 12, 0, phys_k)
            self.phys.sp["hairL"].kick(dx * 14, 0, phys_k)
            self.phys.sp["hairR"].kick(dx * 14, 0, phys_k)
            self.emote("pet", 1.9 + self.aff_lvl * 0.3)
            self.pet_acc += abs(dx) + abs(dy) * 0.5
            if self.pet_acc > 22:
                self.pet_acc = 0.0
                self.pet_hearts += 1
                self.stat_pets += 1
                self.tease_score = max(0.0, self.tease_score - 0.65)
                self.particles.spawn("heart", hx, self.phys.ry - 190 + self.phys.floor_sit_y, 2 if self.aff_lvl >= 4 else 1)
                self.mood = min(100.0, self.mood + 3.0)
                self.add_affinity(4)
                if self.pet_hearts % 2 == 1:
                    self.audio.play("headpat")
                if self.pet_hearts == 2:
                    self.say("pet_high" if self.aff_lvl >= 3 else "pet_low")
            self.idle_t = 0.0
            return

        # Draggable Gift / Candy Box
        if self.mode == "gift_item":
            gf = self.room.gift_item
            gf["x"], gf["y"] = clamp(mx, 18, VW - 18), clamp(my, 16, FLOOR_Y - 12)
            if math.hypot(gf["x"] - self.phys.rx, gf["y"] - (self.phys.ry - 135 + self.phys.floor_sit_y)) < 46:
                self.mode = None
                gf["returning"] = True
                self.audio.play("gift")
                self.tease_score = max(0.0, self.tease_score - 2.5)
                on_bed = self.phys.sitting
                self.particles.spawn("heart", self.phys.rx, self.phys.ry - 186 + self.phys.floor_sit_y, 7 if on_bed else 5)
                self.particles.spawn("star", self.phys.rx, self.phys.ry - 165 + self.phys.floor_sit_y, 6)
                self.phys.kick_all(random.choice((-1, 1)), 0.7, phys_k)
                self.emote("romantic" if on_bed else "flustered", 3.0)
                self.say("gift_bed_care" if on_bed else "gift")
                self.mood = min(100.0, self.mood + (22.0 if on_bed else 18.0))
                self.add_affinity(30 if on_bed else 25)
                self.persist()
            return

        # Draggable Cosplay Glasses
        if self.mode == "glasses_item":
            gi = self.room.glasses_item
            gi["x"], gi["y"] = clamp(mx, 18, VW - 18), clamp(my, 16, FLOOR_Y - 10)
            if math.hypot(gi["x"] - self.phys.rx, gi["y"] - (self.phys.ry - 161 + self.phys.floor_sit_y)) < 34:
                self.mode = None
                gi["returning"] = True
                self.accessory = 0 if self.accessory == 1 else 1
                self.audio.play("sparkle")
                self.particles.spawn("star", self.phys.rx, self.phys.ry - 165 + self.phys.floor_sit_y, 7)
                self.emote("smug" if self.accessory == 1 else "normal", 2.5)
                self.say(f"acc_{self.accessory}")
                self.mood = min(100.0, self.mood + 4.0)
                self.add_affinity(5)
                self.persist()
            return

        # Draggable Retro Camera -> Selfie Flash + Polaroid Card!
        if self.mode == "camera_item":
            ci = self.room.camera_item
            ci["x"], ci["y"] = clamp(mx, 18, VW - 18), clamp(my, 16, FLOOR_Y - 12)
            if math.hypot(ci["x"] - self.phys.rx, ci["y"] - (self.phys.ry - 135 + self.phys.floor_sit_y)) < 46:
                self.mode = None
                ci["returning"] = True
                self.stat_selfies += 1
                self.room.trigger_flash()
                self.audio.play("shutter")
                self.phys.wave_t = 1.6
                self.phys.kick_all(random.choice((-1, 1)), 0.75, phys_k)
                self.particles.spawn("star", self.phys.rx, self.phys.ry - 165 + self.phys.floor_sit_y, 9)
                self.particles.spawn("heart", self.phys.rx, self.phys.ry - 188 + self.phys.floor_sit_y, 2)
                self.emote("starry", 2.6)
                self.say("selfie")
                self.mood = min(100.0, self.mood + 6.0)
                self.add_affinity(10)
                self._snap_polaroid_next = True
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
            if math.hypot(bb["x"] - self.phys.rx, bb["y"] - (self.phys.ry - 150 + self.phys.floor_sit_y)) < 36:
                self.mode = None
                bb["drink_t"] = 2.3
                bb["returning"] = False
                on_bed = self.phys.sitting
                self.tease_score = max(0.0, self.tease_score - 1.8)
                self.emote("romantic" if on_bed else "starry", 2.5)
                self.mood = min(100.0, self.mood + (15.0 if on_bed else 12.0))
                self.say("boba_bed_care" if on_bed else "boba")
                self.audio.play("sip")
                self.particles.spawn("heart", self.phys.rx, self.phys.ry - 188 + self.phys.floor_sit_y, 5 if on_bed else 3)
                self.particles.spawn("star", self.phys.rx, self.phys.ry - 178 + self.phys.floor_sit_y, 3)
                self.add_affinity(18 if on_bed else 12)
                self.persist()
            return

        if self.mode is None and (abs(dx) + abs(dy)) > 5 and self.phys.hit_zone(mx, my, self.outfit):
            k = phys_k * 0.20
            self.phys.sp["hairL"].kick(dx * 4.5, dy * 1.8, k)
            self.phys.sp["hairR"].kick(dx * 4.5, dy * 1.8, k)
            self.phys.sp["tie"].kick(dx * 5.0, dy * 1.5, k)
            self.phys.sp["bangs"].kick(dx * 3.0, 0, k)

        if self.mode == "press" and math.hypot(mx - self.press[0], my - self.press[1]) > 5:
            if self.press_zone in ("armL", "armR"):
                if self.phys.is_floor_manga:
                    self.phys.stand_up("stand")
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
                prev_ai = self.phys.interrupt_for_drag()
                self.mode = "drag"
                self.grab = (self.phys.rx - mx, self.phys.ry - my)
                self.phys.air = True
                self.drag_said = False
                if prev_ai in ("read_manga", "bed_phone"):
                    self.tease_score += 1.6
                    self.emote("pout", 2.4)
                    self.say("tease_busy")
                    self.drag_said = True

        elif self.mode == "drag":
            self.shake_acc += abs(dx) + abs(dy)
            if self.shake_acc > 340:
                self.shake_acc = 0.0
                self.tease_score += 1.5
                self.emote("pout", 2.8)
                self.say("shake_pout")

        elif self.mode == "arm_grab" and self.grab_part:
            part = self.grab_part
            sp = self.phys.sp[part]
            px_loc, py_loc = PIVOTS[part]
            sh_x = self.phys.rx + (px_loc - OX)
            sh_y = self.phys.ry + (py_loc - OY) + self.phys.breath_y + self.phys.floor_sit_y
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
            if not self.phys.sitting:
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
                self.tease_score += 1.4
                self.emote("pout", 2.6)
                self.say("shake_pout")
            elif self.grab_part in ("tie", "skirt"):
                self.emote("flustered", 1.4)
            if self.grab_part == "head":
                if not self.phys.sitting and not self.phys.is_floor_manga:
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
        if self.mode == "gift_item":
            self.room.gift_item["returning"] = True
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
            self.tease_score += 1.15
            if part == "head":
                self.say("cheek")
                self.emote("flustered", 2.0)
                self.phys.kick_all(1 if sp.x < 0 else -1, 0.65, phys_k)
            elif part in ("hairL", "hairR"):
                self.say("hair")
                self.emote("pout", 1.8)
                self.phys.sp["hairB"].kick(-sp.x * 12, -35, phys_k)
            elif part == "tie":
                self.say("tie")
                self.emote("flustered", 2.2)
            elif part == "skirt":
                self.say("skirt")
                self.emote("flustered", 2.4)
            self.grab_part = None

        elif self.mode == "drag":
            if 388 <= self.phys.rx <= 548 and self.phys.ry <= 306 and abs(self.phys.vx) < 280:
                nap = self.room.is_pitch_dark()
                self.phys.sit_on_bed(nap=nap)
                self.audio.play("land")
                self.emote("sleepy" if nap else "smug", 2.4)
                self.say("ai_nap" if nap else "bed_drop")
                self.mood = min(100.0, self.mood + 3.0)
                self.add_affinity(3)
            else:
                self.phys.vx = clamp(self.phys.vx, -MAX_BODY_VEL, MAX_BODY_VEL)
                self.phys.vy = clamp(self.phys.vy, -MAX_BODY_VEL, MAX_BODY_VEL)
                self.emote("surprised", 1.1)

        elif self.mode == "press":
            d = 1 if self.phys.rx > mx else -1
            z = self.press_zone
            busy_ai = self.phys.ai_state in ("read_manga", "bed_phone")
            # Clicking her while she's seated reading manga -> she neatly puts the manga down & stands up!
            if self.phys.ai_state == "read_manga":
                self.phys.stand_up("stand")
                self.audio.play("page")
            if z in ("armL", "armR"):
                self.phys.sp[z].kick((-1 if z == "armL" else 1) * 240, -130, phys_k)
                self.phys.sp["hairL"].kick(d * 95, -35, phys_k)
                self.phys.sp["hairR"].kick(d * 95, -35, phys_k)
                self.emote("starry", 2.0)
                self.mood = min(100.0, self.mood + 5.0)
                self.say("highfive")
                self.particles.spawn("star", mx, my - 8, 5)
                self.audio.play("sparkle")
                self.add_affinity(4)
                self.persist()
            elif z == "cheek":
                self.tease_score += 0.85
                self.phys.sp["head"].kick(d * 200, -50, phys_k)
                self.phys.kick_all(d, 0.65, phys_k)
                self.emote("pout" if busy_ai else "flustered", 2.0)
                self.say("tease_busy" if busy_ai else "cheek")
                self.audio.play("pop")
            elif z in ("hairL", "hairR"):
                self.tease_score += 1.0
                self.phys.sp[z].kick((-1 if z == "hairL" else 1) * 250, -100, phys_k)
                self.phys.sp["hairB"].kick(d * 165, -55, phys_k)
                self.phys.sp["head"].kick(d * 100, -28, phys_k)
                self.emote("pout", 1.8)
                self.say("tease_busy" if busy_ai else "hair")
                self.audio.play("pop")
            elif z == "tie":
                self.tease_score += 1.1
                self.phys.sp["tie"].kick(d * 300, -75, phys_k)
                self.phys.sp["folds"].kick(d * 80, 35, phys_k)
                self.emote("flustered", 2.0)
                self.say("tie")
                self.audio.play("pop")
            elif z == "skirt":
                self.tease_score += 1.3
                self.phys.sp["skirt"].kick(d * 240, -65, phys_k)
                self.emote("flustered", 2.2)
                self.say("skirt")
                self.audio.play("pop")
            else:
                self.tease_score += 0.9
                self.phys.kick_all(d, 1.05, phys_k)
                self.phys.land_sq.kick(-0.95)
                if not self.phys.air and not self.phys.sitting:
                    self.phys.vy, self.phys.air = -150, True
                self.emote("pout" if busy_ai else "blush", 1.8)
                self.say("tease_busy" if busy_ai else "body")
                self.particles.spawn("excl", self.phys.rx + 22, self.phys.ry - 190, 1)
                self.audio.play("pop")

        self.mode = None

    # ------------------------------------------------ main update
    def update(self, dt):
        dt = min(dt, 0.05)
        mx, my = self.mouse
        phys_k = self.saves.data["physics"]
        interacting = (self.mode is not None or self.rmb_petting or self.ui.rps_phase is not None or self.ui.chat_open)

        self.ui.update_ui(dt)
        self.tease_score = max(0.0, self.tease_score - 0.18 * dt)

        # Periodic real-time lighting sync if enabled
        if self.saves.data.get("real_time_sync", False):
            self.rt_sync_cd -= dt
            if self.rt_sync_cd <= 0:
                self.rt_sync_cd = 30.0
                self.sync_real_time_light(silent=True)

        # 1. Character kinematics, springs, multi-phase collar & Living Room AI
        boba_busy = (self.mode == "boba" or self.room.boba["drink_t"] > 0 or self.room.boba["returning"])
        land_imp, idle_ev = self.phys.update(
            dt, self.mouse, self.mode == "drag", self.grab,
            phys_k, self.room.is_pitch_dark(), interacting,
            aff_lvl=self.aff_lvl,
            free_life=self.saves.data.get("free_life", True),
            boba_busy=boba_busy,
            music_on=self.music_on,
            rain_on=self.room.weather_rain,
            idle_t=self.idle_t,
        )

        py_top = self.phys.ry - 186 + self.phys.floor_sit_y
        if idle_ev == "collar_commit_relax":
            self.collar_relaxed = True
            self.audio.play("cloth")
            self.emote("flustered", 2.8)
            self.particles.spawn("heart", self.phys.rx, py_top, 3)
        elif idle_ev == "collar_done_relax":
            self.emote("romantic", 2.6)
            self.persist()
        elif idle_ev == "collar_commit_button":
            self.collar_relaxed = False
            self.audio.play("cloth")
            self.emote("pout", 2.6)
        elif idle_ev == "collar_done_button":
            self.persist()
        elif idle_ev == "blown_kiss":
            self.emote("romantic", 2.2)
            self.particles.spawn("kiss_heart", self.phys.rx + 12, self.phys.ry - 154 + self.phys.floor_sit_y, 1)
            self.audio.play("headpat")
            self.say("kiss_idle")
        elif idle_ev == "hair_tuck":
            self.emote("romantic", 1.8)
        elif idle_ev == "ai_enter_bed_phone":
            self.emote("smug", 2.4)
            self.say("ai_phone")
        elif idle_ev == "ai_enter_bed_nap":
            self.emote("sleepy", 4.0)
            self.say("ai_nap")
            self.particles.spawn("zzz", self.phys.rx + 18, self.phys.ry - 190, 1)
        elif idle_ev == "ai_enter_read_manga":
            self.audio.play("page")
            if self.room.is_dim_or_dark() and not self.room.lamp_on:
                self.emote("pout", 2.6)
                self.say("tease_dark_read")
            else:
                self.emote("starry", 2.5)
                self.say("ai_manga")
        elif idle_ev == "ai_manga_flip":
            self.audio.play("page")
            r = random.random()
            if r < 0.35:
                self.emote("pet", 2.0)
                self.say("ai_manga_react")
            elif r < 0.60:
                self.emote("surprised", 1.8)
        elif idle_ev == "ai_phone_chuckle":
            if random.random() < 0.55:
                self.emote("pet", 1.7)
                self.particles.spawn("star", self.phys.rx + 14, self.phys.ry - 150, 2)
        elif idle_ev == "ai_enter_watch_window":
            if self.room.weather_rain:
                self.emote("romantic", 2.8)
                self.say("ai_window_rain")
            else:
                self.emote("romantic" if self.room.light in (2, 3) else "normal", 2.5)
                self.say("ai_window_night" if self.room.light in (2, 3) else "ai_window_day")
        elif idle_ev == "ai_enter_wardrobe_check":
            self.emote("smug", 2.4)
            self.say("ai_wardrobe")
        elif idle_ev == "ai_enter_self_boba":
            if not boba_busy:
                self.room.boba["drink_t"] = 2.0
                self.audio.play("sip")
                self.emote("pet", 2.2)
                self.say("ai_boba")
        elif idle_ev == "ai_enter_lofi_dance":
            self.emote("pet", 2.5)
            self.say("ai_dance")
            self.particles.spawn("note", self.phys.rx, py_top, 2)
        elif idle_ev == "ai_dance_note":
            self.particles.spawn("note", self.phys.rx, py_top, 1)
        elif idle_ev == "ai_enter_stretch":
            self.emote("pet", 2.6)
            self.say("ai_stretch")
        elif idle_ev == "ai_enter_attention":
            self.emote("romantic", 2.8)
            self.say("ai_attention")
            self.particles.spawn("heart", self.phys.rx, py_top, 2)

        # Autonomous Canon Top-Button Collar Relaxation (Outfits 0, 1 Home Shirt & 4 Canon Shirt!)
        self.collar_check_cd = max(0.0, self.collar_check_cd - dt)
        if (self.outfit in (0, 1, 4) and self.phys.collar_seq_phase == 0
                and not interacting and not self.phys.air and not self.room.is_pitch_dark()):
            if (not self.collar_relaxed and self.aff_lvl >= 4 and self.mood >= 80.0
                    and self.tease_score < 2.0 and self.collar_check_cd <= 0):
                self.collar_check_cd = 22.0
                self.phys.start_collar_anim(True)
                self.emote("flustered", 3.4)
                self.say("collar_relax")
            elif self.collar_relaxed and self.tease_score >= 4.2:
                self.tease_score = 1.8
                self.collar_check_cd = 18.0
                self.phys.start_collar_anim(False)
                self.emote("pout", 2.8)
                self.say("collar_button")

        # Soft shy smile when hovering gently near her face
        self.near_cd = max(0.0, self.near_cd - dt)
        if not interacting and not self.ui.settings and not self.room.is_pitch_dark() and self.phys.ai_state != "bed_nap":
            if abs(mx - self.phys.rx) < 42 and abs(my - (self.phys.ry - 154 + self.phys.floor_sit_y)) < 36:
                self.near_hover_t += dt
                if self.near_hover_t > 1.35 and self.near_cd <= 0 and self.emotion == "normal":
                    self.near_cd = 9.0
                    self.emote("romantic" if self.aff_lvl >= 3 else "flustered", 2.0)
                    if random.random() < 0.45:
                        self.say("near_shy")
            else:
                self.near_hover_t = 0.0

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
                self.emote("flustered", 2.4)
                self.say("land")

        # 2. Room Lerp, pillow collision / counter-throw, boba & drawer items
        ev = self.room.update(dt, self.mode, self.phys, self.particles, self.audio, phys_k, mouse=self.mouse)
        if ev.get("wardrobe_swap"):
            self.outfit = (self.outfit + 1) % OUTFIT_COUNT
            self.particles.spawn("star", self.phys.rx, self.phys.ry - 98, 12)
            self.audio.play("sparkle")
            self.say(f"outfit_{self.outfit}")
            self.emote("romantic" if self.outfit == 4 else "smug", 2.2)
            self.phys.kick_all(1, 0.8, phys_k)
            self.phys.land_sq.kick(-0.85)
            self.persist()
        if ev.get("pillow_counter"):
            self.tease_score += 1.0
            self.emote("smug", 2.5)
            self.say("pillow_counter")
            self.particles.spawn("star", self.phys.rx, self.phys.ry - 166 + self.phys.floor_sit_y, 7)
            self.audio.play("boing")
        elif ev.get("pillow_hit"):
            self.tease_score += 1.2
            self.emote("surprised", 2.0)
            self.say("pillow")
            self.particles.spawn("excl", self.phys.rx + 22, self.phys.ry - 190 + self.phys.floor_sit_y, 1)
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
                self.add_affinity(12)
            elif rps_ev == "lose":
                self.mood = min(100.0, self.mood + 5.0)
                self.emote("smug", 2.6)
                self.say("rps_lose")
                self.audio.play("rps_lose")
                self.add_affinity(4)
            else:
                self.mood = min(100.0, self.mood + 6.0)
                self.emote("pet", 2.4)
                self.say("rps_draw")
                self.particles.spawn("heart", self.phys.rx, self.phys.ry - 185, 2)
                self.audio.play("headpat")
                self.add_affinity(6)
            self.phys.kick_all(1, 0.6, phys_k)
            self.persist()

        # 4. Atmospheric particles
        sun_vis = self.room.cur_sun_alpha > 15.0
        lamp_vis = self.room.cur_lamp_alpha > 80.0
        romantic_vibe = (self.room.light == 3) or (self.mood >= 82.0) or (self.aff_lvl >= 4)
        self.particles.update(dt, sun_vis, lamp_vis, romantic_vibe=romantic_vibe)

        # 5. Sleepy Zzz particles
        if (self.room.is_pitch_dark() or self.phys.ai_state == "bed_nap") and not self.phys.air and not interacting:
            self.sleepy_cd -= dt
            if self.sleepy_cd <= 0:
                self.sleepy_cd = random.uniform(4.5, 7.5)
                self.particles.spawn("zzz", self.phys.rx + 18, self.phys.ry - 192, 1)
                if random.random() < 0.42:
                    self.say("sleepy_dark")

        # 6. Emotion / speech typewriter / idle timers
        self.emo_t -= dt
        if self.emo_t <= 0:
            self.emotion = self.base_emotion()

        if self.speech_t > 0:
            self.speech_t -= dt
            prev = int(self.speech_shown)
            self.speech_shown = min(len(self.speech), self.speech_shown + dt * 30)
            if int(self.speech_shown) != prev and prev % 2 == 0 and prev < len(self.speech):
                if self.speech[prev] not in (" ", "\n", ".", ","):
                    self.audio.blip()

        self.mood += (55.0 - self.mood) * 0.004 * dt
        self.idle_t += dt
        if self.idle_t > 24 and not interacting:
            if self.room.is_pitch_dark():
                self.say("sleepy_dark")
            else:
                self.say("idle_high" if self.aff_lvl >= 3 else "idle_low")
        self.hint_t -= dt

        # 7. Hover outlines & Custom 16-bit Pixel Cursor state
        ui_btn = self.ui.ui_hit(mx, my) if not self.ui.settings else None
        self.ui.hover = ui_btn
        char_hit = bool(self.phys.hit_zone(mx, my, self.outfit)) if not self.ui.settings else False
        if self.ui.settings or self.mode is not None or ui_btn is not None:
            self.hover_obj = None
        else:
            self.hover_obj = self.room.hit_object_name(mx, my, char_hit=char_hit)

        chat_hov = False
        if self.ui.chat_open and not self.ui.settings:
            cr = self.ui.chat_rects()
            chat_hov = self.ui.inr((mx, my), cr["send"]) or any(self.ui.inr((mx, my), r) for r, _, _ in cr["chips"])

        if self.rmb_petting:
            self.cursor_state = "hand_heart"
        elif self.mode in ("drag", "spring_grab", "arm_grab", "pillow", "boba", "glasses_item", "gift_item", "camera_item"):
            self.cursor_state = "hand_grab"
        elif self.ui.settings or ui_btn or self.hover_obj or char_hit or chat_hov:
            self.cursor_state = "hand_open"
        else:
            self.cursor_state = "arrow"

    # ------------------------------------------------ rendering
    def draw(self):
        c = self.canvas
        self.room.draw_background(c, self.assets, hover_obj=self.hover_obj, manga_picked_up=self.phys.is_floor_manga)
        self.room.draw_bed_pillow(c, self.assets, self.mode, hover_obj=self.hover_obj)
        self.particles.draw_ambient(c)

        # Dynamic floor / bed-edge / floor-sit shadow
        if self.phys.sitting:
            self.room.draw_floor_shadow(c, self.phys.rx, 46.0, base_w=46, base_h=8, max_alpha=64, squash=0.0)
        elif self.phys.is_floor_manga:
            self.room.draw_floor_shadow(c, self.phys.rx, 0.0, base_w=72, base_h=12, max_alpha=92, squash=0.0)
        else:
            self.room.draw_floor_shadow(
                c, self.phys.rx, FLOOR_Y - self.phys.ry,
                base_w=54, base_h=10, max_alpha=95, squash=self.phys.land_sq.val
            )

        comp = self.phys.compose(
            self.assets, self.outfit, self.accessory, self.emotion,
            self.mode == "drag", self.grab_part,
            collar_relaxed=self.collar_relaxed,
        )
        lit = self.room.tint_surface(comp, self.phys.rx, self.phys.ry - 100)
        sq = self.phys.land_sq.val
        sx_total = (1.0 - sq * 0.85) * self.phys.twirl_scale_x()
        blit_pivoted(c, lit, (COX, COY), (self.phys.rx, self.phys.ry),
                     angle=0.0, sx=sx_total, sy=1.0 + sq)

        # Subtle 16-bit Bayer-dithered cyan phone glow in dim/dark room
        if (self.phys.ai_state == "bed_phone" and self.phys.sitting and not self.phys.air
                and self.mode != "drag" and (self.room.light in (2, 3) or self.room.curtains_closed)):
            c.blit(self._phone_halo, (int(self.phys.rx - 28), int(self.phys.ry - 178)),
                   special_flags=pygame.BLEND_RGB_ADD)

        self.room.draw_props(c, self.assets, self.mode, hover_obj=self.hover_obj)
        self.particles.draw_foreground(c)

        # Capture crisp Polaroid Selfie snapshot cleanly right before flash & HUD!
        if self._snap_polaroid_next:
            self._snap_polaroid_next = False
            px = int(clamp(self.phys.rx - 36, 0, VW - 72))
            py = int(clamp(self.phys.ry - 188 + self.phys.floor_sit_y, 0, VH - 72))
            snap = c.subsurface((px, py, 72, 72)).copy()
            cap = self.player_name[:9] if self.player_name else "Marin"
            self.ui.trigger_polaroid(snap, label=cap)

        self.room.draw_flash(c)
        if self.speech_t > 0:
            self.ui.draw_speech(c, self.phys.rx, self.phys.ry, self.speech, self.speech_shown,
                                head_offset_y=self.phys.floor_sit_y)
        self.ui.draw_hud(
            c, self.mood, self.aff_lvl, self.affinity_xp,
            self.rps_wins, self.hint_t, self.assets, self.phys.rx, self.phys.ry,
            music_on=self.music_on, rain_on=self.room.weather_rain, mouse_pos=self.mouse,
        )
        self.ui.draw_settings(c, self.saves.data)

        if self.mouse_in_window:
            self.ui.draw_cursor(c, self.mouse, self.cursor_state)

        pygame.transform.scale(c, self.screen.get_size(), self.screen)
        pygame.display.flip()

    # ------------------------------------------------ main loop
    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            dt = min(clock.tick(60) / 1000.0, 0.05)
            sc = self.saves.data["scale"]
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    running = False
                elif ev.type == pygame.WINDOWENTER:
                    self.mouse_in_window = True
                elif ev.type == pygame.WINDOWLEAVE:
                    self.mouse_in_window = False
                elif ev.type == pygame.TEXTINPUT:
                    if self.ui.chat_open and not self.ui.settings:
                        if self._skip_next_textinput:
                            self._skip_next_textinput = False
                        elif len(self.ui.chat_text) < 64:
                            self.ui.chat_text += ev.text
                elif ev.type == pygame.KEYDOWN:
                    if self.ui.chat_open and not self.ui.settings:
                        if ev.key == pygame.K_ESCAPE:
                            self.ui.close_chat()
                        elif ev.key == pygame.K_BACKSPACE:
                            self.ui.chat_text = self.ui.chat_text[:-1]
                        elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            if self.ui.chat_text.strip():
                                txt = self.ui.chat_text
                                self.ui.chat_text = ""
                                self.submit_chat(txt)
                            else:
                                self.ui.close_chat()
                    else:
                        if ev.key == pygame.K_ESCAPE:
                            if self.ui.settings:
                                self.ui.settings = False
                                self.ui.confirm_reset = False
                                self.persist()
                            elif self.ui.rps_phase is not None:
                                self.ui.close_rps()
                        elif not self.ui.settings and ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_t):
                            self.ui.open_chat()
                            if ev.key == pygame.K_t:
                                self._skip_next_textinput = True
                elif ev.type == pygame.MOUSEBUTTONDOWN:
                    if ev.button == 1:
                        self.on_lmb_down(ev.pos[0] / sc, ev.pos[1] / sc)
                    elif ev.button == 3:
                        self.on_rmb_down(ev.pos[0] / sc, ev.pos[1] / sc)
                elif ev.type == pygame.MOUSEMOTION:
                    self.mouse_in_window = True
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
