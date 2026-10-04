"""Draws the demo artwork (original characters) into layers/<Group>/<Name>.png.

Every layer is a full-canvas transparent PNG, the same way layers would be
exported from a layered PSD. Run once:  python make_layers.py
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFont

S = 2000          # drawing size (supersampled for smooth edges)
OUT_SIZE = 1000   # exported layer size
INK = (43, 34, 51, 255)
W = 14
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "layers")
BODY = (480, 700, 1520, 1780)
EYE_L, EYE_R = (820, 1000), (1180, 1000)


def canvas():
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def save(img, group, name):
    folder = os.path.join(ROOT, group)
    os.makedirs(folder, exist_ok=True)
    img = img.resize((OUT_SIZE, OUT_SIZE), Image.LANCZOS)
    img.save(os.path.join(folder, name + ".png"), optimize=True)


def circle(d, cx, cy, r, **kw):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), **kw)


def star(cx, cy, r, inner=0.45, points=5, rot=-90):
    pts = []
    for i in range(points * 2):
        rr = r if i % 2 == 0 else r * inner
        a = math.radians(rot + i * 180 / points)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def flower(d, cx, cy, r, color, center="#ffd23f"):
    for i in range(5):
        a = math.radians(-90 + i * 72)
        circle(d, cx + r * math.cos(a), cy + r * math.sin(a), r * 0.62,
               fill=color, outline=INK, width=8)
    circle(d, cx, cy, r * 0.5, fill=center, outline=INK, width=8)


# ---------------------------------------------------------------- Background
def backgrounds():
    for name, color in {"Sky": "#bfe3ff", "Mint": "#c9f2dc",
                        "Peach": "#ffd9c2", "Lilac": "#e0d4ff"}.items():
        save(Image.new("RGBA", (S, S), color), "Background", name)

    grad = Image.linear_gradient("L").resize((S, S))
    top = Image.new("RGBA", (S, S), "#ff9a8b")
    bottom = Image.new("RGBA", (S, S), "#ffd86f")
    save(Image.composite(bottom, top, grad), "Background", "Sunset")

    img = Image.new("RGBA", (S, S), "#fff3c4")
    d = ImageDraw.Draw(img)
    for row, y in enumerate(range(100, S, 200)):
        for x in range(100 + (row % 2) * 100, S, 200):
            circle(d, x, y, 36, fill="#ffe08a")
    save(img, "Background", "Polka")

    img = Image.new("RGBA", (S, S), "#1d2545")
    d = ImageDraw.Draw(img)
    rng = random.Random(7)
    for _ in range(70):
        x, y = rng.randrange(S), rng.randrange(S)
        if rng.random() < 0.25:
            d.polygon(star(x, y, rng.randint(18, 30)), fill="#fff4b8")
        else:
            circle(d, x, y, rng.randint(4, 9), fill="#ffffff")
    save(img, "Background", "Night")


# ---------------------------------------------------------------------- Body
def bodies():
    colors = {"Cream": ("#f6e3c5", "#fff6e6"), "Honey": ("#e9a94b", "#f8d99a"),
              "Mint": ("#8fd9b6", "#d3f4e4"), "Blue": ("#7fb2f0", "#cfe3fb"),
              "Pink": ("#f49ac1", "#fbd5e5"), "Charcoal": ("#4a4a5a", "#8a8a9c"),
              "Gold": ("#f5c518", "#fff0a3")}
    for name, (base, belly) in colors.items():
        img, d = canvas()
        for box in [(600, 620, 840, 860), (1160, 620, 1400, 860)]:      # ears
            d.ellipse(box, fill=base, outline=INK, width=W)
            x0, y0, x1, y1 = box
            d.ellipse((x0 + 60, y0 + 60, x1 - 60, y1 - 60), fill=belly)
        for box in [(400, 1150, 600, 1470), (1400, 1150, 1600, 1470),   # arms
                    (620, 1690, 920, 1850), (1080, 1690, 1380, 1850)]:  # feet
            d.ellipse(box, fill=base, outline=INK, width=W)
        d.ellipse(BODY, fill=base, outline=INK, width=W)
        d.ellipse((720, 1280, 1280, 1730), fill=belly)
        save(img, "Body", name)


# ------------------------------------------------------------------- Clothes
def bow_tie(d, color, cy=1340):
    d.polygon([(1000, cy), (870, cy - 70), (870, cy + 70)], fill=color, outline=INK, width=8)
    d.polygon([(1000, cy), (1130, cy - 70), (1130, cy + 70)], fill=color, outline=INK, width=8)
    circle(d, 1000, cy, 30, fill=color, outline=INK, width=8)


def clothes():
    top = 1330

    def tee(color):
        def paint(d):
            d.rectangle((400, top, 1600, 1800), fill=color)
            d.line((400, top, 1600, top), fill=INK, width=W)
        return paint

    def striped(d):
        d.rectangle((400, top, 1600, 1800), fill="#ffffff")
        for y in range(top + 40, 1800, 110):
            d.rectangle((400, y, 1600, y + 50), fill="#2f6fd6")
        d.line((400, top, 1600, top), fill=INK, width=W)

    def hoodie(d):
        d.rectangle((400, 1280, 1600, 1800), fill="#7b5cd6")
        d.line((400, 1280, 1600, 1280), fill=INK, width=W)
        d.rounded_rectangle((820, 1520, 1180, 1680), radius=40, outline=INK, width=10)
        for x in (940, 1060):
            d.line((x, 1280, x, 1420), fill="#ffffff", width=12)
            circle(d, x, 1430, 16, fill="#ffffff")

    def overalls(d):
        d.rectangle((400, 1450, 1600, 1800), fill="#3f6fb5")
        for x in (720, 1200):
            d.polygon([(x, 1150), (x + 80, 1150), (x + 80, 1460), (x, 1460)],
                      fill="#3f6fb5", outline=INK, width=8)
            circle(d, x + 40, 1480, 22, fill="#ffd23f", outline=INK, width=6)
        d.line((400, 1450, 1600, 1450), fill=INK, width=W)
        d.rounded_rectangle((900, 1540, 1100, 1680), radius=24, outline=INK, width=10)

    def scarf(d):
        d.rectangle((1140, 1360, 1270, 1600), fill="#e23d4b", outline=INK, width=10)
        d.rounded_rectangle((400, 1270, 1600, 1380), radius=40, fill="#e23d4b",
                            outline=INK, width=10)

    def tuxedo(d):
        d.rectangle((400, top, 1600, 1800), fill="#22222c")
        d.polygon([(880, top), (1120, top), (1000, 1600)], fill="#ffffff", outline=INK, width=8)
        d.line((400, top, 1600, top), fill=INK, width=W)
        for y in (1450, 1520):
            circle(d, 1000, y, 14, fill=INK)
        bow_tie(d, "#e23d4b")

    designs = {"Tee Red": tee("#e85d5d"), "Tee Green": tee("#4fb783"),
               "Striped": striped, "Hoodie": hoodie, "Overalls": overalls,
               "Scarf": scarf, "Tuxedo": tuxedo}
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse(BODY, fill=255)
    for name, paint in designs.items():
        img, d = canvas()
        paint(d)
        out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        out.paste(img, (0, 0), mask)            # clip clothes to the body shape
        ImageDraw.Draw(out).ellipse(BODY, outline=INK, width=W)
        save(out, "Clothes", name)


# ---------------------------------------------------------------------- Eyes
def eyes():
    def dot(d, c):
        circle(d, c[0], c[1], 44, fill=INK)
        circle(d, c[0] + 14, c[1] - 14, 13, fill="#ffffff")

    def arc(d, c, up=True):
        box = (c[0] - 60, c[1] - 45, c[0] + 60, c[1] + 75) if up else \
              (c[0] - 60, c[1] - 75, c[0] + 60, c[1] + 45)
        d.arc(box, 190 if up else 10, 350 if up else 170, fill=INK, width=18)

    def wide(d, c):
        circle(d, c[0], c[1], 72, fill="#ffffff", outline=INK, width=10)
        circle(d, c[0] + 8, c[1] + 6, 32, fill=INK)

    def starry(d, c):
        d.polygon(star(c[0], c[1], 70), fill="#ffd23f", outline=INK, width=8)

    styles = {
        "Dot": lambda d: (dot(d, EYE_L), dot(d, EYE_R)),
        "Happy": lambda d: (arc(d, EYE_L), arc(d, EYE_R)),
        "Sleepy": lambda d: (arc(d, EYE_L, False), arc(d, EYE_R, False)),
        "Wide": lambda d: (wide(d, EYE_L), wide(d, EYE_R)),
        "Star": lambda d: (starry(d, EYE_L), starry(d, EYE_R)),
        "Wink": lambda d: (dot(d, EYE_L), arc(d, EYE_R)),
    }
    for name, paint in styles.items():
        img, d = canvas()
        paint(d)
        save(img, "Eyes", name)


# --------------------------------------------------------------------- Mouth
def mouths():
    def smile(d):
        d.arc((910, 1050, 1090, 1200), 20, 160, fill=INK, width=16)

    def open_(d):
        d.pieslice((920, 1060, 1080, 1220), 0, 180, fill="#8b2942", outline=INK, width=10)

    def tongue(d):
        d.ellipse((960, 1170, 1040, 1250), fill="#ff7aa2", outline=INK, width=8)
        d.rectangle((940, 1150, 1060, 1185), fill=(0, 0, 0, 0))
        smile(d)

    def flat(d):
        d.line((930, 1160, 1070, 1160), fill=INK, width=16)

    def cat(d):
        d.arc((900, 1090, 1000, 1190), 0, 180, fill=INK, width=14)
        d.arc((1000, 1090, 1100, 1190), 0, 180, fill=INK, width=14)

    def whistle(d):
        d.ellipse((965, 1125, 1035, 1205), fill="#8b2942", outline=INK, width=10)

    for name, paint in {"Smile": smile, "Open": open_, "Tongue": tongue,
                        "Flat": flat, "Cat": cat, "Whistle": whistle}.items():
        img, d = canvas()
        paint(d)
        save(img, "Mouth", name)


# ---------------------------------------------------------------------- Face
def faces():
    def glasses(d):
        for c in (EYE_L, EYE_R):
            circle(d, c[0], c[1], 105, fill=(255, 255, 255, 60), outline=INK, width=14)
        d.line((925, 1000, 1075, 1000), fill=INK, width=14)

    def sunglasses(d):
        d.line((930, 990, 1070, 990), fill=INK, width=16)
        for x in (690, 1060):
            d.rounded_rectangle((x, 920, x + 250, 1085), radius=50, fill="#1b1b24",
                                outline=INK, width=10)
            d.line((x + 50, 960, x + 110, 960), fill="#ffffff", width=12)

    def blush(d):
        for x in (630, 1230):
            d.ellipse((x, 1075, x + 140, 1150), fill=(255, 110, 150, 170))

    def freckles(d):
        for sx in (670, 1260):
            for dx, dy in ((0, 0), (40, 25), (75, -5)):
                circle(d, sx + dx, 1100 + dy, 11, fill="#a8643c")

    def eye_patch(d):
        d.line((560, 880, 1180, 1000), fill=INK, width=14)
        d.line((1180, 1000, 1470, 1010), fill=INK, width=14)
        d.ellipse((1075, 900, 1285, 1100), fill="#1b1b24", outline=INK, width=10)

    def bandage(d):
        d.rounded_rectangle((620, 1085, 800, 1150), radius=24, fill="#f3d2a9",
                            outline=INK, width=8)
        for x in (690, 710, 730):
            circle(d, x, 1117, 5, fill="#b98a5a")

    for name, paint in {"Glasses": glasses, "Sunglasses": sunglasses, "Blush": blush,
                        "Freckles": freckles, "Eye Patch": eye_patch,
                        "Bandage": bandage}.items():
        img, d = canvas()
        paint(d)
        save(img, "Face", name)


# ---------------------------------------------------------------------- Head
def heads():
    def party_hat(d):
        d.polygon([(1000, 330), (830, 740), (1170, 740)], fill="#ff6fa5", outline=INK, width=W)
        for x, y in ((960, 560), (1040, 650), (930, 690), (1010, 470)):
            circle(d, x, y, 22, fill="#ffe14d")
        circle(d, 1000, 320, 50, fill="#5ad1e6", outline=INK, width=10)

    def beanie(d):
        d.pieslice((650, 470, 1350, 1050), 180, 360, fill="#e2574c", outline=INK, width=W)
        d.rounded_rectangle((620, 720, 1380, 820), radius=45, fill="#f4f1ea",
                            outline=INK, width=W)
        circle(d, 1000, 460, 60, fill="#f4f1ea", outline=INK, width=10)

    def crown(d):
        d.polygon([(760, 770), (760, 540), (880, 670), (1000, 500), (1120, 670),
                   (1240, 540), (1240, 770)], fill="#ffd23f", outline=INK, width=W)
        for x, c in ((860, "#e23d4b"), (1000, "#3fa7e2"), (1140, "#4fb783")):
            circle(d, x, 720, 26, fill=c, outline=INK, width=6)

    def bow(d):
        cx, cy = 1270, 690
        d.polygon([(cx, cy), (cx - 150, cy - 90), (cx - 150, cy + 90)],
                  fill="#ff5c8a", outline=INK, width=10)
        d.polygon([(cx, cy), (cx + 150, cy - 90), (cx + 150, cy + 90)],
                  fill="#ff5c8a", outline=INK, width=10)
        circle(d, cx, cy, 40, fill="#ff5c8a", outline=INK, width=10)

    def flower_crown(d):
        cols = ["#ff8fb1", "#ffffff", "#b58cff", "#ffffff", "#ff8fb1"]
        for i, x in enumerate(range(720, 1281, 140)):
            y = 760 - 60 * math.sin(math.pi * i / 4)
            flower(d, x, y, 52, cols[i])

    def propeller(d):
        d.line((1000, 560, 1000, 460), fill=INK, width=16)
        d.ellipse((800, 420, 1000, 480), fill="#e23d4b", outline=INK, width=8)
        d.ellipse((1000, 420, 1200, 480), fill="#3fa7e2", outline=INK, width=8)
        circle(d, 1000, 450, 24, fill="#ffd23f", outline=INK, width=8)
        box = (760, 540, 1240, 960)
        d.pieslice(box, 180, 240, fill="#e23d4b")
        d.pieslice(box, 240, 300, fill="#ffd23f")
        d.pieslice(box, 300, 360, fill="#3fa7e2")
        d.arc(box, 180, 360, fill=INK, width=W)
        d.line((760, 750, 1240, 750), fill=INK, width=W)

    for name, paint in {"Party Hat": party_hat, "Beanie": beanie, "Crown": crown,
                        "Bow": bow, "Flower Crown": flower_crown,
                        "Propeller Cap": propeller}.items():
        img, d = canvas()
        paint(d)
        save(img, "Head", name)


# --------------------------------------------------------------------- Items
def items():
    def balloon(d):
        d.line((1520, 1300, 1680, 830), fill=INK, width=10)
        d.ellipse((1540, 480, 1820, 830), fill="#e23d4b", outline=INK, width=W)
        d.ellipse((1600, 540, 1660, 620), fill=(255, 255, 255, 170))

    def flower_item(d):
        d.line((1520, 1420, 1640, 1020), fill="#3d9a5f", width=18)
        flower(d, 1640, 1000, 80, "#ff8fb1")

    def lollipop(d):
        d.line((1520, 1420, 1640, 1050), fill="#ffffff", width=20)
        circle(d, 1660, 990, 130, fill="#ff6fa5", outline=INK, width=W)
        d.arc((1580, 910, 1740, 1070), 0, 300, fill="#ffffff", width=18)

    def wand(d):
        d.line((1520, 1420, 1650, 1040), fill="#8a5a2b", width=20)
        d.polygon(star(1670, 980, 130), fill="#ffd23f", outline=INK, width=10)

    def book(d):
        d.rounded_rectangle((1420, 1320, 1700, 1580), radius=20, fill="#4f7fd6",
                            outline=INK, width=W)
        d.line((1470, 1320, 1470, 1580), fill=INK, width=10)
        for y in (1400, 1450):
            d.line((1520, y, 1650, y), fill="#ffffff", width=12)

    def umbrella(d):
        d.line((1520, 1420, 1520, 660), fill=INK, width=18)
        d.pieslice((1180, 380, 1860, 960), 180, 360, fill="#3fa7e2", outline=INK, width=W)
        for x in (1350, 1520, 1690):
            d.line((1520, 380, x, 670), fill=INK, width=8)

    for name, paint in {"Balloon": balloon, "Flower": flower_item, "Lollipop": lollipop,
                        "Star Wand": wand, "Book": book, "Umbrella": umbrella}.items():
        img, d = canvas()
        paint(d)
        save(img, "Items", name)


# ---------------------------------------------------------------------- Logo
def logo():
    """Brand overlay kept as its own layer so it always sits on top."""
    img, d = canvas()
    d.rounded_rectangle((500, 1866, 1500, 1972), radius=53, fill=(255, 255, 255, 240),
                        outline=INK, width=8)
    font = ImageFont.load_default(size=52)
    d.text((1000, 1918), "PIXEL PALS - DEMO COLLECTION", font=font, fill=INK, anchor="mm")
    save(img, "Logo", "Logo")


if __name__ == "__main__":
    for step in (backgrounds, bodies, clothes, eyes, mouths, faces, heads, items, logo):
        step()
    print("Layers written to", ROOT)
