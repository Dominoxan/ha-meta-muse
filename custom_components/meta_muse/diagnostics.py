"""Diagnostics for Meta Muse Image."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_API_KEY, DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry, with the API key redacted."""
    coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)

    return {
        "entry": {
            "title": entry.title,
            "entry_id": entry.entry_id,
            "source": entry.source,
            "configured": bool(entry.data.get(CONF_API_KEY)),
            "options": dict(entry.options),
        },
        "state": (
            {
                "image_count": coordinator.image_count,
                "cost_total_usd": round(coordinator.cost_total, 2),
                "last_image_path": (
                    str(coordinator.last_image_path)
                    if coordinator.last_image_path is not None
                    else None
                ),
                "last_prompt": coordinator.last_prompt,
                "language": coordinator.language,
                "default_size": coordinator.default_size,
                "output_dir": str(coordinator.output_dir),
                "chat_model": coordinator.chat_model,
                "control_ha": coordinator.control_ha,
                "system_prompt": coordinator.system_prompt,
            }
            if coordinator is not None
            else None
        ),
    }
