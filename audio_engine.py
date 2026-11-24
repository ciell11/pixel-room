# -*- coding: utf-8 -*-
"""AudioEngine: smooth, clipping-free 16-bit procedural SFX synthesizer."""
import math
import random
import array
import pygame
from constants import SR, clamp


def synth_tone(f0, f1, dur, wave="tri", vol=0.25, vib=0.0, attack=0.008, lp_alpha=0.35):
    """Synthesize a warm, smoothed, soft-clipped 16-bit mono sound segment."""
    n = max(1, int(SR * dur))
    out = array.array("h", [0]) * n
    ph = 0.0
    lp = 0.0
    rnd = random.Random(int(f0 * 17 + dur * 1000))
    for i in range(n):
        t = i / SR
        p = i / n
        f = f0 + (f1 - f0) * p
        if vib:
            f *= 1.0 + 0.04 * math.sin(6.283185 * vib * t)
        ph += f / SR
        fr = ph % 1.0
        if wave == "sq":
            raw = 0.7 if fr < 0.5 else -0.7
        elif wave == "tri":
            raw = 4.0 * abs(fr - 0.5) - 1.0
        elif wave == "sine":
            raw = math.sin(6.283185 * fr)
        elif wave == "noise":
            raw = rnd.uniform(-1.0, 1.0)
        else:
            raw = math.sin(6.283185 * fr) * 0.7 + (4.0 * abs(fr - 0.5) - 1.0) * 0.3

        # Smooth one-pole low-pass filter removes harsh digital edges
        lp += (raw - lp) * lp_alpha
        # Smooth Hann-like attack & curved decay (zero pop/click at endpoints)
        env_in = min(1.0, t / max(0.002, attack))
        env_out = min(1.0, (1.0 - p) * 14.0) * ((1.0 - p) ** 1.45)
        sample = math.tanh(lp * env_in * env_out * vol * 1.45)
        out[i] = int(clamp(sample, -0.95, 0.95) * 31000)
    return out


def concat_pcm(*parts):
    res = array.array("h")
    for p in parts:
        res.extend(p)
    return res


def mix_pcm(*parts):
    n = max(len(p) for p in parts)
    out = array.array("h", [0]) * n
    for i in range(n):
        acc = 0.0
        for p in parts:
            if i < len(p):
                acc += p[i] / 32000.0
        out[i] = int(clamp(math.tanh(acc), -0.95, 0.95) * 31000)
    return out


