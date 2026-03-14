# Phase 2 Research

## Findings From Current Workflow

### 1. Header cards
Nagłówek już ma `gap:12px`, ale wizualnie kafle nadal zlewają się przez zbyt podobne tło, ciasny rytm i brak mocniejszego rozdzielenia od copy w hero.

### 2. Section naming
Aktualny HTML nadal używa copy `Wszystkie projekty widoczne w RCL`, a wersja tekstowa `Wszystkie projekty w RCL`. Obie wersje wymagają zmiany na `Najnowsze projekty w RCL`.

### 3. Metadata spacing
Po fazie 1 HTML używa separatora `&middot;`, ale plan nadal powinien objąć:
- zwiększenie odstępu i wysokości linii metadanych,
- spójny render w sekcji głównej i w sekcji końcowej,
- odpowiednik tych zmian w plain text.

### 4. Footer branding
Stopka nadal jest bardzo techniczna i zawiera tylko źródło oraz datę. Brakuje nazwy newslettera i podpisu autora.

### 5. Scope boundary
Ta faza nie powinna zmieniać źródła danych ani pipeline AI. Dotyczy wyłącznie prezentacji, copy i końcowego odbioru maila.

## Implications
- Większość zmian da się zamknąć w `Build Email If Any`.
- Największe ryzyko regresji to rozjazd między HTML i plain text, więc obie reprezentacje trzeba planować razem.
- Faza 2 powinna zakończyć się realnym sendem testowym, ale nie musi już zmieniać heurystyk AI.
