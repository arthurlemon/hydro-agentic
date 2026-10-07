# Avancement

## Dépôt

- Dépôt privé `arthurlemon/hydro-agentic` créé et connexion SSH personnelle vérifiée.
- Plan initial conservé puis traduit en français avec ses 28 sections.
- Exécution demandée : phases 0 à 2, arrêt avant la configuration Foundry.

## Décisions

- uv gère Python 3.12, `.venv`, les dépendances et toutes les commandes Python.
- OpenRouter remplace l’option Ollama. La clé est maintenant configurée; modèle par défaut `openai/gpt-5.6-luna`, vérifié dans le catalogue OpenRouter.
- PostgreSQL remplace SQLite à la demande de l’utilisateur. Les contrôles minimaux d’approbation sont introduits dès la phase 1 : aucune création sans état persistant et approbation.
- La recherche initiale est lexicale, sans embeddings; le contrat permet son remplacement.
- Identité locale de démonstration configurée par l’hôte, jamais par le LLM.
- Interfaces partagées : modèles Pydantic → services → registre d’outils; registre et client MCP → même boucle agentique.

## Phase 0

Projet uv, configuration secrète masquée, schémas Pydantic, données synthétiques et sept documents français ajoutés. Premier cycle : 3 tests en échec pour modules absents, puis 3 réussis; Ruff et mypy réussis. Commit `0b1cf86`.

## Phase 1 — implémentée et essayée avec le modèle réel

Services JSON, recherche lexicale, dix outils typés, preuves et état PostgreSQL (initialement SQLite), approbation séparée, ordre simulé idempotent. Boucle autonome OpenRouter avec appels d’outils variables et récupération itérative; plafond d’étapes et conclusion structurée vérifiée. CLI d’investigation, lecture, approbation, rejet et reprise.

Tests initiaux des services/contrôles en échec puis 15 réussis; ajout de l’agent : 12 nouveaux échecs attendus pour module absent puis suite de 29 tests réussie. Ces résultats utilisent un double du modèle.

## Phase 2 — transport MCP implémenté et testé

Serveur et client MCP stdio réels. Catalogue de dix outils, schémas d’entrée/sortie et même registre métier. Tests dans des sous-processus : lecture, refus, boucle d’investigation, brouillon, approbation hors agent, reconnexion puis création sans doublon. Suite initiale CLI/MCP : 4 échecs pour modules absents, puis 34 tests réussis avec le parcours complet.

## Revue et corrections

Une revue indépendante a relevé quatre défauts : comparaison lexicale de fuseaux, investigations concurrentes, message fournisseur nul et procédure vide/illisible. Tests de régression : 7 échecs observés et 2 cas déjà couverts; corrections puis **43 tests réussis**.

- Les instants de télémétrie sont comparés comme des dates avec fuseau.
- Initialement, un verrou de fichier par incident protégeait l’investigation complète. La migration PostgreSQL le remplace par un verrou consultatif de session partagé entre processus.
- Les messages fournisseurs non objets deviennent des erreurs métier et l’état passe à `failed`.
- Les documents vides, blancs ou UTF-8 invalides renvoient une erreur structurée.

Autres décisions d’implémentation : SDK MCP `Server` bas niveau pour contrôler les schémas et l’enveloppe d’erreur; commandes `state` et `resume` pour distinguer consultation et création approuvée; consignes dans `agent/loop.py`, sans fichier supplémentaire. Les contrats et les objectifs du plan restent identiques.

## Vérification initiale des phases 0 à 2

Contrôles finaux : `uv run pytest -q` — 43 tests réussis; `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy` (17 fichiers), `uv build` et `git diff --check` réussis. Distribution source et wheel construites. Les tests MCP utilisent de vrais processus locaux; les appels OpenRouter restent simulés.

- Phases 3 à 9 non commencées; aucune ressource Azure créée. Persistance, approbation et audit minimal ont été avancés pour sécuriser le parcours local.

## Passage à PostgreSQL et GPT-5.6 Luna

- Modèle par défaut testé puis poussé sur `main` : commit `8ab9ce8`, 44 tests réussis avant migration.
- PostgreSQL 17 lancé avec Docker Compose sur `127.0.0.1:55432`, volume persistant. Aucun ancien fichier SQLite contenant des incidents à convertir.
- Dépôt `state/postgres.py` avec psycopg, JSONB, transactions et verrous de lignes, insertion concurrente idempotente et verrou d’investigation de session. URI masquée dans la configuration; erreurs de connexion sans identifiants.
- Suite exécutée contre PostgreSQL dans des schémas isolés : **48 tests réussis**, dont CLI/MCP réels, rollback, démarrage concurrent, unicité et verrou interprocessus. Les quatre nouveaux tests ont d’abord échoué avant l’implémentation du dépôt.
- Migration poussée sur `main` : commit `e9625a4`; Ruff, mypy, construction et 48 tests validés.

## Premiers essais réels et précision du contrat

Les appels réels GPT-5.6 Luna ont fonctionné avec les outils Python et MCP. Trois premières investigations ont conclu `insufficient_evidence`, dont deux résultats trop prudents : le modèle a interprété `baseline_stddev` comme l’écart-type en °C plutôt que comme le score normalisé déjà calculé. Les observations et les résumés persistés montrent cette ambiguïté; aucune création d’ordre n’a eu lieu.

Correction du contrat de télémétrie : `measurement_definitions` explique désormais la quantité `temperature_z_score`, son unité et le calcul déjà effectué. Le nom du champ et les valeurs restent compatibles avec les données existantes. Un test a d’abord échoué faute de définition, puis la suite de **49 tests** a réussi, ainsi que Ruff et mypy. Correction poussée : `b806c50`.

Les quatre scénarios rejoués avec GPT-5.6 Luna donnent les résultats attendus : P1 sous 24 h avec brouillon en attente (MCP), absence d’urgence pour le faible risque (MCP), preuves insuffisantes sans huile confirmée (Python), preuves insuffisantes pour l’actif inconnu (Python). Une création sans approbation a ensuite été refusée via MCP. [Bilan et observations](essais-openrouter.md).

Point d’arrêt : PostgreSQL fonctionne localement, `INC-1001` attend une approbation, aucun ordre n’a été créé pendant ces essais réels. La prochaine phase est la configuration Foundry; aucune ressource Azure n’a été créée.
