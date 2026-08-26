---
name: poetic-collage-grid-jl-paper
description: Create or revise a finished 3:4 vertical poetic diptych from one user-supplied photo, with equal upper and lower halves, a cinematic edge-to-edge photo below, real photo fragments inside a centered English poem above, authentic typewriter-ink lettering, and restrained cellulose-fibre torn edges. Use for the tactile paper-print variant of the Poetic Collage Grid JL style; do not use for nostalgic vintage posters, heavy distress, letterboxed photos, or layouts without one-to-one fragment mapping.
---

# Poetic Collage Grid JL — Paper Print

Create one finished PNG from one source photo. Preserve the source as photography: do not redraw, extend, distort, locally retouch, beautify, replace, or invent visual content. This is the tactile alternate to the clean `poetic-collage-grid-jl` look. Add physical surface character without turning the work into a vintage scene.

## Before composing

- Inspect the source image at full useful detail.
- Preserve user-supplied wording, palette, crop count, crop focus, or texture strength unless it makes the layout impossible.
- Write in English by default. Use another language only when explicitly requested.
- Derive the pale Morandi upper color from the photo unless the user provides one.
- Use the natural cinematic film look below and restrained paper-print treatment above by default.
- Read [poetry-and-crops.md](references/poetry-and-crops.md) before choosing words or regions.
- Read [film-look.md](references/film-look.md) before choosing the photographic finish.
- Read [paper-print-direction.md](references/paper-print-direction.md) before choosing texture or typography strength.
- Read [render-spec.md](references/render-spec.md) when preparing renderer input.

## Immutable visual logic

- Output exactly one portrait PNG at 3:4; default to 1536 × 2048 px.
- Divide it into two flush, equal horizontal panels. At the default size, each panel is 1536 × 1024 px.
- Fill the entire lower panel with a proportional `cover` crop of the source. Never stretch, squeeze, letterbox, pillarbox, or leave margins.
- Apply one coherent natural cinematic grade before extracting fragments: restrained saturation, soft highlight shoulder and shadow toe, subtly cool shadows, warm highlights, faint vignette, and very light monochromatic grain.
- Keep the upper Morandi field pale and low-saturation. Add only subtle neutral paper grain and sparse fine fibres. Do not yellow, stain, antique, sepia-tone, or add nostalgic props.
- Use 3–6 distinct, non-overlapping fragments from the visible lower panel. Two are acceptable for an extremely sparse image.
- Place each fragment inline within one compact poem and enclose it with one consistent bracket pair; use parentheses by default.
- Replace the exact matching lower region with solid white. Each upper fragment and lower void must retain the same aspect ratio, displayed dimensions, and lightly torn edge profile.
- Give fragment edges, void edges, and the central horizontal split a physically plausible but restrained torn-paper structure: a slow tear contour, fine micro-notches, and sparse semi-transparent cellulose fibres on both sides of the edge. Keep the overall silhouette nearly rectangular; no dramatic deckle edge.
- Use near-black typewriter ink over a monospaced mechanical typewriter skeleton. Render individual glyph strikes with small differences in pressure, baseline, ink spread, missing ink, and edge deposits. Readability and a calm shared baseline remain primary.
- Write one restrained English sentence or sentence-like clause, normally 12–24 words. It should read as one poem, not several captions.
- Let the renderer wrap it into 1–3 centered lines without manual breaks by default. Center the complete poem block horizontally and vertically in the upper panel.
- Default to 36 px at 1536 × 2048, with 34–40 px as the normal range. The smaller monospaced setting should resemble a real typed sentence rather than display lettering. Do not vary type family, color, or size within the poem.
- Do not add borders, shadows, rounded corners, arrows, labels, numbering, decorative rules, gradients, logos, watermarks, fake stock labels, light leaks, scratches, or dust.

## Compose and render

1. Identify the photograph's subject, atmosphere, time, material details, negative space, and quiet tension.
2. Select regions that can act as visual nouns or sensory evidence. Preserve identities and avoid awkward slices through faces, eyes, or joints unless requested.
3. Write one image-specific English sentence that reads naturally around the fragments.
4. Build a JSON spec using normalized source coordinates. Keep the poem runs continuous and use the default restrained texture settings unless the source needs a gentler treatment.
5. Run:

   ```bash
   python3 scripts/render_diptych.py --image /absolute/path/to/source.jpg --spec /absolute/path/to/spec.json --output /absolute/path/to/final.png
   ```

6. Inspect the PNG at full size. Revise and rerender when any acceptance check fails. Return only the final PNG unless the user explicitly asks for specs or intermediate assets.

## Acceptance checks

- Canvas is exactly 3:4 with two equal 50% panels; the lower image touches every edge of its panel and remains proportional.
- The lower photo reads as naturally cinematic rather than visibly filtered; skin, whites, shadows, and identifying colors remain credible.
- The upper field reads as clean Morandi paper, not as an aged or retro-colored background.
- Lettering reads as real ribbon ink from a mechanical typewriter: monospaced, dark, slightly pressure-varied, and imperfect per glyph, without becoming distressed, blurred, theatrical, or difficult to read.
- Every fragment is extracted from the graded lower photo and maps one-to-one to an equally sized white void with the identical restrained edge profile.
- Fragment, void, and split edges contain convincing micro-notches and translucent paper fibres rather than a generic wavy outline; the effect remains subtle, never chunky, fuzzy, ragged, or theatrical.
- Poem is English unless otherwise requested, occupies 1–3 lines, reads as one sentence or clause, and is centered as one block.
- No crop is clipped by the cover placement; no bracket splits across lines; no punctuation starts a line; no fragment is stranded alone.
- The poem is concrete and image-specific, with no stock inspirational language.
- Only the final PNG is returned.
