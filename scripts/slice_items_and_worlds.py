import os
import numpy as np
from PIL import Image

BRAIN_DIR = r"C:\Users\mattu\.gemini\antigravity\brain\62d8ba8d-f8cc-4638-843c-c985cfff8617"
PROJECT_ROOT = r"c:\Users\mattu\Documents\MyProjects\pokemon-games"
ICONS_DIR = os.path.join(PROJECT_ROOT, "assets", "icons")
ITEMS_DIR = os.path.join(PROJECT_ROOT, "assets", "items")
SAGASE_ASSETS = os.path.join(PROJECT_ROOT, "sagase", "assets")

for d in [ICONS_DIR, ITEMS_DIR, SAGASE_ASSETS]:
    os.makedirs(d, exist_ok=True)

def find_dividers(img_arr):
    h, w, _ = img_arr.shape
    gray = img_arr.mean(axis=2)
    def best_line(profile, approx):
        lo = max(0, int(approx - len(profile) * 0.05))
        hi = min(len(profile), int(approx + len(profile) * 0.05))
        return lo + int(np.argmin(profile[lo:hi]))
    x1 = best_line(gray.mean(axis=0), w / 3.0)
    x2 = best_line(gray.mean(axis=0), 2.0 * w / 3.0)
    y1 = best_line(gray.mean(axis=1), h / 3.0)
    y2 = best_line(gray.mean(axis=1), 2.0 * h / 3.0)
    return [0, x1, x2, w], [0, y1, y2, h]

def main():
    sheet_path = os.path.join(BRAIN_DIR, "game_items_3x3_notext_1794898250427.jpg")
    img = Image.open(sheet_path).convert("RGB")
    xs, ys = find_dividers(np.array(img))
    pad = max(6, int(img.width * 0.01))

    names = [
        "pokeball_roulette", "masterball", "three_balls",
        "berries", "pokecenter", "trophy_goal",
        "rocket_balloon", "explosion_trap", "thunder_orb",
    ]
    idx = 0
    for r in range(3):
        for c in range(3):
            nm = names[idx]
            idx += 1
            left = xs[c] + (pad if c > 0 else pad // 2)
            right = xs[c + 1] - (pad if c < 2 else pad // 2)
            top = ys[r] + (pad if r > 0 else pad // 2)
            bottom = ys[r + 1] - (pad if r < 2 else pad // 2)
            crop = img.crop((left, top, right, bottom))

            if nm == "pokeball_roulette":
                crop.resize((512, 512), Image.Resampling.LANCZOS).save(os.path.join(ICONS_DIR, "icon-512.png"), "PNG", optimize=True)
                crop.resize((192, 192), Image.Resampling.LANCZOS).save(os.path.join(ICONS_DIR, "icon-192.png"), "PNG", optimize=True)
                crop.resize((180, 180), Image.Resampling.LANCZOS).save(os.path.join(ICONS_DIR, "apple-touch-icon.png"), "PNG", optimize=True)

            crop.resize((360, 360), Image.Resampling.LANCZOS).save(
                os.path.join(ITEMS_DIR, f"{nm}.webp"), "WEBP", quality=87, method=6
            )

    worlds = [
        ("world_forest_1794898220818.jpg", "world_forest.webp"),
        ("world_beach_1794898234005.jpg", "world_beach.webp"),
        ("world_carnival_1794898245217.jpg", "world_carnival.webp"),
        ("world_temple_v2_1794898283107.jpg", "world_temple.webp"),
    ]
    for src_fn, dst_fn in worlds:
        wimg = Image.open(os.path.join(BRAIN_DIR, src_fn)).convert("RGB")
        # Save crisp 1920x1080 panoramic WebP
        wimg = wimg.resize((1920, 1080), Image.Resampling.LANCZOS)
        wimg.save(os.path.join(SAGASE_ASSETS, dst_fn), "WEBP", quality=86, method=6)

    print("Sliced 9 game items + 3 PWA icons + 4 HD panoramic worlds!")

if __name__ == "__main__":
    main()
