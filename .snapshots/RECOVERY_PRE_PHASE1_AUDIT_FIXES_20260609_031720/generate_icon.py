"""
Universal Clipboard — Icon Generator
Generates ic_launcher.png at all Android mipmap sizes and a 512px master.
Also creates the desktop tray icon (assets/icon.png).
Run from the repo root:  python generate_icon.py
"""
import os
import math
from PIL import Image, ImageDraw, ImageFont

# ── Sizes ──────────────────────────────────────────────────────────────────────
MIPMAP_SIZES = {
    "mipmap-mdpi":    48,
    "mipmap-hdpi":    72,
    "mipmap-xhdpi":   96,
    "mipmap-xxhdpi":  144,
    "mipmap-xxxhdpi": 192,
}
MASTER_SIZE  = 512
RES_DIR      = os.path.join("android", "app", "src", "main", "res")
ASSETS_DIR   = os.path.join("desktop", "assets")


def draw_icon(size: int) -> Image.Image:
    """Draw the clipboard icon at the given pixel size."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # ── Background: rounded square, deep blue-purple gradient ──────────────────
    radius = size // 6
    # Simulate gradient: top=#1a1a2e, bottom=#16213e
    for y in range(size):
        t = y / size
        r = int(26  + t * (22  - 26))
        g = int(26  + t * (33  - 26))
        b = int(46  + t * (62  - 46))
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

    # Clip gradient to rounded square
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    img.putalpha(mask)

    # ── Clipboard body ─────────────────────────────────────────────────────────
    pad  = size * 0.14
    cb_l = int(pad)
    cb_t = int(size * 0.22)
    cb_r = int(size - pad)
    cb_b = int(size * 0.88)
    cr   = size // 12  # corner radius of clipboard

    # Shadow
    shadow_offset = max(2, size // 60)
    draw.rounded_rectangle(
        [cb_l + shadow_offset, cb_t + shadow_offset, cb_r + shadow_offset, cb_b + shadow_offset],
        radius=cr, fill=(0, 0, 0, 80)
    )
    # Body
    draw.rounded_rectangle([cb_l, cb_t, cb_r, cb_b], radius=cr, fill=(255, 255, 255, 240))

    # ── Clipboard clip (top center bar) ────────────────────────────────────────
    clip_w  = size * 0.30
    clip_h  = size * 0.09
    clip_l  = (size - clip_w) / 2
    clip_t  = size * 0.15
    clip_r  = clip_l + clip_w
    clip_b  = clip_t + clip_h
    clip_cr = clip_h / 2
    draw.rounded_rectangle([clip_l, clip_t, clip_r, clip_b], radius=clip_cr,
                            fill=(255, 255, 255, 255), outline=(180, 190, 210, 255),
                            width=max(1, size // 60))

    # ── Content lines on clipboard ─────────────────────────────────────────────
    lx1 = cb_l + size * 0.10
    lx2 = cb_r - size * 0.10
    line_color = (160, 170, 195, 200)
    lw  = max(1, size // 50)
    for i, y_frac in enumerate([0.52, 0.63, 0.73]):
        y = int(size * y_frac)
        # Shorter last line for realism
        x2 = lx2 if i < 2 else lx1 + (lx2 - lx1) * 0.55
        draw.rounded_rectangle([int(lx1), y - lw, int(x2), y + lw],
                               radius=lw, fill=line_color)

    # ── Lightning bolt (bottom-right, cyan glow) ──────────────────────────────
    bolt_cx = int(size * 0.735)
    bolt_cy = int(size * 0.735)
    bolt_r  = int(size * 0.175)

    # Glow rings
    for glow in range(3, 0, -1):
        alpha = 40 + glow * 15
        gr = bolt_r + glow * (size // 40)
        draw.ellipse([bolt_cx - gr, bolt_cy - gr, bolt_cx + gr, bolt_cy + gr],
                     fill=(0, 212, 255, alpha))

    # Circle background
    draw.ellipse([bolt_cx - bolt_r, bolt_cy - bolt_r, bolt_cx + bolt_r, bolt_cy + bolt_r],
                 fill=(0, 30, 60, 230))
    draw.ellipse([bolt_cx - bolt_r + 1, bolt_cy - bolt_r + 1,
                  bolt_cx + bolt_r - 1, bolt_cy + bolt_r - 1],
                 outline=(0, 212, 255, 200), width=max(1, size // 55))

    # Lightning bolt shape (polygon)
    s = bolt_r * 0.55
    bolt_pts = [
        (bolt_cx +  0.08 * s * 2, bolt_cy - 1.0 * s),
        (bolt_cx - 0.35 * s * 2, bolt_cy + 0.10 * s),
        (bolt_cx + 0.05 * s * 2, bolt_cy + 0.10 * s),
        (bolt_cx - 0.08 * s * 2, bolt_cy + 1.0 * s),
        (bolt_cx + 0.45 * s * 2, bolt_cy - 0.10 * s),
        (bolt_cx - 0.05 * s * 2, bolt_cy - 0.10 * s),
    ]
    draw.polygon(bolt_pts, fill=(0, 212, 255, 255))

    return img


def save_icon(img: Image.Image, path: str):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    img.save(path, "PNG")
    print(f"  OK  {path}  ({img.width}x{img.height})")


def main():
    print("\nGenerating Universal Clipboard icons...\n")

    # Master 512px
    master = draw_icon(MASTER_SIZE)
    save_icon(master, os.path.join(ASSETS_DIR, "icon.png"))
    save_icon(master, "icon_512.png")

    # Android mipmap sizes (normal + round — same image)
    for folder, size in MIPMAP_SIZES.items():
        icon = draw_icon(size)
        base = os.path.join(RES_DIR, folder)
        save_icon(icon, os.path.join(base, "ic_launcher.png"))
        save_icon(icon, os.path.join(base, "ic_launcher_round.png"))

    print("\nAll icons generated successfully!\n")


if __name__ == "__main__":
    main()
