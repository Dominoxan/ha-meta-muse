# Changelog

Wszystkie istotne zmiany w tym projekcie. Format: [Keep a Changelog](https://keepachangelog.com/pl/1.1.0/),
wersjonowanie: [SemVer](https://semver.org/lang/pl/).

## [1.1.0] — 2026-11-17

### Dodane
- Platforma `conversation`: agent **Meta Muse Spark** (`conversation.meta_muse_spark`) z tool callingiem
  do Home Assistant (`control_ha`), limitem 8 rund narzędzi i polskim promptem systemowym.
- Opcje: `model` (`muse-spark-1.3` / `1.2` / `1.1` / `1.3-contributor`), `control_ha`, `prompt`.
- `async_get_options_flow` — w UI pojawia się przycisk „Konfiguruj”.
- Branding: `brand/icon.png` (512×512), `brand/logo.png` (1024×683).
- `dependencies`: `conversation` obok `ai_task` i `image`.

### Poprawione
- `ImageEntity`: czyszczenie `cached_property` (`image_last_updated`, `image_url`) po nowym obrazie —
  wcześniej frontend pokazywał stary obraz mimo nowego stanu encji.

## [1.0.0] — 2026-11-17

### Dodane
- Pierwsze wydanie: usługa `muse_image.generate`, platforma `ai_task` (Generate image),
  `image.muse_ostatni_obraz`, `sensor.muse_image_koszt` (USD, przywracany po restarcie),
  konfiguracja YAML (`async_step_import`) i UI, opcje katalogu/rozmiaru/języka, diagnostyka bez klucza API.
