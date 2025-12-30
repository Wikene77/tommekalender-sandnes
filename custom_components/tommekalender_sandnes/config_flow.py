from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id(user_input["url"])
            self._abort_if_unique_id_configured()

            title = (user_input.get("name") or "Tømmekalender").strip()

            return self.async_create_entry(
                title=title,
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required("url"): str,
                vol.Optional("name", default="Tømmekalender Sandnes Kommune"): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema)
