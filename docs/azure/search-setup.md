# Azure AI Search Free

## Ressource créée

- Groupe : `rg-hydro-agentic-poc`, abonnement `Azure subscription 1`.
- Service : `hydro-search-c80f4df6`, **Free**, `Canada Central`.
- Endpoint : `https://hydro-search-c80f4df6.search.windows.net`.
- Index : `procedures-v1`, sept procédures synthétiques, textes complets.
- Authentification : Entra avec `az login`; clés désactivées (`disableLocalAuth=true`).
- Rôles sur ce service uniquement : Search Service Contributor et Search Index Data Contributor pour l’utilisateur de développement. En production, séparer l’indexation de la lecture et attribuer seulement Data Reader à l’application.

La création Free dans East US 2 a été refusée par Azure faute de capacité. La création dans Canada Central a réussi, sans changement de niveau tarifaire. Foundry reste dans East US 2 : les procédures synthétiques transitent entre ces régions via les sorties d’outils. Ne pas utiliser cette configuration pour des données opérationnelles Hydro.

Le niveau Free est partagé : 50 Mo, un service gratuit par abonnement, pas de garantie de disponibilité. Aucun classement sémantique, embedding, vectorisation ou capacité payante n’a été activé. La recherche utilise **BM25 et l’analyseur `fr.lucene`**; ce n’est pas une recherche vectorielle.

## Configuration et indexation

```dotenv
HYDRO_SEARCH_BACKEND=azure
AZURE_SEARCH_ENDPOINT=https://hydro-search-c80f4df6.search.windows.net
AZURE_SEARCH_INDEX=procedures-v1
```

```bash
az login
uv sync --locked
uv run hydro-agent index-procedures
```

La commande crée/met à jour le schéma de cet index et charge les fichiers Markdown. Elle refuse les fichiers vides ou illisibles et signale une indexation partielle. Elle ne supprime pas les documents déjà indexés : après retrait d’une procédure, sa suppression du catalogue cloud doit être gérée explicitement. Ne pas réutiliser cet index pour des documents hors de ce PoC.

`HYDRO_SEARCH_BACKEND=local` sélectionne explicitement la recherche locale. En mode Azure, une panne ou un défaut de configuration produit une erreur : **aucun repli local automatique**. Le processus MCP reçoit le backend, l’endpoint et le nom d’index, mais jamais la clé OpenRouter.

Les résultats de `search_procedures` contiennent un extrait non fiable. Seul `get_procedure` fournit le document complet et une citation utilisable par les contrôles métier. Les sources gardent le format `procedure:TR-MAINT-004`; les preuves complètes sont copiées dans l’incident PostgreSQL.

## Vérifications réelles

La requête « surchauffe de transformateur avec dégradation d’huile » a retourné `TR-MAINT-004` en premier et `TR-OIL-002` en deuxième. `ATTACK-001` apparaît également : son contenu reste non fiable et ne peut autoriser une action. La lecture complète de `TR-MAINT-004` a été vérifiée via le service Azure et via MCP.

Foundry GPT-5-mini, outils MCP et Search Azure ont investigué `EVT-48392-SEARCH` en **trois appels de modèle**. Résultat persisté : `INC-1018`, inspection P1 sous 24 heures, cinq citations récupérées et brouillon `awaiting_approval`. L’appel MCP de création sans approbation a été refusé; état inchangé, approbation et ordre absents. Les incidents précédents `INC-1001` et `INC-1017` restent en attente.

## Infrastructure reproductible

`infra/search.bicep` fixe le niveau **Free**, désactive les clés et décrit les deux rôles nécessaires au développement. Il ne crée ni Foundry, ni stockage, ni Databricks.

```bash
az bicep build --file infra/search.bicep
az deployment group what-if --resource-group rg-hydro-agentic-poc \
  --template-file infra/search.bicep \
  --parameters principalId=<identifiant-objet-Entra>
```

Le fichier a été compilé; le service existant et ses rôles ont été créés avec Azure CLI. Aucun déploiement Bicep n’est annoncé comme exécuté. La création des rôles par Bicep est désactivée par défaut afin de ne pas dupliquer les affectations CLI existantes. Pour un **nouveau** service, ajouter `createRoleAssignments=true`; vérifier le `what-if` avant déploiement.

Références : [RBAC, y compris Free](https://learn.microsoft.com/en-us/azure/search/search-security-enable-roles), [limites de service](https://learn.microsoft.com/en-us/azure/search/search-limits-quotas-capacity), [analyseurs linguistiques](https://learn.microsoft.com/en-us/azure/search/index-add-language-analyzers).
