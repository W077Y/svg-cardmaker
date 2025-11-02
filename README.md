# svg-cardmaker

A flexible, scriptable card generator for RPGs, board games, and collectible card systems — written in Python and based on SVG templates.  
Originally built for D&D-style magic items, but works for any kind of custom card design.

## Features

- **Modular JSON card database** — split your cards into multiple files (e.g. `weapons.json`, `potions.json`)
- **SVG-based layout** — crisp vector output, perfect for printing or digital use
- **Automatic theming** — background color adapts to rarity (Common → Legendary)
- **Dynamic text sizing** — title font scales to fit available space
- **Batch rendering** — generate all cards in one go
- **Collect & Print tool** — combine multiple cards into printable A4 sheets (PDF)
- **Open format** — everything is plain JSON, SVG, and Python

---

## Example Card Definition

Each card is a simple JSON object stored in a file inside the `cards/` folder:

```json
{
  "cards": [
    {
      "name": "Potion of Supreme Healing",
      "rarity": "Very Rare",
      "type_line": "Item \u2014 Consumable (potion)",
      "rules_text": [
        "A character who drinks the magical red fluid in this vial regains 10d4 + 20 hit points. Drinking or administering a potion takes an action."
        ],
      "flavor_text": "Nur einmal wagte ein Magier, sie zu brauen - und seitdem spricht niemand mehr von seinem Tod, nur von seinem Werk.",
      "set_code": "MYR",
      "collector": "004/999 U",
      "author": "wschu",
      "copyright": "\u00a9 Myrdell Homebrew 2025",
      "art_path": "art/potion-of-supreme-healing.png",
      "pt": "10d4+20",
      "price": "8500 GP",
      "weight": "1/2 lb"
    }
  ]
}
```

![Potion of Supreme Healing](out_cards/Potion_of_Supreme_Healing.svg)

---

## Usage

### Generate SVG cards

```bash
python generate_cards.py cards/
```

This command:

- loads all .json files in cards/

- creates .svg files for each entry in out/cards/

- applies rarity-based color themes

- inserts art, text, and metadata

### Collect and print

```bash
python collect_and_print.py `
  --cards ".\out_cards" `
  --add "Potion_of_Healing=3" `
  --add "Potion_of_Greater_Healing=3" `
  --add "Potion_of_Superior_Healing=2" `
  --add "Potion_of_Supreme_Healing=1" `
  --out "out/print_sheets/cards_print.pdf" `
  --crop
```

Creates printable A4 sheets (3×3 cards per page) with optional crop marks.

---

## Requirements

- Python 3.9+

- Pillow for image processing

- Inkscape (for SVG → PNG rasterization)

