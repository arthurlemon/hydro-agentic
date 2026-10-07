# Configuration Foundry du PoC

## Ressources créées

| Ressource | Valeur |
|---|---|
| Groupe | `rg-hydro-agentic-poc` |
| Compte Foundry | `hydro-agentic-c80f4df6` — AIServices S0, identité gérée |
| Projet | `hydro-investigation` — identité gérée |
| Région | `eastus2` |
| Déploiement actif | `hydro-gpt-5-mini-poc` |
| Modèle/version | `gpt-5-mini` / `2025-08-07` |
| Type/capacité | `GlobalStandard` / `50`, sans capacité réservée |
| Agent actif | `hydro-investigator`, version `3`, dix fonctions et schéma de conclusion |
| Endpoint projet | `https://hydro-agentic-c80f4df6.services.ai.azure.com/api/projects/hydro-investigation` |

États vérifiés `Succeeded` pour le compte, le projet et le déploiement. Rôle Foundry User attribué à l’utilisateur connecté au niveau du projet, en plus de son rôle Owner sur l’abonnement. Publication réelle de l’agent réussie; authentification via `az login`, pas de clé Azure à copier.

Le premier déploiement `hydro-gpt-5-mini`, capacité 1, a accepté la première réponse puis refusé le tour suivant en HTTP 429. Même après passage à 50, les en-têtes du chemin d’inférence annonçaient encore 1 requête/minute et 1 000 tokens/minute, alors que la gestion Azure affichait 50 et 50 000. Un nouveau déploiement `hydro-gpt-5-mini-poc` a donc été créé directement à 50; les versions 2 puis 3 de l’agent le référencent. Les essais réels à plusieurs tours ont réussi sur ce nouveau déploiement. L’ancien déploiement a été supprimé; les anciennes versions de l’agent restent dans l’historique.

La capacité 50 correspond à un quota déclaré de 50 requêtes/minute et 50 000 tokens/minute, pas à des tokens prépayés ou à du calcul réservé. La facture dépend des tokens réellement utilisés. Réduire la capacité peut provoquer des HTTP 429 pendant une investigation; ne pas confondre quota, consommation et disponibilité garantie.

## Trouver les ressources dans le portail

Compte connecté `arten33@gmail.com`, répertoire Default Directory, abonnement Azure subscription 1. Dans Azure Portal : groupe `rg-hydro-agentic-poc` → compte `hydro-agentic-c80f4df6` → portail Foundry. Dans le **nouveau Foundry**, sélectionner le projet `hydro-investigation`, puis Agents → `hydro-investigator` version 3. L’ancien portail classique et un autre répertoire/filtre d’abonnement peuvent afficher une liste vide. Région East US 2.

Les fonctions sont relayées par notre application locale; le playground du portail ne sait pas joindre notre MCP stdio ni PostgreSQL. Utiliser la CLI pour le parcours complet. Les conversations d’essai sont supprimées au mieux à la fermeture, mais les agents versionnés et l’audit PostgreSQL restent disponibles.

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
  --resource-group rg-hydro-agentic-poc --deployment-name hydro-gpt-5-mini-poc \
  --model-name gpt-5-mini --model-version 2025-08-07 --model-format OpenAI \
  --sku-name GlobalStandard --sku-capacity 50
az cognitiveservices account project create --name hydro-agentic-c80f4df6 \
  --resource-group rg-hydro-agentic-poc --project-name hydro-investigation \
  --location eastus2 --display-name 'Investigation synthétique d’actifs' \
  --description 'PoC hydro-agentic, données synthétiques uniquement' --assign-identity
```

Créer le projet et le déploiement séquentiellement : Azure a refusé une création parallèle avec `RequestConflict`, puis la création séquentielle a réussi.

## Coûts et arrêt

Les appels de modèle sont facturés à l’usage et consomment les crédits. Pas d’agent hébergé en conteneur, de capacité provisionnée, d’AI Search, de Cosmos ou de Databricks créé dans cette étape. Le plafond d’étapes limite une investigation, pas les dépenses de l’abonnement. Ne pas désactiver la protection des dépenses pour ce PoC sans décision explicite.

Ne supprimer le groupe `rg-hydro-agentic-poc` qu’après confirmation : cela supprime le compte, le projet, ses agents et le déploiement. Les données PostgreSQL locales ne sont pas dans ce groupe.
