# Configuration Foundry du PoC

## Ressources créées

| Ressource | Valeur |
|---|---|
| Groupe | `rg-hydro-agentic-poc` |
| Compte Foundry | `hydro-agentic-c80f4df6` — AIServices S0, identité gérée |
| Projet | `hydro-investigation` — identité gérée |
| Région | `eastus2` |
| Déploiement | `hydro-gpt-5-mini` |
| Modèle/version | `gpt-5-mini` / `2025-08-07` |
| Type/capacité | `GlobalStandard` / `1`, sans capacité réservée |
| Endpoint projet | `https://hydro-agentic-c80f4df6.services.ai.azure.com/api/projects/hydro-investigation` |

États vérifiés `Succeeded` pour le compte, le projet et le déploiement. Rôle Foundry User attribué à l’utilisateur connecté au niveau du projet, en plus de son rôle Owner sur l’abonnement. Authentification via `az login`, pas de clé Azure à copier.

L’abonnement est un essai gratuit avec protection des dépenses `On`. GPT-5.6 Luna est dans le catalogue, mais son quota vaut zéro dans les deux régions vérifiées. GPT-5-mini en East US 2 a un quota disponible et est compatible `agentsV2` et Responses. GlobalStandard ne garantit pas un traitement des données exclusivement dans la région du compte; uniquement des données synthétiques sont utilisées.

## Commandes de création utilisées

```bash
az provider register --namespace Microsoft.CognitiveServices --wait
az group create --name rg-hydro-agentic-poc --location eastus2 \
  --tags project=hydro-agentic environment=poc
az cognitiveservices account create --name hydro-agentic-c80f4df6 \
  --resource-group rg-hydro-agentic-poc --location eastus2 --kind AIServices \
  --sku S0 --custom-domain hydro-agentic-c80f4df6 --assign-identity \
  --allow-project-management true --tags project=hydro-agentic environment=poc
az cognitiveservices account deployment create --name hydro-agentic-c80f4df6 \
  --resource-group rg-hydro-agentic-poc --deployment-name hydro-gpt-5-mini \
  --model-name gpt-5-mini --model-version 2025-08-07 --model-format OpenAI \
  --sku-name GlobalStandard --sku-capacity 1
az cognitiveservices account project create --name hydro-agentic-c80f4df6 \
  --resource-group rg-hydro-agentic-poc --project-name hydro-investigation \
  --location eastus2 --display-name 'Investigation synthétique d’actifs' \
  --description 'PoC hydro-agentic, données synthétiques uniquement' --assign-identity
```

Créer le projet et le déploiement séquentiellement : Azure a refusé une création parallèle avec `RequestConflict`, puis la création séquentielle a réussi.

## Coûts et arrêt

Les appels de modèle sont facturés à l’usage et consomment les crédits. Pas d’agent hébergé en conteneur, de capacité provisionnée, d’AI Search, de Cosmos ou de Databricks créé dans cette étape. Le plafond d’étapes limite une investigation, pas les dépenses de l’abonnement. Ne pas désactiver la protection des dépenses pour ce PoC sans décision explicite.

Ne supprimer le groupe `rg-hydro-agentic-poc` qu’après confirmation : cela supprime le compte, le projet, ses agents et le déploiement. Les données PostgreSQL locales ne sont pas dans ce groupe.
