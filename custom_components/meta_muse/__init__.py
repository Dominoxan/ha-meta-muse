"""The Meta Muse Image integration."""

from __future__ import annotations

import base64
from dataclasses import dataclass
import json
import logging
from pathlib import Path
import re
from typing import TYPE_CHECKING

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util

from .const import (
    API_GENERATIONS_URL,
    CHAT_COMPLETIONS_URL,
    CHAT_REQUEST_TIMEOUT,
    CONF_CONTROL_HA,
    CONF_DEFAULT_SIZE,
    CONF_FILENAME,
    CONF_LANGUAGE,
    CONF_MODEL,
    CONF_OUTPUT_DIR,
    CONF_OVERWRITE,
    CONF_PROMPT,
    CONF_SIZE,
    COST_PER_IMAGE,
    DEFAULT_CHAT_MODEL,
    DEFAULT_LANGUAGE,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SIZE,
    DEFAULT_SYSTEM_PROMPT,
    DOMAIN,
    MODEL_NAME,
    REQUEST_TIMEOUT,
    SERVICE_GENERATE,
)

if TYPE_CHECKING:
    from .image import MuseImageEntity
    from .sensor import MuseImageCostSensor

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.AI_TASK,
    Platform.IMAGE,
    Platform.SENSOR,
    Platform.CONVERSATION,
]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_API_KEY): cv.string,
                vol.Optional(CONF_OUTPUT_DIR): cv.string,
                vol.Optional(CONF_DEFAULT_SIZE): cv.string,
                vol.Optional(CONF_LANGUAGE): cv.string,
                vol.Optional(CONF_MODEL): cv.string,
                vol.Optional(CONF_CONTROL_HA): cv.boolean,
                vol.Optional(CONF_PROMPT): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

GENERATE_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PROMPT): cv.string,
        vol.Optional(CONF_SIZE): cv.string,
        vol.Optional(CONF_FILENAME): cv.string,
        vol.Optional(CONF_OVERWRITE, default=False): cv.boolean,
    }
)

_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]")


def sanitize_filename(filename: str) -> str:
    """Return a safe lowercase .png filename (no path separators, no traversal)."""
    name = filename.replace("\\", "/").split("/")[-1]
    name = name.replace("..", "")
    name = _FILENAME_RE.sub("_", name).strip("._-")
    if not name:
        name = "obraz"
    if name.lower().endswith(".png"):
        name = f"{name[:-4]}.png"
    else:
        name = f"{name}.png"
    return name


@dataclass(slots=True)
class GenerateResult:
    """Result of a single image generation."""

    image_bytes: bytes
    path: Path
    filename: str
    cost: float


