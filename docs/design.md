# Willam | Data & AI — design and portrait

## Identity

The identity uses a custom W monogram, a restrained circuit motif, numbered editorial sections and a subtle blue gradient. The banner is an original static SVG, not a remote rendering service. The palette is navy `#0A1425`, slate `#0F172A`, electric blue `#2563EB`, pale blue `#60A5FA`, white `#F8FAFC` and gray `#94A3B8`.

GitHub strips custom page CSS and scripts from READMEs. The profile therefore uses native Markdown, ordinary HTML paragraphs, expandable details, self-contained SVG images and `<picture>` sources with `prefers-color-scheme`. Width-constrained images scale within GitHub's content column. The social buttons wrap naturally; project text remains selectable, searchable and accessible at narrow widths. The portrait sits inside About Me in a single column so that phones do not inherit an unreadable two-column table.

The header, portrait and activity chart each have explicit light and dark variants, with light as the fallback. The activity chart also has a 400-pixel mobile composition with larger labels. The dark portrait uses a pale blue inner field inside a navy frame so the face retains its original positive tonal relationships rather than becoming a photographic negative. The roadmap uses neutral icon tiles to preserve the original brand colors and retain contrast for black/navy logos in both modes. All images have meaningful alt text or empty alt text when decorative. No external fonts or JavaScript are required.

## Portrait processing

The only portrait input was the user-supplied `perfil.jpg`, 1087 × 1447 pixels. The source is deliberately left outside the public repository; the public outputs are genuinely derived ASCII.

Reproduction:

```bash
python -m pip install -r requirements.txt
python scripts/generate_ascii.py /path/to/perfil.jpg --columns 160
```

The pipeline corrects EXIF orientation and uses an explicit crop `(285, 130, 825, 715)` around the original hair, face, neck and shoulders. OpenCV GrabCut attenuates the plain studio background. A modest bilateral filter, blended CLAHE local contrast and mild unsharp masking preserve the source expression without geometric face warping or synthetic reconstruction.

The grayscale crop is downsampled using Lanczos at **80, 120 and 160 columns**. Row counts account for the cell's 6.6-to-11 width/height ratio. Printable ASCII glyphs are selected by calibrated font ink density. Every non-space glyph is positioned explicitly in SVG to prevent cumulative font fallback drift, and spaces remain present in the text export.

The SVGs contain only uniform background rectangles, groups and visible ASCII text, plus accessibility metadata. They contain no source bitmap, embedded raster, face-shaped paths or external references. Each generated SVG glyph is checked against the selected text file in the tests.

Outputs:

- `assets/ascii/portrait.txt`: selected 160-column text.
- `portrait-light.svg` and `portrait-dark.svg`: blue theme variants.
- `portrait-mono.svg`: black and white.
- `portrait-{80,120,160}.txt` and `portrait-{80,120,160}-{light,dark,mono}.svg`: review alternatives.
- `parameters.json`: crop, character scale, selected resolution and processing notes.
- `preview/ascii-comparison.png`: local side-by-side comparison, excluded from Git.

Visual comparison selected 160 columns because it better preserves the hair outline, eye spacing, teeth and smile than 80 columns. Recognition remains subjective: ASCII loses fine texture and blue shading changes perceived contrast. At the 280-pixel README display size, individual glyphs merge into tonal detail; opening the SVG reveals the characters. The supplied variants remain available for personal review. A font renderer may introduce small differences between Windows and Linux; fixed character coordinates preserve the overall proportions.

## Editorial credibility

The README expresses the supplied Computer Science background, Peru location and AI Engineering goal. It does not assert employment, seniority, certifications, expert status, project outcomes or tools not supported by public work. Requested technologies are presented explicitly as a learning roadmap. Code and repository metadata provide a separate evidence path.

All empty specialties stay hidden until a real repository has a matching topic. The initial public inventory has no recognized specialty topics, so **Other Projects** is the accurate initial presentation. Adding truthful descriptions and topics to existing repositories will make the portfolio more informative.
