from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import List

# Vi importerer Pickup + parser-funksjon fra coordinator foreløpig?
# NEI (sirkulær import). Derfor lager vi et lite "provider-API":
# Provideren returnerer liste av dict: {"date": date, "types": [...]}

def parse(html: str) -> list[dict]:
    """Parse hentavfall.no HTML and return pickups."""
    # Denne funksjonen blir fylt senere når vi flytter parseren ut.
    # Foreløpig: vi flytter _parse_pickups til denne filen i steg 2.
    raise NotImplementedError
