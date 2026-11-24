# Pixel Room — Marin Kitagawa (`v0.6-beta` — Marin Art Overhaul)

A cozy 16-bit interactive pixel-art desktop room & companion featuring **Marin Kitagawa** from *My Dress-Up Darling* (*Sono Bisque Doll wa Koi wo Suru*), built with Python + Pygame-CE (native `640×360` with pixel-perfect DPI-aware Nearest-Neighbor `1x`/`2x`/`3x` scaling, material-aware *sel-out* colored outlines, Bayer-dithered lighting, offline Russian/English Chat, Cozy Rain weather, and clamped multi-layer spring-damper physics).

> **Download Windows Standalone `.exe` (No Python required):** grab `PixelRoom.exe` directly from the **[Releases](../../releases)** tab!
>
> *Unofficial non-commercial fan project. Marin Kitagawa and My Dress-Up Darling belong to Shinichi Fukuda / Square Enix.*

---

## Screenshots

| Canon Relaxed Shirt, Blushing Wink & Chat | Floor-Sitting Manga & Rainy Night Window | Polaroid Selfie & Bed Smartphone Pose |
| :---: | :---: | :---: |
| ![Canon Shirt, Wink & Chat](screenshots/cute_chat_home.png) | ![Floor Manga & Rain](screenshots/floor_manga_rain.png) | ![Polaroid & Cozy Bed Pose](screenshots/polaroid_dance_rain.png) |

---

## What's New in `v0.6-beta` (*Marin Art Overhaul*)

- **Complete Commercial-Grade 16-Bit Sprite Redesign:** Marin's entire multi-layer character rig (`generate_assets.py`) has been redrawn from scratch to modern visual-novel / indie pixel-art standards (*VA-11 Hall-A* / *Stardew Valley* inspired).
- **Voluminous S-Wave Hair & Organic Coral-Pink Ombre:** replaced stiff triangular hair and jagged bangs with flowing S-curved ribbon locks, split wispy side strands, canon overlapping forelocks with Marin's signature center strand, a curved broken angel-halo highlight, and a 10-step golden-blonde → coral-pink ombre.
- **Graceful Anatomy, Tailored Proportions & Dainty Hands:** sloped shoulders, natural bust drape, pinched hourglass waist, sleek `4px` tailored neckties (`tie` & `tie_loose`), slender `4px` forearms with wrist bangles and open dainty hands (no boxy fists!), and smooth tapered legs with detailed loafers, plush coral slippers, striped *zettai ryouiki* thigh-highs, and street sneakers.
- **Hue-Shifted Shading & Material-Aware Directional `sel-out`:** warm peach-cream skin with rosy-terracotta shadows, cool periwinkle-lavender shading on white shirts, honey-amber hair shadows, and material-aware colored outlines with softer top-left lit edges.
- **All 5 Outfits + Relaxed Variants & Polished Poses:** every outfit (`0` School, `1` Home Knot Shirt, `2` Oversized Lavender Hoodie, `3` Mint Ringer Streetwear, `4` Canon Relaxed Short-Sleeve Shirt) now includes both standard and relaxed/open-neckline variants, plus refined `bed_phone`, *yokozuwari* `read_manga` / `manga_turn`, `collar`, `stretch`, and a playful blushing **wink (`>`)** expression!

---

## Controls

- **Chat with Marin (`Enter` / `T` or Chat Bubble icon):** type anything in Russian or English (full Cyrillic support + 4 one-click Quick Reply chips!) — flirt, give compliments, tell her your name (`"Меня зовут ..."`), talk about anime/cosplay, or give room commands (`"включи музыку"`, `"включи дождь"`, `"почитай мангу"`, `"сядь на кровать"`, `"переоденься"`, `"давай поиграем"`, `"жарко тут"`).
- **LMB (Drag / Pull / Drop on Bed / Toss):** grab & toss Marin — or **drop her onto the bed** so she sits dangling her legs with her smartphone! Pull her arms, hair, tie, skirt, or cheek like elastic springs; throw the bed pillow (**throw it 2 times and she catches it & fires it back!**); feed bubble tea; or drag **cosplay glasses**, the **candy/gift box**, and the **retro camera** (with **Polaroid selfie card!**) out of the nightstand drawers.
- **RMB (Hold & Move on Head):** gentle headpat with a custom pixel heart-hand cursor — builds Mood & **Affinity (Lv.1 → Lv.5)**.
- **Click Room Objects (1px hover outlines):** click the **open window glass** or **Rain icon** for Cozy Rain, slide **curtains**, toggle **Fairy Lights** and **table lamp**, open the **wardrobe** (5 outfits), swap **wall posters** (3 designs), open **nightstand drawers**, bounce the **laundry basket**, or click the **floor manga** so Marin sits on the rug to read!
- **Corner Icons:** Settings (`0–150%` physics, volume, *Always on Top*, **Free Life AI**, **Cozy Rain**, **Real-Time Clock Lighting Sync**, **Mini-Stats**, window scale, Reset Pose, Reset Progress), Wardrobe, Accessories, Lighting, **16-bit Lo-Fi Music**, **Weather (Rain)**, **Rock-Paper-Scissors**, **Chat**, 10 Emotions, and Wave.

---

## Run from Source

```bash
pip install -r requirements.txt
python generate_assets.py
python pixelroom.py
```

To build a single-file Windows `.exe`:

```bash
python build.py
```
