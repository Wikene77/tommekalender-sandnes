from __future__ import annotations

import datetime as dt
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME, DOMAIN, WASTE_TYPES


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    # Calendar summary sensor (first upcoming)
    entities.append(TommekalenderCalendarSensor(coordinator, entry.entry_id))

    # Next-by-type sensors
    for label in WASTE_TYPES.keys():
        entities.append(TommekalenderNextSensor(coordinator, entry.entry_id, label))

    async_add_entities(entities)


class _BaseTommekalenderSensor(CoordinatorEntity, SensorEntity):
    """Common behavior for all sensors in this integration."""

    _attr_has_entity_name = True
    _attr_should_poll = False  # Coordinator drives updates

    @property
    def available(self) -> bool:
        # Prevent sticky "unavailable" if a fetch fails briefly
        return self.coordinator.last_update_success

    def _data(self) -> dict[str, Any]:
        # Always return a dict to avoid None/KeyError issues
        d = getattr(self.coordinator, "data", None)
        return d if isinstance(d, dict) else {}

    def _common_attrs(self) -> dict[str, Any]:
        data = self._data()
        return {
            "source_url": data.get("source_url"),
        }


class TommekalenderNextSensor(_BaseTommekalenderSensor):
    _attr_device_class = SensorDeviceClass.DATE
    _attr_icon = "mdi:trash-can-outline"

    def __init__(self, coordinator, entry_id: str, label: str) -> None:
        super().__init__(coordinator)
        self._label = label

        slug = WASTE_TYPES[label]
        self._attr_name = f"{label}"
        self._attr_unique_id = f"{entry_id}_next_{slug}"

    @property
    def native_value(self) -> dt.date | None:
        data = self._data()
        iso = (data.get("next") or {}).get(self._label)
        if not iso:
            return None
        try:
            return dt.date.fromisoformat(iso)
        except (TypeError, ValueError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self._data()
        attrs = self._common_attrs()
        attrs.update(
            {
                "type": self._label,
                # Nice to have for UI/templates:
                "next": data.get("next"),
                "upcoming": data.get("upcoming"),
            }
        )
        return attrs


class TommekalenderCalendarSensor(_BaseTommekalenderSensor):
    _attr_device_class = SensorDeviceClass.DATE
    _attr_icon = "mdi:calendar"

    def __init__(self, coordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_name = "Kalender"
        self._attr_unique_id = f"{entry_id}_calendar"

    @property
    def native_value(self) -> dt.date | None:
        data = self._data()
        upcoming = data.get("upcoming") or []
        if not upcoming:
            return None

        first = upcoming[0].get("date")
        if not first:
            return None

        try:
            return dt.date.fromisoformat(first)
        except (TypeError, ValueError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self._data()
        upcoming = data.get("upcoming") or []
        first_types = upcoming[0].get("types") if upcoming else []

        attrs = self._common_attrs()
        attrs.update(
            {
                "next_types": first_types,
                "upcoming": upcoming,
                "next": data.get("next"),
            }
        )
        return attrs
