"""Build PNG cards and desktop/mobile sheets without a browser at update time."""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ASSETS = Path(__file__).resolve().parents[1] / "assets"
SCALE = 2
CARD_WIDTH = 400
GAP = 16
GAMES = (
    ("hi3", "Honkai Impact 3rd", "#e97868"),
    ("gs", "Genshin Impact", "#58b6a8"),
    ("sr", "Honkai: Star Rail", "#9784e5"),
    ("zzz", "Zenless Zone Zero", "#ed9868"),
)


def font(size: float, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Use locally installed fonts; generation never downloads web fonts."""
    filename = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    candidates = (
        Path("/usr/share/fonts/truetype/dejavu") / filename,
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / ("arialbd.ttf" if bold else "arial.ttf"),
        Path(filename),
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(str(candidate), round(size * SCALE))
        except OSError:
            continue
    raise RuntimeError("Install DejaVu Sans or Arial before generating profile images")


def save_png(image: Image.Image, path: Path, *, photo: bool = False) -> None:
    # Photographic cards use a shared 256-colour palette to keep mobile transfers small.
    if photo:
        image = image.convert("RGB").quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    image.save(path, format="PNG", optimize=True)


def render_activity_card(path: Path) -> Image.Image:
    """Rasterize the simple, self-generated SVG shapes using Pillow."""
    root = ET.parse(path).getroot()
    image = Image.new("RGB", (int(root.attrib["width"]) * SCALE, int(root.attrib["height"]) * SCALE), "white")
    draw = ImageDraw.Draw(image)
    for element in root:
        tag = element.tag.rsplit("}", 1)[-1]
        a = element.attrib
        fill = a.get("fill", "#1f2328")
        if tag == "rect":
            x, y, w, h = (float(a.get(k, 0)) * SCALE for k in ("x", "y", "width", "height"))
            draw.rounded_rectangle((x, y, x + w, y + h), radius=float(a.get("rx", 0)) * SCALE, fill=fill, outline=a.get("stroke"), width=SCALE)
        elif tag == "circle":
            x, y, r = (float(a[k]) * SCALE for k in ("cx", "cy", "r"))
            draw.ellipse((x - r, y - r, x + r, y + r), fill=fill)
        elif tag == "text":
            anchor = {"end": "rs", "middle": "ms"}.get(a.get("text-anchor"), "ls")
            draw.text((float(a["x"]) * SCALE, float(a["y"]) * SCALE), "".join(element.itertext()), fill=fill, font=font(float(a.get("font-size", 16)), a.get("font-weight", "400") in ("600", "700", "bold")), anchor=anchor)
    return image


def save_layouts(name: str, cards: list[Image.Image], *, photo: bool = False) -> None:
    """Default to a readable single column; wide browsers select the two-column sheet."""
    width, height = cards[0].size
    if any(card.size != (width, height) for card in cards):
        raise ValueError("All cards in a sheet must have the same dimensions")
    gap = GAP * SCALE
    for layout, columns in (("mobile", 1), ("desktop", 2)):
        rows = (len(cards) + columns - 1) // columns
        canvas = Image.new("RGB", (width * columns + gap * (columns - 1), height * rows + gap * (rows - 1)), "white")
        for index, card in enumerate(cards):
            canvas.paste(card, ((index % columns) * (width + gap), (index // columns) * (height + gap)))
        save_png(canvas, ASSETS / f"{name}-{layout}.png", photo=photo)


def build_activity_images() -> None:
    cards = []
    for key in ("github-stats", "github-languages"):
        card = render_activity_card(ASSETS / f"{key}.svg")
        save_png(card, ASSETS / f"{key}.png")
        cards.append(card)
    save_layouts("github-activity", cards)


def build_game_images() -> None:
    cards = []
    for key, title, accent in GAMES:
        # These are rasterized copies of the existing, distinct HoYoverse cards.
        with Image.open(ASSETS / f"hoyo-{key}.png") as source:
            artwork = source.convert("RGB").resize((376 * SCALE, 124 * SCALE), Image.Resampling.LANCZOS)
        card = Image.new("RGB", (CARD_WIDTH * SCALE, 172 * SCALE), "white")
        draw = ImageDraw.Draw(card)
        draw.rounded_rectangle((0, 0, card.width - 1, card.height - 1), radius=8 * SCALE, outline="#d0d7de", width=SCALE)
        draw.line((12 * SCALE, 0, 388 * SCALE, 0), fill=accent, width=3 * SCALE)
        draw.text((12 * SCALE, 24 * SCALE), title, fill="#1f2328", font=font(16, bold=True), anchor="ls")
        card.paste(artwork, (12 * SCALE, 36 * SCALE))
        cards.append(card)
    save_layouts("hoyo-games", cards, photo=True)


if __name__ == "__main__":
    build_activity_images()
    build_game_images()
