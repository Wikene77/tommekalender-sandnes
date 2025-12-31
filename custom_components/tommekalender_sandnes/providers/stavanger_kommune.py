from __future__ import annotations

import datetime as dt
import re
from typing import Dict, List


MONTHS_NO = {
    "januar": 1,
    "februar": 2,
    "mars": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "november": 11,
    "desember": 12,
}


def _strip_tags_keep_img_alt(html: str) -> str:
    """Strip tags but keep img alt/title text, plus tolerate accessibility 'Image: X' text."""
    html = re.sub(
        r'<img[^>]*(?:alt|title)="([^"]+)"[^>]*>',
        r" \1 ",
        html,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


def parse(html: str) -> List[Dict]:
    """
    Parse Stavanger kommune calendar HTML and return list of:
      {"date": dt.date, "types": [str, ...]}
    Robust strategy:
      - detect month heading "Måned <måned> <år>"
      - detect lines like "07.01 - onsdag Image: Juletre [Image: ...]"
      - types are taken from 'Image: TYPE' or from preserved <img alt/title="TYPE">
    """
    text = _strip_tags_keep_img_alt(html)

    # Example: "Måned januar 2026"
    month_re = re.compile(r"\bMåned\s+([A-Za-zæøåÆØÅ]+)\s+(20\d{2})\b", re.IGNORECASE)

    # Date like "07.01"
    ddmm_re = re.compile(r"\b(\d{1,2})\.(\d{1,2})\b")

    # Waste type can show as "Image: Juletre" (accessibility text)
    # Keep it conservative so it doesn't swallow too much text.
    image_type_re = re.compile(
        r"\bImage:\s*([A-Za-zæøåÆØÅ][A-Za-zæøåÆØÅ \-/]{0,40})",
        re.IGNORECASE,
    )

    # Split into chunks starting at month headings
    chunks = re.split(r"(?=\bMåned\s+)", text)

    pickups: List[Dict] = []

    for chunk in chunks:
        m = month_re.search(chunk)
        if not m:
            continue

        month_name = (m.group(1) or "").strip().lower()
        year = int(m.group(2))
        month_no = MONTHS_NO.get(month_name)
        if not month_no:
            continue

        # Parse all dates inside this month chunk
        for dmatch in ddmm_re.finditer(chunk):
            dd = int(dmatch.group(1))
            mm = int(dmatch.group(2))

            # If the page ever shows odd month numbers, fall back to month heading.
            if not (1 <= mm <= 12):
                mm = month_no

            try:
                date = dt.date(year, mm, dd)
            except ValueError:
                continue

            start = dmatch.end()
            window = chunk[start : start + 220]  # small lookahead window

            types: List[str] = []

            # Prefer explicit "Image: TYPE" labels
            for tm in image_type_re.finditer(window):
                t = tm.group(1).strip()
                # Cut off at common separators that could appear after the label
                t = re.split(r"\s{2,}|\bLast ned\b|\bGnr\b|\bKommune\b", t)[0].strip(" -:;,")
                if t and t not in types:
                    types.append(t)

            # Fallback: sometimes alt/title text is injected without "Image:"
            if not types:
                # Conservative: grab capitalized word sequences, skip weekdays
                caps_re = re.compile(r"\b([A-ZÆØÅ][a-zæøå]+(?:\s+[A-ZÆØÅ][a-zæøå]+)*)\b")
                for cm in caps_re.finditer(window):
                    cand = cm.group(1).strip()
                    if cand and cand.lower() not in (
                        "onsdag",
                        "torsdag",
                        "fredag",
                        "lørdag",
                        "søndag",
                        "mandag",
                        "tirsdag",
                    ):
                        if cand not in types:
                            types.append(cand)
                    if len(types) >= 4:
                        break

            if types:
                pickups.append({"date": date, "types": types})

    # Merge duplicates per date
    merged: Dict[dt.date, set] = {}
    for it in pickups:
        d = it["date"]
        merged.setdefault(d, set()).update(it.get("types") or [])

    out = [{"date": d, "types": sorted(list(ts))} for d, ts in merged.items()]
    out.sort(key=lambda x: x["date"])
    return out
