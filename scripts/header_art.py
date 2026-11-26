"""Static vector recreation of the supplied black, electric-blue and cyan banner."""
from __future__ import annotations

import math


ICONS = {
    "chart": '<path d="M-16 14h32M-13 12V2h5v10m6 0V-5h5v17m6 0v-25h5v25"/>',
    "database": '<ellipse cy="-10" rx="14" ry="6"/><path d="M-14-10v21c0 8 28 8 28 0v-21M-14-3c0 8 28 8 28 0m-28 8c0 8 28 8 28 0"/>',
    "brain": '<path d="M0-11c-7-12-15-3-12 2-9 1-9 12-3 14-4 9 7 17 15 9m0-25c7-12 15-3 12 2 9 1 9 12 3 14 4 9-7 17-15 9V-11M-8-6l3 5-5 5m18-10L5-1l5 5M-8 10l8 4 8-4"/>',
    "cloud": '<path d="M-14 11c-11-1-10-15 0-16 1-16 24-16 27-2 15-1 17 18 3 18h-30Z"/>',
    "code": '<path d="m-12-10-11 10 11 10m24-20 11 10-11 10M5-15l-10 30"/>',
    "cubes": '<path d="m0-19 11 6v13L0 6-11 0v-13L0-19Zm-11 6L0-7l11-6M0-7V6m-11-6-11 7v13l11 6 11-6V6m-22 1 11 6L0 6m-11 7v13M11 0l11 7v13l-11 6-11-6m22-13-11 6L0 6m11 7v13"/>',
}


def particle_waves(width: int, height: int) -> str:
    """Perspective particle ribbons, sampled deterministically as visible dots."""
    parts = []
    mobile = width < 600
    # In mobile the art occupies the lower half, behind the compact chip.
    base_height = height - (95 if mobile else 80)
    for layer in (0, 1):
        start = 170 if mobile else (480 if layer else 300)
        end = width + 30
        step = 7 if mobile else 9
        amplitude = 27 if mobile else (58 if layer == 0 else 34)
        phase = 1.5 if layer == 0 else -0.9
        for row in range(19):
            depth = row / 18
            for x in range(start, end, step):
                xx = x + (row % 2)*step/2
                wave = math.sin(xx/(72 if mobile else 125)+phase)
                yy = base_height + amplitude*wave + depth*(61 if mobile else 90)
                yy += (1-depth)*math.sin(xx/(130 if mobile else 230))*11
                alpha = (0.82 if layer else 0.43)*(1-depth)**1.1
                alpha *= min(1, max(0, (xx-start)/130))
                color = ("#00BDFF" if row < 3 else "#007CFF") if layer else "#0659FF"
                radius = (0.75 if mobile else 1.05)*(1-0.35*depth)
                if yy < height+2 and alpha > .015:
                    parts.append(f'<ellipse cx="{xx:.1f}" cy="{yy:.1f}" rx="{radius:.2f}" ry="{radius*.61:.2f}" fill="{color}" opacity="{alpha:.3f}"/>')
        points=[]
        for x in range(start,end,4):
            yy=base_height+amplitude*math.sin(x/(72 if mobile else 125)+phase)+math.sin(x/(130 if mobile else 230))*11
            points.append(f'{x},{yy:.1f}')
        path='M'+' '.join(points)
        parts.append(f'<path d="{path}" fill="none" stroke="url(#wave-stream)" stroke-width="{3.5 if layer else 2.3}" opacity="{.9 if layer else .6}" filter="url(#wave-glow)"/>')
        parts.append(f'<path d="{path}" fill="none" stroke="url(#wave-stream)" stroke-width="{1 if layer else .75}" opacity="{.95 if layer else .55}"/>')
    return '\n'.join(parts)


