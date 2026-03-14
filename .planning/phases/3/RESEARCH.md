# Phase 3 Research

## Findings From Existing Verification

### 1. Transport and layout are no longer the bottleneck
Po fazie 1 i 2 workflow:
- dochodzi do `Send via Resend`,
- wysyła realnego maila,
- ma już poprawiony layout i spójne copy.

To oznacza, że faza 3 może skupić się na treści bez ponownego rozwiązywania problemów infrastrukturalnych.

### 2. Strong projects vs weak projects
Dotychczasowe próbki pokazują dwa wzorce:
- projekty z dobrym uzasadnieniem dają mocne, konkretne summary i `keyChanges`,
- projekty ze słabszym materiałem nadal potrafią brzmieć zbyt ogólnie, mimo że formalnie spełniają schemat.

### 3. Current AI prompt already blocks title paraphrase
Prompt zabrania zaczynania od tytułu aktu, ale to nie wystarcza do wymuszenia odpowiednio konkretnego poziomu merytorycznego dla wszystkich projektów.

### 4. Existing post-processing can be extended
`Finalize Project Analysis` już:
- odrzuca odpowiedzi zbyt podobne do tytułu,
- składa fallback z `keyChanges`,
- zapewnia author-aware summary.

To dobry punkt do dalszego tuningu jakości bez przebudowy architektury.

## Implications
- Faza 3 powinna objąć zarówno prompt, jak i review gotowego newslettera.
- Najbardziej wartościowe będzie zdefiniowanie jasnych kryteriów redakcyjnych dla summary.
- Finalna decyzja o ukończeniu fazy powinna zależeć od jakości realnego maila, a nie tylko od statusu `success`.
