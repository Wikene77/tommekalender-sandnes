DOMAIN = "tommekalender_sandnes"

DEFAULT_NAME = "Tømmekalender"
DEFAULT_SCAN_INTERVAL_HOURS = 12

# LEFT side must match text found in hentavfall.no HTML (img alt/title etc.)
# RIGHT side is used as slug in entity names.
WASTE_TYPES = {
    "Restavfall": "restavfall",
    "Matavfall": "matavfall",
    "Papir": "papir",
    "Plastemballasje": "plast",
    "Juletre": "juletre",
}
