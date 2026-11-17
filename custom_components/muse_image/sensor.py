"""Cost sensor for Meta Muse Image."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import ATTR_KOSZT_OBRAZU, ATTR_OBRAZY, COST_PER_IMAGE, DOMAIN

if TYPE_CHECKING:
    from . import MuseImageCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the cost sensor."""
    coordinator: MuseImageCoordinator = hass.data[DOMAIN][entry.entry_id]
    entity = MuseImageCostSensor(coordinator)
    coordinator.sensor_entity = entity
    async_add_entities([entity])


class MuseImageCostSensor(RestoreSensor):
    """Sensor reporting the total cost of generated images."""

    _attr_name = "Muse image koszt"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = "USD"
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator: MuseImageCoordinator) -> None:
        """Initialize the sensor."""
        self._coordinator = coordinator
        self._attr_unique_id = f"{coordinator.entry.entry_id}_cost"

    @property
    def native_value(self) -> float:
        """Return the total cost in USD."""
        return round(self._coordinator.cost_total, 2)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the image count and per-image cost."""
        return {
            ATTR_OBRAZY: self._coordinator.image_count,
            ATTR_KOSZT_OBRAZU: COST_PER_IMAGE,
        }

    async def async_added_to_hass(self) -> None:
        """Restore the cost counters from the previous run."""
        await super().async_added_to_hass()

        last_sensor_data = await self.async_get_last_sensor_data()
        if last_sensor_data is not None and last_sensor_data.native_value is not None:
            try:
                self._coordinator.cost_total = float(last_sensor_data.native_value)
            except (TypeError, ValueError):
                pass

        if (state := await self.async_get_last_state()) is not None:
            obrazy = state.attributes.get(ATTR_OBRAZY)
            if isinstance(obrazy, int):
                self._coordinator.image_count = obrazy

    @callback
    def async_update_cost(self) -> None:
        """Write the updated cost state."""
        self.async_write_ha_state()
