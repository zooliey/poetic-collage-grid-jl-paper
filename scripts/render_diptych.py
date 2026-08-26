#!/usr/bin/env python3
"""Render a paper-textured 3:4 poetic fragment/void diptych from one photograph."""

from __future__ import annotations

import argparse
import colorsys
import json
import math
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    from PIL import Image, ImageChops, ImageColor, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps, ImageStat
except ImportError as exc:  # pragma: no cover - environment-specific message
    raise SystemExit("Pillow is required: install it with `python3 -m pip install Pillow`.") from exc


RESAMPLE = Image.Resampling.LANCZOS
FORBIDDEN_LINE_START = set("，。！？；：、）》】〕〉…—”’」』!?;:,.%)]}")


@dataclass
class Atom:
    kind: str
    width: float
    height: int
    value: Any
    forced_break: bool = False


def fail(message: str) -> None:
    raise ValueError(message)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def parse_hex(value: str, field: str) -> tuple[int, int, int]:
    try:
        return ImageColor.getrgb(value)
    except ValueError as exc:
        fail(f"{field} must be a valid color, got {value!r}.")
        raise exc


def auto_morandi(source: Image.Image) -> tuple[int, int, int]:
    sample = source.convert("RGB").resize((64, 64), RESAMPLE)
    r, g, b = (channel / 255 for channel in ImageStat.Stat(sample).median[:3])
    hue, lightness, saturation = colorsys.rgb_to_hls(r, g, b)
    # Keep the source hue while lifting and graying it into a paper-like Morandi tint.
    muted_saturation = clamp(saturation * 0.32, 0.045, 0.14)
    muted_lightness = clamp(0.905 + (lightness - 0.5) * 0.025, 0.89, 0.93)
    rr, gg, bb = colorsys.hls_to_rgb(hue, muted_lightness, muted_saturation)
    return tuple(round(channel * 255) for channel in (rr, gg, bb))


def parse_film_look(value: Any) -> dict[str, Any]:
    settings: dict[str, Any] = {
        "enabled": True,
        "strength": 0.72,
        "grain": 0.024,
        "seed": 17,
    }
    if value is None or value is False or value == "off":
        settings["enabled"] = False
        return settings
    if value is True or value == "cinematic":
        return settings
    if not isinstance(value, dict):
        fail("`film_look` must be `cinematic`, `off`, true, false, or an object.")
    unknown = set(value) - {"enabled", "strength", "grain", "seed"}
    if unknown:
        fail(f"Unknown `film_look` fields: {sorted(unknown)}.")
    settings.update(value)
    if not isinstance(settings["enabled"], bool):
        fail("`film_look.enabled` must be true or false.")
    settings["strength"] = float(settings["strength"])
    settings["grain"] = float(settings["grain"])
    settings["seed"] = int(settings["seed"])
    if not 0 <= settings["strength"] <= 1:
        fail("`film_look.strength` must be between 0 and 1.")
    if not 0 <= settings["grain"] <= 0.10:
        fail("`film_look.grain` must be between 0 and 0.10.")
    return settings


def parse_paper_texture(value: Any) -> dict[str, Any]:
    settings: dict[str, Any] = {
        "enabled": True,
        "strength": 0.12,
        "fiber": 0.08,
        "seed": 61,
    }
    if value is None or value is False or value == "off":
        settings["enabled"] = False
        return settings
    if value is True or value == "subtle":
        return settings
    if not isinstance(value, dict):
        fail("`paper_texture` must be `subtle`, `off`, true, false, or an object.")
    unknown = set(value) - {"enabled", "strength", "fiber", "seed"}
    if unknown:
        fail(f"Unknown `paper_texture` fields: {sorted(unknown)}.")
    settings.update(value)
    if not isinstance(settings["enabled"], bool):
        fail("`paper_texture.enabled` must be true or false.")
    settings["strength"] = float(settings["strength"])
    settings["fiber"] = float(settings["fiber"])
    settings["seed"] = int(settings["seed"])
    if not 0 <= settings["strength"] <= 0.35:
        fail("`paper_texture.strength` must be between 0 and 0.35.")
    if not 0 <= settings["fiber"] <= 0.30:
        fail("`paper_texture.fiber` must be between 0 and 0.30.")
    return settings