class MuseImageCoordinator:
    """Shared state, Meta API client and cost accounting."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.entry = entry
        self.api_key: str = entry.data[CONF_API_KEY]
        self.session = async_get_clientsession(hass)
        self.output_dir: Path = Path(
            entry.options.get(
                CONF_OUTPUT_DIR, entry.data.get(CONF_OUTPUT_DIR, DEFAULT_OUTPUT_DIR)
            )
        )
        self.default_size: str = entry.options.get(CONF_DEFAULT_SIZE, DEFAULT_SIZE)
        self.language: str = entry.options.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
        self.chat_model: str = entry.options.get(CONF_MODEL, DEFAULT_CHAT_MODEL)
        self.control_ha: bool = entry.options.get(CONF_CONTROL_HA, True)
        self.system_prompt: str = entry.options.get(CONF_PROMPT, DEFAULT_SYSTEM_PROMPT)
        self.image_count: int = 0
        self.cost_total: float = 0.0
        self.last_image_path: Path | None = None
        self.last_prompt: str | None = None
        self.image_entity: MuseImageEntity | None = None
        self.sensor_entity: MuseImageCostSensor | None = None

    async def async_generate(
        self,
        prompt: str,
        size: str | None = None,
        filename: str | None = None,
        overwrite: bool = False,
    ) -> GenerateResult:
        """Generate an image, save it to disk and update counters."""
        size = size or self.default_size
        b64 = await self._async_call_api(prompt, size)

        fname = sanitize_filename(filename) if filename else self._default_filename()
        path = self.output_dir / fname
        if path.exists() and not overwrite:
            raise HomeAssistantError(
                f"Plik {path} już istnieje. Użyj opcji overwrite, aby go nadpisać."
            )

        image_bytes = await self.hass.async_add_executor_job(
            self._decode_and_save, b64, path
        )

        cost = COST_PER_IMAGE  # n=1: jeden obraz = 0.01 USD
        self.image_count += 1
        self.cost_total += cost
        self.last_image_path = path
        self.last_prompt = prompt

        if self.image_entity is not None:
            self.image_entity.async_refresh_image()
        if self.sensor_entity is not None:
            self.sensor_entity.async_update_cost()

        return GenerateResult(image_bytes, path, fname, cost)

    async def _async_call_api(self, prompt: str, size: str) -> str:
        """Call the Meta Model API and return the base64 image string."""
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "n": 1,
            "size": size,
            "output_format": "png",
            "response_format": "b64_json",
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with self.session.post(
                API_GENERATIONS_URL,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
            ) as resp:
                if resp.status >= 400:
                    self._raise_api_error(resp.status, await resp.text())
                data = await resp.json()
        except aiohttp.ClientError as err:
            raise HomeAssistantError(
                f"Nie udało się połączyć z Meta API: {err}"
            ) from err

        images = data.get("data") if isinstance(data, dict) else None
        if (
            not images
            or not isinstance(images[0], dict)
            or not images[0].get("b64_json")
        ):
            raise HomeAssistantError("Meta API nie zwróciło obrazu.")

        return images[0]["b64_json"]

    def _raise_api_error(self, status: int, text: str) -> None:
        """Raise a readable, key-free error for a 4xx/5xx response."""
        message = text
        try:
            error = json.loads(text).get("error")
            if isinstance(error, dict):
                message = error.get("message") or text
            elif isinstance(error, str):
                message = error
        except (json.JSONDecodeError, AttributeError):
            pass
        raise HomeAssistantError(f"Meta API zwróciło błąd {status}: {message}")

    async def async_chat(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> dict:
        """Call the Meta Model chat completions endpoint and return the message."""
        payload: dict = {
            "model": self.chat_model,
            "messages": messages,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with self.session.post(
                CHAT_COMPLETIONS_URL,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=CHAT_REQUEST_TIMEOUT),
            ) as resp:
                if resp.status >= 400:
                    self._raise_api_error(resp.status, await resp.text())
                data = await resp.json()
        except aiohttp.ClientError as err:
            raise HomeAssistantError(
                f"Nie udało się połączyć z Meta API: {err}"
            ) from err

        choices = data.get("choices") if isinstance(data, dict) else None
        if not choices or not isinstance(choices[0], dict):
            raise HomeAssistantError("Meta API nie zwróciło odpowiedzi.")
        message = choices[0].get("message")
        if not isinstance(message, dict):
            raise HomeAssistantError("Meta API zwróciło nieprawidłową odpowiedź.")
        return message

    def _decode_and_save(self, b64: str, path: Path) -> bytes:
        """Decode base64 and write the PNG file (runs in the executor)."""
        data = base64.b64decode(b64 + "=" * (-len(b64) % 4))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return data

    def _default_filename(self) -> str:
        """Return a timestamped default filename."""
        return f"muse_{dt_util.now().strftime('%Y%m%d_%H%M%S')}.png"


async def _handle_generate_service(call: ServiceCall) -> ServiceResponse:
    """Handle the meta_muse.generate service."""
    coordinators: dict[str, MuseImageCoordinator] = call.hass.data.get(DOMAIN, {})
    if not coordinators:
        raise HomeAssistantError("Integracja Meta Muse Image nie jest skonfigurowana.")

    coordinator = next(iter(coordinators.values()))
    result = await coordinator.async_generate(
        prompt=call.data[CONF_PROMPT],
        size=call.data.get(CONF_SIZE),
        filename=call.data.get(CONF_FILENAME),
        overwrite=call.data[CONF_OVERWRITE],
    )
    return {
        "path": str(result.path),
        "filename": result.filename,
        "cost": result.cost,
        "obrazy": coordinator.image_count,
        "koszt_calkowity": round(coordinator.cost_total, 2),
    }


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Meta Muse Image and its service."""
    hass.data.setdefault(DOMAIN, {})

    hass.services.async_register(
        DOMAIN,
        SERVICE_GENERATE,
        _handle_generate_service,
        schema=GENERATE_SERVICE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    if config.get(DOMAIN):
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=dict(config[DOMAIN]),
            )
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up Meta Muse Image from a config entry."""
    coordinator = MuseImageCoordinator(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    try:
        await hass.async_add_executor_job(
            lambda: coordinator.output_dir.mkdir(parents=True, exist_ok=True)
        )
    except OSError as err:
        _LOGGER.warning(
            "Nie można utworzyć katalogu wyjściowego %s: %s",
            coordinator.output_dir,
            err,
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_options))


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Unload a config entry."""
    await hass.config_entries.async_unload_platforms_or_raise(entry, PLATFORMS)
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
