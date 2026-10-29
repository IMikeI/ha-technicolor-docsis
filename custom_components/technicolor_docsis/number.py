"""User-adjustable polling interval stored in the integration options."""

import math

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TechnicolorConfigEntry
from .api import device_identifier
from .const import (
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
)
from .coordinator import RouterCoordinator

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant, entry: TechnicolorConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add the local configuration control to the router device."""
    async_add_entities([PollingIntervalNumber(entry.runtime_data)])


class PollingIntervalNumber(NumberEntity):
    """Keep the configuration control available independently of router reads."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_entity_category = EntityCategory.CONFIG
    _attr_device_class = NumberDeviceClass.DURATION
    _attr_translation_key = "update_interval"
    _attr_icon = "mdi:timer-cog-outline"
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_native_min_value = MIN_UPDATE_INTERVAL
    _attr_native_max_value = MAX_UPDATE_INTERVAL
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: RouterCoordinator) -> None:
        self.coordinator = coordinator
        self._attr_unique_id = f"{device_identifier(coordinator.data)}_{CONF_UPDATE_INTERVAL}"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> int:
        return self.coordinator.config_entry.options.get(
            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
        )

    async def async_set_native_value(self, value: float) -> None:
        """Change the shared interval without reloading or fetching router data."""
        if (
            not math.isfinite(value)
            or value != int(value)
            or not MIN_UPDATE_INTERVAL <= value <= MAX_UPDATE_INTERVAL
        ):
            raise ServiceValidationError(
                f"The interval must be a whole number between {MIN_UPDATE_INTERVAL} "
                f"and {MAX_UPDATE_INTERVAL} seconds"
            )
        self.coordinator.async_set_poll_interval(int(value))
        self.async_write_ha_state()
