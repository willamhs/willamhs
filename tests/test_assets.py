from pathlib import Path
import json
import xml.etree.ElementTree as ET

import numpy as np

from scripts.common import ROOT
from scripts.generate_ascii import ascii_rows, portrait_svg
from scripts.validate_profile import validate


def test_all_local_assets_are_valid():
    validate()


def test_ascii_dimensions_and_aspect():
    rows = ascii_rows(np.tile(np.linspace(0,255,100,dtype=np.uint8),(150,1)),120)
    assert len(rows) == 108
    assert all(len(row) == 120 for row in rows)
    assert all(32 <= ord(c) <= 126 for row in rows for c in row)
    assert all(row[-1] == " " for row in rows)


def test_svg_escapes_glyphs_and_contains_no_image():
    for theme in ("light","dark","mono"):
        svg = portrait_svg(['<&" >', '@#  .'],theme)
        root = ET.fromstring(svg)
        assert "<image" not in svg and "data:image" not in svg
        assert "&lt;" in svg and "&amp;" in svg
        assert len(list(root.iter('{http://www.w3.org/2000/svg}text'))) == 7


def test_selected_svg_encodes_the_text_exactly():
    rows = (ROOT / "assets/ascii/portrait.txt").read_text(encoding="ascii").splitlines()
    for theme in ("light","dark","mono"):
        tree = ET.parse(ROOT / f"assets/ascii/portrait-{theme}.svg")
        glyphs = list(tree.iter('{http://www.w3.org/2000/svg}text'))
        assert ''.join(e.text for e in glyphs) == ''.join(c for row in rows for c in row if c != ' ')


def test_icon_sources_have_real_local_files():
    manifest = json.loads((ROOT / "assets/icons/sources.json").read_text(encoding="utf-8"))
    for icon, source in manifest.items():
        assert (ROOT / f"assets/icons/tech/{icon}.svg").exists()
        assert len(source["sha256"]) == 64
        assert source["url"].startswith("https://")
