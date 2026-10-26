"""Configuration and options flows for Molekule."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .api import ApiConnectionError, AuthenticationError, MolekuleApi
from .const import (
    DOMAIN,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_REFRESH_RATE,
    CONF_REFRESH_RATE_DEFAULT,
    CONF_SILENT_AUTO,
)

_LOGGER = logging.getLogger(__name__)
_USER_SCHEMA = vol.Schema({vol.Required(CONF_EMAIL): str, vol.Required(CONF_PASSWORD): str})
_PASSWORD_SCHEMA = vol.Schema({vol.Required(CONF_PASSWORD): str})


async def _async_validate_input(user_input: dict[str, Any]) -> dict[str, str]:
    """Validate credentials and connectivity, always releasing the temporary client."""
    api = MolekuleApi(user_input[CONF_EMAIL], user_input[CONF_PASSWORD])
    try:
        await api.authenticate()
        if await api.get_devices() is None:
            return {"base": "cannot_connect"}
    except AuthenticationError:
        return {"base": "invalid_auth"}
    except ApiConnectionError:
        return {"base": "cannot_connect"}
    except Exception:
        _LOGGER.exception("Unexpected error validating Molekule connection")
        return {"base": "unknown"}
    finally:
        await api.close()
    return {}


class MolekuleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up a Molekule account and recover expired credentials."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            errors = await _async_validate_input(user_input)
            if not errors:
                existing_entry = await self.async_set_unique_id(user_input[CONF_EMAIL])
                if existing_entry:
                    # Retain support for updating an account through Add Integration.
                    return self.async_update_reload_and_abort(
                        existing_entry, data_updates=user_input, reason="reauth_successful"
                    )
                return self.async_create_entry(title=user_input[CONF_EMAIL], data=user_input)
        return self.async_show_form(step_id="user", data_schema=_USER_SCHEMA, errors=errors)

    async def async_step_reauth(self, entry_data: dict[str, Any]):
        """Ask for a new password for the existing account."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None):
        """Validate and replace credentials without changing account or entity IDs."""
        errors = {}
        if user_input is not None:
            entry = self._get_reauth_entry()
            password_update = {CONF_PASSWORD: user_input[CONF_PASSWORD]}
            errors = await _async_validate_input({**entry.data, **password_update})
            if not errors:
                return self.async_update_reload_and_abort(entry, data_updates=password_update)
        return self.async_show_form(
            step_id="reauth_confirm", data_schema=_PASSWORD_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return a flow whose config entry is provided by Home Assistant."""
        return MolekuleOptionsFlow()


class MolekuleOptionsFlow(config_entries.OptionsFlowWithReload):
    """Change polling and automatic-mode options, then reload the integration."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_REFRESH_RATE,
                    default=self.config_entry.options.get(
                        CONF_REFRESH_RATE,
                        self.config_entry.options.get("sync_interval", CONF_REFRESH_RATE_DEFAULT),
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=1)),
                vol.Optional(
                    CONF_SILENT_AUTO,
                    default=self.config_entry.options.get(CONF_SILENT_AUTO, False),
                ): bool,
            }),
        )