def parse_print_style(value: Any) -> dict[str, Any]:
    settings: dict[str, Any] = {
        "enabled": True,
        "ink_variation": 0.18,
        "registration_shift": 0.55,
        "baseline_jitter": 0.65,
        "ink_spread": 0.14,
        "seed": 67,
    }
    if value is None or value is False or value == "off":
        settings["enabled"] = False
        return settings
    if value is True or (isinstance(value, str) and value in {"letterpress", "typewriter"}):
        return settings
    if not isinstance(value, dict):
        fail("`print_style` must be `typewriter`, `letterpress`, `off`, true, false, or an object.")
    unknown = set(value) - {
        "enabled",
        "ink_variation",
        "registration_shift",
        "baseline_jitter",
        "ink_spread",
        "seed",
    }
    if unknown:
        fail(f"Unknown `print_style` fields: {sorted(unknown)}.")
    settings.update(value)
    if not isinstance(settings["enabled"], bool):
        fail("`print_style.enabled` must be true or false.")
    settings["ink_variation"] = float(settings["ink_variation"])
    settings["registration_shift"] = float(settings["registration_shift"])
    settings["baseline_jitter"] = float(settings["baseline_jitter"])
    settings["ink_spread"] = float(settings["ink_spread"])
    settings["seed"] = int(settings["seed"])
    if not 0 <= settings["ink_variation"] <= 0.40:
        fail("`print_style.ink_variation` must be between 0 and 0.40.")
    if not 0 <= settings["registration_shift"] <= 1.5:
        fail("`print_style.registration_shift` must be between 0 and 1.5 px.")
    if not 0 <= settings["baseline_jitter"] <= 1.5:
        fail("`print_style.baseline_jitter` must be between 0 and 1.5 px.")
    if not 0 <= settings["ink_spread"] <= 0.35:
        fail("`print_style.ink_spread` must be between 0 and 0.35.")
    return settings


def parse_torn_edges(value: Any) -> dict[str, Any]:
    settings: dict[str, Any] = {
        "enabled": True,
        "roughness": 0.18,
        "split_roughness": 0.14,
        "fiber": 0.22,
        "seed": 73,
    }
    if value is None or value is False or value == "off":
        settings["enabled"] = False
        return settings
    if value is True or value == "subtle":
        return settings
    if not isinstance(value, dict):
        fail("`torn_edges` must be `subtle`, `off`, true, false, or an object.")
    unknown = set(value) - {"enabled", "roughness", "split_roughness", "fiber", "seed"}
    if unknown:
        fail(f"Unknown `torn_edges` fields: {sorted(unknown)}.")
    settings.update(value)
    if not isinstance(settings["enabled"], bool):
        fail("`torn_edges.enabled` must be true or false.")
    settings["roughness"] = float(settings["roughness"])
    settings["split_roughness"] = float(settings["split_roughness"])
    settings["fiber"] = float(settings["fiber"])
    settings["seed"] = int(settings["seed"])
    if not 0 <= settings["roughness"] <= 0.60:
        fail("`torn_edges.roughness` must be between 0 and 0.60.")
    if not 0 <= settings["split_roughness"] <= 0.50:
        fail("`torn_edges.split_roughness` must be between 0 and 0.50.")
    if not 0 <= settings["fiber"] <= 0.60:
        fail("`torn_edges.fiber` must be between 0 and 0.60.")
    return settings


def stable_seed(text: str) -> int:
    value = 2166136261
    for byte in text.encode("utf-8"):
        value ^= byte
        value = (value * 16777619) & 0xFFFFFFFF
    return value


