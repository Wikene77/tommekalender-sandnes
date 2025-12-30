from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN

DEFAULT_TITLE = "Tømmekalender Sandnes Kommune"


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id(user_input["url"])
            self._abort_if_unique_id_configured()

            # Keep entry.title stable for predictable calendar entity_id
            # (Sensors are controlled via device_info in sensor.py anyway)
            return self.async_create_entry(
                title=DEFAULT_TITLE,
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required("url"): str,
                # Optional: keep the field if you want it for future use,
                # but it will NOT affect entry.title.
                vol.Optional("name", default=DEFAULT_TITLE): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema)
