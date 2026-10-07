# Phase 3 — agent natif Foundry

## Décisions approuvées

GPT-5-mini sur Foundry, région East US 2. GPT-5.6 Luna reste le modèle OpenRouter. Abonnement d’essai actif, protection des dépenses conservée. Fournisseur Microsoft.CognitiveServices enregistré. Aucun quota Luna disponible dans les régions vérifiées; quota GlobalStandard GPT-5-mini disponible en East US 2.

## Architecture retenue

Un projet Foundry contient un agent natif de type prompt, avec consignes françaises et les dix contrats d’outils. L’API Responses retourne les fonctions à exécuter; l’application les exécute par le registre Python ou le client MCP stdio, puis renvoie les résultats. Foundry ne peut pas appeler directement notre stdio ni notre PostgreSQL local.

Les contrôles de citations, l’identité locale, les preuves, le brouillon, l’approbation et l’idempotence restent dans les services existants. Pas d’outil d’approbation exposé. Les conversations cloud ne remplacent pas l’état métier. Seules les données synthétiques sont envoyées au cloud.

Authentification Microsoft Entra via la session Azure CLI; aucune clé Azure dans Git. Agent versionné et référence de version explicite. Une nouvelle conversation par investigation; pas de reprise conversationnelle automatique ni de retry réseau susceptible de rejouer une action. Les délais et erreurs sont convertis en erreurs métier sans token divulgué.

Ressources minimales : groupe dédié, compte Foundry avec identité gérée, projet, déploiement GPT-5-mini GlobalStandard de petite capacité. Pas de capacité réservée, d’agent hébergé en conteneur, de Search payant, de Cosmos ou de Databricks dans cette phase. Le modèle est facturé à l’usage; les crédits et la limite de dépenses ne constituent pas une garantie de disponibilité.

## Plan d’exécution dans la session

### 1. Infrastructure
- [x] Vérifier les commandes CLI actuelles; créer le groupe, le compte et le projet.
- [x] Déployer GPT-5-mini version `2025-08-07`, GlobalStandard. Capacité 1 acceptée mais insuffisante au premier essai; déploiement actif initialisé à 50, sans calcul réservé. Ancien déploiement supprimé.
- [x] Vérifier les endpoints et états; rôle Foundry User ajouté au projet. Ressources décrites dans `docs/foundry-setup.md`. L’accès de données sera vérifié lors de la publication de l’agent.

### 2. Adaptateur et CLI
- [x] Écrire `tests/test_foundry.py` avant `src/hydro_agent/agent/foundry.py` : version figée, conversion des fonctions, plusieurs tours sans duplication, réponses invalides, erreurs sans secrets et fermeture des clients.
- [x] Observer RED avec `uv run pytest tests/test_foundry.py -q`.
- [x] Ajouter le SDK `azure-ai-projects` 2.x, `azure-identity` et aiohttp avec uv. Interface compatible `ModelClient.complete(messages, tools)`, règles métier inchangées.
- [x] Ajouter `--provider openrouter|foundry`, configuration endpoint/déploiement/nom/version; OpenRouter reste le défaut. Séparer la publication d’agent de son invocation pour éviter des versions automatiques à chaque exécution.
- [ ] Tests CLI de configuration et absence de dépendance à une clé OpenRouter pour Foundry; suite entière, Ruff, mypy, build. Commit et push.

### 3. Essais réels
- [x] Publier une version du véritable agent dans Foundry; version 3 avec dix fonctions, consignes et schéma de conclusion.
- [x] Utiliser des événements synthétiques distincts pour ne pas écraser le brouillon OpenRouter INC-1001.
- [x] Vérifier P1/brouillon via MCP, faible risque et preuves insuffisantes, puis le refus de création sans approbation.
- [ ] Consigner endpoints et résultats sans clés, tokens ou scores de qualité inventés. Commit et push.

## Points à vérifier

Schémas de fonctions non stricts pour conserver les paramètres optionnels Pydantic; conservation des appels de raisonnement dans la conversation Responses; refus d’un incident déjà figé; timeout et réponse incomplète; authentification sans fallback OpenRouter; nettoyage des clients et des conversations de test; permissions de données différentes du rôle Owner de gestion.

## Sources

- https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/prompt-agent
- https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/function-calling
- https://learn.microsoft.com/en-us/azure/foundry/tutorials/quickstart-create-foundry-resources
- https://azure.microsoft.com/en-us/pricing/details/foundry-agent-service/
