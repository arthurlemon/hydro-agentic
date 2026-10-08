# Passage vers Azure et la production

Les phases 0 à 2 sont locales. Foundry et Azure AI Search Free sont désormais configurés et testés réellement. PostgreSQL, l’exécution des outils et MCP restent locaux. Aucun endpoint Databricks ni Application Insights n’a été créé.

| Composant local | Cible prévue | Travail restant |
|---|---|---|
| OpenRouter | Agent natif dans Azure Foundry | Projet, déploiement, agent et adaptateur créés; essais réels suivis dans le plan de phase 3 |
| MCP stdio | Transport distant compatible avec l’intégration retenue | Hébergement, identité, contrôle d’accès et réseau; stdio n’est pas un endpoint cloud |
| JSON actifs/télémétrie/historique | Services internes autorisés | Adaptateurs typés, observabilité et erreurs |
| Prédiction JSON | Endpoint Databricks Model Serving | Adaptateur et contrat testés hors ligne; workspace/modèle/endpoint et validation réelle restent à faire |
| Markdown + recherche lexicale | Azure AI Search Free | Index BM25 français créé, sept procédures et citations testées; synchronisation des suppressions, limites Free et accès de production restent à gérer |
| PostgreSQL local | PostgreSQL géré ou Cosmos DB facultatif | Transactions/idempotence adaptées, concurrence et sauvegardes |
| Rôles d’environnement | Identité vérifiée côté backend | Entra ID ou autre fournisseur, rôles et approbations authentifiées |
| Journal PostgreSQL + OpenTelemetry JSONL | Collecteur OTLP + Application Insights facultatif | Corrélation Python/MCP livrée; hébergement, rétention, rotation, alertes et coûts restent à définir |
| Dix évaluations programmées isolées | Évaluations avec modèle réel | Deux modes LLM disponibles mais nouvelle suite non exécutée avec LLM; vérification sémantique des résumés reste à compléter |

## Passage à Foundry

1. Réalisé : clé OpenRouter locale configurée et parcours réels Python/MCP exécutés avec GPT-5.6 Luna.
2. Réalisé : outils choisis, citations, brouillon et refus de création avant approbation examinés. Voir [les essais](../history/essais-openrouter.md).
3. Réalisé : abonnement gratuit connecté, protection des dépenses activée. GPT-5-mini en East US 2 approuvé par l’utilisateur, car le quota Luna vaut zéro dans les régions vérifiées.
4. Ressources et droits créés; SDK Projects 2.x, agent natif et API Responses. Voir [configuration](../azure/foundry-setup.md) et [plan de phase 3](../plans/phase-3-foundry.md). Le transport MCP reste local : l’application traite les appels de fonctions retournés par Foundry.
