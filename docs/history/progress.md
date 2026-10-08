# Avancement

## Dépôt

- Dépôt privé `arthurlemon/hydro-agentic` créé et connexion SSH personnelle vérifiée.
- Plan initial conservé puis traduit en français avec ses 28 sections.
- Demande initiale : phases 0 à 2, puis phase 3 autorisée après création du compte Azure et choix de GPT-5-mini.

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

Point d’arrêt des essais OpenRouter : PostgreSQL fonctionne localement, `INC-1001` attend une approbation, aucun ordre n’a été créé pendant ces essais réels. La configuration Foundry a ensuite été autorisée.

## Phase 3 — intégration Foundry et essais

- Azure CLI installé et connecté; abonnement d’essai actif, rôle Owner et protection des dépenses activée. Fournisseur CognitiveServices enregistré. Quota Luna nul dans les régions vérifiées; GPT-5-mini en East US 2 approuvé par l’utilisateur.
- Groupe, compte AIServices avec identité, projet avec identité et déploiement GlobalStandard créés; rôle Foundry User ajouté au projet. Documentation d’infrastructure poussée : `f2d47bd`.
- SDK Projects 2.8.0, Identity 1.26.0 et transport aiohttp gérés par uv. Première publication échouée faute d’aiohttp, puis publication réussie après ajout du transport; un test ouvre/ferme le véritable SDK sans réseau.
- Agent natif versionné avec les dix fonctions et consignes françaises. Adaptateur Responses conserve la conversation cloud et n’envoie que les nouveaux messages utilisateur/résultats d’outils, sans dupliquer les réponses ou perdre les items de raisonnement. Choix explicite `--provider foundry`; pas de clé Azure, de fallback ni de retry d’inférence automatique.
- Tests nouveaux : module absent observé avant implémentation; deux tests CLI d’abord en échec; régressions HTTP 429 et préservation de l’erreur du modèle à travers MCP d’abord en échec, puis corrigées.
- Revue indépendante : le schéma final manquait dans les consignes publiées. Correction testée RED→GREEN, agent version 3 publié et sélectionné. Même passe : erreurs d’URL mal formée converties, retries de publication désactivés avec timeouts, fermeture du projet et du credential tentée sans masquer l’erreur originale. Quatre nouveaux cas ont d’abord échoué.
- Premiers essais : appels réels et fonctions métier réussis, puis HTTP 429. La gestion affichait capacité 50, mais les en-têtes d’inférence affichaient encore les limites de capacité 1. Nouveau déploiement initialisé à 50, essais suivants réussis; ancien déploiement supprimé.
- Version 3 : P1 avec sept citations et brouillon `INC-1013` en attente, faible risque `INC-1014` sans urgence, température seule `INC-1015` et actif inconnu `INC-1016` avec preuves insuffisantes. Création sans approbation refusée via MCP, état inchangé. `INC-1001` OpenRouter reste inchangé.
- L’audit du premier P1 version 3 révélait 24 appels modèle : après préparation, une reformulation était refusée car le brouillon était figé. Test reproduisant ce coût supplémentaire en échec, puis arrêt déterministe après le lot d’outils produisant un brouillon validé. Aucun contrôle de preuve ou d’approbation assoupli. Essai final : `INC-1017`, P1 sous 24 h, huit citations valides, cinq appels modèle, attente d’approbation. Création sans approbation de nouveau refusée via MCP; état inchangé.
- Dernière suite : **69 tests réussis**, mypy valide 18 fichiers. Les tests automatisés ne consomment ni OpenRouter ni Azure; les investigations précédentes sont de véritables appels facturés. [Bilan des essais](essais-foundry.md).
- Ruff, formatage (50 fichiers), construction source/wheel et `git diff --check` réussis. Lecture réelle de la version 3 : dix fonctions et schéma complet de conclusion présents; limite de dépenses Azure toujours `On`. Application et PostgreSQL restent locaux. Phases 4 à 9 non commencées.
- Phase 3 terminée et poussée sur `main` : `2afe91d`. Arrêt demandé après le travail courant; aucune phase suivante lancée. PostgreSQL local et le déploiement Foundry restent disponibles; aucun ordre créé dans les essais réels.

## Phase 4 — recherche Azure (reprise autorisée)

- Demande de poursuivre les phases suivantes reçue; l’arrêt précédent est levé. Plan : [phases 4 à 9](../plans/plan-phases-4-9.md).
- Search Free créé en Canada Central après refus de capacité en East US 2. Clés désactivées, Entra et rôles limités au service; sept documents indexés dans `procedures-v1`, BM25 français sans embeddings ni offre payante. Bicep compilé, pas de déploiement Bicep exécuté.
- Contrat `ProcedureSearch`, adaptateur Azure et configuration propagée à MCP. Aucun repli local silencieux; extraits non probants, documents complets et sources inchangées. Dix tests d’abord en échec, puis suite de **79 tests réussis**, Ruff/formatage, mypy (19 fichiers), construction et diff vérifiés.
- Recherche réelle : TR-MAINT-004 puis TR-OIL-002. Investigation réelle Foundry → MCP → Azure Search : `INC-1018`, P1 sous 24 heures, cinq citations, trois appels modèle, attente d’approbation. Création sans approbation refusée via MCP et état inchangé. Les anciens incidents restent inchangés. [Configuration et bilan](../azure/search-setup.md).

