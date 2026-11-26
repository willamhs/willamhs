# Willam | Data & AI — design and portrait

## Identity

The header follows the supplied visual reference: a near-black background, electric-blue and cyan particle waves, a luminous isometric AI chip with six orbiting technology icons, white “Willam” lettering and a cyan “Data & AI” gradient. It deliberately omits the full-name label, monogram, education and location. Both GitHub themes retain this same cinematic header palette. Gradient social buttons and eight native HTML area cards extend the identity. All disciplines have equal visual treatment; no card is labeled as a primary direction.

Header colors include near-black `#01090E`, midnight blue `#010714`, electric blue `#0065F2`, cyan `#00CFFF`, ice blue `#84E4FF` and white `#FAFCFF`. The surrounding sections retain navy `#0A1425`, electric blue `#2563EB` and pale blue `#60A5FA`. The vector recreation is built by `scripts/header_art.py`; all light effects and particle dots are static SVG elements. It is not a bitmap copy of the reference.

GitHub strips custom page CSS and scripts from READMEs. The profile therefore uses native Markdown, ordinary HTML paragraphs, expandable details, self-contained SVG images and `<picture>` sources with `prefers-color-scheme`. Width-constrained images scale within GitHub's content column. The social buttons wrap naturally; project text remains selectable, searchable and accessible at narrow widths. About Me places the actual ASCII vector beside the text on desktop and beneath it on phones. The portrait is nested as real SVG text, never as an embedded bitmap.

The header, About Me composition, footer, portrait and activity chart have light and dark variants. Separate mobile compositions keep their text readable without squeezing desktop artwork. Area cards are native HTML tables with equal-width columns, selectable headings, descriptions, project counters and repository links. Only the decorative black-to-blue headers and original-color brand icons are static SVGs. Native GitHub styling adapts the text to the theme. A README cannot use custom CSS to turn a two-column table into a single-column grid on phones; long unbroken tokens may require native horizontal scrolling.

The portrait uses solid black, heavier monospace glyphs on a white field, including in dark mode; its navy frame fits the surrounding design. The portrait is larger in both About Me compositions so that facial detail survives downscaling. The roadmap uses neutral icon tiles to preserve original brand colors and retain contrast. All images have meaningful alt text or empty alt text when decorative. No external fonts or JavaScript are required.

## Portrait processing

The only portrait input was the user-supplied `perfil.jpg`, 1087 × 1447 pixels. The source is deliberately left outside the public repository; the public outputs are genuinely derived ASCII.

Reproduction:

```bash
python -m pip install -r requirements.txt
python scripts/generate_ascii.py /path/to/perfil.jpg --columns 160 --ink black
```

The pipeline corrects EXIF orientation and uses an explicit crop `(285, 130, 825, 715)` around the original hair, face, neck and shoulders. OpenCV GrabCut attenuates the plain studio background. A modest bilateral filter, blended CLAHE local contrast and mild unsharp masking preserve the source expression without geometric face warping or synthetic reconstruction.

The grayscale crop is downsampled using Lanczos at **80, 120 and 160 columns**. Row counts account for the cell's 6.6-to-11 width/height ratio. Printable ASCII glyphs are selected by calibrated bold-font ink density, with a mild midtone gain of 0.84. Displayed glyphs use weight 600 and solid black for greater visibility at README size. Every non-space glyph is positioned explicitly in SVG to prevent cumulative font fallback drift, and spaces remain present in the text export.

The SVGs contain only uniform background rectangles, groups and visible ASCII text, plus accessibility metadata. They contain no source bitmap, embedded raster, face-shaped paths or external references. Each generated SVG glyph is checked against the selected text file in the tests.

Outputs:

- `assets/ascii/portrait.txt`: selected 160-column text.
- `portrait-light.svg` and `portrait-dark.svg`: high-contrast black ASCII, with theme-aware frames.
- `portrait-blue.svg`: optional blue-ink alternative.
- `portrait-mono.svg`: black and white.
- `portrait-{80,120,160}.txt` and `portrait-{80,120,160}-{light,dark,mono}.svg`: review alternatives.
- `parameters.json`: crop, character scale, selected resolution and processing notes.
- `preview/ascii-comparison.png`: local side-by-side comparison, excluded from Git.

Visual comparison selected 160 columns because it better preserves the hair outline, eye spacing, teeth and smile than 80 columns. Recognition remains subjective: ASCII loses fine texture. Black ink, heavier glyphs and the enlarged 300-pixel desktop portrait improve perceived contrast. At README size, individual glyphs merge into tonal detail; opening the SVG reveals the characters. The supplied variants remain available for personal review. Font renderers may introduce small differences between Windows and Linux; fixed coordinates preserve the overall proportions.

## Editorial credibility

The README expresses the supplied Computer Science background, Peru location and AI Engineering goal. It does not assert employment, seniority, certifications, expert status, project outcomes or tools not supported by public work. Requested technologies are presented explicitly as a learning roadmap. Code and repository metadata provide a separate evidence path.

The eight core disciplines remain visible in **Areas and projects**, with honest empty states. Real projects are generated directly inside the matching area's HTML card. Business Intelligence is separate from Data Analytics; Cloud Computing is separate from MLOps & LLMOps. Software Engineering and Other Projects appear when populated. The initial public inventory has no recognized specialty topics, so **Other Projects** is the accurate initial presentation for those repositories. Adding truthful descriptions and topics makes the portfolio more informative.

`scripts/portfolio_areas.py` generates the native area markup and small colored-icon headers. `config/categories.json` defines the categories and their technology marks. The composite focus-grid images were removed so a design build cannot restore the old image-based layout. The hourly updater preserves all manually authored content outside its markers.
