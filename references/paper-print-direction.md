# Paper, print, and torn-edge direction

Use this guide to add tactile material character without changing the clean contemporary mood.

## Upper paper field

- Keep the source-derived Morandi hue, pale value, and low saturation.
- Add fine neutral luminance grain and a sparse scattering of short fibres. Texture should become apparent at full resolution, not from across the room.
- Preserve a clean field around the centered poem. Paper texture is a material cue, not a decorative background.
- Do not add yellowing, sepia, stains, foxing, creases, burn marks, torn corners, printed illustrations, vintage ephemera, or a nostalgic color cast.

## Printed typography

- Use a monospaced Courier-style mechanical typewriter skeleton. Prefer an installed Courier New Bold/Courier face over a clean proportional display typewriter; do not copy, extract, or package a font from a reference image.
- Render each glyph as its own typebar strike. Vary pressure, horizontal registration, and baseline by less than about one pixel at the default size, then add restrained ribbon-ink spread.
- Give the ink small density changes within strokes: a few pale pinholes, slightly heavier edge deposits, and occasional faint offset impressions. Letters should not repeat as perfectly identical digital stamps.
- Apply the same treatment to letters, punctuation, and brackets. Preserve a calm baseline and regular monospaced rhythm; do not rotate glyphs, use alternate fonts per letter, or create ransom-note typography.
- Keep ink near black and optically solid at reading distance. Reduce variation before counters close, thin strokes disappear, words gray out, or texture becomes more noticeable than the sentence.

## Fragment and void edges

- Use one deterministic mask per crop and reuse it for the upper photo fragment and lower white void so the correspondence remains exact.
- Build each edge from three scales: a slow tear contour, scattered single-pixel notches, and a sparse semi-transparent cellulose fringe. A generic smooth wave or uniformly blurred rectangle is not sufficient.
- Keep each silhouette almost rectangular. At 1536 × 2048, the contour should ordinarily move only 1–3 px, with a few partly transparent fibres extending about one additional pixel.
- Let inner edge fibres partially reveal the photograph or paper below and let outer fibres remain sparse. The edge should feel physically separated, not feathered by a software blur.
- Do not add outlines, drop shadows, bevels, curled paper, white borders around upper fragments, or chunky torn-paper silhouettes.

## Central split

- Preserve the mathematical 50/50 panel division. A paper overhang of roughly 1–3 px may interrupt the otherwise straight boundary.
- Reuse the same multiscale logic at the split: a restrained contour, micro-notches, and sparse semi-transparent fibres carrying the actual upper-paper texture.
- Keep the split quiet and continuous. It should feel like the lower edge of a real paper sheet, not a repeated digital wave, ripped collage seam, or decorative divider.

## Strength decisions

- Use the default `subtle` settings for ordinary requests.
- Lower paper, print, and torn-edge settings together for already textured scans or compression-heavy images.
- Raise only one characteristic at a time when explicitly requested. Never compensate for an unclear source by adding more distress.
