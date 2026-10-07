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

Projet uv, configuration secrète masquée, schémas Pydantic, données synthétiques et sept documents français ajoutés. Premier cycle de tests : 3 échecs pour modules absents, puis 3 tests réussis après implémentation. Les contrôles de lint et de typage restent à exécuter avant le commit.

## Phases suivantes

- Phase 1 : services, état, agent et CLI en cours.
- Phase 2 : transport MCP à implémenter.
- Validation réelle du modèle : en attente de `OPENROUTER_API_KEY`.
- Phases 3 à 9 : non commencées; aucune ressource Azure créée.
