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


def build_lofi_loop():
    """Generate a seamless, click-free 16-bit chill lo-fi accompaniment loop (~5.33s, 90 BPM)."""
    bpm = 90.0
    beat_sec = 60.0 / bpm
    total_beats = 8
    n = int(SR * beat_sec * total_beats)
    buf = [0.0] * n
    two_pi = 6.2831853

    # Warm mellow electric-piano chord progression: Fmaj7 -> Em7 -> Dm7 -> Cmaj7
    chords = [
        (174.61, 220.00, 261.63, 329.63),
        (164.81, 196.00, 246.94, 293.66),
        (146.83, 174.61, 220.00, 261.63),
        (130.81, 164.81, 196.00, 246.94),
    ]
    clen = n // 4
    for ci, notes in enumerate(chords):
        s0 = ci * clen
        for i in range(clen):
            t = i / SR
            p = i / clen
            # Smooth fade-in & fade-out per chord guarantees zero clicks
            env = min(1.0, t / 0.05) * min(1.0, (1.0 - p) * 16.0) * ((1.0 - p * 0.68) ** 1.25)
            v = 0.0
            for f in notes:
                wob = 1.0 + 0.0018 * math.sin(two_pi * 2.0 * t)
                v += math.sin(two_pi * f * wob * t) * 0.22
                v += math.sin(two_pi * f * 2.0 * wob * t) * 0.025
            buf[s0 + i] += v * env * 0.30

    # Soft muffled kick & gentle brushed snare
    bsamp = int(SR * beat_sec)
    rnd = random.Random(108)
    for b in (0.0, 2.0, 3.5, 4.0, 6.0):
        s0 = int(b * bsamp)
        klen = int(SR * 0.14)
        for i in range(klen):
            idx = (s0 + i) % n
            t = i / SR
            p = i / klen
            f = 105.0 * ((1.0 - p) ** 2.2) + 42.0
            env = min(1.0, t / 0.006) * ((1.0 - p) ** 2.0)
            buf[idx] += math.sin(two_pi * f * t) * env * 0.34
    for b in (1.0, 3.0, 5.0, 7.0):
        s0 = int(b * bsamp)
        slen = int(SR * 0.085)
        lp = 0.0
        for i in range(slen):
            idx = (s0 + i) % n
            p = i / slen
            lp += (rnd.uniform(-1.0, 1.0) - lp) * 0.22
            env = min(1.0, p * 16.0) * ((1.0 - p) ** 2.3)
            buf[idx] += lp * env * 0.16

    # Gentle low-pass + crossfade seam (first/last 400 samples) for a 100% click-free loop!
    lp = 0.0
    for i in range(n):
        lp += (buf[i] - lp) * 0.28
        buf[i] = math.tanh(lp * 1.2)
    seam = 400
    for i in range(seam):
        w = i / float(seam)
        buf[i] = buf[i] * w + buf[n - seam + i] * (1.0 - w)

    out = array.array("h", [int(clamp(x, -0.92, 0.92) * 30000) for x in buf])
    return pygame.mixer.Sound(buffer=out.tobytes())


def build_rain_loop():
    """Generate a very quiet, warm, heavily muffled rain-behind-window loop (~4.0s) with true overlap-add seamless loop."""
    dur = 4.0
    n = int(SR * dur)
    seam = 2000
    total = n + seam
    buf = [0.0] * total
    rnd = random.Random(2026)
    lp1 = lp2 = lp3 = 0.0
    # Warm-up filter so sample 0 starts smoothly at steady-state
    for _ in range(512):
        w = rnd.uniform(-1.0, 1.0)
        lp1 += (w - lp1) * 0.055
        lp2 += (lp1 - lp2) * 0.038
        lp3 += (lp2 - lp3) * 0.028

    for i in range(total):
        w = rnd.uniform(-1.0, 1.0)
        # 3-stage deep low-pass strips harsh high hissing -> cozy muffled rain outside a closed glass window!
        lp1 += (w - lp1) * 0.055
        lp2 += (lp1 - lp2) * 0.038
        lp3 += (lp2 - lp3) * 0.028
        swell = 0.90 + 0.10 * math.sin(6.2831853 * ((i % n) / float(n)))
        buf[i] = lp3 * 0.55 * swell

    # Rare, very quiet, delicate soft glass raindrop taps (strictly inside middle of loop)
    for _ in range(8):
        s0 = rnd.randint(seam + 400, n - seam - 400)
        dlen = int(SR * 0.026)
        f0 = rnd.uniform(420.0, 680.0)
        for j in range(dlen):
            p = j / dlen
            env = min(1.0, p * 10.0) * ((1.0 - p) ** 2.6)
            buf[s0 + j] += math.sin(6.2831853 * f0 * (1.0 - 0.15 * p) * (j / SR)) * env * 0.022

    # True tail-to-head Hann crossfade: sample[0] continues directly from sample[n-1] -> ZERO loop click!
    for i in range(seam):
        w = 0.5 - 0.5 * math.cos(math.pi * i / float(seam))
        buf[i] = buf[i] * w + buf[n + i] * (1.0 - w)

    out = array.array("h", [int(clamp(math.tanh(x * 0.9), -0.85, 0.85) * 30000) for x in buf[:n]])
    return pygame.mixer.Sound(buffer=out.tobytes())