class AudioEngine:
    def __init__(self, initial_volume=0.6):
        self.ok = pygame.mixer.get_init() is not None
        self.sounds = {}
        self.blips = []
        if not self.ok:
            return

        mk = lambda pcm: pygame.mixer.Sound(buffer=pcm.tobytes())
        # UI & clicks (warm woody square/tri blend)
        self.sounds["click"] = mk(synth_tone(920, 680, 0.04, "tri", 0.24, attack=0.004, lp_alpha=0.45))
        self.sounds["pop"] = mk(synth_tone(640, 260, 0.085, "tri", 0.28, attack=0.004, lp_alpha=0.5))
        self.sounds["boing"] = mk(synth_tone(190, 520, 0.20, "tri", 0.38, vib=14, attack=0.008, lp_alpha=0.4))
        self.sounds["snap"] = mk(synth_tone(280, 620, 0.13, "tri", 0.30, vib=18, attack=0.005, lp_alpha=0.45))

        # Soft pillow muffled thump + plush rustle
        self.sounds["pillow"] = mk(mix_pcm(
            synth_tone(135, 62, 0.13, "sine", 0.52, attack=0.005, lp_alpha=0.35),
            synth_tone(0, 0, 0.10, "noise", 0.22, attack=0.008, lp_alpha=0.14),
        ))

        # Pleasant gentle headpat chime + warm purr undertone
        self.sounds["headpat"] = mk(mix_pcm(
            concat_pcm(
                synth_tone(784, 880, 0.055, "sine", 0.22, attack=0.01, lp_alpha=0.5),
                synth_tone(1046, 1175, 0.10, "sine", 0.22, attack=0.01, lp_alpha=0.5),
            ),
            synth_tone(196, 210, 0.14, "sine", 0.12, vib=12, attack=0.02, lp_alpha=0.25),
        ))

        # Smooth fabric curtain slide & wooden wardrobe creak/whoosh
        self.sounds["curtain"] = mk(synth_tone(0, 0, 0.24, "noise", 0.26, attack=0.05, lp_alpha=0.12))
        self.sounds["wardrobe"] = mk(mix_pcm(
            synth_tone(160, 225, 0.16, "tri", 0.22, attack=0.02, lp_alpha=0.20),
            synth_tone(0, 0, 0.22, "noise", 0.24, attack=0.05, lp_alpha=0.14),
        ))
        self.sounds["drawer"] = mk(mix_pcm(
            synth_tone(195, 130, 0.11, "tri", 0.28, attack=0.01, lp_alpha=0.25),
            synth_tone(0, 0, 0.11, "noise", 0.18, attack=0.015, lp_alpha=0.15),
        ))
        self.sounds["page"] = mk(synth_tone(0, 0, 0.11, "noise", 0.24, attack=0.012, lp_alpha=0.28))

        # Bubble tea pleasant sip + pop
        self.sounds["sip"] = mk(concat_pcm(
            synth_tone(420, 740, 0.09, "sine", 0.24, attack=0.01, lp_alpha=0.45),
            synth_tone(580, 960, 0.12, "sine", 0.25, attack=0.01, lp_alpha=0.45),
        ))

        # Retro camera mechanical shutter + flash pop!
        self.sounds["shutter"] = mk(concat_pcm(
            synth_tone(0, 0, 0.035, "noise", 0.42, attack=0.002, lp_alpha=0.55),
            synth_tone(1600, 900, 0.03, "tri", 0.26, attack=0.002, lp_alpha=0.5),
            synth_tone(440, 1280, 0.12, "sine", 0.16, attack=0.02, lp_alpha=0.4),
        ))

        self.sounds["lamp"] = mk(concat_pcm(
            synth_tone(1650, 1150, 0.018, "tri", 0.20, attack=0.002, lp_alpha=0.5),
            synth_tone(320, 290, 0.05, "sine", 0.12, attack=0.005, lp_alpha=0.35),
        ))
        self.sounds["land"] = mk(synth_tone(145, 52, 0.12, "sine", 0.46, attack=0.004, lp_alpha=0.35))
        self.sounds["sparkle"] = mk(concat_pcm(
            synth_tone(1046, 1046, 0.045, "sine", 0.22, attack=0.006),
            synth_tone(1318, 1318, 0.045, "sine", 0.22, attack=0.006),
            synth_tone(1568, 1568, 0.09, "sine", 0.24, attack=0.006),
        ))

        # RPS minigame SFX
        self.sounds["rps_tick"] = mk(synth_tone(587, 620, 0.06, "tri", 0.26, attack=0.004, lp_alpha=0.5))
        self.sounds["rps_win"] = mk(concat_pcm(
            synth_tone(523, 523, 0.06, "tri", 0.26, attack=0.005),
            synth_tone(659, 659, 0.06, "tri", 0.26, attack=0.005),
            synth_tone(784, 784, 0.06, "tri", 0.26, attack=0.005),
            synth_tone(1046, 1046, 0.14, "sine", 0.28, attack=0.008),
        ))
        self.sounds["rps_lose"] = mk(concat_pcm(
            synth_tone(440, 415, 0.08, "tri", 0.24, attack=0.006),
            synth_tone(349, 311, 0.14, "tri", 0.24, attack=0.008),
        ))

        # Soft voice blips for speech bubble typewriter
        self.blips = [
            mk(synth_tone(f, f * 1.06, 0.035, "tri", 0.11, attack=0.004, lp_alpha=0.4))
            for f in (510, 575, 640, 710, 780)
        ]
        self.set_volume(initial_volume)

    def set_volume(self, v):
        vol = clamp(float(v), 0.0, 1.0)
        for snd in list(self.sounds.values()) + self.blips:
            snd.set_volume(vol)

    def play(self, name):
        if self.ok and name in self.sounds:
            self.sounds[name].play()

    def blip(self):
        if self.ok and self.blips:
            random.choice(self.blips).play()
