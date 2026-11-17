# Meta Muse — integracja Home Assistant

Generowanie obrazów (**Muse Image**, `muse-image-1.0`) i agent czatu (**Muse Spark**, `muse-spark-1.3`)
przez Meta Model API, prosto w Home Assistant. Wersja **1.1.0**, zero zewnętrznych zależności.

## Co daje

| Platforma | Efekt |
|---|---|
| `ai_task` | `ai_task.muse_image` — akcja *Generate image* z promptu (widoczna w Narzędziach deweloperskich i automatyzacjach) |
| usługa `muse_image.generate` | generowanie z poziomu skryptu/przycisku, zwraca ścieżkę, nazwę pliku i koszt |
| `image` | `image.muse_ostatni_obraz` — ostatnio wygenerowany obraz (atrybut `last_prompt`) |
| `sensor` | `sensor.muse_image_koszt` — suma kosztów w USD + liczba obrazów |
| `conversation` | `conversation.meta_muse_spark` — agent „Meta Muse Spark” do Assist, potrafi sterować HA (tool calling) |

Każdy zwrócony obraz kosztuje **$0.01** (cennik Meta Model API). Obrazy lądują w `/media/muse`
(katalog konfigurowalny) i są widoczne w Mediach HA.

## Instalacja

### HACS (custom repository)

1. HACS → ⋮ → **Custom repositories**.
2. URL: `https://github.com/Dominoxan/ha-muse-image`, kategoria **Integration**.
3. Zainstaluj „Meta Muse”, potem **zrestartuj Home Assistant**.
4. Ustawienia → Urządzenia i usługi → **Dodaj integrację** → „Meta Muse” → wklej klucz API.

### Ręcznie

Skopiuj `custom_components/muse_image/` do `/config/custom_components/muse_image/` i zrestartuj HA.

## Konfiguracja

Klucz API: [dev.meta.ai](https://dev.meta.ai) → Model API key.

### YAML (opcjonalnie)

```yaml
# configuration.yaml
muse_image:
  api_key: !secret muse_model_api_key
  output_dir: /media/muse
  default_size: 1536x1024
  # v1.1 — opcjonalne:
  model: muse-spark-1.3
  control_ha: true
  prompt: "Jesteś asystentem inteligentnego domu. Odpowiadaj po polsku."
```

```yaml
# secrets.yaml
muse_model_api_key: "LLM|..."
```

### Opcje (UI)

Ustawienia → Urządzenia i usługi → Meta Muse → **Konfiguruj**:

- **Model czatu** — `muse-spark-1.3` (domyślny), `1.2`, `1.1`, `1.3-contributor`,
- **Sterowanie Home Assistant** — dostęp agenta do narzędzi HA (encje wystawione do Assist),
- **Instrukcje systemowe** — prompt systemowy agenta,
- **Katalog wyjściowy**, **Domyślny rozmiar**, **Język promptu**.

## Przykłady

```yaml
action: muse_image.generate
data:
  prompt: "Minimalistyczna ikona samolotu na granatowym tle, bez tekstu"
  size: "1536x1024"
  filename: "samolot"
  overwrite: true
```

Odpowiedź: `path: /media/muse/samolot.png`, `cost: 0.01`, `obrazy: 1`, `koszt_calkowity: 0.01`.

```yaml
action: ai_task.generate_image
data:
  entity_id: ai_task.muse_image
  task_name: "ikona palmy"
  instructions: "Prosta ikona palmy na piaskowym tle, płaska, bez tekstu"
```

```yaml
action: conversation.process
data:
  agent_id: conversation.meta_muse_spark
  text: "Jaka jest temperatura w kuchni?"
```

## Agent w Assist

Ustawienia → Głosowi asystenci → wybierz pipeline → **Agent konwersacji**: „Meta Muse Spark”.
Wyłączenie „Sterowanie Home Assistant” w opcjach odbiera agentowi funkcję `CONTROL` — zostaje czysty czat.

## Uwagi

- Meta nie ma TTS — integracja świadomie nie wystawia platformy `tts`.
- Rozmiar (`size`) ustawia **proporcje**, nie dokładne piksele; model zwraca własną rozdzielczość.
- Długie generowanie (>30 s) potrafi przekroczyć timeout odpowiedzi usługi — plik i licznik i tak się zgadzają.
- Klucz API jest redagowany w diagnostyce.

## Licencja

MIT — patrz [LICENSE](LICENSE).
