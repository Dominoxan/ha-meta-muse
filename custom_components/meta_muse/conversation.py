"""Conversation platform for Meta Muse Image (Meta Muse Spark agent)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Literal

import probatio

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import llm
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.json import json_dumps

from .const import DOMAIN, MAX_TOOL_ITERATIONS

if TYPE_CHECKING:
    from . import MuseImageCoordinator

_LIMIT_EXCEEDED_MESSAGE = (
    f"Przekroczono limit {MAX_TOOL_ITERATIONS} rund wywołań narzędzi. "
    "Przerywam, żeby uniknąć zapętlenia rozmowy."
)


def _format_tool(
    tool: llm.Tool, custom_serializer: Any | None
) -> dict[str, Any]:
    """Format an HA tool as an OpenAI-compatible function tool."""
    unsupported_keys = {"oneOf", "anyOf", "allOf", "enum", "not"}
    schema = probatio.to_openapi(
        tool.parameters, custom_serializer=custom_serializer, openapi_version="3.1.0"
    )
    if unsupported_keys.intersection(schema):
        schema = {k: v for k, v in schema.items() if k not in unsupported_keys}
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": schema,
        },
    }


def _build_messages(content: list[conversation.Content]) -> list[dict[str, Any]]:
    """Convert the chat log content to OpenAI chat-completions messages."""
    messages: list[dict[str, Any]] = []
    for item in content:
        if isinstance(item, conversation.SystemContent):
            messages.append({"role": "system", "content": item.content})
        elif isinstance(item, conversation.UserContent):
            messages.append({"role": "user", "content": item.content})
        elif isinstance(item, conversation.AssistantContent):
            message: dict[str, Any] = {"role": "assistant"}
            if item.content is not None:
                message["content"] = item.content
            if item.tool_calls:
                message["tool_calls"] = [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.tool_name,
                            "arguments": json_dumps(tool_call.tool_args),
                        },
                    }
                    for tool_call in item.tool_calls
                ]
            messages.append(message)
        elif isinstance(item, conversation.ToolResultContent):
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": item.tool_call_id,
                    "content": json_dumps(
                        {"data": item.result.data, "error": item.result.error}
                    ),
                }
            )
    return messages


def _assistant_from_message(
    agent_id: str, message: dict[str, Any], tools_enabled: bool
) -> conversation.AssistantContent:
    """Build an AssistantContent from a Meta API chat-completions message."""
    content: str | None = message.get("content")
    tool_calls: list[llm.ToolInput] | None = None

    raw_tool_calls = message.get("tool_calls") if tools_enabled else None
    if raw_tool_calls:
        tool_calls = []
        for tool_call in raw_tool_calls:
            function = tool_call.get("function") if isinstance(tool_call, dict) else {}
            if not isinstance(function, dict):
                function = {}
            name = function.get("name") or ""
            try:
                args = json.loads(function.get("arguments") or "{}")
            except (json.JSONDecodeError, TypeError):
                args = {}
            if not isinstance(args, dict):
                args = {}
            tool_input = llm.ToolInput(tool_name=name, tool_args=args)
            if call_id := tool_call.get("id"):
                tool_input.id = call_id
            tool_calls.append(tool_input)

    return conversation.AssistantContent(
        agent_id=agent_id,
        content=content,
        tool_calls=tool_calls,
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Meta Muse Spark conversation agent."""
    coordinator: MuseImageCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MuseSparkConversationEntity(coordinator)])


class MuseSparkConversationEntity(
    conversation.ConversationEntity,
    conversation.AbstractConversationAgent,
):
    """Conversation agent backed by the Meta Muse Spark model."""

    _attr_has_entity_name = True
    _attr_name = "Meta Muse Spark"

    def __init__(self, coordinator: MuseImageCoordinator) -> None:
        """Initialize the agent."""
        self._coordinator = coordinator
        self._attr_unique_id = f"{coordinator.entry.entry_id}_conversation"
        if coordinator.control_ha:
            self._attr_supported_features = (
                conversation.ConversationEntityFeature.CONTROL
            )

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return MATCH_ALL

    async def async_added_to_hass(self) -> None:
        """When the entity is added to Home Assistant."""
        await super().async_added_to_hass()
        conversation.async_set_agent(self.hass, self._coordinator.entry, self)

    async def async_will_remove_from_hass(self) -> None:
        """When the entity will be removed from Home Assistant."""
        conversation.async_unset_agent(self.hass, self._coordinator.entry)
        await super().async_will_remove_from_hass()

    async def _async_handle_message(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> conversation.ConversationResult:
        """Process the user input and call the Meta API."""
        llm_hass_api: str | None = (
            llm.LLM_API_ASSIST if self._coordinator.control_ha else None
        )
        try:
            await chat_log.async_provide_llm_data(
                user_input.as_llm_context(DOMAIN),
                llm_hass_api,
                self._coordinator.system_prompt,
                user_input.extra_system_prompt,
            )
        except conversation.ConverseError as err:
            return err.as_conversation_result()

        await self._async_handle_chat_log(chat_log)

        return conversation.async_get_result_from_chat_log(user_input, chat_log)

    async def _async_handle_chat_log(self, chat_log: conversation.ChatLog) -> None:
        """Generate an answer for the chat log, executing HA tools as needed."""
        tools_enabled = chat_log.llm_api is not None
        tools: list[dict[str, Any]] | None = None
        if chat_log.llm_api:
            tools = [
                _format_tool(tool, chat_log.llm_api.custom_serializer)
                for tool in chat_log.llm_api.tools
            ]

        for _iteration in range(MAX_TOOL_ITERATIONS):
            messages = _build_messages(chat_log.content)
            message = await self._coordinator.async_chat(messages, tools)
            assistant = _assistant_from_message(
                self.entity_id, message, tools_enabled
            )
            async for _tool_result in chat_log.async_add_assistant_content(assistant):
                pass
            if not chat_log.unresponded_tool_results:
                return

        # Iteration limit reached: add a readable error, never raise.
        chat_log.async_add_assistant_content_without_tools(
            conversation.AssistantContent(
                agent_id=self.entity_id,
                content=_LIMIT_EXCEEDED_MESSAGE,
            )
        )