## Phases 5–6 — confirmation des contrôles déjà présents

- Transactions PostgreSQL, état hors conversation, verrou interprocessus, brouillon figé, approbation/rejet et ordre unique déjà livrés : pas de réimplémentation ni de Cosmos DB.
- Couverture CLI ajoutée pour rejet par superviseur, état conservé après redémarrage, impossibilité de reprise et de réapprobation. Suite : **80 tests réussis**, Ruff et mypy valides. Tests CLI/MCP d’approbation/reprise/idempotence et tests PostgreSQL concurrents réexécutés dans la suite.
- [Procédure humaine et limites](../guides/approbation-reprise.md) documentées. Aucun incident applicatif approuvé ou ordre créé; la base applicative n’a pas été arrêtée. Phase 4 poussée : `d362503`.

## Phase 7 — traces corrélées

- Reprise après redémarrage : `main` propre, phases 4–6 déjà livrées, aucune réimplémentation. Validation de persistance/rejet poussée : `71ebb43`.
- OpenTelemetry par CLI, investigation, modèle, outil et requête MCP. Contexte W3C en métadonnées, corrélation de l’audit PostgreSQL, JSONL privé séparé de stdout MCP. Requêtes sous forme d’empreinte et longueur, pas de prompts/documents/arguments complets.
- Trois tests d’abord en échec, puis réussis, dont vrai processus MCP et exception contenant un texte sensible. Suite **83 tests**, Ruff, mypy (21 fichiers), construction et diff vérifiés. Phase poussée : `d8252b0`. [Limites et export OTLP facultatif](../guides/observabilite.md).

## Phase 8 — évaluations exécutables

- Dix scénarios dans des copies de données et un schéma PostgreSQL propre, supprimé après exécution. Le mode programmé exerce le backend et la boucle sans prétendre mesurer un LLM; modes Foundry/OpenRouter réels disponibles mais non exécutés dans cette nouvelle suite.
- Vérificateur testé avec résultat invalide et valide; code de sortie non nul vérifié. Résultat observé versionné : **10/10 en régression**; aucune note sémantique d’hallucination annoncée. Suite **87 tests**, Ruff et mypy (24 fichiers) réussis. Phase poussée : `72df20e`. [Rapports et limites](../evaluations/runner.md).

## Phase 9 — contrat analytique

- `AnalyticsService.predict` et adaptateurs JSON/Databricks ajoutés; JSON reste le défaut. Refus d’actif inconnu avant appel distant, endpoint contrôlé, validation de la réponse pour le même actif, délais et erreurs sans réponse brute ni substitution silencieuse.
- Seize cas d’abord en échec, puis réussis; deux vérifications supplémentaires pour autre actif et sélection distante sans configuration. Suite **105 tests**, mypy (25 fichiers) réussis. L’ordre des imports Ruff a ensuite été corrigé.
- Aucun compte/endpoint Databricks créé, aucun essai Azure Databricks lancé. [Contrat et configuration facultative](../guides/databricks.md). Les incidents applicatifs `INC-1001`, `INC-1017` et `INC-1018` sont toujours en attente, sans approbation ni ordre, vérification PostgreSQL exécutée.
- Revue indépendante des phases 7–9 : trois défauts confirmés — coercition des probabilités distantes booléennes/textuelles, preuves imbriquées insuffisamment vérifiées et approbation invalide acceptée par l’évaluateur (pas par le backend). Cinq cas ont échoué avant correction, puis validation stricte, contrôle des observations et métadonnées d’approbation. Suite finale **110 tests réussis**, Ruff et mypy (25 fichiers) réussis.
- Rapports enrichis avec appels modèle terminés, outils observés et tokens disponibles (`null` pour le double); assertion manquante observée en échec puis corrigée. Nouvelle exécution : **10/10 en régression**, rapport versionné régénéré. Aucun nouvel appel cloud ni nouvelle ressource payante durant les phases 7–9.

## Évolution vers une démonstration cloud — design

- Demande : héberger agents/outils, prompts, évaluations et traces dans Azure, avec UX métier et interface d’ingénierie, corpus public plus large et illustration des parcours Microsoft Learn. Databricks reporté. Orientation budgétaire : 30 USD/mois à vérifier avant déploiement.
- Ajout demandé : arrêt/suppression facile des services payants après la démo. [Design proposé](../architecture/cloud-demo.md) et [contrat de cycle de vie](../azure/demo-lifecycle.md) : ressources possédées versus externes, groupes runtime/data/observabilité/expériences, export et suppression ciblés, frais résiduels explicités.
- Docs réorganisées par architecture, Azure, guides, données, évaluations, apprentissage, plans et historique; index ajouté et liens locaux vérifiés. Inventaire du catalogue public Hydro-Québec et licences consignés; aucun dataset complet ingéré ni nouvelle ressource cloud créée dans ce lot documentaire.
- Prochaine étape : relecture du design écrit, puis plan d’implémentation du premier lot (visibilité cloud et cycle de vie commun).
