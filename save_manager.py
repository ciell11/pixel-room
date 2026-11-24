# -*- coding: utf-8 -*-
"""SaveManager: bulletproof JSON persistence with corruption recovery, stats, chat memory & backward compatibility."""
import os
import json
from constants import app_dir, clamp, OUTFIT_COUNT, ACC_COUNT


DEFAULT_SAVE = {
    "outfit": 0,
    "accessory": 0,
    "collar_relaxed": False,
    "mood": 65.0,
    "affinity_xp": 0,
    "light": 2,
    "lamp_on": True,
    "fairy_on": True,
    "curtains_closed": False,
    "poster_idx": 0,
    "weather_rain": False,
    "real_time_sync": False,
    "free_life": True,
    "music_on": False,
    "physics": 1.0,
    "volume": 0.6,
    "topmost": False,
    "scale": 0,
    "rps_wins": 0,
    "player_name": "",
    "stat_pets": 0,
    "stat_selfies": 0,
    "stat_chats": 0,
}


class SaveManager:
    def __init__(self):
        local_path = os.path.join(app_dir(), "save.json")
        appdata_path = os.path.join(
            os.getenv("APPDATA") or os.path.expanduser("~"), "PixelRoom", "save.json"
        )
        self.path = local_path if self._is_writable(app_dir()) else appdata_path
        self.data = dict(DEFAULT_SAVE)
        self.load()

    @staticmethod
    def _is_writable(folder):
        try:
            probe = os.path.join(folder, ".pixelroom_write_test")
            with open(probe, "w", encoding="utf-8") as f:
                f.write("ok")
            os.remove(probe)
            return True
        except Exception:
            return False

    @staticmethod
    def _safe_int(val, default):
        try:
            return int(val)
        except Exception:
            return default

    @staticmethod
    def _safe_float(val, default):
        try:
            v = float(val)
            return default if (v != v) else v
        except Exception:
            return default

    def load(self):
        self.data = dict(DEFAULT_SAVE)
        try:
            if os.path.exists(self.path):
                with open(self.path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    for k in DEFAULT_SAVE:
                        if k in loaded:
                            self.data[k] = loaded[k]
        except Exception:
            self.data = dict(DEFAULT_SAVE)
        self._sanitize()
        return self.data

    def _sanitize(self):
        d = self.data
        d["outfit"] = self._safe_int(d.get("outfit"), 0) % OUTFIT_COUNT
        d["accessory"] = self._safe_int(d.get("accessory"), 0) % ACC_COUNT
        d["collar_relaxed"] = bool(d.get("collar_relaxed", False))
        d["mood"] = float(clamp(self._safe_float(d.get("mood"), 65.0), 0.0, 100.0))
        d["affinity_xp"] = max(0, self._safe_int(d.get("affinity_xp"), 0))
        d["light"] = int(clamp(self._safe_int(d.get("light"), 2), 0, 3))
        d["lamp_on"] = bool(d.get("lamp_on", True))
        d["fairy_on"] = bool(d.get("fairy_on", True))
        d["curtains_closed"] = bool(d.get("curtains_closed", False))
        d["poster_idx"] = self._safe_int(d.get("poster_idx"), 0) % 3
        d["weather_rain"] = bool(d.get("weather_rain", False))
        d["real_time_sync"] = bool(d.get("real_time_sync", False))
        d["free_life"] = bool(d.get("free_life", True))
        d["music_on"] = bool(d.get("music_on", False))
        d["physics"] = round(float(clamp(self._safe_float(d.get("physics"), 1.0), 0.0, 1.5)), 2)
        d["volume"] = round(float(clamp(self._safe_float(d.get("volume"), 0.6), 0.0, 1.0)), 2)
        d["topmost"] = bool(d.get("topmost", False))
        d["scale"] = max(0, self._safe_int(d.get("scale"), 0))
        d["rps_wins"] = max(0, self._safe_int(d.get("rps_wins"), 0))
        pn = d.get("player_name", "")
        d["player_name"] = str(pn).strip()[:20] if isinstance(pn, str) else ""
        d["stat_pets"] = max(0, self._safe_int(d.get("stat_pets"), 0))
        d["stat_selfies"] = max(0, self._safe_int(d.get("stat_selfies"), 0))
        d["stat_chats"] = max(0, self._safe_int(d.get("stat_chats"), 0))

    def save(self):
        self._sanitize()
        try:
            parent = os.path.dirname(self.path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            os.replace(tmp, self.path)
        except Exception:
            pass

    def reset_defaults(self, keep_scale=None):
        self.data = dict(DEFAULT_SAVE)
        if keep_scale is not None:
            self.data["scale"] = keep_scale
        self.save()
        return self.data
