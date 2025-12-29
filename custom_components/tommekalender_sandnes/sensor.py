from __future__ import annotations

import datetime as dt
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME, DOMAIN, WASTE_TYPES


MAX_UPCOMING = 5

# More explanatory icons per waste type (fallback included)
WASTE_ICONS = {
    "Restavfall": "mdi:trash-can",
    "Matavfall": "mdi:food-apple-outline",
    "Papir": "mdi:file-document-outline",
    "Plastemballasje": "mdi:bottle-soda-classic-outline",
    "Juletre": "mdi:pine-tree",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    # Calendar summary sensor
    entities.append(TommekalenderCalendarSensor(coordinator, entry.entry_id))

    # Next-by-type sensors
    for label in WASTE_TYPES.keys():
        entities.append(TommekalenderNextSensor(coordinator, entry.entry_id, label))

    async_add_entities(entities)


class _BaseTommekalenderSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    def _data(self) -> dict[str, Any]:
        d = getattr(self.coordinator, "data", None)
        return d if isinstance(d, dict) else {}

    def _upcoming5(self) -> list[dict[str, Any]]:
        return (self._data().get("upcoming") or [])[:MAX_UPCOMING]

    def _common_attrs(self) -> dict[str, Any]:
        return {
            "source_url": self._data().get("source_url"),
        }


class TommekalenderNextSensor(_BaseTommekalenderSensor):
    _attr_device_class = SensorDeviceClass.DATE

    def __init__(self, coordinator, entry_id: str, label: str) -> None:
        super().__init__(coordinator)
        self._label = label

        slug = WASTE_TYPES[label]
        self._attr_name = label
        self._attr_unique_id = f"{entry_id}_next_{slug}"

    @property
    def icon(self) -> str:
        return WASTE_ICONS.get(self._label, "mdi:trash-can-outline")

    @property
    def native_value(self) -> dt.date | None:
        iso = (self._data().get("next") or {}).get(self._label)
        if not iso:
            return None
        try:
            return dt.date.fromisoformat(iso)
        except (TypeError, ValueError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs = self._common_attrs()
        attrs.update(
            {
                "type": self._label,
                "upcoming": self._upcoming5(),
            }
        )
        return attrs


class TommekalenderCalendarSensor(_BaseTommekalenderSensor):
    _attr_device_class = SensorDeviceClass.DATE
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_name = "Kalender"
        self._attr_unique_id = f"{entry_id}_calendar"

    @property
    def native_value(self) -> dt.date | None:
        upcoming = self._upcoming5()
        if not upcoming:
            return None
        try:
            return dt.date.fromisoformat(upcoming[0]["date"])
        except (KeyError, TypeError, ValueError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        upcoming = self._upcoming5()
        first_types = upcoming[0].get("types") if upcoming else []

        attrs = self._common_attrs()
        attrs.update(
            {
                "next_types": first_types,
                "upcoming": upcoming,
            }
        )
        return attrs
