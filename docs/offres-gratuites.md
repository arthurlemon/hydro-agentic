# Offres gratuites et crédits pour le PoC

Vérification de la documentation officielle pendant la préparation de la phase 3. Les offres et quotas peuvent changer; vérifier leur admissibilité avant chaque création de service.

| Service | Option retenue ou envisageable | Limite/coût à retenir |
|---|---|---|
| Azure | Abonnement d’essai avec 200 USD de crédits sur 30 jours | Protection des dépenses actuellement activée; les crédits ne rendent pas les modèles gratuits indéfiniment |
| Foundry, agent prompt natif | Agent utilisé dans la phase 3 | Pas de supplément d’orchestration pour cet agent; tokens du modèle et éventuels outils/services facturés |
| Foundry, agent hébergé | Non utilisé | Calcul du conteneur facturé; inutile pour ce parcours |
| Azure AI Search | Niveau **Free**, à examiner à la phase 4 | Un service gratuit par abonnement, 50 Mo; embeddings externes potentiellement payants. Le niveau Developer serverless n’est pas le niveau Free |
| PostgreSQL | Docker local | Aucun service Azure de base de données créé |
| Databricks | **Free Edition**, uniquement pour expérimentation personnelle non commerciale | Gratuit sous politique d’usage équitable; serverless, MLflow et ressources limitées, accès réseau sortant restreint, pas de SLA ni de réseau privé |
| Azure Databricks | Ne pas activer pour le moment | Essai de 14 jours sur les DBU, pas une gratuité générale des VM/disques/autres ressources Azure |

Free Edition n’est pas une base pour un pilote opérationnel ou commercial chez Hydro. La possibilité de servir le modèle CPU simulé et de l’appeler depuis ce projet doit encore être vérifiée concrètement avant la phase Databricks. Aucun compte, cluster ni endpoint Databricks créé pendant la phase 3.

Le choix actuel minimise les ressources : Foundry facturé aux tokens avec crédits d’essai, application et PostgreSQL locaux, sans Search payant, Cosmos ni Databricks. Quota de déploiement et consommation sont distincts : GlobalStandard capacité 50 ne réserve pas du calcul et ne garantit pas un plafond de facture par investigation.

## Sources officielles

- [Compte Azure gratuit et crédits](https://azure.microsoft.com/en-us/free/)
- [Tarification Foundry Agent Service](https://azure.microsoft.com/en-us/pricing/details/foundry-agent-service/)
- [Limites Azure AI Search](https://learn.microsoft.com/en-us/azure/search/search-limits-quotas-capacity)
- [Databricks Free Edition](https://www.databricks.com/product/free-edition)
- [Limites Free Edition](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations)
- [Essai Azure Databricks et facturation](https://learn.microsoft.com/en-us/azure/databricks/getting-started/free-trial)
