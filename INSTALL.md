# Meta Muse Image — instalacja i testowanie

Integracja generuje obrazy przez Meta Model API (`muse-image-1.0`) i pokazuje
ostatni obraz na dashboardzie. Wersja 1.0.0, zero zewnętrznych zależności.

## 1. Kopiowanie plików

Skopiuj katalog `custom_components/meta_muse/` do `/config/custom_components/meta_muse/`
na HAOS (np. przez add-on Samba/SSH lub File editor).

Struktura po instalacji:

```
/config/custom_components/meta_muse/
  __init__.py
  manifest.json
  const.py
  config_flow.py
  ai_task.py
  image.py
  sensor.py
  conversation.py
  diagnostics.py
  services.yaml
  strings.json
  translations/en.json
```

## 2. Konfiguracja YAML (opcja A)

W `/config/configuration.yaml`:

```yaml
meta_muse:
  api_key: !secret model_api_key
  output_dir: /media/muse
  default_size: 1536x1024
  # v2 — opcjonalne (poniżej wartości domyślne):
  model: muse-spark-1.3
  control_ha: true
  prompt: "Jesteś asystentem inteligentnego domu. Odpowiadaj po polsku."
```

I w `/config/secrets.yaml`:

```yaml
model_api_key: "TU_WKLEJ_KLUCZ_MODEL_API"
```

Po restarcie HA integracja pojawi się w Ustawienia → Urządzenia i usługi jako
„Meta Muse Image". `api_key` trafia do wpisu konfiguracyjnego, `output_dir`
i `default_size` do opcji.

`api_key` możesz też podać jawnie (bez `!secret`), ale `!secret` jest zalecane.

## 3. Konfiguracja przez UI (opcja B)

Ustawienia → Urządzenia i usługi → Dodaj integrację → wyszukaj „Meta Muse Image".
Podajesz klucz API. `output_dir`, `default_size` i `language` zmieniasz później
w przycisku „Konfiguruj" (opcje).

## 4. Testowanie generowania

Developer Tools → Akcje (Actions):

```yaml
action: meta_muse.generate
data:
  prompt: "Zachód słońca nad górami"
  size: "1536x1024"
  filename: "zachod.png"
  overwrite: true
```

Wymagane jest tylko `prompt`. Odpowiedź zwraca np.:

```yaml
path: /media/muse/zachod.png
filename: zachod.png
cost: 0.01
obrazy: 1
koszt_calkowity: 0.01
```

Oczekiwany plik: `/media/muse/zachod.png` (przy domyślnym `output_dir`:
`/media/muse/muse_YYYYMMDD_HHMMSS.png`).

## 5. Encje

| Encja | Opis |
|-------|------|
| `ai_task.meta_muse` | Zadanie AI: generuje obraz z promptu. |
| `image.muse_ostatni_obraz` | Ostatnio wygenerowany obraz (atrybut `last_prompt`). |
| `sensor.meta_muse_koszt` | Suma kosztów w USD (atrybuty: `obrazy`, `koszt_obrazu`). |
| `conversation.meta_muse_spark` | Agent czatu „Meta Muse Spark" (v2). |

## 6. Gdy się nie ładuje

Sprawdź logi:

```
homeassistant.components.meta_muse
```

w Ustawienia → System → Logi. Najczęstsze przyczyny:

- Brak pliku w `/config/custom_components/meta_muse/` albo literówka w nazwie
  katalogu → w logach „Integration not found" / „Platform not found".
- Nieprawidłowy YAML w `configuration.yaml` (wcięcia) → błąd walidacji konfiguracji.
- Zły klucz API → integracja się załaduje, ale generowanie rzuci
  „Meta API zwróciło błąd 401/403". Klucza nie ma w logach (jest redagowany).
- Katalog `/media/muse` bez praw zapisu → ostrzeżenie przy starcie i błąd
  „Nie można utworzyć katalogu" przy generowaniu.

## 7. Koszty

Każdy zwrócony obraz kosztuje **0.01 USD**. `sensor.meta_muse_koszt` sumuje
koszty w ramach bieżącej sesji i przywraca wartość po restarcie HA.

## 8. Agent czatu „Meta Muse Spark" (v2)

Integracja wystawia agenta rozmowy opartego na modelu `muse-spark-1.3`.
Agent odpowiada na tekst i — przy włączonym sterowaniu — może zmieniać stan
Home Assistant (światła, sceny, urządzenia) przez narzędzia asystenta HA.

### 8.1 Wybór agenta w Assist

Ustawienia → Głosowi asystenci → wybierz istniejącego asystenta (albo dodaj
nowy) → w polu „Agent konwersacji" wybierz „Meta Muse Spark".

### 8.2 Opcje agenta

Ustawienia → Urządzenia i usługi → Meta Muse Image → „Konfiguruj":

- **Model czatu** — jeden z: `muse-spark-1.3` (domyślny), `muse-spark-1.2`,
  `muse-spark-1.1`, `muse-spark-1.3-contributor`.
- **Sterowanie Home Assistant** — włącz/wyłącz dostęp do narzędzi HA
  (światła, sceny itd.). Domyślnie włączone.
- **Instrukcje systemowe** — prompt systemowy agenta (domyślnie polski).

### 8.3 Test przez `conversation.process`

Developer Tools → Akcje (Actions):

```yaml
action: conversation.process
data:
  agent_id: conversation.meta_muse_spark
  text: "Włącz światło w salonie"
```

Oczekiwany efekt: odpowiedź agenta w polu `response.speech`, np. potwierdzenie
„Włączyłem światło w salonie." — a przy włączonym sterowaniu encja światła
rzeczywiście zmienia stan na `on`.

Test czystej rozmowy (bez sterowania):

```yaml
action: conversation.process
data:
  agent_id: conversation.meta_muse_spark
  text: "Jaka jest dziś pogoda w Krakowie?"
```

### 8.4 Jak wyłączyć sterowanie HA

Ustawienia → Urządzenia i usługi → Meta Muse Image → „Konfiguruj" →
przełącz „Sterowanie Home Assistant" na wyłączone. Po zapisie integracja się
przeładuje, a agent przestanie otrzymywać narzędzia HA (encja
`conversation.meta_muse_spark` straci funkcję CONTROL). W YAML odpowiada temu
klucz `control_ha: false`.
