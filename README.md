# Investigation agentique d’actifs électriques

Preuve de concept inspirée de pratiques d’un distributeur d’électricité. Toutes les données et procédures sont **synthétiques**. Aucun accès à un réseau électrique ou aux systèmes d’Hydro-Québec.

## Développement avec uv

```bash
uv python install 3.12
uv sync --locked
cp .env.example .env
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

Python est sélectionné par `.python-version`, l’environnement `.venv` et les dépendances sont gérés exclusivement avec **uv**; `uv.lock` fixe leurs versions. Exécuter les commandes depuis la racine du dépôt.

## Documentation

- [Plan du projet — 28 sections](PROJECT_PLAN.md)
- [Plan des phases 0 à 2](docs/plan-phases-0-2.md)
- [Avancement et vérifications](docs/progress.md)

La documentation, les procédures, les consignes et l’affichage sont en français. Les identifiants techniques restent en anglais. OpenRouter sera utilisé pour le modèle local à l’application; la clé sera ajoutée dans `.env`, jamais dans Git. Foundry intervient à la phase 3.
