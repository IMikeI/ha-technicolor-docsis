"""DOCSIS channel measurements and independent error-table slots."""

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TechnicolorConfigEntry
from .coordinator import RouterCoordinator
from .data import CHANNEL_TABLES, TABLE_NAMES, number, row_identity
from .entity import RouterEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class RouterSensorDescription(SensorEntityDescription):
    """Describe a raw router field without inferring unavailable values."""

    numeric: bool = True


MEASUREMENT = SensorStateClass.MEASUREMENT
COUNTER = SensorStateClass.TOTAL_INCREASING
CHANNEL_SENSORS = (
    RouterSensorDescription(
        key="PowerLevel",
        translation_key="power",
        native_unit_of_measurement="dBmV",
        state_class=MEASUREMENT,
    ),
    RouterSensorDescription(
        key="SNRLevel",
        translation_key="snr",
        native_unit_of_measurement="dB",
        state_class=MEASUREMENT,
    ),
    RouterSensorDescription(
        key="Frequency",
        translation_key="frequency",
        native_unit_of_measurement="MHz",
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    RouterSensorDescription(
        key="StartFrequency",
        translation_key="start_frequency",
        native_unit_of_measurement="MHz",
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    RouterSensorDescription(
        key="PLCFrequency",
        translation_key="plc_frequency",
        native_unit_of_measurement="MHz",
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    RouterSensorDescription(
        key="CentralFrequency",
        translation_key="central_frequency",
        native_unit_of_measurement="MHz",
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    RouterSensorDescription(
        key="BandWidth",
        translation_key="bandwidth",
        native_unit_of_measurement="MHz",
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    RouterSensorDescription(
        key="SymbolRate",
        translation_key="symbol_rate",
        native_unit_of_measurement="Bd",
        state_class=MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    RouterSensorDescription(key="Modulation", translation_key="modulation", numeric=False),
    RouterSensorDescription(key="FFT", translation_key="fft", numeric=False),
    RouterSensorDescription(
        key="Profile",
        translation_key="profile",
        numeric=False,
        entity_registry_enabled_default=False,
    ),
    RouterSensorDescription(
        key="ChannelType",
        translation_key="channel_type",
        numeric=False,
        entity_registry_enabled_default=False,
    ),
    RouterSensorDescription(
        key="Octets",
        translation_key="octets",
        native_unit_of_measurement="B",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=COUNTER,
        entity_registry_enabled_default=False,
    ),
    RouterSensorDescription(key="Correcteds", translation_key="corrected", state_class=COUNTER),
    RouterSensorDescription(
        key="Uncorrectables", translation_key="uncorrectable", state_class=COUNTER
    ),
)
ERROR_SENSORS = tuple(
    description
    for description in CHANNEL_SENSORS
    if description.key in ("Octets", "Correcteds", "Uncorrectables")
)
SYSTEM_SENSORS = (
    RouterSensorDescription(key="CMStatus", translation_key="cm_status", numeric=False),
    RouterSensorDescription(
        key="UpTime",
        translation_key="uptime",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RouterSensorDescription(
        key="CPUUsage",
        translation_key="cpu_usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RouterSensorDescription(
        key="MemTotal",
        translation_key="memory_total",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    RouterSensorDescription(
        key="MemFree",
        translation_key="memory_free",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: TechnicolorConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    known: set[tuple[str, str, str]] = set()
    async_add_entities(
        RouterSensor(coordinator, description)
        for description in SYSTEM_SENSORS
        if description.key in coordinator.data["system"]
    )

    @callback
    def discover_channels() -> None:
        entities = []
        for table in (*CHANNEL_TABLES, "ErrTbl"):
            descriptions = ERROR_SENSORS if table == "ErrTbl" else CHANNEL_SENSORS
            for row in coordinator.data["modem"][table]:
                identity = row_identity(table, row)
                if identity is None:
                    continue
                for description in descriptions:
                    key = (table, identity, description.key)
                    if description.key in row and key not in known:
                        known.add(key)
                        entities.append(RouterSensor(coordinator, description, table, identity))
        if entities:
            async_add_entities(entities)

    discover_channels()
    entry.async_on_unload(coordinator.async_add_listener(discover_channels))


class RouterSensor(RouterEntity, SensorEntity):
    """One measurement; additional channel fields remain in the lock attributes."""

    entity_description: RouterSensorDescription

    def __init__(
        self,
        coordinator: RouterCoordinator,
        description: RouterSensorDescription,
        table: str | None = None,
        identity: str | None = None,
    ) -> None:
        super().__init__(coordinator, description.key, table, identity)
        self.entity_description = description
        self._attr_translation_placeholders = (
            {"channel": f"{TABLE_NAMES[table]} {identity}"} if table else {}
        )

    @property
    def native_value(self) -> int | float | str | None:
        value = (self.row or {}).get(self.entity_description.key)
        if self.entity_description.numeric:
            return number(value, self.entity_description.native_unit_of_measurement)
        return str(value).strip() if value is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.key == "CMStatus":
            return {
                key: value
                for key, value in (self.row or {}).items()
                if key not in ("SerialNumber", "CMMACAddress")
            }
        if self.table:
            attributes = {"source_table": self.table}
            attributes["statistics_slot" if self.table == "ErrTbl" else "channel_id"] = (
                self.identity
            )
            return attributes
        return None
