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
- [Architecture et limites](docs/architecture.md)
- [Contrats des outils](docs/tool-contracts.md)
- [Modèle de menaces](docs/threat-model.md)
- [Passage aux services Azure](docs/production-mapping.md)

La documentation, les procédures, les consignes et l’affichage sont en français. Les identifiants techniques restent en anglais. OpenRouter sera utilisé pour le modèle local à l’application; la clé sera ajoutée dans `.env`, jamais dans Git. Foundry intervient à la phase 3.

## Investigation réelle avec OpenRouter

Après avoir copié `.env.example` vers `.env`, renseigner `OPENROUTER_API_KEY` et choisir un modèle prenant en charge les appels d’outils avec `OPENROUTER_MODEL` (défaut : `openai/gpt-5.6-luna`). Cette exécution appelle une API payante selon la tarification du modèle; aucun appel réseau n’est nécessaire pour les tests.

```bash
# Phase 1 : outils Python directs, recommandation sans brouillon.
uv run hydro-agent investigate EVT-48392

# Phase 2 : même agent, outils via un sous-processus MCP.
# --prepare demande explicitement un brouillon si les preuves le justifient.
uv run hydro-agent investigate EVT-48392 --transport mcp --prepare
uv run hydro-agent state INC-1001
```

Le numéro d’incident est renvoyé par la commande; `INC-1001` correspond au premier incident d’une base neuve. Une nouvelle investigation du même événement réutilise l’incident. Un brouillon soumis à approbation est figé : utiliser `state`, `approve`, `reject` ou `resume` plutôt que relancer l’investigation.

```bash
# Action humaine séparée : identité SIMULÉE, contrôlée par l’environnement local.
HYDRO_ACTOR=superviseure-locale HYDRO_ROLE=maintenance_supervisor \
  uv run hydro-agent approve INC-1001

# Reprise après approbation, sans nouvel appel au LLM.
uv run hydro-agent resume INC-1001
uv run hydro-agent resume INC-1001  # Renvoie le même ordre, sans doublon.
```

`reject INC-1001` permet au superviseur de rejeter un brouillon. Aucun ordre n’est créé par `approve`. Les rôles locaux servent à tester les contrôles métier; ils ne constituent pas une authentification de production.

### Scénarios inclus

| Événement | Situation synthétique | Résultat attendu |
|---|---|---|
| `EVT-48392` | Température élevée et dégradation d’huile actuelle confirmée | Inspection P1 sous 24 h, preuves citées, approbation obligatoire |
| `EVT-LOW` | Température normale et faible risque ML | Aucune intervention urgente |
| `EVT-TEMP` | Température élevée, ancien constat d’huile uniquement | Investigation complémentaire, preuves insuffisantes |
| `EVT-UNKNOWN` | Actif absent du registre | Échec sûr des outils, aucune invention |

Les tests ajoutent une panne ML, une procédure absente, un document malveillant, des rôles interdits et des créations concurrentes. Ils utilisent un **double de modèle**; ils ne mesurent pas la qualité d’un LLM réel.

### Serveur MCP autonome

Pour un incident déjà présent dans SQLite :

```bash
uv run hydro-mcp --incident INC-1001
```

Le serveur utilise stdio pour JSON-RPC et stderr pour les diagnostics. Le client doit être local et de confiance. Aucun serveur HTTP ni accès Foundry distant n’est configuré. La base et l’audit sont stockés dans `.hydro/incidents.sqlite3` (exclu de Git).
