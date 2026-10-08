# Phases 4 à 9 — plan d’exécution

**Objectif :** poursuivre le PoC existant avec recherche Azure, preuves de reprise, traces et évaluations exécutables, sans remplacer les contrôles métier.

**Architecture :** mêmes outils Python/MCP et agents OpenRouter/Foundry. Services interchangeables; état et autorisations PostgreSQL hors du modèle. Exécution dans cette session, avec commits et pushes sur `main` après vérification.

**Contraintes :** Python 3.12 et uv exclusivement; prose française; données synthétiques uniquement; Azure AI Search **Free seulement**, aucune migration automatique vers une offre payante. PostgreSQL conservé. Aucun ordre réel ni approbation des incidents de démonstration existants. Databricks réel facultatif, à configurer séparément.

**Points de vérification :** panne Azure sans recherche locale cachée; extrait distinct du document complet; contenu injecté toujours non fiable; reprise/idempotence après arrêt; absence de secrets dans les traces; évaluations distinguant double de modèle et vrai LLM.

## 1. Phase 4 — recherche Azure

- [x] Créer Search Free avec authentification Entra, désactiver les clés et documenter/Bicep les ressources.
- [x] Ajouter un contrat `ProcedureSearch.get/search` et `AzureSearchService`, même format de citations que la recherche locale.
- [x] Indexer les sept procédures, avec analyseur français, recherche lexicale BM25; aucun embedding payant requis, aucune prétention de recherche vectorielle.
- [x] Configurer explicitement le service choisi, propager la configuration au processus MCP, aucune substitution silencieuse.
- [x] Tests RED→GREEN : documents/index, accès complet, panne, configuration, erreurs et transport MCP. Vérifier une recherche et une investigation Foundry réelles sur un événement distinct.

## 2. Phases 5–6 — état et approbation

- [x] Confirmer les livrables PostgreSQL déjà implémentés : transactions, verrou interprocessus, reprise, approbation/rejet, brouillon figé et ordre unique.
- [x] Exécuter les tests CLI/MCP après redémarrage; documenter la procédure d’approbation, sans approuver les incidents réels existants.
- [x] Compléter uniquement les manques observés; Cosmos reste facultatif et non déployé. Pas de changement métier requis; ajout de couverture CLI du rejet.

## 3. Phase 7 — observabilité

- [x] Ajouter traces OpenTelemetry par investigation, modèle et outil, identifiant de trace propagé à MCP et audit PostgreSQL.
- [x] Journal JSONL local séparé de stdout MCP, avec latence, résultats, empreintes de requêtes/citations et usage; ne pas journaliser clés, URI de connexion, prompts ou documents complets.
- [x] Tester la corrélation Python/MCP, erreurs et masquage; documenter l’export OTLP facultatif. Pas d’Application Insights payant par défaut.

## 4. Phase 8 — évaluations

- [x] Créer `scripts/run_evals.py` et un rapport JSON/Markdown issu des dix cas définis dans le plan.
- [x] Vérifications structurelles exécutables R1–R7, échec non nul pour violation, résultats observés et données manquantes explicites; limites sémantiques documentées.
- [x] Mode de régression sans LLM distant clairement étiqueté; mode LLM réel facultatif pour mesurer l’agent, sans confondre les deux (pas encore exécuté dans cette suite).
- [x] Tester le vérificateur avec un résultat volontairement invalide, les dix cas et l’isolation des états.

## 5. Phase 9 — analytique remplaçable

- [x] Contrat `AnalyticsService.predict`, adaptateur JSON simulé et adaptateur Databricks de service de modèle configurable.
- [x] Tester erreurs, temps limites, schéma de prédiction et interdiction de fabriquer une valeur en cas de panne.
- [x] Documenter les limites Free Edition et les paramètres nécessaires; aucun workspace/endpoint créé, essai Azure Databricks non ouvert. Validation distante facultative en attente de configuration.

Chaque étape se termine par pytest complet, Ruff, mypy et les vérifications pertinentes, puis documentation des résultats et push.
