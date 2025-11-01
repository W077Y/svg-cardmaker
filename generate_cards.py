#!/usr/bin/env python3

import argparse
import json
import re
import base64
from glob import glob
from pathlib import Path
from string import Template

SVG_TEMPLATE = r"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="${card_w}px" height="${card_h}px" viewBox="0 0 ${card_w} ${card_h}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    ${clipping_art}
  </defs>

  <!-- frame -->
  ${frame_str}
  
  <!-- Title bar -->
  ${title_str}

  <!-- Art -->
  ${art_img}

  <!-- Type line -->
  ${type_str}

  <!-- Rules text box -->
  ${rules_str}

  <!-- Optional -->
  ${opt_str}

  <!-- Footer -->
  ${footer_str}
</svg>
"""

def data_uri_for_image(path, mime="image/png"):
    p = Path(path)
    if not p.exists():
        return None
    data = p.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}"

def wrap_svg_text(text, width_chars=62, line_height=20, x=None):  
    if isinstance(text, list):
        tmp = ""
        for el in text:
            tmp += el + "\n"
        text = tmp

    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    lines = []
    for para in text.split("\n"):
        if para.strip() == "":
            lines.append({"text": "", "newline": True})
            continue
        for line in __import__("textwrap").wrap(para, width=width_chars, break_long_words=False):
            lines.append({"text": line, "newline": True})
    tspans = []
    y = 0
    for entry in lines:
        t = entry["text"]
        tspans.append(f'<tspan x="{x}" dy="{y}">{t}</tspan>')
        y = line_height
        if t == "":
            y += line_height

    return "\n    ".join(tspans)

def build_frame_str(theme) -> str:
    (card_w, card_h) = theme["card_sz"]
    (x,y,w,h) = theme["inner_rec"]
    frame_str =  f'<rect x="0" y="0" width="{card_w}" height="{card_h}" fill="{theme["frame_bg"]}" rx="18" ry="18"/>' 
    frame_str += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{theme["frame_inner"]}" rx="14" ry="14" stroke="{theme["frame_border"]}" stroke-width="2"/>'
    return frame_str

def build_title_str(theme, name, rarity) -> str:
    (x, y, w, h) = theme["title_rec"]
    title_str = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" ry="8" fill="{theme["title_bg"]}" stroke="{theme["frame_border"]}" stroke-width="2"/>'

    (x, y, fs) = theme["title_txt_rec"]
    title_str += f'<text x="{x}" y="{y}" font-family="{theme["font_serif"]}" font-size="{fs}" font-weight="700" fill="{theme["title_fg"]}">{name}</text>'

    (x, y, fs) = theme["title_rarity_rec"]
    title_str += f'<text x="{x}" y="{y}" font-family="{theme["font_serif"]}" font-size="{fs}" text-anchor="end" fill="{theme["title_fg"]}">{rarity}</text>'
    return title_str

def build_art_str(theme, art_path) -> tuple[str, str]:
    (x, y, w, h) = theme["art_rec"]
    clipping_art = f'<clipPath id="artClip"><rect x="{x}" y="{y}" rx="10" ry="10" width="{w}" height="{h}" /></clipPath>'
    art_img = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" ry="10" fill="{theme["art_bg"]}" stroke="{theme["frame_border"]}" stroke-width="2"/>'
    if art_path:
        mime = "image/png"
        ap = str(art_path).lower()
        if ap.endswith(".jpg") or ap.endswith(".jpeg"):
            mime = "image/jpeg"
        uri = data_uri_for_image(art_path, mime=mime)
        if uri:
            art_img = f'<image href="{uri}" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice" clip-path="url(#artClip)" />'
    art_img += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" ry="10" fill-opacity="0" stroke="{theme["frame_border"]}" stroke-width="2"/>'

    return (clipping_art, art_img)

def build_type_str(theme, type) -> str:
    (x, y, w, h) = theme["type_rec"]
    type_str =  f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" ry="6" fill="{theme["type_bg"]}" stroke="{theme["frame_border"]}" stroke-width="2"/>'

    (x, y, fs) = theme["type_txt_rec"]
    type_str += f'<text x="{x}" y="{y}" font-family="{theme["font_sans"]}" font-size="{fs}" font-weight="600" fill="{theme["type_fg"]}">{type}</text>'
    return type_str

def build_rules_str(theme, rules, flavor) -> str:
    (x, y, w, h) = theme["rules_rec"]
    rules_str =  f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" ry="10" fill="{theme["rules_bg"]}" stroke="{theme["frame_border"]}" stroke-width="2"/>'

    (x, y, fs) = theme["rules_txt_rec"]

    rules_lines = wrap_svg_text(rules, width_chars=60, x=x, line_height=fs)
    rules_str += f'<text x="{x}" y="{y}" font-family="{theme["font_serif"]}" font-size="{fs}" fill="{theme["rules_fg"]}">{rules_lines}</text>'

    (x, y, fs) = theme["flavor_txt_rec"]
    flavor_lines=""
    if flavor:
      flavor_lines = wrap_svg_text("“" + flavor + "”", width_chars=60, x=x, line_height=fs)
    rules_str += f'<text x="{x}" y="{y}" font-family="{theme["font_serif"]}" font-size="{fs}" font-style="italic" fill="{theme["flavor_fg"]}">{flavor_lines}</text>'
    return rules_str

def build_optional_str(theme, pt, price, weight) -> str:
    (x, y, w, h) = theme["opt_box"]
    (tx, ty, fs) = theme["opt_txt_rec"]
    opt_str = ""
    for el in [pt, price, weight]:
        if el:
            opt_str += f'<g><rect x="{x - w}" y="{y}" width="{w}" height="{h}" rx="8" ry="8" fill="{theme["pt_bg"]}" stroke="{theme["frame_border"]}" stroke-width="2"/>'
            opt_str += f'<text x="{tx}" y="{ty}" font-family="{theme["font_serif"]}" font-size="{fs}" font-weight="700" text-anchor="middle" fill="{theme["pt_fg"]}">{el}</text></g>'
            x  -= (w + 6)
            tx -= (w + 6)
    return opt_str

def build_footer_str(theme, set_code, collector, author, copyright_str) -> str:
    (x, y, fs) = theme["footer_txt_rec_l"]
    footer_str =  f'<g><text x="{x}" y="{y}" font-family="{theme["font_sans"]}" font-size="{fs}" fill="{theme["footer_fg"]}">{set_code} • {collector} • {author}</text>'

    (x, y, fs) = theme["footer_txt_rec_r"]
    footer_str += f'<text x="{x}" y="{y}" font-family="{theme["font_sans"]}" font-size="{fs}" text-anchor="end" fill="{theme["footer_fg"]}">{copyright_str}</text></g>'
    return footer_str

def get_theme( name, rarity) -> dict:
    card_width = 744
    card_height = 1039
    outer_padding = 12
    inner_padding = outer_padding + 6
    inner_width = card_width - 2*inner_padding
    title_h = 52
    
    art_y = inner_padding + title_h + 6
    art_h = 430

    type_y = art_y + art_h + 6
    type_h = 52

    rules_y = type_y + type_h + 6
    rules_h = 360

    opt_y = rules_y + rules_h + 6
    opt_h = 52

    theme = {
        "frame_bg": "#1b1b1b",
        "frame_inner": "#B0B0B0",
        "frame_border": "#121212",
        "title_bg": "#e9e3d9",
        "title_fg": "#111",
        "art_bg": "#ddd",
        "type_bg": "#ece7de",
        "type_fg": "#222",
        "rules_bg": "#f6f2ea",
        "rules_fg": "#222",
        "flavor_fg": "#555",
        "footer_fg": "#444",
        "pt_bg": "#e9e3d9",
        "pt_fg": "#111",
        "font_serif": "Georgia, 'Times New Roman', serif",
        "font_sans": "Inter, Arial, sans-serif",

        "card_sz": (card_width, card_height),
        "inner_rec": (outer_padding, outer_padding, card_width - 2*outer_padding, card_height - 2*outer_padding),
        "title_rec":        (inner_padding, inner_padding, inner_width, title_h),
        "title_txt_rec":    (               inner_padding + 18, inner_padding + title_h - 16, 32),
        "title_rarity_rec": (card_width - 2*inner_padding - 18, inner_padding + title_h - 16, 24),
        "art_rec": (inner_padding, art_y, inner_width, art_h),
        "type_rec": (inner_padding, type_y, inner_width, type_h),
        "type_txt_rec": (inner_padding + 18, type_y + type_h - 18, 24),
        "rules_rec":     (inner_padding, rules_y, inner_width, rules_h),
        "rules_txt_rec": (inner_padding + 18,           rules_y + 6 + 24, 24),
        "flavor_txt_rec":(inner_padding + 18, rules_y + rules_h - 48, 24),
        "footer_txt_rec_l":(               inner_padding + 11, card_height - inner_padding - 6, 11),
        "footer_txt_rec_r":(card_width - 2*inner_padding - 11, card_height - inner_padding - 6, 11),
        "opt_box": (inner_padding + inner_width, opt_y, 150, 54),
        "opt_txt_rec":(inner_padding + inner_width - 75, opt_y + opt_h - 16, 24),
    }

    theme.update(name)

    rarity_colors = {
    "Common":     "#B0B0B0",
    "Uncommon":   "#81AD82",
    "Rare":       "#B8D8F1",
    "Very Rare":  "#F1DAB6",
    "Legendary":  "#CF9F9F",
    "Quest":      "#E9E3B5",
    }
    if rarity in rarity_colors:
        theme["frame_inner"] = rarity_colors[rarity]
    return theme

def build_svg(card: dict, out_dir: Path) -> Path:
    theme = get_theme(card.get("theme", {}), card.get("rarity","Common"))


    frame_str = build_frame_str(theme)
    title_str = build_title_str(theme, card.get("name","Unnamed Item"), card.get("rarity","Common"))
    (clipping_art, art_img) = build_art_str(theme, card.get("art_path"))
    type_str = build_type_str(theme, card.get("type_line","Item — Wondrous"))

    rules_str = build_rules_str(theme, card.get("rules_text","—"), card.get("flavor_text","").strip())
    
    opt_str = build_optional_str(theme, card.get("pt", None), card.get("price", None), card.get("weight", None))
    footer_str = build_footer_str(theme, card.get("set_code","DND"), card.get("collector","001/001"), card.get("author",""), card.get("copyright","© 2025"))

    (w,h) = theme["card_sz"]
    svg = Template(SVG_TEMPLATE).substitute(
        frame_str=frame_str,
        title_str=title_str,
        clipping_art=clipping_art,
        art_img=art_img,
        type_str=type_str,
        rules_str=rules_str,
        opt_str=opt_str,
        footer_str=footer_str,
        card_w=w,
        card_h=h,
        )

    safe = re.sub(r"[^a-zA-Z0-9_-]+", "_", card.get("name","card")).strip("_")
    out = out_dir / f"{safe}.svg"
    out.write_text(svg, encoding="utf-8")
    return out

def main(cards_path:Path, output_path:Path):
    cards = []
    if cards_path.is_file():
        cfg = json.loads(Path(cards_path).read_text(encoding="utf-8"))
        cards.extend(cfg.get("cards", []))

    elif cards_path.is_dir():
        for json_path in sorted(cards_path.glob("*.json")):
            try:
                data = json.loads(json_path.read_text(encoding="utf-8"))
                cards_in_file = data.get("cards", [])
                cards.extend(cards_in_file)
                print(f"Loaded {len(cards_in_file)} cards from {json_path.name}")
            except Exception as e:
                print(f"Fehler in {json_path.name}: {e}")


    output_path.mkdir(parents=True, exist_ok=True)

    made = []
    for card in cards:
        made.append(build_svg(card, output_path))


    print(f"Generated {len(made)} cards into: {output_path.resolve()}")
    for pth in made:
        print(" -", pth.name)

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="D&D SVG Card Generator")
    p.add_argument("-i", "--input",  type=str, default="card-db",   help="Path to cards.json")
    p.add_argument("-o", "--output", type=str, default="out_cards", help="Output directory")
    args = p.parse_args()

    main(Path(args.input), Path(args.output))
