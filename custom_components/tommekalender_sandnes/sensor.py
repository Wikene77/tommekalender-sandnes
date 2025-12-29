from __future__ import annotations

import datetime as dt

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

    # “Calendar” sensor (upcoming/summary)
    entities.append(TommekalenderCalendarSensor(coordinator, entry.entry_id))

    # Next-by-type sensors
    for label in WASTE_TYPES.keys():
        entities.append(TommekalenderNextSensor(coordinator, entry.entry_id, label))

    async_add_entities(entities)


class TommekalenderNextSensor(CoordinatorEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.DATE
    _attr_icon = "mdi:trash-can-outline"

    def __init__(self, coordinator, entry_id: str, label: str) -> None:
        super().__init__(coordinator)
        self._label = label

        slug = WASTE_TYPES[label]
        self._attr_name = f"{DEFAULT_NAME} {label}"
        self._attr_unique_id = f"{entry_id}_next_{slug}"

    @property
    def native_value(self):
        iso = (self.coordinator.data.get("next") or {}).get(self._label)
        if not iso:
            return None
        try:
            return dt.date.fromisoformat(iso)
        except ValueError:
            return None

    @property
    def extra_state_attributes(self):
        return {
            "type": self._label,
            "source_url": self.coordinator.data.get("source_url"),
        }


class TommekalenderCalendarSensor(CoordinatorEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.DATE
    _attr_icon = "mdi:calendar"

    def __init__(self, coordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_name = f"{DEFAULT_NAME} Kalender"
        self._attr_unique_id = f"{entry_id}_calendar"

    @property
    def native_value(self):
        upcoming = self.coordinator.data.get("upcoming") or []
        if not upcoming:
            return None
        first = upcoming[0].get("date")
        if not first:
            return None
        try:
            return dt.date.fromisoformat(first)
        except ValueError:
            return None

    @property
    def extra_state_attributes(self):
        upcoming = self.coordinator.data.get("upcoming") or []
        first_types = upcoming[0].get("types") if upcoming else []
        return {
            "next_types": first_types,
            "upcoming": upcoming,
            "source_url": self.coordinator.data.get("source_url"),
        }
