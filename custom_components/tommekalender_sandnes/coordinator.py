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


def _strip_tags(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


def _find_types_in_text(block: str) -> List[str]:
    b = block.lower()
    found: List[str] = []
    for label in WASTE_TYPES.keys():
        if label.lower() in b:
            found.append(label)
    return found


def _parse_pickups(html: str) -> List[Pickup]:
    base_year = _guess_base_year(html)
    text = _strip_tags(html)

    # tolerant dd.mm
    date_re = re.compile(r"\b(\d{1,2})\.(\d{1,2})\b")
    matches = list(date_re.finditer(text))

    pickups: List[Pickup] = []

    for m in matches:
        dd = int(m.group(1))
        mm = int(m.group(2))

        start = m.end()
        end = min(len(text), start + 260)
        block = text[start:end]

        types = _find_types_in_text(block)
        if not types:
            continue

        try:
            d = dt.date(base_year, mm, dd)
        except ValueError:
            continue

        pickups.append(Pickup(date=d, types=types))

    # merge same date
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

        pickups = _parse_pickups(html)
        today = dt.date.today()

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
        ][:30]

        return {
            "next": {k: (v.isoformat() if v else None) for k, v in next_by_type.items()},
            "upcoming": upcoming,
            "source_url": self._url,
        }
