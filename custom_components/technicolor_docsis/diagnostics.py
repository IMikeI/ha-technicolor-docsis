"""Redacted snapshots without credentials, addresses, serial numbers or MACs."""

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import TechnicolorConfigEntry
from .const import CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: TechnicolorConfigEntry
) -> dict:
    coordinator = entry.runtime_data
    return {
        "update_interval": entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
        "last_update_success": coordinator.last_update_success,
        "router": async_redact_data(coordinator.data, {"SerialNumber", "CMMACAddress"}),
    }
