# Meta Muse

Integracja Home Assistant do Meta Model API:

- **Muse Image** (`muse-image-1.0`) — generowanie obrazów z promptu; usługa `meta_muse.generate`, platforma AI Task, encja `image.meta_muse_ostatni_obraz`, trwały licznik kosztów (`$0.01` za obraz).
- **Muse Spark** (`muse-spark-1.3`) — agent czatu do Assist (`conversation.meta_muse_spark`) z tool callingiem do Home Assistant.

Zero zewnętrznych zależności, konfiguracja przez YAML albo UI, obraz trafia do `/media/muse`.

Pełny opis, konfiguracja i rozwiązywanie problemów: [README](README.md).