def chip_art(cx: float, cy: float, scale: float = 1) -> str:
    parts=[f'<g transform="translate({cx} {cy}) scale({scale})">',
        '<ellipse cy="72" rx="112" ry="45" fill="#003BBA" opacity="0.15" filter="url(#halo)"/>',
        '<circle r="144" fill="none" stroke="url(#orbit)" stroke-width="1.5"/>',
        '<circle r="144" fill="none" stroke="#008FFF" stroke-width="1.5" opacity="0.22" filter="url(#wave-glow)"/>']
    # Parallel rounded diamond layers create the isometric chip in the reference.
    diamond='M-15-63Q-8-69 2-65L86-30Q101-24 88-13L14 45Q5 52-7 48L-85 15Q-99 9-87-2Z'
    for y,fill,stroke in [(47,"#020E27","#0057D8"),(35,"#031435","#0069E8"),(22,"#041838","#00A8FF")]:
        parts.append(f'<path d="{diamond}" transform="translate(0 {y})" fill="{fill}" stroke="{stroke}" stroke-opacity="0.58" stroke-width="0.8"/>')
    parts.extend([
        f'<path d="{diamond}" transform="translate(0 14)" fill="#012665" stroke="#00D5FF" stroke-width="3.2" filter="url(#chip-glow)"/>',
        f'<path d="{diamond}" transform="translate(0 14)" fill="#03204D" stroke="#77F4FF" stroke-width="1.8"/>',
        f'<path d="{diamond}" fill="url(#chip-face)" stroke="#00C8FF" stroke-width="1.2"/>',
        '<path d="M-10-53Q-6-56 2-53L75-24Q80-22 74-17L9 33Q5 37-4 33L-74 4Q-81 0-74-6Z" fill="#020D25" stroke="#036BE3" stroke-width="0.65"/>',
        '<g transform="matrix(1 .18 -.28 .78 -3 -6)"><text x="0" y="12" font-family="Arial,Helvetica,sans-serif" font-size="51" font-weight="700" text-anchor="middle" fill="#35CFFF" filter="url(#chip-glow)">AI</text><text x="0" y="12" font-family="Arial,Helvetica,sans-serif" font-size="51" font-weight="700" text-anchor="middle" fill="#55DEFF">AI</text></g>'
    ])
    positions=[("chart",0,-144),("database",-122,-78),("brain",126,-78),("cloud",-139,42),("code",131,49),("cubes",0,144)]
    for icon,x,y in positions:
        parts.append(f'<g transform="translate({x} {y})"><rect x="-27" y="-25" width="54" height="50" rx="12" fill="#020C1C" stroke="#008CFF" stroke-width=".9"/><rect x="-27" y="-25" width="54" height="50" rx="12" fill="none" stroke="#006AFF" stroke-width="1" opacity=".35" filter="url(#wave-glow)"/><g transform="scale(.82)" fill="none" stroke="#84E4FF" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">{ICONS[icon]}</g></g>')
    return '\n'.join(parts)+'</g>'


