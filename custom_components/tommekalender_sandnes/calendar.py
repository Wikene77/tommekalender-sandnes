from __future__ import annotations

import datetime as dt
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DEFAULT_NAME, DOMAIN

MAX_EVENTS = 30


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([TommekalenderCalendarEntity(coordinator, entry)])


class TommekalenderCalendarEntity(CoordinatorEntity, CalendarEntity):
    """
    Key idea:
    - has_entity_name=False => entity_id becomes based on this entity's own name only
    - name is entry.title (e.g. "Tømmekalender Sandnes Kommune")
      => calendar.tommekalender_sandnes_kommune (no extra "_tomming")
    """
    _attr_has_entity_name = False
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

        # IMPORTANT: this drives the entity_id
        self._attr_name = (entry.title or f"{DEFAULT_NAME} Sandnes Kommune").strip()
        self._attr_unique_id = f"{entry.entry_id}_calendar_entity"

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def device_info(self) -> dict[str, Any]:
        # Same device identifiers as sensors (nice grouping), but device name doesn't affect entity_id now
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": DEFAULT_NAME,
            "manufacturer": "hentavfall.no",
            "model": "Waste calendar",
        }

    def _data(self) -> dict[str, Any]:
        d = getattr(self.coordinator, "data", None)
        return d if isinstance(d, dict) else {}

    def _upcoming(self) -> list[dict[str, Any]]:
        items = self._data().get("upcoming") or []
        return items[:MAX_EVENTS] if isinstance(items, list) else []

    def _to_event(self, item: dict[str, Any]) -> CalendarEvent | None:
        date_s = item.get("date")
        types = item.get("types") or []
        if not date_s:
            return None

        try:
            d = dt.date.fromisoformat(date_s)
        except ValueError:
            return None

        start = dt_util.start_of_local_day(dt_util.as_local(dt.datetime.combine(d, dt.time.min)))
        end = start + dt.timedelta(days=1)

        summary = f"Tømming: {', '.join(types)}" if types else "Tømming"
        source_url = self._data().get("source_url")

        return CalendarEvent(
            summary=summary,
            start=start,
            end=end,
            description=f"Kilde: {source_url}" if source_url else None,
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
            if ev.end <= start_date or ev.start >= end_date:
                continue
            events.append(ev)
        return events

    @property
    def event(self) -> CalendarEvent | None:
        now = dt_util.now()
        for it in self._upcoming():
            ev = self._to_event(it)
            if ev and ev.end > now:
                return ev
        return None
