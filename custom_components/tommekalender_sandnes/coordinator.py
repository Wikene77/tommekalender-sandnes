from __future__ import annotations

import asyncio
import datetime as dt
import logging
import re
from dataclasses import dataclass
from typing import Dict, List

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL_HOURS, WASTE_TYPES

_LOGGER = logging.getLogger(__name__)


@dataclass
class Pickup:
    date: dt.date
    types: List[str]


def _guess_base_year(html: str) -> int:
    years = [int(y) for y in re.findall(r"\b(20\d{2})\b", html)]
    return min(years) if years else dt.date.today().year


def _strip_tags_keep_img_alt(html: str) -> str:
    """Strip HTML tags, but keep <img alt/title> text.

    hentavfall.no uses icons with the waste type name in alt/title.
    If we blindly remove tags, we lose the waste type labels.
    """
    # Turn <img ... alt="Restavfall" ...> into " Restavfall " before stripping.
    html = re.sub(
        r'<img[^>]*(?:alt|title)="([^"]+)"[^>]*>',
        r" \1 ",
        html,
        flags=re.IGNORECASE,
    )

    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


# Backwards-compatible alias used by older parsing logic
def _strip_tags(html: str) -> str:
    return _strip_tags_keep_img_alt(html)


def _extract_rows_by_month(html: str) -> List[tuple[int, int, str]]:
    """Return list of (month, year, tbody_html) found in data-month="M-YYYY"."""
    out: List[tuple[int, int, str]] = []

    # Example: <tbody data-month="1-2026" ...> ... </tbody>
    tbody_re = re.compile(
        r'<tbody[^>]*\bdata-month\s*=\s*"(?P<m>\d{1,2})-(?P<y>20\d{2})"[^>]*>(?P<body>.*?)</tbody>',
        re.IGNORECASE | re.DOTALL,
    )

    for m in tbody_re.finditer(html):
        month = int(m.group("m"))
        year = int(m.group("y"))
        body = m.group("body")
        out.append((month, year, body))

    return out


def _find_types_in_text(block: str) -> List[str]:
    b = block.lower()
    found: List[str] = []
    for label in WASTE_TYPES.keys():
        if label.lower() in b:
            found.append(label)
    return found


def _parse_pickups(html: str) -> List[Pickup]:
    """Parse pickups from hentavfall.no.

    Primary strategy (robust): parse the calendar table structure:
      - <tbody data-month="M-YYYY"> gives the year (and month)
      - each <tr class="waste-calendar__item"> contains the date + <img alt/title="TYPE">

    Fallback strategy: text-scan for dd.mm + waste type labels.
    """
    today = dt.date.today()
    pickups: List[Pickup] = []

    # 1) Structured parse from table (preferred)
    month_bodies = _extract_rows_by_month(html)
    if month_bodies:
        tr_re = re.compile(
            r"<tr[^>]*\bwaste-calendar__item\b[^>]*>(?P<tr>.*?)</tr>",
            re.IGNORECASE | re.DOTALL,
        )
        ddmm_re = re.compile(r"\b(\d{1,2})\.(\d{1,2})\b")
        dd_only_re = re.compile(r"\b(\d{1,2})\b")

        for month_attr, year, tbody_html in month_bodies:
            for tr_m in tr_re.finditer(tbody_html):
                row_html = tr_m.group("tr")
                row_text = _strip_tags_keep_img_alt(row_html)

                # Date is usually dd.mm in the first column, but be tolerant.
                mm = month_attr
                ddmm = ddmm_re.search(row_text)
                if ddmm:
                    dd = int(ddmm.group(1))
                    mm = int(ddmm.group(2))
                else:
                    # Some layouts might show only day number inside month tbody.
                    dd_only = dd_only_re.search(row_text)
                    if not dd_only:
                        continue
                    dd = int(dd_only.group(1))

                types = _find_types_in_text(row_text)
                if not types:
                    continue

                try:
                    d = dt.date(year, mm, dd)
                except ValueError:
                    continue

                pickups.append(Pickup(date=d, types=types))

    # 2) Fallback: text scan (handles unexpected HTML changes)
    if not pickups:
        base_year = _guess_base_year(html)
        text = _strip_tags_keep_img_alt(html)

        date_re = re.compile(r"\b(\d{1,2})\.(\d{1,2})\b")
        for m in date_re.finditer(text):
            dd = int(m.group(1))
            mm = int(m.group(2))

            start = m.end()
            end = min(len(text), start + 300)
            block = text[start:end]

            types = _find_types_in_text(block)
            if not types:
                continue

            # Prefer a year that makes the date >= today (important around new year)
            d = None
            for y in (base_year, base_year + 1):
                try:
                    cand = dt.date(y, mm, dd)
                except ValueError:
                    continue
                if cand >= today:
                    d = cand
                    break

            if d is None:
                continue

            pickups.append(Pickup(date=d, types=types))

    # Merge duplicates per date
    merged: Dict[dt.date, set[str]] = {}
    for p in pickups:
        merged.setdefault(p.date, set()).update(p.types)

    out = [Pickup(date=d, types=sorted(list(ts))) for d, ts in merged.items()]
    out.sort(key=lambda p: p.date)
    return out


class TommekalenderCoordinator(DataUpdateCoordinator[Dict]):
    def __init__(self, hass: HomeAssistant, url: str) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name="Tommekalender",
            update_interval=dt.timedelta(hours=DEFAULT_SCAN_INTERVAL_HOURS),
        )
        self._url = url

    async def _async_update_data(self) -> Dict:
        session = async_get_clientsession(self.hass)

        try:
            async with session.get(self._url, timeout=20) as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"HTTP {resp.status}")
                html = await resp.text()
        except asyncio.TimeoutError as e:
            raise UpdateFailed("Timeout") from e
        except Exception as e:
            raise UpdateFailed(str(e)) from e

        # --- Provider routing ---
        url_lc = self._url.lower()

        if "stavanger.kommune.no" in url_lc:
            from .providers.stavanger_kommune import parse as parse_pickups

            raw_pickups = parse_pickups(html)  # list[dict]: {"date": dt.date, "types": [...]}
            # Konverter til Pickup-objekter for resten av koden:
            pickups = []
            for it in raw_pickups:
                d = it.get("date")
                types = it.get("types") or []
                if d and types:
                    pickups.append(Pickup(date=d, types=types))
            pickups.sort(key=lambda p: p.date)

        else:
            # Default: Sandnes/hentavfall.no parser (eksisterende logikk)
            pickups = _parse_pickups(html)

        today = dt.date.today()

        next_by_type: Dict[str, dt.date | None] = {k: None for k in WASTE_TYPES.keys()}
        for p in pickups:
            if p.date < today:
                continue
            for t in p.types:
                if t not in next_by_type:
                    continue
                if next_by_type[t] is None:
                    next_by_type[t] = p.date


        upcoming = [
            {"date": p.date.isoformat(), "types": p.types}
            for p in pickups
            if p.date >= today
        ][:30]

        return {
            "next": {k: (v.isoformat() if v else None) for k, v in next_by_type.items()},
            "upcoming": upcoming,
            "source_url": self._url,
        }
