"""Image platform for Meta Muse Image."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import ATTR_LAST_PROMPT, DOMAIN

if TYPE_CHECKING:
    from . import MuseImageCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the last-image entity."""
    coordinator: MuseImageCoordinator = hass.data[DOMAIN][entry.entry_id]
    entity = MuseImageEntity(coordinator)
    coordinator.image_entity = entity
    async_add_entities([entity])


class MuseImageEntity(ImageEntity):
    """Image entity showing the last generated image."""

    _attr_name = "Meta Muse ostatni obraz"

    def __init__(self, coordinator: MuseImageCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator.hass)
        self._coordinator = coordinator
        self._attr_unique_id = f"{coordinator.entry.entry_id}_last_image"
        self._attr_content_type = "image/png"

    def image(self) -> bytes | None:
        """Return the bytes of the last image (called via the executor)."""
        path = self._coordinator.last_image_path
        if path is None:
            return None
        try:
            return path.read_bytes()
        except OSError:
            return None

    async def async_added_to_hass(self) -> None:
        """Adopt the image restored by the coordinator (survives HA restarts)."""
        await super().async_added_to_hass()
        path = self._coordinator.last_image_path
        if path is None:
            return
        mtime = await self.hass.async_add_executor_job(self._file_mtime, path)
        if mtime is None:
            return
        self._attr_image_last_updated = mtime
        self.__dict__.pop("image_last_updated", None)
        self.__dict__.pop("image_url", None)
        self.async_write_ha_state()

    @staticmethod
    def _file_mtime(path) -> "datetime | None":
        """Return the file modification time in UTC."""
        try:
            return dt_util.utc_from_timestamp(path.stat().st_mtime)
        except OSError:
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the last prompt as an attribute."""
        return {ATTR_LAST_PROMPT: self._coordinator.last_prompt}

    @callback
    def async_refresh_image(self) -> None:
        """Force re-reading the image file after a new generation."""
        self._cached_image = None
        self._attr_image_last_updated = dt_util.utcnow()
        # cached_property values are memoised in __dict__ — drop them so the new
        # timestamp/URL reach the frontend instead of the stale cached value.
        self.__dict__.pop("image_last_updated", None)
        self.__dict__.pop("image_url", None)
        self.async_write_ha_state()
