# Passage vers Azure et la production

Les phases 0 à 2 sont locales. La phase 3 ajoute un compte Azure Foundry, un projet et un agent natif GPT-5-mini; aucun index de recherche ni endpoint Databricks n’a été créé.

| Composant local | Cible prévue | Travail restant |
|---|---|---|
| OpenRouter | Agent natif dans Azure Foundry | Projet, déploiement, agent et adaptateur créés; essais réels suivis dans le plan de phase 3 |
| MCP stdio | Transport distant compatible avec l’intégration retenue | Hébergement, identité, contrôle d’accès et réseau; stdio n’est pas un endpoint cloud |
| JSON actifs/télémétrie/historique | Services internes autorisés | Adaptateurs typés, observabilité et erreurs |
| Prédiction JSON | Endpoint Databricks Model Serving | Schéma, authentification, disponibilité, absence de prédiction sans résultat |
| Markdown + recherche lexicale | Azure AI Search | Index, ingestion, retrieval, citations et coût du niveau disponible |
| PostgreSQL local | PostgreSQL géré ou Cosmos DB facultatif | Transactions/idempotence adaptées, concurrence et sauvegardes |
| Rôles d’environnement | Identité vérifiée côté backend | Entra ID ou autre fournisseur, rôles et approbations authentifiées |
| Journal PostgreSQL | OpenTelemetry + Application Insights | Traces, requêtes, citations, jetons, latence et refus |
| Doubles déterministes | Évaluations avec modèle réel | Scénarios et mesures observées, sans pourcentages inventés |

## Passage à Foundry

1. Réalisé : clé OpenRouter locale configurée et parcours réels Python/MCP exécutés avec GPT-5.6 Luna.
2. Réalisé : outils choisis, citations, brouillon et refus de création avant approbation examinés. Voir [les essais](essais-openrouter.md).
3. Réalisé : abonnement gratuit connecté, protection des dépenses activée. GPT-5-mini en East US 2 approuvé par l’utilisateur, car le quota Luna vaut zéro dans les régions vérifiées.
4. Ressources et droits créés; SDK Projects 2.x, agent natif et API Responses. Voir [configuration](foundry-setup.md) et [plan de phase 3](phase-3-foundry.md). Le transport MCP reste local : l’application traite les appels de fonctions retournés par Foundry.
