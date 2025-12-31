from __future__ import annotations

import datetime as dt
import re
from typing import List, Dict


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

    # We walk through the text in order, switching context when we see a month heading.
    # Example: "Måned januar 2026"
    month_re = re.compile(r"\bMåned\s+([A-Za-zæøåÆØÅ]+)\s+(20\d{2})\b", re.IGNORECASE)

    # Date line: "07.01 - onsdag  Image: Juletre"
    # We will find dd.mm occurrences and then look for waste types nearby.
    ddmm_re = re.compile(r"\b(\d{1,2})\.(\d{1,2})\b")

    # Waste type can show as "Image: Juletre" (accessibility text)
    image_type_re = re.compile(r"\bImage:\s*([A-Za-zæøåÆØÅ \-/]+)", re.IGNORECASE)

    # Split into chunks to preserve order and make "lookahead" easier
    # (This is simple but works well for these pages)
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

        # Now parse all dates inside this month chunk
        # We'll scan for dd.mm occurrences and grab types from a short window after each date.
        for dmatch in ddmm_re.finditer(chunk):
            dd = int(dmatch.group(1))
            mm = int(dmatch.group(2))

            # Some pages use dd.mm where mm matches the month; trust mm if present.
            # If mm seems missing/odd, fall back to the month heading.
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
                # cut off at common separators that could appear after the label
                t = re.split(r"\s{2,}|\bLast ned\b|\bGnr\b|\bKommune\b", t)[0].strip(" -:;,")
                if t and t not in types:
                    types.append(t)

            # Fallback: sometimes alt/title text is injected without "Image:"
            if not types:
                # look for known-looking words near the date: take up to 3 capitalized tokens in a row
                # (kept conservative to avoid picking random words)
                caps_re = re.compile(r"\b([A-ZÆØÅ][a-zæøå]+(?:\s+[A-ZÆØÅ][a-zæøå]+)*)\b")
                for cm in caps_re.finditer(window):
                    cand = cm.group(1).strip()
                    if cand and cand.lower() not in ("onsdag", "torsdag", "fredag", "lørdag", "søndag", "mandag", "tirsdag"):
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
