# Plan d’implémentation — phases 0 à 2

Exécution native dans cette session, selon la demande de l’utilisateur. Spécification : [PROJECT_PLAN.md](../PROJECT_PLAN.md).

## Objectif et décisions

Livrer un parcours local français avec données synthétiques, services typés, SQLite, agent à appels d’outils et transport MCP stdio. Aucun service Azure à provisionner.

- Python 3.12, uv, Pydantic, pytest, Ruff, mypy, SDK MCP officiel et HTTPX.
- OpenRouter fournit le modèle, configurable avec `OPENROUTER_MODEL` et `OPENROUTER_API_KEY`; l’utilisateur ajoutera la clé au moment de la vérification réelle.
- Un double de modèle sert aux tests reproductibles; seule une exécution avec un véritable modèle démontre le choix autonome d’outils.
- Recherche lexicale normalisée avec citations; interface remplaçable par Azure AI Search.
- Autorisations définies par le processus hôte; aucune identité ou approbation fournie par le modèle.
- SQLite : incident unique par événement, approbation liée au brouillon, création transactionnelle unique par incident.
- Documentation, consignes, descriptions d’outils, données narratives et affichage en français; noms techniques en anglais.

## Vérifications prioritaires

Horodatages avec fuseau et fenêtre relative à l’événement; absence de données et pannes sans invention; refus des arguments supplémentaires; approbation non falsifiable par les outils; création concurrente et reprise après redémarrage.

## Tâches

### 1. Traduction et phase 0

- [ ] Traduire le plan, le README et le suivi sans perdre les exigences.
- [ ] Créer `pyproject.toml`, `.env.example`, `.gitignore`, paquet et configuration.
- [ ] Ajouter modèles Pydantic et jeux synthétiques : risque élevé, faible risque, température seule, actif inconnu.
- [ ] Tester la validation des valeurs, fuseaux et données; exécuter pytest, Ruff et mypy.
- [ ] Commit de la phase 0.

### 2. Services et état

Fichiers : `models.py`, `services/data.py`, `services/search.py`, `state/sqlite.py`, `tools/registry.py`.

- [ ] Écrire puis exécuter des tests initialement en échec pour données absentes, télémétrie datée, recherche accentuée, accès interdit et idempotence.
- [ ] Implémenter les interfaces `DataService`, `SearchService`, `IncidentRepository` et `ToolRegistry.call(name, arguments)`.
- [ ] Relier les preuves récupérées à l’incident; refuser tout brouillon non étayé et toute création sans approbation persistée.
- [ ] Vérifier reprise, rejet, falsification, modification après approbation et création concurrente.

### 3. Agent et CLI — phase 1

Fichiers : `agent/model.py`, `agent/loop.py`, `agent/instructions.md`, `cli.py`, `scripts/run_local.py`.

- [ ] Tester une sélection d’outils variable, une recherche supplémentaire, un outil indisponible, une réponse non structurée et la limite d’itérations.
- [ ] Implémenter l’adaptateur OpenRouter et un protocole de modèle injectable dans les tests.
- [ ] Fournir `investigate`, `status`, `approve`, `reject`, `create` en CLI; approbation hors de l’agent.
- [ ] Vérifier le scénario élevé, les preuves insuffisantes et le blocage d’un appel malveillant sans approbation.
- [ ] Demander la clé OpenRouter pour l’investigation réelle; distinguer cette validation des tests sans réseau.
- [ ] Commit de la phase 1.

### 4. MCP — phase 2

Fichiers : `mcp/server.py`, `mcp/client.py`, tests d’intégration stdio.

- [ ] Tester le catalogue, les schémas d’entrée/sortie, les erreurs et les autorisations par un vrai sous-processus MCP.
- [ ] Exposer les dix outils avec FastMCP et réutiliser les mêmes services.
- [ ] Fournir un client MCP implémentant le même contrat que les outils directs.
- [ ] Vérifier le parcours complet via MCP, les citations, l’approbation et l’absence de doublon.
- [ ] Documenter architecture, contrats, limites locales et configuration Foundry à venir.
- [ ] Exécuter tous les contrôles, commit et push; arrêter avant la phase 3.
