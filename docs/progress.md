# Avancement

## Dépôt

- Dépôt privé `arthurlemon/hydro-agentic` créé et connexion SSH personnelle vérifiée.
- Plan initial conservé puis traduit en français avec ses 28 sections.
- Exécution demandée : phases 0 à 2, arrêt avant la configuration Foundry.

## Décisions

- uv gère Python 3.12, `.venv`, les dépendances et toutes les commandes Python.
- OpenRouter remplace l’option Ollama à la demande de l’utilisateur. Clé fournie ultérieurement, tests sans réseau en attendant.
- SQLite et les contrôles minimaux d’approbation sont introduits dès la phase 1 : aucune création sans état persistant et approbation.
- La recherche initiale est lexicale, sans embeddings; le contrat permet son remplacement.
- Identité locale de démonstration configurée par l’hôte, jamais par le LLM.
- Interfaces partagées : modèles Pydantic → services → registre d’outils; registre et client MCP → même boucle agentique.

## Phase 0

Projet uv, configuration secrète masquée, schémas Pydantic, données synthétiques et sept documents français ajoutés. Premier cycle : 3 tests en échec pour modules absents, puis 3 réussis; Ruff et mypy réussis. Commit `0b1cf86`.

## Phase 1 — implémentée, validation du modèle réel en attente

Services JSON, recherche lexicale, dix outils typés, preuves et état SQLite, approbation séparée, ordre simulé idempotent. Boucle autonome OpenRouter avec appels d’outils variables et récupération itérative; plafond d’étapes et conclusion structurée vérifiée. CLI d’investigation, lecture, approbation, rejet et reprise.

Tests initiaux des services/contrôles en échec puis 15 réussis; ajout de l’agent : 12 nouveaux échecs attendus pour module absent puis suite de 29 tests réussie. Ces résultats utilisent un double du modèle.

## Phase 2 — transport MCP implémenté et testé

Serveur et client MCP stdio réels. Catalogue de dix outils, schémas d’entrée/sortie et même registre métier. Tests dans des sous-processus : lecture, refus, boucle d’investigation, brouillon, approbation hors agent, reconnexion puis création sans doublon. Suite initiale CLI/MCP : 4 échecs pour modules absents, puis 34 tests réussis avec le parcours complet.

## Revue et corrections

Une revue indépendante a relevé quatre défauts : comparaison lexicale de fuseaux, investigations concurrentes, message fournisseur nul et procédure vide/illisible. Tests de régression : 7 échecs observés et 2 cas déjà couverts; corrections puis **43 tests réussis**.

- Les instants de télémétrie sont comparés comme des dates avec fuseau.
- Un verrou de fichier par incident protège l’investigation complète et autorise une reprise après libération. Décision : verrou local macOS/Linux plutôt qu’une génération distribuée, car le PoC est mono-machine; un autre déploiement exigera un mécanisme adapté.
- Les messages fournisseurs non objets deviennent des erreurs métier et l’état passe à `failed`.
- Les documents vides, blancs ou UTF-8 invalides renvoient une erreur structurée.

Autres décisions d’implémentation : SDK MCP `Server` bas niveau pour contrôler les schémas et l’enveloppe d’erreur; commandes `state` et `resume` pour distinguer consultation et création approuvée; consignes dans `agent/loop.py`, sans fichier supplémentaire. Les contrats et les objectifs du plan restent identiques.

## Point d’arrêt

Contrôles finaux : `uv run pytest -q` — 43 tests réussis; `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy` (17 fichiers), `uv build` et `git diff --check` réussis. Distribution source et wheel construites. Les tests MCP utilisent de vrais processus locaux; les appels OpenRouter restent simulés.

- Ajouter `OPENROUTER_API_KEY` à `.env` puis vérifier les parcours réels Python et MCP. Aucun score de qualité LLM n’est encore mesuré.
- Phases 3 à 9 non commencées; aucune ressource Azure créée. SQLite, approbation et audit minimal ont été avancés pour sécuriser le parcours local.
