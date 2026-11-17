"""AI Task platform for Meta Muse Image."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components import ai_task, conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN, MODEL_NAME

if TYPE_CHECKING:
    from . import MuseImageCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the AI Task entity."""
    coordinator: MuseImageCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MuseImageTaskEntity(coordinator)])


class MuseImageTaskEntity(ai_task.AITaskEntity):
    """AI Task entity that generates images with Meta Muse."""

    _attr_name = "Meta Muse"

    def __init__(self, coordinator: MuseImageCoordinator) -> None:
        """Initialize the entity."""
        self._coordinator = coordinator
        self._attr_unique_id = f"{coordinator.entry.entry_id}_ai_task"
        self._attr_supported_features = ai_task.AITaskEntityFeature.GENERATE_IMAGE

    async def _async_generate_image(
        self,
        task: ai_task.GenImageTask,
        chat_log: conversation.ChatLog,
    ) -> ai_task.GenImageTaskResult:
        """Generate an image from the task instructions."""
        result = await self._coordinator.async_generate(
            prompt=task.instructions,
            size=self._coordinator.default_size,
        )
        return ai_task.GenImageTaskResult(
            image_data=result.image_bytes,
            conversation_id=chat_log.conversation_id,
            mime_type="image/png",
            model=MODEL_NAME,
            revised_prompt=task.instructions,
        )
