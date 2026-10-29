"""Technicolor DOCSIS custom integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    EVENT_HOMEASSISTANT_STOP,
    Platform,
)
from homeassistant.core import Event, HomeAssistant

from .api import RouterClient
from .coordinator import RouterCoordinator

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.NUMBER]
TechnicolorConfigEntry = ConfigEntry[RouterCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: TechnicolorConfigEntry) -> bool:
    """Validate the first snapshot before creating entities."""
    client = RouterClient(
        entry.data[CONF_HOST], entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD]
    )
    coordinator = RouterCoordinator(hass, entry, client)
    try:
        await coordinator.async_config_entry_first_refresh()
        entry.runtime_data = coordinator
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except BaseException:
        await client.close()
        raise

    async def close_on_shutdown(event: Event) -> None:
        await client.close()

    entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, close_on_shutdown))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: TechnicolorConfigEntry) -> bool:
    """Unload platforms and close only this integration's session."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.client.close()
    return unloaded
