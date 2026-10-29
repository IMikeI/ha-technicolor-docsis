"""Shared device identity and missing-channel availability."""

from typing import Any

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import device_identifier
from .coordinator import RouterCoordinator
from .data import find_row


class RouterEntity(CoordinatorEntity[RouterCoordinator]):
    """Read a current row rather than retaining stale channel data."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: RouterCoordinator,
        key: str,
        table: str | None = None,
        identity: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self.table = table
        self.identity = identity
        suffix = f"{table}_{identity}_{key}" if table else key
        self._attr_unique_id = f"{device_identifier(coordinator.data)}_{suffix}"
        self._attr_device_info = coordinator.device_info

    @property
    def row(self) -> dict[str, Any] | None:
        if self.table is None:
            return self.coordinator.data["system"]
        return find_row(self.coordinator.data, self.table, self.identity)

    @property
    def available(self) -> bool:
        return super().available and self.row is not None