def smooth_profile(length: int, maximum: int, rng: random.Random) -> list[int]:
    if maximum <= 0:
        return [0] * length
    spacing = max(4, min(13, length // 10 or 4))
    knots = [rng.randint(0, maximum) for _ in range(length // spacing + 3)]
    values: list[int] = []
    for index in range(length):
        position = index / spacing
        left = min(int(position), len(knots) - 2)
        fraction = position - left
        smooth = fraction * fraction * (3 - 2 * fraction)
        values.append(round(knots[left] * (1 - smooth) + knots[left + 1] * smooth))
    return values


def fibrous_profile(length: int, maximum: int, rng: random.Random) -> list[int]:
    """Blend a slow torn contour with restrained single-pixel paper breaks."""
    values = smooth_profile(length, maximum, rng)
    for index, value in enumerate(values):
        if rng.random() < 0.32:
            value += rng.choice((-1, 0, 0, 0, 1))
        if rng.random() < 0.035:
            value += rng.choice((-1, 1))
        values[index] = int(clamp(value, 0, maximum))
    return values


def random_luma(size: tuple[int, int], rng: random.Random) -> Image.Image:
    count = size[0] * size[1]
    try:
        noise_bytes = rng.randbytes(count)
    except AttributeError:  # pragma: no cover
        noise_bytes = bytes(rng.randrange(256) for _ in range(count))
    return Image.frombytes("L", size, noise_bytes)


def fiberize_mask(core: Image.Image, rng: random.Random, strength: float) -> Image.Image:
    """Give a solid cut mask a translucent cellulose fringe and tiny voids."""
    if strength <= 0:
        return core
    noise = random_luma(core.size, rng).filter(ImageFilter.GaussianBlur(0.22))
    inner_edge = ImageChops.subtract(core, core.filter(ImageFilter.MinFilter(3)))
    outer_edge = ImageChops.subtract(core.filter(ImageFilter.MaxFilter(3)), core)

    inner_floor = round(205 - 95 * strength)
    inner_texture = noise.point(
        [round(inner_floor + (255 - inner_floor) * value / 255) for value in range(256)]
    )
    interior = ImageChops.subtract(core, inner_edge)
    inner_fibres = ImageChops.multiply(inner_edge, inner_texture)

    outer_peak = round(72 + 260 * strength)
    outer_texture = noise.point(
        [0 if value < 150 else round((value - 150) * outer_peak / 105) for value in range(256)]
    )
    outer_fibres = ImageChops.multiply(outer_edge, outer_texture)
    return ImageChops.lighter(ImageChops.lighter(interior, inner_fibres), outer_fibres)


def torn_mask(size: tuple[int, int], settings: dict[str, Any], salt: str) -> Image.Image:
    width, height = size
    if not settings["enabled"] or settings["roughness"] <= 0:
        return Image.new("L", size, 255)
    maximum = min(4, max(1, round(1 + float(settings["roughness"]) * 7)))
    rng = random.Random(int(settings["seed"]) + stable_seed(salt))
    top = fibrous_profile(width, maximum, rng)
    right = fibrous_profile(height, maximum, rng)
    bottom = fibrous_profile(width, maximum, rng)
    left = fibrous_profile(height, maximum, rng)
    points: list[tuple[int, int]] = []
    points.extend((x, top[x]) for x in range(width))
    points.extend((width - 1 - right[y], y) for y in range(height))
    points.extend((x, height - 1 - bottom[x]) for x in range(width - 1, -1, -1))
    points.extend((left[y], y) for y in range(height - 1, -1, -1))
    core = Image.new("L", size, 0)
    ImageDraw.Draw(core).polygon(points, fill=255)
    return fiberize_mask(core, rng, float(settings["fiber"]))


def make_paper_panel(
    size: tuple[int, int],
    color: tuple[int, int, int],
    settings: dict[str, Any],
) -> Image.Image:
    panel = Image.new("RGB", size, color)
    if not settings["enabled"] or settings["strength"] <= 0:
        return panel
    width, height = size
    rng = random.Random(int(settings["seed"]))
    count = width * height
    try:
        noise_bytes = rng.randbytes(count)
    except AttributeError:  # pragma: no cover
        noise_bytes = bytes(rng.randrange(256) for _ in range(count))
    noise = Image.frombytes("L", size, noise_bytes).filter(ImageFilter.GaussianBlur(0.45))
    amplitude = max(1, round(8 * float(settings["strength"]) / 0.12))
    noise = noise.point(
        [round(128 + (value - 128) * amplitude / 128) for value in range(256)]
    )
    panel = ImageChops.add(panel, Image.merge("RGB", (noise, noise, noise)), scale=1.0, offset=-128)

    fiber = float(settings["fiber"])
    if fiber > 0:
        overlay = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        fiber_count = round((width + height) * 0.025 * fiber / 0.08)
        for _ in range(fiber_count):
            x = rng.randrange(width)
            y = rng.randrange(height)
            length = rng.randint(8, 34)
            shade = rng.choice((-1, 1))
            tone = tuple(clamp(channel + shade * 18, 0, 255) for channel in color)
            alpha = rng.randint(5, 12)
            draw.line((x, y, min(width - 1, x + length), y + rng.choice((-1, 0, 1))), fill=(*map(int, tone), alpha), width=1)
        panel = Image.alpha_composite(panel.convert("RGBA"), overlay).convert("RGB")
    return panel


def apply_split_fringe(
    canvas: Image.Image,
    top_panel: Image.Image,
    split_y: int,
    settings: dict[str, Any],
) -> None:
    if not settings["enabled"] or settings["split_roughness"] <= 0:
        return
    maximum = min(4, max(1, round(1 + float(settings["split_roughness"]) * 8)))
    rng = random.Random(int(settings["seed"]) + 1000003)
    depths = fibrous_profile(canvas.width, maximum, rng)
    strip_height = maximum + 2
    core = Image.new("L", (canvas.width, strip_height), 0)
    draw = ImageDraw.Draw(core)
    for x, depth in enumerate(depths):
        if depth:
            draw.line((x, 0, x, depth - 1), fill=255)
    mask = fiberize_mask(core, rng, float(settings["fiber"]))
    source = top_panel.crop(
        (0, max(0, top_panel.height - strip_height), top_panel.width, top_panel.height)
    )
    if source.height != strip_height:
        source = source.resize((top_panel.width, strip_height), RESAMPLE)
    canvas.paste(source, (0, split_y), mask)


def draw_print_text(
    canvas: Image.Image,
    position: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    color: tuple[int, int, int],
    settings: dict[str, Any],
    salt: int,
) -> None:
    if not text:
        return
    if not settings["enabled"]:
        ImageDraw.Draw(canvas).text(position, text, font=font, fill=color)
        return
    bbox = font.getbbox(text)
    pad = 7
    width = max(1, bbox[2] - bbox[0] + pad * 2 + 4)
    height = max(1, bbox[3] - bbox[1] + pad * 2 + 4)
    mask = Image.new("L", (width, height), 0)
    variation = float(settings["ink_variation"])
    registration = float(settings["registration_shift"])
    baseline = float(settings["baseline_jitter"])
    spread = float(settings["ink_spread"])
    rng = random.Random(int(settings["seed"]) + salt)

    # Strike each glyph separately so pressure, baseline, and registration are
    # imperfect in the way a physical typebar meets paper and ribbon.
    for index, character in enumerate(text):
        if character.isspace():
            continue
        prefix = float(font.getlength(text[:index]))
        jitter_x = round(rng.uniform(-registration * 0.45, registration * 0.45))
        jitter_y = round(rng.uniform(-baseline, baseline))
        impression = clamp(0.88 + rng.uniform(-variation * 0.28, variation * 0.34), 0.72, 1.0)
        glyph = Image.new("L", mask.size, 0)
        ImageDraw.Draw(glyph).text(
            (pad - bbox[0] + prefix + jitter_x, pad - bbox[1] + jitter_y),
            character,
            font=font,
            fill=round(255 * impression),
        )
        if spread > 0:
            swollen = glyph.filter(ImageFilter.MaxFilter(3))
            glyph = Image.blend(glyph, swollen, spread)
        if registration > 0 and rng.random() < 0.72:
            echo = Image.new("L", mask.size, 0)
            echo.paste(glyph, (rng.choice((-1, 1)), rng.choice((0, 0, 1))))
            echo_alpha = min(0.15, 0.045 + registration * 0.07)
            echo = echo.point([round(value * echo_alpha) for value in range(256)])
            glyph = ImageChops.lighter(glyph, echo)
        mask = ImageChops.lighter(mask, glyph)

    if variation > 0:
        texture = random_luma(mask.size, rng).filter(ImageFilter.GaussianBlur(0.28))
        density_floor = round(245 - 300 * variation)
        texture = texture.point(
            [round(density_floor + (255 - density_floor) * value / 255) for value in range(256)]
        )
        mask = ImageChops.multiply(mask, texture)

        # Sparse pale pinholes and dark edge deposits keep the result material,
        # but remain too small to interrupt reading at the intended scale.
        dropout = Image.new("L", mask.size, 255)
        dropout_draw = ImageDraw.Draw(dropout)
        flecks = round(width * height * variation * 0.0017)
        for _ in range(flecks):
            x = rng.randrange(width)
            y = rng.randrange(height)
            dropout_draw.point((x, y), fill=rng.randint(55, 190))
        mask = ImageChops.multiply(mask, dropout)

        outer_edge = ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(3)), mask)
        deposits = random_luma(mask.size, rng).point(
            [0 if value < 220 else round((value - 220) * min(170, 70 + 300 * variation) / 35) for value in range(256)]
        )
        mask = ImageChops.lighter(mask, ImageChops.multiply(outer_edge, deposits))
    ink = Image.new("RGB", mask.size, color)
    canvas.paste(ink, (position[0] + bbox[0] - pad, position[1] + bbox[1] - pad), mask)


def radial_edge_mask(size: tuple[int, int]) -> Image.Image:
    small_width = 256
    small_height = max(64, round(small_width * size[1] / size[0]))
    pixels = bytearray(small_width * small_height)
    center_x = (small_width - 1) / 2
    center_y = (small_height - 1) / 2
    for y in range(small_height):
        dy = (y - center_y) / max(1, center_y)
        row = y * small_width
        for x in range(small_width):
            dx = (x - center_x) / max(1, center_x)
            radius = math.sqrt(dx * dx + dy * dy)
            edge = clamp((radius - 0.38) / 0.62, 0, 1)
            pixels[row + x] = round(255 * edge * edge)
    return Image.frombytes("L", (small_width, small_height), bytes(pixels)).resize(size, RESAMPLE)


def apply_film_look(panel: Image.Image, settings: dict[str, Any]) -> Image.Image:
    if not settings["enabled"] or settings["strength"] <= 0:
        return panel
    strength = float(settings["strength"])

    # A restrained photochemical grade: a soft shoulder/toe, lightly lowered
    # chroma, cool shadows, warm highlights, and no local retouching.
    graded = ImageEnhance.Color(panel).enhance(1 - 0.075 * strength)
    curve_mix = 0.22 * strength
    black_lift = 0.010 * strength
    tone_lut: list[int] = []
    for value in range(256):
        x = value / 255
        smooth = x * x * (3 - 2 * x)
        y = x * (1 - curve_mix) + smooth * curve_mix
        y += black_lift * (1 - y) * (1 - y)
        tone_lut.append(round(255 * clamp(y, 0, 1)))
    graded = graded.point(tone_lut * 3)

    luminance = ImageOps.grayscale(graded)
    duotone = ImageOps.colorize(luminance, black="#233039", white="#F2DCC3")
    graded = Image.blend(graded, duotone, 0.055 * strength)

    highlight_mask = luminance.point(
        [0 if value < 188 else round(255 * (value - 188) / 67) for value in range(256)]
    )
    highlight_mask = highlight_mask.filter(
        ImageFilter.GaussianBlur(radius=max(3, round(min(panel.size) * 0.010)))
    )
    highlight_mask = highlight_mask.point(
        [round(value * 0.16 * strength) for value in range(256)]
    )
    warm_highlights = Image.blend(graded, Image.new("RGB", panel.size, "#F3B27B"), 0.22)
    graded = Image.composite(warm_highlights, graded, highlight_mask)

    vignette_mask = radial_edge_mask(panel.size).point(
        [round(value * 0.17 * strength) for value in range(256)]
    )
    darker_edges = ImageEnhance.Brightness(graded).enhance(0.80)
    graded = Image.composite(darker_edges, graded, vignette_mask)

    grain = float(settings["grain"])
    if grain > 0:
        rng = random.Random(int(settings["seed"]))
        count = panel.width * panel.height
        try:
            noise_bytes = rng.randbytes(count)
        except AttributeError:  # pragma: no cover - Python < 3.9 fallback
            noise_bytes = bytes(rng.randrange(256) for _ in range(count))
        noise = Image.frombytes("L", panel.size, noise_bytes).filter(ImageFilter.GaussianBlur(0.18))
        amplitude = max(1, round(255 * grain))
        grain_lut = [round(128 + (value - 128) * amplitude / 128) for value in range(256)]
        noise = noise.point(grain_lut)
        grain_rgb = Image.merge("RGB", (noise, noise, noise))
        graded = ImageChops.add(graded, grain_rgb, scale=1.0, offset=-128)

    return graded


def load_font(path: str | None, language: str, size: int) -> ImageFont.FreeTypeFont:
    candidates: list[Path] = []
    if path:
        candidates.append(Path(path).expanduser())
    if language.lower().startswith("zh"):
        candidates.extend(
            Path(p)
            for p in (
                "/System/Library/Fonts/PingFang.ttc",
                "/System/Library/Fonts/Hiragino Sans GB.ttc",
                "/System/Library/Fonts/STHeiti Light.ttc",
                "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            )
        )
    else:
        candidates.extend(
            Path(p)
            for p in (
                "/System/Library/Fonts/Supplemental/Courier New Bold.ttf",
                "/System/Library/Fonts/Supplemental/Courier New.ttf",
                "/System/Library/Fonts/Courier.ttc",
                "/System/Library/Fonts/Supplemental/AmericanTypewriter.ttc",
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
            )
        )
    for candidate in candidates:
        if candidate.is_file():
            try:
                return ImageFont.truetype(str(candidate), size=size)
            except OSError:
                continue
    fail("No suitable print-style font was found. Set `font_path` to an installed font.")
    raise AssertionError


def render_photo(
    source: Image.Image,
    panel_size: tuple[int, int],
    fit: str,
    focus: tuple[float, float],
    backdrop: tuple[int, int, int],
) -> tuple[Image.Image, float, float, float]:
    sw, sh = source.size
    pw, ph = panel_size
    if fit != "cover":
        fail("`fit` is fixed at `cover`; the lower photo must fill its half edge to edge.")
    scale = max(pw / sw, ph / sh)
    rw, rh = max(1, round(sw * scale)), max(1, round(sh * scale))
    resized = source.resize((rw, rh), RESAMPLE)
    panel = Image.new("RGB", (pw, ph), backdrop)
    offset_x = -round(clamp(focus[0] * rw - pw / 2, 0, max(0, rw - pw)))
    offset_y = -round(clamp(focus[1] * rh - ph / 2, 0, max(0, rh - ph)))
    panel.paste(resized, (offset_x, offset_y))
    return panel, scale, float(offset_x), float(offset_y)


def validate_box(box: Any, crop_id: str) -> tuple[float, float, float, float]:
    if not isinstance(box, list) or len(box) != 4 or not all(isinstance(v, (int, float)) for v in box):
        fail(f"Crop {crop_id!r} box must be [x, y, width, height].")
    x, y, width, height = map(float, box)
    if width <= 0 or height <= 0 or x < 0 or y < 0 or x + width > 1 or y + height > 1:
        fail(f"Crop {crop_id!r} box must be positive and fully inside normalized source bounds.")
    return x, y, width, height


def boxes_overlap(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return max(ax, bx) < min(ax + aw, bx + bw) and max(ay, by) < min(ay + ah, by + bh)


def split_text(text: str) -> Iterable[str | None]:
    # None is an explicit line break. Latin words stay intact; CJK can wrap per glyph.
    lines = text.split("\n")
    pattern = re.compile(r"\s+|[A-Za-z0-9]+(?:[’'\-][A-Za-z0-9]+)*|[^\sA-Za-z0-9]")
    for line_index, line in enumerate(lines):
        for token in pattern.findall(line):
            yield token
        if line_index < len(lines) - 1:
            yield None


def font_metrics(font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    box = font.getbbox("Ag中")
    return box[1], max(1, box[3] - box[1])


def make_atoms(
    poem: list[dict[str, Any]],
    patches: dict[str, Image.Image],
    font: ImageFont.FreeTypeFont,
    brackets: tuple[str, str],
) -> list[Atom]:
    atoms: list[Atom] = []
    _, text_height = font_metrics(font)
    crop_usage = {key: 0 for key in patches}
    bracket_gap = max(4, round(font.size * 0.12))
    for run in poem:
        if not isinstance(run, dict):
            fail("Every poem run must be an object.")
        if run.get("break") is True:
            atoms.append(Atom("break", 0, 0, None, forced_break=True))
        elif "text" in run:
            if not isinstance(run["text"], str):
                fail("Poem `text` values must be strings.")
            for token in split_text(run["text"]):
                if token is None:
                    atoms.append(Atom("break", 0, 0, None, forced_break=True))
                elif token:
                    atoms.append(Atom("text", float(font.getlength(token)), text_height, token))
        elif "crop" in run:
            crop_id = run["crop"]
            if crop_id not in patches:
                fail(f"Poem references unknown crop {crop_id!r}.")
            crop_usage[crop_id] += 1
            patch = patches[crop_id]
            left_width = float(font.getlength(brackets[0]))
            right_width = float(font.getlength(brackets[1]))
            width = left_width + bracket_gap + patch.width + bracket_gap + right_width
            atoms.append(
                Atom(
                    "crop",
                    width,
                    max(text_height, patch.height),
                    (crop_id, patch, left_width, right_width, bracket_gap),
                )
            )
        else:
            fail("A poem run must contain `text`, `crop`, or `break`.")
    unused = [key for key, count in crop_usage.items() if count == 0]
    repeated = [key for key, count in crop_usage.items() if count > 1]
    if unused or repeated:
        fail(f"Every crop must appear exactly once in the poem; unused={unused}, repeated={repeated}.")
    return atoms


def trim_spaces(atoms: list[Atom]) -> list[Atom]:
    trimmed = list(atoms)
    while trimmed and trimmed[0].kind == "text" and str(trimmed[0].value).isspace():
        trimmed.pop(0)
    while trimmed and trimmed[-1].kind == "text" and str(trimmed[-1].value).isspace():
        trimmed.pop()
    return trimmed


def wrap_atoms(atoms: list[Atom], available_width: int) -> list[list[Atom]]:
    lines: list[list[Atom]] = []
    current: list[Atom] = []
    width = 0.0
    for atom in atoms:
        if atom.forced_break:
            lines.append(trim_spaces(current))
            current, width = [], 0.0
            continue
        if not current and atom.kind == "text" and str(atom.value).isspace():
            continue
        if current and width + atom.width > available_width:
            # Keep closing punctuation with the previous line when possible.
            if atom.kind == "text" and str(atom.value) in FORBIDDEN_LINE_START:
                current.append(atom)
                width += atom.width
            else:
                lines.append(trim_spaces(current))
                current, width = [], 0.0
                if atom.kind == "text" and str(atom.value).isspace():
                    continue
        if atom.width > available_width and atom.kind != "text":
            fail("An inline fragment is wider than the available poem width; reduce its crop box.")
        current.append(atom)
        width += atom.width
    if current or not lines:
        lines.append(trim_spaces(current))
    return [line for line in lines if line]


def line_dimensions(lines: list[list[Atom]]) -> list[tuple[float, int]]:
    return [(sum(atom.width for atom in line), max(atom.height for atom in line)) for line in lines]


def choose_layout(
    poem: list[dict[str, Any]],
    patches: dict[str, Image.Image],
    brackets: tuple[str, str],
    language: str,
    font_path: str | None,
    fixed_size: int | None,
    size_range: tuple[int, int],
    available_width: int,
    available_height: int,
    line_gap_ratio: float,
    max_lines: int,
) -> tuple[ImageFont.FreeTypeFont, list[list[Atom]], list[tuple[float, int]], int]:
    sizes = [fixed_size] if fixed_size else list(range(size_range[1], size_range[0] - 1, -1))
    for size in sizes:
        if size is None or size <= 0:
            continue
        font = load_font(font_path, language, int(size))
        atoms = make_atoms(poem, patches, font, brackets)
        lines = wrap_atoms(atoms, available_width)
        dimensions = line_dimensions(lines)
        gap = round(size * line_gap_ratio)
        total_height = sum(height for _, height in dimensions) + gap * max(0, len(lines) - 1)
        stranded_fragment = len(lines) > 1 and any(
            len(line) == 1 and line[0].kind == "crop" for line in lines
        )
        if (
            not stranded_fragment
            and len(lines) <= max_lines
            and max((width for width, _ in dimensions), default=0) <= available_width
            and total_height <= available_height
        ):
            return font, lines, dimensions, gap
    fail("The poem and fragments do not fit in the centered upper half within `max_lines`; shorten the poem or reduce crop boxes.")
    raise AssertionError


def draw_poem(
    canvas: Image.Image,
    top_height: int,
    poem: list[dict[str, Any]],
    patches: dict[str, Image.Image],
    spec: dict[str, Any],
) -> None:
    width = canvas.width
    side_margin = float(spec.get("side_margin", 0.075))
    top_padding = float(spec.get("top_padding", 0.10))
    if not 0.03 <= side_margin <= 0.2 or not 0.03 <= top_padding <= 0.25:
        fail("`side_margin` and `top_padding` are outside useful bounds.")
    available_width = round(width * (1 - 2 * side_margin))
    available_height = round(top_height * (1 - 2 * top_padding))
    language = str(spec.get("language", "en"))
    raw_brackets = spec.get("brackets", ["(", ")"])
    if not isinstance(raw_brackets, list) or len(raw_brackets) != 2 or not all(isinstance(x, str) for x in raw_brackets):
        fail("`brackets` must contain two strings.")
    brackets = (raw_brackets[0], raw_brackets[1])
    raw_range = spec.get("font_size_range", [34, 40])
    if not isinstance(raw_range, list) or len(raw_range) != 2:
        fail("`font_size_range` must contain [minimum, maximum].")
    size_range = (int(raw_range[0]), int(raw_range[1]))
    if size_range[0] < 12 or size_range[1] < size_range[0]:
        fail("`font_size_range` is invalid.")
    fixed_size = spec.get("font_size", 36)
    if fixed_size is not None:
        fixed_size = int(fixed_size)
    line_gap_ratio = float(spec.get("line_gap", 0.60))
    max_lines = int(spec.get("max_lines", 3))
    if not 1 <= max_lines <= 3:
        fail("`max_lines` must be between 1 and 3.")
    font, lines, dimensions, gap = choose_layout(
        poem,
        patches,
        brackets,
        language,
        spec.get("font_path"),
        fixed_size,
        size_range,
        available_width,
        available_height,
        line_gap_ratio,
        max_lines,
    )
    total_height = sum(height for _, height in dimensions) + gap * max(0, len(lines) - 1)
    y = round((top_height - total_height) / 2)
    text_color = parse_hex(str(spec.get("text_color", "#171716")), "text_color")
    print_settings = parse_print_style(spec.get("print_style", "typewriter"))
    font_top, text_height = font_metrics(font)
    left_bracket, right_bracket = brackets
    token_index = 0
    for line, (line_width, line_height) in zip(lines, dimensions):
        x = (width - line_width) / 2
        for atom in line:
            if atom.kind == "text":
                text_y = y + (line_height - text_height) / 2 - font_top
                token = str(atom.value)
                draw_print_text(
                    canvas,
                    (round(x), round(text_y)),
                    token,
                    font,
                    text_color,
                    print_settings,
                    token_index + stable_seed(token),
                )
                token_index += 1
            elif atom.kind == "crop":
                _, patch, left_width, right_width, bracket_gap = atom.value
                text_y = y + (line_height - text_height) / 2 - font_top
                draw_print_text(
                    canvas,
                    (round(x), round(text_y)),
                    left_bracket,
                    font,
                    text_color,
                    print_settings,
                    token_index + 1009,
                )
                token_index += 1
                x += left_width + bracket_gap
                patch_y = y + (line_height - patch.height) / 2
                canvas.paste(
                    patch,
                    (round(x), round(patch_y)),
                    patch.getchannel("A") if patch.mode == "RGBA" else None,
                )
                x += patch.width + bracket_gap
                draw_print_text(
                    canvas,
                    (round(x), round(text_y)),
                    right_bracket,
                    font,
                    text_color,
                    print_settings,
                    token_index + 2027,
                )
                token_index += 1
                x += right_width
                continue
            x += atom.width
        y += line_height + gap


def render(image_path: Path, spec_path: Path, output_path: Path) -> dict[str, Any]:
    with spec_path.open("r", encoding="utf-8") as handle:
        spec = json.load(handle)
    if not isinstance(spec, dict):
        fail("The render spec root must be an object.")
    source = ImageOps.exif_transpose(Image.open(image_path)).convert("RGB")
    raw_canvas = spec.get("canvas", [1536, 2048])
    if not isinstance(raw_canvas, list) or len(raw_canvas) != 2:
        fail("`canvas` must be [width, height].")
    canvas_width, canvas_height = map(int, raw_canvas)
    if canvas_width <= 0 or canvas_height <= 0 or canvas_width * 4 != canvas_height * 3:
        fail("Canvas dimensions must reduce exactly to a 3:4 portrait ratio.")
    split = float(spec.get("split", 0.5))
    if abs(split - 0.5) > 1e-9:
        fail("`split` is fixed at 0.5; upper and lower panels must be equal halves.")
    top_height = round(canvas_height * split)
    bottom_height = canvas_height - top_height
    background_value = spec.get("background", "auto")
    preliminary_background = auto_morandi(source)
    hole_color = parse_hex(str(spec.get("hole_color", "#FFFFFF")), "hole_color")
    raw_focus = spec.get("focus", [0.5, 0.5])
    if not isinstance(raw_focus, list) or len(raw_focus) != 2:
        fail("`focus` must be [x, y].")
    focus = (clamp(float(raw_focus[0]), 0, 1), clamp(float(raw_focus[1]), 0, 1))
    panel, scale, offset_x, offset_y = render_photo(
        source,
        (canvas_width, bottom_height),
        str(spec.get("fit", "cover")),
        focus,
        preliminary_background,
    )
    film_settings = parse_film_look(spec.get("film_look", "cinematic"))
    panel = apply_film_look(panel, film_settings)
    background = auto_morandi(panel) if background_value == "auto" else parse_hex(str(background_value), "background")
    paper_settings = parse_paper_texture(spec.get("paper_texture", "subtle"))
    torn_settings = parse_torn_edges(spec.get("torn_edges", "subtle"))
    top_panel = make_paper_panel((canvas_width, top_height), background, paper_settings)
    canvas = Image.new("RGB", (canvas_width, canvas_height), background)
    canvas.paste(top_panel, (0, 0))
    canvas.paste(panel, (0, top_height))
    apply_split_fringe(canvas, top_panel, top_height, torn_settings)

    raw_crops = spec.get("crops")
    poem = spec.get("poem")
    if not isinstance(raw_crops, list) or not 2 <= len(raw_crops) <= 6:
        fail("`crops` must contain 2–6 crop definitions; 3–6 is preferred.")
    if not isinstance(poem, list) or not poem:
        fail("`poem` must be a non-empty list of runs.")
    crop_boxes: dict[str, tuple[float, float, float, float]] = {}
    for entry in raw_crops:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str) or not entry["id"]:
            fail("Every crop needs a non-empty string `id`.")
        crop_id = entry["id"]
        if crop_id in crop_boxes:
            fail(f"Duplicate crop id {crop_id!r}.")
        crop_boxes[crop_id] = validate_box(entry.get("box"), crop_id)
    crop_items = list(crop_boxes.items())
    for index, (first_id, first_box) in enumerate(crop_items):
        for second_id, second_box in crop_items[index + 1 :]:
            if boxes_overlap(first_box, second_box):
                fail(f"Crops {first_id!r} and {second_id!r} overlap; choose distinct regions.")

    sw, sh = source.size
    patches: dict[str, Image.Image] = {}
    hole_rects: dict[str, tuple[int, int, int, int]] = {}
    cut_masks: dict[str, Image.Image] = {}
    for crop_id, (x, y, crop_width, crop_height) in crop_boxes.items():
        left = round(x * sw * scale + offset_x)
        upper = round(y * sh * scale + offset_y)
        right = round((x + crop_width) * sw * scale + offset_x)
        lower = round((y + crop_height) * sh * scale + offset_y)
        if left < 0 or upper < 0 or right > canvas_width or lower > bottom_height:
            fail(f"Crop {crop_id!r} is clipped by the lower-panel fit/focus; revise its box or focus.")
        if right - left < 16 or lower - upper < 16:
            fail(f"Crop {crop_id!r} displays smaller than 16 px; enlarge its box.")
        absolute_rect = (left, top_height + upper, right, top_height + lower)
        patch = panel.crop((left, upper, right, lower)).convert("RGBA")
        mask = torn_mask(patch.size, torn_settings, crop_id)
        patch.putalpha(mask)
        patches[crop_id] = patch
        cut_masks[crop_id] = mask
        hole_rects[crop_id] = absolute_rect

    bottom_area = canvas_width * bottom_height
    void_area = sum((right - left) * (lower - upper) for left, upper, right, lower in hole_rects.values())
    if void_area / bottom_area > 0.12:
        fail("White voids occupy more than 12% of the lower panel; reduce crop sizes or count.")
    for crop_id, rect in hole_rects.items():
        left, upper, right, lower = rect
        hole = Image.new("RGB", (right - left, lower - upper), hole_color)
        canvas.paste(hole, (left, upper), cut_masks[crop_id])

    draw_poem(canvas, top_height, poem, patches, spec)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="PNG", optimize=True)
    return {
        "output": str(output_path.resolve()),
        "size": [canvas_width, canvas_height],
        "split": split,
        "background": "#%02X%02X%02X" % background,
        "crops": len(patches),
        "film_look": {
            "enabled": film_settings["enabled"],
            "strength": film_settings["strength"],
            "grain": film_settings["grain"],
        },
        "paper_texture": {
            "enabled": paper_settings["enabled"],
            "strength": paper_settings["strength"],
            "fiber": paper_settings["fiber"],
        },
        "print_style": parse_print_style(spec.get("print_style", "typewriter")),
        "torn_edges": {
            "enabled": torn_settings["enabled"],
            "roughness": torn_settings["roughness"],
            "split_roughness": torn_settings["split_roughness"],
            "fiber": torn_settings["fiber"],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, type=Path, help="Source photograph")
    parser.add_argument("--spec", required=True, type=Path, help="UTF-8 JSON render spec")
    parser.add_argument("--output", required=True, type=Path, help="Final PNG path")
    args = parser.parse_args()
    try:
        result = render(args.image, args.spec, args.output)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
