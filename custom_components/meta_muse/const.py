"""Constants for the Meta Muse Image integration."""

from typing import Final

DOMAIN: Final = "meta_muse"

# Config / options keys (names in English).
CONF_API_KEY: Final = "api_key"
CONF_OUTPUT_DIR: Final = "output_dir"
CONF_DEFAULT_SIZE: Final = "default_size"
CONF_LANGUAGE: Final = "language"
CONF_MODEL: Final = "model"
CONF_CONTROL_HA: Final = "control_ha"

# Service fields.
CONF_PROMPT: Final = "prompt"
CONF_SIZE: Final = "size"
CONF_FILENAME: Final = "filename"
CONF_OVERWRITE: Final = "overwrite"

SERVICE_GENERATE: Final = "generate"

# Sensor / image entity attribute names.
ATTR_OBRAZY: Final = "obrazy"
ATTR_KOSZT_OBRAZU: Final = "koszt_obrazu"
ATTR_LAST_PROMPT: Final = "last_prompt"

# Meta Model API facts (do not change).
MODEL_NAME: Final = "muse-image-1.0"
API_BASE_URL: Final = "https://api.meta.ai/v1"
API_GENERATIONS_URL: Final = f"{API_BASE_URL}/images/generations"
CHAT_COMPLETIONS_URL: Final = f"{API_BASE_URL}/chat/completions"
REQUEST_TIMEOUT: Final = 180  # seconds; generation can be slow
CHAT_REQUEST_TIMEOUT: Final = 120  # seconds; chat turn timeout

# One returned image costs 0.01 USD; n images = n * 0.01 USD.
COST_PER_IMAGE: Final = 0.01

# Defaults.
DEFAULT_OUTPUT_DIR: Final = "/media/muse"
DEFAULT_SIZE: Final = "1536x1024"
DEFAULT_LANGUAGE: Final = "pl"

# Conversation (chat) defaults.
DEFAULT_CHAT_MODEL: Final = "muse-spark-1.3"
CHAT_MODELS: Final = [
    "muse-spark-1.3",
    "muse-spark-1.2",
    "muse-spark-1.1",
    "muse-spark-1.3-contributor",
]
MAX_TOOL_ITERATIONS: Final = 8

DEFAULT_SYSTEM_PROMPT: Final = (
    "Jesteś Meta Muse Spark, asystent inteligentnego domu opartego na Home "
    "Assistant. Odpowiadaj po polsku, zwięźle i konkretnie. Gdy użytkownik "
    "prosi o zmianę stanu domu (światła, urządzenia, sceny), użyj dostępnych "
    "narzędzi i potwierdź krótko, co zostało zrobione."
)
