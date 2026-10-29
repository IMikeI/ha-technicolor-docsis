"""One read-only polling cycle shared by all router entities."""

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AuthenticationError, RouterClient, RouterError, device_identifier
from .const import CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL, DOMAIN, NAME

_LOGGER = logging.getLogger(__name__)


class RouterCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch all measurements together and preserve authentication semantics."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: RouterClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=NAME,
            update_interval=timedelta(
                seconds=entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
            ),
            always_update=False,
        )
        self.client = client

    @callback
    def async_set_poll_interval(self, seconds: int) -> None:
        """Persist the interval and reschedule only an already active polling timer."""
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            options={**self.config_entry.options, CONF_UPDATE_INTERVAL: seconds},
        )
        self.update_interval = timedelta(seconds=seconds)
        if self._unsub_refresh is not None:
            self._schedule_refresh()

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self.client.async_get_data()
        except AuthenticationError as err:
            raise ConfigEntryAuthFailed("Router credentials were rejected") from err
        except RouterError as err:
            raise UpdateFailed(str(err)) from err
        if self.config_entry.unique_id != device_identifier(data):
            raise UpdateFailed("The configured address now belongs to a different router")
        return data

    @property
    def device_info(self) -> DeviceInfo:
        """Register one physical router, not one device per channel."""
        system = self.data["system"]
        return DeviceInfo(
            identifiers={(DOMAIN, device_identifier(self.data))},
            name="Technicolor CGA4233-EU",
            manufacturer=system.get("Manufacturer", "Technicolor").strip(),
            model=system["ModelName"].strip(),
            sw_version=system.get("SoftwareVersion", "").strip(),
            hw_version=system.get("HardwareVersion", "").strip(),
            serial_number=system.get("SerialNumber", "").strip() or None,
            configuration_url=self.client.host,
        )
