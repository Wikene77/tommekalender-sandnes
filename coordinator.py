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
    types: List[str]  # labels like "Restavfall"


def _guess_base_year(html: str) -> int:
    years = [int(y) for y in re.findall(r"\b(20\d{2})\b", html)]
    return min(years) if years else dt.date.today().year


def _strip_tags_keep_alt(html: str) -> str:
    """
    Make <img alt="Restavfall"> visible as [Restavfall] in the plain text,
    then strip remaining tags and normalize whitespace.
    """
    html = re.sub(r"<img[^>]*alt=[\"']([^\"']+)[\"'][^>]*>", r" [\1] ", html, flags=re.I)
    html = re.sub(r"<[^>]+>", " ", html)
    html = re.sub(r"\s+", " ", html).strip()
    return html


def _parse_pickups(html: str) -> List[Pickup]:
    base_year = _guess_base_year(html)
    text = _strip_tags_keep_alt(html)

    # Matches: "02.01 - fredag"
    pattern = re.compile(r"\b(\d{1,2})\.(\d{1,2})\s*-\s*([a-zæøå]+)\b", re.I)
    matches = list(pattern.finditer(text))

    raw: List[Pickup] = []

    for i, m in enumerate(matches):
        dd = int(m.group(1))
        mm = int(m.group(2))

        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end]

        types: List[str] = []
        for label in WASTE_TYPES.keys():
            if f"[{label}]" in block:
                types.append(label)

        if not types:
            continue

        # Handle year turn: if we are in December and calendar starts in January etc.
        # Use base_year, but if month is "far behind" current month at end of year, bump year.
        year = base_year
        try:
            d = dt.date(year, mm, dd)
        except ValueError:
            continue

        raw.append(Pickup(date=d, types=types))

    # Merge pickups with same date (e.g. Matavfall + Papir same day)
    merged: Dict[dt.date, set[str]] = {}
    for p in raw:
        merged.setdefault(p.date, set()).update(p.types)

    out = [Pickup(date=d, types=sorted(list(ts))) for d, ts in merged.items()]
    out.sort(key=lambda p: p.date)
    return out


class HentAvfallCoordinator(DataUpdateCoordinator[Dict]):
    def __init__(self, hass: HomeAssistant, url: str) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,  # IMPORTANT: must not be None
            name="HentAvfall",
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

        pickups = _parse_pickups(html)
        today = dt.date.today()

        # Next date per type
        next_by_type: Dict[str, dt.date | None] = {k: None for k in WASTE_TYPES.keys()}
        for p in pickups:
            if p.date < today:
                continue
            for t in p.types:
                if next_by_type[t] is None:
                    next_by_type[t] = p.date

        upcoming = [
            {"date": p.date.isoformat(), "types": p.types}
            for p in pickups
            if p.date >= today
        ][:60]

        # Debug (enable by setting log level for this integration to debug)
        _LOGGER.debug("Parsed pickups=%s, next_by_type=%s", len(pickups), next_by_type)

        return {
            "next": {k: (v.isoformat() if v else None) for k, v in next_by_type.items()},
            "upcoming": upcoming,
            "source_url": self._url,
        }
