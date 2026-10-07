# Plan d’implémentation — phases 0 à 2

Exécution native dans cette session, selon la demande de l’utilisateur. Spécification : [PROJECT_PLAN.md](../PROJECT_PLAN.md).

## Objectif et décisions

Livrer un parcours local français avec données synthétiques, services typés, PostgreSQL, agent à appels d’outils et transport MCP stdio. Aucun service Azure à provisionner. PostgreSQL remplace le choix SQLite initial à la demande de l’utilisateur.

- Python 3.12, uv, Pydantic, pytest, Ruff, mypy, SDK MCP officiel et HTTPX.
- OpenRouter configurable avec `OPENROUTER_MODEL` et `OPENROUTER_API_KEY`; clé ajoutée par l’utilisateur pour l’essai réel.
- Double de modèle pour les tests reproductibles; aucune validation autonome réelle revendiquée sans modèle.
- Recherche lexicale normalisée avec citations; interface remplaçable par Azure AI Search.
- Identité attachée par l’hôte; aucune identité ou approbation fournie par le modèle.
- PostgreSQL : événement unique, approbation liée au brouillon, création transactionnelle unique.
- Documentation, consignes, descriptions d’outils, données narratives et affichage en français; noms techniques en anglais.

## Vérifications prioritaires

Fuseaux et fenêtre relative à l’événement; absence de données et pannes sans invention; arguments supplémentaires refusés; approbation non falsifiable par les outils; concurrence et reprise après redémarrage.

## 1. Traduction et phase 0

- [x] Traduction des 28 sections, README et suivi.
- [x] Projet uv, configuration, modèles Pydantic et données synthétiques.
- [x] Tests en échec puis réussis; pytest, Ruff et mypy.
- [x] Commit de la phase 0.

## 2. Services et état

Fichiers : `models.py`, `services/data.py`, `services/search.py`, `state/postgres.py`, `tools/registry.py`.

- [x] Tests initiaux de données absentes, télémétrie datée, recherche accentuée, autorisations et idempotence.
- [x] Interfaces `DataService`, `SearchService`, `IncidentRepository`, `ToolRegistry.call(name, arguments)`.
- [x] Preuves liées à l’incident; brouillon étayé et création avec approbation persistée uniquement.
- [x] Reprise, rejet, falsification, modification après approbation et créations concurrentes.

## 3. Agent et CLI — phase 1

Fichiers : `agent/model.py`, `agent/loop.py`, `cli.py`, `scripts/run_local.py`.

- [x] Sélection variable d’outils, recherche supplémentaire, panne, réponse invalide et limite d’étapes.
- [x] Adaptateur OpenRouter et protocole de modèle injectable.
- [x] CLI `investigate`, `state`, `approve`, `reject`, `resume`; approbation hors agent.
- [x] Cas de risque élevé, faible risque, température seule, actif inconnu et document malveillant.
- [ ] Validation avec une clé OpenRouter réelle (attente de configuration utilisateur).

## 4. MCP — phase 2

Fichiers : `mcp/server.py`, `mcp/client.py`, tests d’intégration stdio.

- [x] Catalogue, schémas, erreurs et autorisations dans un vrai sous-processus MCP.
- [x] Dix outils via le SDK MCP officiel, registre métier partagé.
- [x] Client MCP implémentant le contrat de la boucle d’agent.
- [x] Parcours avec double de modèle via MCP, citations, approbation et reconnexion idempotente.
- [x] Architecture, contrats, menaces, limites et configuration Foundry à venir documentés.
- [x] Revue indépendante et corrections avec tests de régression.
- [x] Contrôles finaux réussis : 43 tests, Ruff, mypy, distribution source et wheel.
- [x] Commits `0b1cf86` et `78345cd` poussés sur `origin/main`.

Arrêt avant la phase 3. Les écarts mineurs au découpage initial et les vérifications sont consignés dans [le suivi](progress.md).
