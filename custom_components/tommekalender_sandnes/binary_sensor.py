from __future__ import annotations

import datetime as dt
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, DEFAULT_NAME


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            TommekalenderPickupBinarySensor(coordinator, entry, days=0),
            TommekalenderPickupBinarySensor(coordinator, entry, days=1),
        ]
    )


class TommekalenderPickupBinarySensor(CoordinatorEntity, BinarySensorEntity):
    _attr_has_entity_name = False
    _attr_should_poll = False

    def __init__(self, coordinator, entry: ConfigEntry, days: int) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._days = days

        suffix = "i_dag" if days == 0 else "i_morgen"
        name = "Tømming i dag" if days == 0 else "Tømming i morgen"

        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_tomming_{suffix}"

    @property
    def is_on(self) -> bool:
        today = dt.date.today() + dt.timedelta(days=self._days)
        today_iso = today.isoformat()

        for item in self._upcoming():
            if item.get("date") == today_iso:
                return True
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        today = dt.date.today() + dt.timedelta(days=self._days)
        today_iso = today.isoformat()

        for item in self._upcoming():
            if item.get("date") == today_iso:
                return {
                    "date": today_iso,
                    "types": item.get("types", []),
                    "source_url": self._data().get("source_url"),
                }

        return {
            "date": today_iso,
            "types": [],
            "source_url": self._data().get("source_url"),
        }

    def _data(self) -> dict[str, Any]:
        data = getattr(self.coordinator, "data", {})
        return data if isinstance(data, dict) else {}

    def _upcoming(self) -> list[dict[str, Any]]:
        return self._data().get("upcoming", [])
