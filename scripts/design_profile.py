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

FOCUS_AREAS = [
    ("ai", "AI Engineering", "Generative AI · LLMs · RAG · AI agents", "Intelligent applications with a clear purpose.", "PRIMARY DIRECTION"),
    ("analytics", "Data Analytics", "Python · SQL · Exploratory analysis", "Find the story behind the numbers.", "UNDERSTAND"),
    ("dashboard", "Business Intelligence", "Power BI · Tableau · Data storytelling", "Turn complex data into clear decisions.", "COMMUNICATE"),
    ("science", "Data Science", "Statistics · Experiments · Predictive analysis", "Explore patterns. Ask better questions.", "DISCOVER"),
    ("neural", "Machine Learning & Deep Learning", "Scikit-learn · PyTorch · TensorFlow", "Learn how models predict, see and adapt.", "MODEL"),
    ("pipeline", "Data Engineering", "ETL / ELT · Spark · Data pipelines", "Build the foundations of useful data products.", "CONNECT"),
    ("cloud", "Cloud Computing", "Google Cloud · AWS · Microsoft Azure", "Bring data and intelligent systems together.", "SCALE"),
    ("code", "MLOps & LLMOps", "Evaluation · Deployment · Observability", "Make intelligent systems more dependable.", "OPERATE"),
]


def svg_start(width, height, title, desc=""):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="visual-title visual-desc">',
        f'<title id="visual-title">{escape(title)}</title><desc id="visual-desc">{escape(desc)}</desc>']


def hero(theme="dark", mobile=False):
    try:
        from .header_art import create_header
    except ImportError:
        from header_art import create_header
    return create_header(theme,mobile)


def focus_grid(theme, icons, mobile=False):
    dark = theme == "dark"
    width, card_w, gap, pad = (440, 416, 14, 12) if mobile else (1120, 542, 16, 10)
    rows = len(FOCUS_AREAS) if mobile else 4
    card_h = 184 if mobile else 188
    height = rows*card_h+(rows-1)*gap+2*pad
    bg, ink, secondary, border = ("#0B1B35", "#F8FAFC", "#A8BFDE", "#244776") if dark else ("#F5F9FF", "#0F2852", "#48658B", "#CDDEF7")
    parts = svg_start(width,height,"Eight areas of focus", "Learning roadmap: AI Engineering and Generative AI; Data Analytics; Business Intelligence; Data Science; Machine Learning and Deep Learning; Data Engineering; Cloud Computing; MLOps and LLMOps. Areas of interest, not claims of professional experience.")
    parts.append(f'''<defs><linearGradient id="primary" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#0D3378"/><stop offset="1" stop-color="#2563EB"/></linearGradient><linearGradient id="card"><stop stop-color="{bg}"/><stop offset="1" stop-color="{'#10284F' if dark else '#EAF3FF'}"/></linearGradient><linearGradient id="accent"><stop stop-color="#2563EB"/><stop offset="1" stop-color="#60A5FA"/></linearGradient></defs>''')
    for index, (icon,title,tags,description,label) in enumerate(FOCUS_AREAS):
        x = pad if mobile else pad+(index%2)*(card_w+gap)
        y = pad+(index if mobile else index//2)*(card_h+gap)
        primary = index == 0
        text = "#F8FAFC" if primary else ink
        muted = "#BFDBFE" if primary else secondary
        parts.append(f'<g transform="translate({x} {y})"><rect x="1" y="1" width="{card_w-2}" height="{card_h-2}" rx="18" fill="url(#{"primary" if primary else "card"})" stroke="{"#60A5FA" if primary else border}"/><rect x="22" y="0" width="66" height="3" rx="1.5" fill="url(#accent)"/>')
        parts.append(f'<rect x="22" y="21" width="40" height="40" rx="11" fill="{"#DBEAFE" if primary else "#2563EB"}" fill-opacity="0.12"/><svg x="31" y="30" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="{"#DBEAFE" if primary else "#3B82F6"}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{icons[icon]}</svg>')
        parts.append(f'<g font-family="Arial,Helvetica,sans-serif"><text x="{card_w-24}" y="44" font-size="10" font-weight="700" letter-spacing="1.4" text-anchor="end" fill="{muted}">{label}</text>')
        size = 20 if mobile and len(title)>30 else 23
        parts.append(f'<text x="23" y="91" font-size="{size}" font-weight="700" fill="{text}">{escape(title)}</text>')
        parts.append(f'<text x="23" y="122" font-size="{14 if mobile else 16}" fill="{muted}">{escape(description)}</text>')
        parts.append(f'<text x="23" y="157" font-size="{12 if mobile else 13}" fill="{muted}">{escape(tags)}</text></g></g>')
    return '\n'.join(parts)+'</svg>\n'


def about_card(theme, mobile=False):
    dark = theme == "dark"
    width, height = (440,710) if mobile else (1120,420)
    bg,ink,muted = ("#0B1B35","#F8FAFC","#A8BFDE") if dark else ("#F0F6FF","#102B55","#48658B")
    parts = svg_start(width,height,"Meet Willam Huaman", "Computer Science background, based in Peru. Focused on learning AI Engineering and sharing data and AI knowledge. The portrait is actual ASCII derived from Willam's supplied photograph.")
    parts.append(f'<defs><linearGradient id="about-blue"><stop stop-color="{bg}"/><stop offset="1" stop-color="{"#123C7D" if dark else "#DFEBFF"}"/></linearGradient></defs><rect x="1" y="1" width="{width-2}" height="{height-2}" rx="20" fill="url(#about-blue)" stroke="{"#244776" if dark else "#CDDEF7"}"/>')
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


def build_identity(icons):
    for theme in ('light','dark'):
        for mobile in (False,True):
            suffix=f'{theme}{"-mobile" if mobile else ""}'
            atomic_write(ROOT / f'assets/banners/header-{suffix}.svg',hero(theme,mobile))
            atomic_write(ROOT / f'assets/areas/focus-{suffix}.svg',focus_grid(theme,icons,mobile))
            atomic_write(ROOT / f'assets/banners/about-{suffix}.svg',about_card(theme,mobile))
            atomic_write(ROOT / f'assets/banners/footer-{suffix}.svg',footer(theme,mobile))