class AudioEngine:
    def __init__(self, initial_volume=0.6):
        self.ok = pygame.mixer.get_init() is not None
        self.sounds = {}
        self.blips = []
        self.lofi = None
        self.lofi_ch = None
        self.rain = None
        self.rain_ch = None
        self.vol = initial_volume
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
        self.sounds["cloth"] = mk(mix_pcm(
            synth_tone(0, 0, 0.15, "noise", 0.20, attack=0.025, lp_alpha=0.16),
            synth_tone(480, 620, 0.06, "sine", 0.12, attack=0.01, lp_alpha=0.4),
        ))

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

        # v0.3-beta Romantic & Cozy SFX: fairy lights twinkle, gift unwrap, Affinity level-up chord!
        self.sounds["fairy"] = mk(concat_pcm(
            synth_tone(1318, 1397, 0.045, "sine", 0.18, attack=0.008, lp_alpha=0.5),
            synth_tone(1760, 1975, 0.09, "sine", 0.18, attack=0.008, lp_alpha=0.5),
        ))
        self.sounds["gift"] = mk(concat_pcm(
            synth_tone(659, 784, 0.055, "tri", 0.24, attack=0.006, lp_alpha=0.5),
            synth_tone(987, 1175, 0.06, "sine", 0.24, attack=0.006, lp_alpha=0.5),
            synth_tone(1318, 1568, 0.12, "sine", 0.26, attack=0.008, lp_alpha=0.5),
        ))
        self.sounds["level_up"] = mk(mix_pcm(
            concat_pcm(
                synth_tone(523, 523, 0.07, "sine", 0.22, attack=0.01),
                synth_tone(659, 659, 0.07, "sine", 0.22, attack=0.01),
                synth_tone(784, 784, 0.07, "sine", 0.22, attack=0.01),
                synth_tone(987, 987, 0.08, "sine", 0.22, attack=0.01),
                synth_tone(1175, 1175, 0.24, "sine", 0.24, attack=0.015),
            ),
            synth_tone(261.6, 261.6, 0.48, "sine", 0.16, attack=0.03, lp_alpha=0.35),
        ))

        # Soft voice blips for speech bubble typewriter
        self.blips = [
            mk(synth_tone(f, f * 1.06, 0.035, "tri", 0.11, attack=0.004, lp_alpha=0.4))
            for f in (510, 575, 640, 710, 780)
        ]
        self.set_volume(initial_volume)

    def set_volume(self, v):
        vol = clamp(float(v), 0.0, 1.0)
        self.vol = vol
        for snd in list(self.sounds.values()) + self.blips:
            snd.set_volume(vol)
        if self.lofi:
            self.lofi.set_volume(vol * 0.50)
        if self.rain:
            self.rain.set_volume(vol * 0.11)

    def set_music(self, enabled):
        if not self.ok:
            return
        if enabled:
            if self.lofi is None:
                self.lofi = build_lofi_loop()
            self.lofi.set_volume(self.vol * 0.50)
            if self.lofi_ch is None or not self.lofi_ch.get_busy():
                self.lofi_ch = self.lofi.play(loops=-1)
        elif self.lofi_ch:
            self.lofi_ch.stop()
            self.lofi_ch = None

    def set_rain(self, enabled):
        if not self.ok:
            return
        if enabled:
            if self.rain is None:
                self.rain = build_rain_loop()
            self.rain.set_volume(self.vol * 0.11)
            if self.rain_ch is None or not self.rain_ch.get_busy():
                self.rain_ch = self.rain.play(loops=-1)
        elif self.rain_ch:
            self.rain_ch.stop()
            self.rain_ch = None

    def play(self, name):
        if self.ok and name in self.sounds:
            self.sounds[name].play()

    def blip(self):
        if self.ok and self.blips:
            random.choice(self.blips).play()
