from __future__ import annotations

import datetime as dt

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, DEFAULT_NAME, WASTE_TYPES


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    # 1) Én “kalender”-sensor som bærer upcoming-lista (og kan være master i automasjoner)
    entities.append(TommekalenderSensor(coordinator, entry))

    # 2) En sensor per avfallstype: state = neste dato (DATE device_class)
    for label in WASTE_TYPES.keys():
        entities.append(HentAvfallNextSensor(coordinator, entry, label))

    async_add_entities(entities)


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.data.get("name", DEFAULT_NAME),
        manufacturer="hentavfall.no",
        model="Tømmekalender (scraper)",
        configuration_url=entry.data.get("url"),
    )


class TommekalenderSensor(CoordinatorEntity, SensorEntity):
    """
    Samlesensor:
    - state: neste hentedato (eldste dato i upcoming, hvis finnes)
    - attributes: upcoming + source_url
    """
    _attr_has_entity_name = True
    _attr_icon = "mdi:calendar-trash"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_calendar"
        self._attr_name = "Kalender"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self) -> str | None:
        upcoming = self.coordinator.data.get("upcoming") or []
        if not upcoming:
            return None
        # upcoming er [{date:'YYYY-MM-DD', types:[...]}] og er allerede sortert
        d = upcoming[0].get("date")
        return d if isinstance(d, str) else None

    @property
    def extra_state_attributes(self):
        return {
            "source_url": self.coordinator.data.get("source_url"),
            "upcoming": self.coordinator.data.get("upcoming"),
        }


class HentAvfallNextSensor(CoordinatorEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.DATE
    _attr_icon = "mdi:trash-can-outline"
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry: ConfigEntry, label: str) -> None:
        super().__init__(coordinator)
        self._label = label
        self._entry = entry

        slug = WASTE_TYPES[label]  # f.eks. "restavfall"
        self._attr_name = slug.replace("_", " ").title()
        self._attr_unique_id = f"{entry.entry_id}_next_{slug}"
        self._attr_device_info = _device_info(entry)

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
