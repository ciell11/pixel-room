"""Build PixelRoom.exe (single file, windowed, 640x360 high-bit assets bundled).
Run: py build.py
"""
import os
import struct
import subprocess
import sys

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, here)
import generate_assets
import pixelroom as pr

# Ensure high-bit PNG assets are fresh
generate_assets.generate_all()

# Make icon.ico (PNG-in-ICO) from the pixel heart
pygame.init()
img = pygame.transform.scale(pr.pattern_surface(pr.HEART_P, {"#": pr.PINK, "+": pr.WHITE}, scale=4), (64, 64))
png = os.path.join(here, "icon.png")
pygame.image.save(img, png)
data = open(png, "rb").read()
with open(os.path.join(here, "icon.ico"), "wb") as f:
    f.write(struct.pack("<HHH", 0, 1, 1))
    f.write(struct.pack("<BBBBHHII", 64, 64, 0, 0, 1, 32, len(data), 22))
    f.write(data)
os.remove(png)

subprocess.check_call([
    sys.executable, "-m", "PyInstaller",
    "--noconfirm", "--clean", "--onefile", "--windowed",
    "--name", "PixelRoom",
    "--icon", "icon.ico",
    "--add-data", "assets;assets",
    "--exclude-module", "numpy",
    "--exclude-module", "PIL",
    "--exclude-module", "tkinter",
    "pixelroom.py",
], cwd=here)
print("Built:", os.path.join(here, "dist", "PixelRoom.exe"))
