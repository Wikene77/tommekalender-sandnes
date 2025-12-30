from __future__ import annotations

import datetime as dt
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME, DOMAIN


MAX_EVENTS = 30  # hvor mange du vil eksponere i kalender


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([TommekalenderCalendarEntity(coordinator, entry)])


class TommekalenderCalendarEntity(CoordinatorEntity, CalendarEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = "Tømming"  # blir "Tømmekalender Tømming" i UI
        self._attr_unique_id = f"{entry.entry_id}_calendar_tomming"

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.title or DEFAULT_NAME,
            "manufacturer": "hentavfall.no",
            "model": "Waste calendar",
        }

    def _upcoming(self) -> list[dict[str, Any]]:
        data = getattr(self.coordinator, "data", None)
        if not isinstance(data, dict):
            return []
        items = data.get("upcoming") or []
        if not isinstance(items, list):
            return []
        return items[:MAX_EVENTS]

    def _to_event(self, item: dict[str, Any]) -> CalendarEvent | None:
        # item: {"date": "YYYY-MM-DD", "types": ["Restavfall", ...]}
        date_s = item.get("date")
        types = item.get("types") or []
        if not date_s:
            return None

        try:
            d = dt.date.fromisoformat(date_s)
        except ValueError:
            return None

        # All-day event i lokal tid
        start = dt.datetime.combine(d, dt.time.min)
        end = start + dt.timedelta(days=1)

        summary = "Tømming: " + ", ".join(types) if types else "Tømming"
        return CalendarEvent(
            summary=summary,
            start=start,
            end=end,
            description=f"Kilde: {getattr(self.coordinator, 'data', {}).get('source_url')}",
            location="Sandnes kommune",
        )

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: dt.datetime,
        end_date: dt.datetime,
    ) -> list[CalendarEvent]:
        events: list[CalendarEvent] = []
        for it in self._upcoming():
            ev = self._to_event(it)
            if not ev:
                continue

            # filtrer på tidsrom
            if ev.end <= start_date or ev.start >= end_date:
                continue

            events.append(ev)
        return events

    @property
    def event(self) -> CalendarEvent | None:
        # “neste event” (brukes av mange kort)
        now = dt.datetime.now()
        for it in self._upcoming():
            ev = self._to_event(it)
            if ev and ev.end > now:
                return ev
        return None