def create_header(theme="dark", mobile=False):
    # Both GitHub themes deliberately retain the reference's cinematic palette.
    width,height=(440,440) if mobile else (1200,400)
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="header-title header-description">',
        '<title id="header-title">Willam | Data &amp; AI</title>',
        '<desc id="header-description">From curiosity to intelligent systems. Black and midnight-blue background, cyan lettering, a luminous AI chip surrounded by data and technology icons, and electric-blue particle waves.</desc>',
        f'''<defs>
<linearGradient id="night" x1="0" y1="0" x2="1" y2=".8"><stop stop-color="#01090E"/><stop offset=".5" stop-color="#010714"/><stop offset="1" stop-color="#021032"/></linearGradient>
<radialGradient id="corner"><stop stop-color="#005CE8" stop-opacity=".88"/><stop offset=".45" stop-color="#003582" stop-opacity=".25"/><stop offset="1" stop-color="#000818" stop-opacity="0"/></radialGradient>
<radialGradient id="bottom"><stop stop-color="#043EB7" stop-opacity=".52"/><stop offset="1" stop-color="#00133C" stop-opacity="0"/></radialGradient>
<linearGradient id="letter-blue" x1="0" y1="1" x2="1" y2="0"><stop stop-color="#169BF9"/><stop offset="1" stop-color="#49D5EF"/></linearGradient>
<linearGradient id="rule"><stop stop-color="#00BAFF"/><stop offset=".26" stop-color="#005DEB"/><stop offset="1" stop-color="#003BB3" stop-opacity="0"/></linearGradient>
<linearGradient id="wave-stream"><stop stop-color="#005BFF" stop-opacity="0"/><stop offset=".25" stop-color="#006CFF"/><stop offset=".60" stop-color="#5AEEFF"/><stop offset="1" stop-color="#006CFF"/></linearGradient>
<linearGradient id="orbit"><stop stop-color="#007BE8"/><stop offset=".33" stop-color="#31D6FF"/><stop offset=".66" stop-color="#0861E1"/><stop offset="1" stop-color="#2EDBFF"/></linearGradient>
<linearGradient id="chip-face" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#06142D"/><stop offset="1" stop-color="#00265C"/></linearGradient>
<filter id="chip-glow" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="3"/></filter>
<filter id="wave-glow" x="-15%" y="-100%" width="130%" height="300%"><feGaussianBlur stdDeviation="2.3"/></filter>
<filter id="halo" x="-80%" y="-100%" width="260%" height="300%"><feGaussianBlur stdDeviation="13"/></filter>
<clipPath id="bounds"><rect width="{width}" height="{height}" rx="14"/></clipPath>
</defs><g clip-path="url(#bounds)"><rect width="{width}" height="{height}" fill="url(#night)"/>
<ellipse cx="{width}" cy="-12" rx="{width*.32}" ry="{height*.58}" fill="url(#corner)"/>
<ellipse cx="-10" cy="{height+60}" rx="{width*.4}" ry="{height*.60}" fill="url(#bottom)"/>''']
    parts.append(particle_waves(width,height))
    if mobile:
        parts.append(chip_art(286,266,.62))
        parts.append('''<g font-family="Arial,Helvetica,sans-serif"><text x="25" y="73" font-size="43" letter-spacing="-1.8" font-weight="700" fill="#FAFCFF">Willam</text><rect x="178" y="37" width="5" height="44" rx="2" fill="#006BFF"/><text x="195" y="73" font-size="42" letter-spacing="-1.7" font-weight="700" fill="url(#letter-blue)">Data &amp; AI</text>
<text x="27" y="112" font-size="17" fill="#BBD5E8">From curiosity to intelligent systems.</text>
<rect x="27" y="140" width="230" height="5" rx="2.5" fill="url(#rule)"/>
<rect x="27" y="385" width="4" height="34" rx="2" fill="url(#rule)"/>
<text x="42" y="396" font-size="10" font-weight="600" letter-spacing="1.1" fill="#A6C2DF">LEARN WITH PURPOSE. BUILD WITH CARE.</text>
<text x="42" y="414" font-size="10" font-weight="600" letter-spacing="1.1" fill="#A6C2DF">SHARE WHAT WORKS.</text></g>''')
    else:
        parts.append(chip_art(960,175,.90))
        parts.append('''<g font-family="Arial,Helvetica,sans-serif"><text x="65" y="164" font-size="73" letter-spacing="-3" font-weight="700" fill="#FAFCFF">Willam</text><rect x="332" y="110" width="8" height="64" rx="2" fill="#0065F2"/><text x="355" y="164" font-size="72" letter-spacing="-3" font-weight="700" fill="url(#letter-blue)">Data &amp; AI</text>
<text x="69" y="212" font-size="27" letter-spacing="-.4" fill="#BBD5E8">From curiosity to intelligent systems.</text>
<rect x="71" y="243" width="265" height="6" rx="3" fill="url(#rule)"/><rect x="71" y="243" width="64" height="6" rx="3" fill="#00AFFF" opacity=".85"/>
<rect x="71" y="319" width="5" height="27" rx="2.5" fill="#007BFF"/>
<text x="88" y="337" font-size="13" font-weight="600" letter-spacing="2" fill="#ADC5E4">LEARN WITH PURPOSE. BUILD WITH CARE. SHARE WHAT WORKS.</text></g>''')
    return '\n'.join(parts)+'</g></svg>\n'
