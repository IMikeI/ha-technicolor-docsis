"""Operational status and per-channel DOCSIS lock indicators."""

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TechnicolorConfigEntry
from .coordinator import RouterCoordinator
from .data import CHANNEL_TABLES, TABLE_NAMES, row_identity
from .entity import RouterEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant, entry: TechnicolorConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    known: set[tuple[str, str]] = set()
    async_add_entities([RouterConnection(coordinator)])

    @callback
    def discover_channels() -> None:
        entities = []
        for table in CHANNEL_TABLES:
            for row in coordinator.data["modem"][table]:
                identity = row_identity(table, row)
                if identity is not None and (table, identity) not in known:
                    known.add((table, identity))
                    entities.append(RouterChannelLock(coordinator, table, identity))
        if entities:
            async_add_entities(entities)

    discover_channels()
    entry.async_on_unload(coordinator.async_add_listener(discover_channels))


class RouterConnection(RouterEntity, BinarySensorEntity):
    """DOCSIS operational status, not an external Internet connectivity test."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_translation_key = "connection"

    def __init__(self, coordinator: RouterCoordinator) -> None:
        super().__init__(coordinator, "connection")

    @property
    def is_on(self) -> bool | None:
        status = (self.row or {}).get("CMStatus")
        return str(status).strip().upper() == "OPERATIONAL" if status is not None else None


class RouterChannelLock(RouterEntity, BinarySensorEntity):
    """Expose raw channel metadata without inventing error-slot mappings."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_translation_key = "channel_lock"

    def __init__(self, coordinator: RouterCoordinator, table: str, identity: str) -> None:
        super().__init__(coordinator, "lock", table, identity)
        self._attr_translation_placeholders = {"channel": f"{TABLE_NAMES[table]} {identity}"}

    @property
    def is_on(self) -> bool | None:
        status = (self.row or {}).get("LockStatus")
        return str(status).strip().lower() == "locked" if status is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"source_table": self.table, **(self.row or {})}
