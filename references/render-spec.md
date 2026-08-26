# Render specification

The renderer consumes UTF-8 JSON. Coordinates are normalized to the original source image before the lower-panel `cover` fit.

## Minimal spec

```json
{
  "language": "en",
  "poem": [
    {"text": "The city spends "},
    {"crop": "light"},
    {"text": " too quickly, but "},
    {"crop": "sign"},
    {"text": " slows the night while "},
    {"crop": "boat"},
    {"text": " reaches the far bank first."}
  ],
  "crops": [
    {"id": "light", "box": [0.45, 0.40, 0.06, 0.06]},
    {"id": "sign", "box": [0.80, 0.38, 0.07, 0.06]},
    {"id": "boat", "box": [0.55, 0.55, 0.07, 0.035]}
  ]
}
```

Each `box` is `[x, y, width, height]`, with values from 0 to 1. It must remain fully visible after lower-panel fitting. Omitted surface settings use the restrained paper-print defaults.

## Full option set

```json
{
  "canvas": [1536, 2048],
  "split": 0.5,
  "fit": "cover",
  "focus": [0.5, 0.5],
  "film_look": {
    "enabled": true,
    "strength": 0.72,
    "grain": 0.024,
    "seed": 17
  },
  "paper_texture": {
    "enabled": true,
    "strength": 0.12,
    "fiber": 0.08,
    "seed": 61
  },
  "print_style": {
    "enabled": true,
    "ink_variation": 0.18,
    "registration_shift": 0.55,
    "baseline_jitter": 0.65,
    "ink_spread": 0.14,
    "seed": 67
  },
  "torn_edges": {
    "enabled": true,
    "roughness": 0.18,
    "split_roughness": 0.14,
    "fiber": 0.22,
    "seed": 73
  },
  "language": "en",
  "background": "auto",
  "text_color": "#171716",
  "hole_color": "#FFFFFF",
  "brackets": ["(", ")"],
  "font_path": null,
  "font_size": 36,
  "font_size_range": [34, 40],
  "max_lines": 3,
  "side_margin": 0.075,
  "top_padding": 0.10,
  "line_gap": 0.60,
  "poem": [],
  "crops": []
}
```

## Fields

- `canvas`: output dimensions; they must reduce exactly to 3:4.
- `split`: fixed at `0.5`. Both panels occupy exactly half the canvas; the subtle boundary fibre is only a visual overhang.
- `fit`: fixed at `cover`. The lower photo fills its half edge to edge without distortion or bars.
- `focus`: normalized source focus used to position the proportional cover crop.
- `film_look`: defaults to `cinematic`. An object accepts `enabled`, `strength` from 0 to 1, `grain` from 0 to 0.10, and integer `seed`. Prefer `strength` around 0.45–0.88 and `grain` around 0.02–0.04.
- `paper_texture`: defaults to `subtle`. An object accepts `enabled`, `strength` from 0 to 0.35, `fiber` from 0 to 0.30, and integer `seed`. The normal range is `strength` 0.08–0.18 and `fiber` 0.04–0.12.
- `print_style`: defaults to `typewriter`; `letterpress` remains a compatible alias. An object accepts `enabled`, `ink_variation` from 0 to 0.40, `registration_shift` from 0 to 1.5 px, `baseline_jitter` from 0 to 1.5 px, `ink_spread` from 0 to 0.35, and integer `seed`. The defaults reproduce dark mechanical ribbon ink with restrained per-glyph irregularity; increase one characteristic at a time.
- `torn_edges`: defaults to `subtle`. An object accepts `enabled`, `roughness` from 0 to 0.60, `split_roughness` from 0 to 0.50, `fiber` from 0 to 0.60, and integer `seed`. `fiber` controls the sparse semi-transparent cellulose fringe shared by each fragment/void pair and used again at the central split. Keep the three texture values below roughly 0.30 unless the user explicitly asks for stronger edges.
- `language`: defaults to `en`. Change it only when the user explicitly requests another language.
- `background`: `auto` derives a pale Morandi color from the graded image. A custom hex color should remain pale and low-saturation.
- `font_path`: optional absolute path to a user-authorized installed font. The renderer prefers an installed Courier New Bold/Courier-style monospaced face for English and does not package system or reference-image fonts.
- `font_size`: defaults to 36 px at 1536 × 2048. Set it to `null` only for automatic selection inside `font_size_range`.
- `max_lines`: defaults to 3; values above 3 are rejected.
- `side_margin` and `top_padding`: fractions of the upper panel.
- `line_gap`: multiple of the font size between visual lines.
- `poem`: ordered runs using `{"text":"…"}` and `{"crop":"id"}`. Explicit breaks are supported only for deliberate 2–3-line cadence.
- `crops`: unique IDs and normalized source rectangles. Every crop must occur exactly once in the poem.

## Coordinate workflow

1. Set `focus` for the fixed 3:2 lower-panel viewport. Portrait sources lose top and bottom content, so preserve the narrative center deliberately.
2. Choose source regions that remain fully visible under that cover placement.
3. Express each region in normalized source coordinates.
4. Choose film and surface strengths. Omit them for the default restrained treatment.
5. Keep displayed fragments appropriate for inline typography. The renderer uses one mask per fragment/void pair, preserving size, aspect ratio, and edge profile.
6. Run the renderer. If it reports clipping, overflow, or more than three lines, revise the crop, focus, or poem; do not change the 50/50 split or cover fit.
