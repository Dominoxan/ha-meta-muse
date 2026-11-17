# Changelog

Wszystkie istotne zmiany w tym projekcie. Format: [Keep a Changelog](https://keepachangelog.com/pl/1.1.0/),
wersjonowanie: [SemVer](https://semver.org/lang/pl/).

## [2.1.0] — 2026-11-17

### Dodane
- Liczniki kosztów przeżywają restart HA i odtworzenie wpisu: stan zapisywany do
  `<output_dir>/.meta_muse_stats.json` (`obrazy`, `koszt_usd`, `last_prompt`, `updated`)
  po każdym obrazie i wczytywany przy starcie. `RestoreSensor` został jako fallback.
- `last_prompt` encji obrazu jest przywracany razem z licznikami.

## [2.0.1] — 2026-11-17

### Poprawione
- `image.meta_muse_ostatni_obraz` pokazywał złamaną miniaturkę po restarcie HA: `last_image_path`
  żyje tylko w pamięci. Przy starcie integracja przywraca teraz najnowszy plik PNG z katalogu
  wyjściowego, a encja ustawia `image_last_updated` z mtime pliku.

## [2.0.0] — 2026-11-17

### Zmienione (BREAKING)
- Domena integracji `muse_image` → **`meta_muse`** (integracja nie robi już tylko obrazów).
- Klucz YAML `muse_image:` → `meta_muse:`, usługa `muse_image.generate` → `meta_muse.generate`.
- Nazwy encji (a więc i `entity_id`): `ai_task.meta_muse`, `image.meta_muse_ostatni_obraz`,
  `sensor.meta_muse_koszt`; agent `conversation.meta_muse_spark` bez zmian.
- Repozytorium: `Dominoxan/ha-meta-muse` (wcześniej `ha-muse-image`, stary URL przekierowuje).

### Migracja z 1.x
1. Usuń katalog `custom_components/muse_image/` i stary wpis integracji (Ustawienia → Urządzenia i usługi).
2. Zmień klucz w `configuration.yaml` na `meta_muse:` i zrestartuj HA.
3. Popraw odwołania do usługi `muse_image.generate` i starych `entity_id` w automatyzacjach/skryptach.
   Licznik kosztów startuje od zera.

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
- Pierwsze wydanie: usługa `meta_muse.generate`, platforma `ai_task` (Generate image),
  `image.muse_ostatni_obraz`, `sensor.meta_muse_koszt` (USD, przywracany po restarcie),
  konfiguracja YAML (`async_step_import`) i UI, opcje katalogu/rozmiaru/języka, diagnostyka bez klucza API.
