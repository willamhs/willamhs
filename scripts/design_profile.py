"""Original blue-gradient visual system for Willam's GitHub profile.

Static SVG only. Separate desktop/mobile layouts keep labels readable on phones.
The focus cards describe a learning direction, never fictitious completed work.
"""
from __future__ import annotations

from html import escape
from pathlib import Path

try:
    from .common import ROOT, atomic_write
except ImportError:
    from common import ROOT, atomic_write

def svg_start(width, height, title, desc=""):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="visual-title visual-desc">',
        f'<title id="visual-title">{escape(title)}</title><desc id="visual-desc">{escape(desc)}</desc>']


def hero(theme="dark", mobile=False):
    try:
        from .header_art import create_header
    except ImportError:
        from header_art import create_header
    return create_header(theme,mobile)


def about_card(theme, mobile=False):
    width, height = (440,710) if mobile else (1120,420)
    bg,ink,muted = "#000000","#F8FAFC","#B5C0D0"
    parts = svg_start(width,height,"Meet Willam Huaman", "Computer Science background, based in Peru. Focused on learning AI Engineering and sharing data and AI knowledge. The portrait is actual ASCII derived from Willam's supplied photograph.")
    parts.append(f'<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="20" fill="{bg}" stroke="#1E293B"/>')
    x,y = (27,44) if mobile else (44,55)
    parts.append(f'<g font-family="Arial,Helvetica,sans-serif"><text x="{x}" y="{y}" font-size="12" letter-spacing="2.2" fill="#3B82F6" font-weight="700">THE PERSON BEHIND THE DATA</text>')
    if mobile:
        parts.append(f'<text x="27" y="96" font-size="32" font-weight="700" fill="{ink}">Curious by nature.</text><text x="27" y="135" font-size="32" font-weight="700" fill="{ink}">Building with purpose.</text>')
        for i,line in enumerate(["Computer Science background.","Based in Peru. Growing toward AI Engineering.","Learning, creating and sharing along the way."]):
            parts.append(f'<text x="28" y="{182+i*27}" font-size="16" fill="{muted}">{line}</text>')
        px,py,pw,ph = 78,265,284,354
        bottom=674
    else:
        parts.append(f'<text x="44" y="128" font-size="43" font-weight="700" letter-spacing="-1" fill="{ink}">Curious by nature.</text><text x="44" y="180" font-size="43" font-weight="700" letter-spacing="-1" fill="{ink}">Building with purpose.</text>')
        for i,line in enumerate(["Computer Science background. Based in Peru.","Growing toward AI Engineering through practical learning.","Sharing the journey through Willam | Data &amp; AI."]):
            parts.append(f'<text x="46" y="{237+i*31}" font-size="20" fill="{muted}">{line}</text>')
        parts.append('<rect x="45" y="346" width="62" height="4" rx="2" fill="#2563EB"/><rect x="113" y="346" width="26" height="4" rx="2" fill="#60A5FA"/>')
        px,py,pw,ph = 758,24,300,370
        bottom=0
    parts.append('</g>')
    portrait=(ROOT / f'assets/ascii/portrait-{theme}.svg').read_text(encoding='utf-8')
    # Embed vector text, never a raster image, into this static composition.
    import re
    portrait=re.sub(r'<svg\b[^>]*>',lambda m: re.sub(r'\s(?:width|height)="[^"]*"','',m.group())[:-1]+f' x="{px}" y="{py}" width="{pw}" height="{ph}">',portrait,count=1)
    # Scope portrait accessibility IDs to avoid collisions inside the outer SVG.
    portrait=portrait.replace('id="title"','id="portrait-title"').replace('id="desc"','id="portrait-desc"').replace('aria-labelledby="title desc"','aria-labelledby="portrait-title portrait-desc"')
    parts.append(portrait)
    if mobile:
        parts.append(f'<text x="220" y="{bottom}" font-family="Arial,Helvetica,sans-serif" font-size="11" letter-spacing="2" fill="{muted}" text-anchor="middle">REAL PHOTO. REAL ASCII. MY IDENTITY.</text>')
    return '\n'.join(parts)+'</svg>\n'


def footer(theme, mobile=False):
    if mobile:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="440" height="160" viewBox="0 0 440 160" role="img" aria-label="Let us build something useful. Data, AI and technology education."><defs><linearGradient id="f"><stop stop-color="#0A285E"/><stop offset="1" stop-color="#2563EB"/></linearGradient></defs><rect width="440" height="160" rx="20" fill="url(#f)"/><g font-family="Arial,Helvetica,sans-serif" text-anchor="middle"><text x="220" y="57" font-size="25" font-weight="700" fill="#F8FAFC">Let’s build something useful.</text><text x="220" y="96" font-size="15" fill="#BFDBFE">Data. Intelligent systems.</text><text x="220" y="121" font-size="15" fill="#BFDBFE">Knowledge worth sharing.</text></g></svg>\n'
    parts=svg_start(1120,172,"Let's build something useful", "Connect with Willam about data, AI and technology education.")
    parts.append('<defs><linearGradient id="f"><stop stop-color="#0A285E"/><stop offset="1" stop-color="#2563EB"/></linearGradient></defs><rect width="1120" height="172" rx="20" fill="url(#f)"/><circle cx="1060" cy="20" r="100" fill="#60A5FA" opacity="0.12"/><g font-family="Arial,Helvetica,sans-serif" text-anchor="middle"><text x="560" y="71" font-size="34" font-weight="700" fill="#F8FAFC">Let’s build something useful.</text><text x="560" y="111" font-size="18" fill="#BFDBFE">Data. Intelligent systems. Knowledge worth sharing.</text></g></svg>\n')
    return '\n'.join(parts)


def build_identity():
    for theme in ('light','dark'):
        for mobile in (False,True):
            suffix=f'{theme}{"-mobile" if mobile else ""}'
            atomic_write(ROOT / f'assets/banners/header-{suffix}.svg',hero(theme,mobile))
            atomic_write(ROOT / f'assets/banners/about-{suffix}.svg',about_card(theme,mobile))
            atomic_write(ROOT / f'assets/banners/footer-{suffix}.svg',footer(theme,mobile))
