"""GUI setup, reconfiguration, reauthentication and polling options."""

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers import selector

from .api import AuthenticationError, RouterClient, RouterError, device_identifier, normalize_host
from .const import (
    CONF_UPDATE_INTERVAL,
    DEFAULT_HOST,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_USERNAME,
    DOMAIN,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    NAME,
)


class TechnicolorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure a single physical cable modem."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return await self._async_configure("user", user_input)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._async_configure("reconfigure", user_input)

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._async_configure("reauth_confirm", user_input)

    async def _async_configure(
        self, step: str, user_input: dict[str, Any] | None
    ) -> ConfigFlowResult:
        entry = None
        if step == "reconfigure":
            entry = self._get_reconfigure_entry()
        elif step == "reauth_confirm":
            entry = self._get_reauth_entry()
        defaults = entry.data if entry else {}
        errors: dict[str, str] = {}
        if user_input is not None:
            defaults = user_input
            client = None
            try:
                host = normalize_host(user_input[CONF_HOST])
                client = RouterClient(host, user_input[CONF_USERNAME], user_input[CONF_PASSWORD])
                data = await client.async_get_data()
            except ValueError:
                errors[CONF_HOST] = "invalid_host"
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except RouterError:
                errors["base"] = "cannot_connect"
            else:
                unique_id = device_identifier(data)
                if entry and entry.unique_id != unique_id:
                    return self.async_abort(reason="wrong_device")
                config = {**user_input, CONF_HOST: host}
                if entry:
                    return self.async_update_reload_and_abort(
                        entry,
                        data_updates=config,
                        reason="reauth_successful"
                        if step == "reauth_confirm"
                        else "reconfigure_successful",
                    )
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=f"{NAME} CGA4233-EU", data=config)
            finally:
                if client:
                    await client.close()
        return self.async_show_form(
            step_id=step,
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, DEFAULT_HOST)): str,
                    vol.Required(
                        CONF_USERNAME, default=defaults.get(CONF_USERNAME, DEFAULT_USERNAME)
                    ): str,
                    vol.Required(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                    ),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "TechnicolorOptionsFlow":
        return TechnicolorOptionsFlow()


class TechnicolorOptionsFlow(config_entries.OptionsFlowWithReload):
    """Reload after changing the bounded update interval."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            interval = user_input[CONF_UPDATE_INTERVAL]
            if MIN_UPDATE_INTERVAL <= interval <= MAX_UPDATE_INTERVAL:
                return self.async_create_entry(title="", data={CONF_UPDATE_INTERVAL: int(interval)})
            errors["base"] = "invalid_interval"
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_UPDATE_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=MIN_UPDATE_INTERVAL,
                            max=MAX_UPDATE_INTERVAL,
                            step=1,
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement="s",
                        )
                    ),
                }
            ),
            errors=errors,
        )
