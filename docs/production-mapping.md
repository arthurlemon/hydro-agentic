# Passage vers Azure et la production

Les phases 0 à 2 sont locales. Aucun compte Azure, projet Foundry, index de recherche ou endpoint Databricks n’a été créé.

| Composant local | Cible prévue | Travail restant |
|---|---|---|
| OpenRouter | Modèle dans Azure AI Foundry | Projet, déploiement compatible outils, adaptateur et test réel |
| MCP stdio | Transport distant compatible avec l’intégration retenue | Hébergement, identité, contrôle d’accès et réseau; stdio n’est pas un endpoint cloud |
| JSON actifs/télémétrie/historique | Services internes autorisés | Adaptateurs typés, observabilité et erreurs |
| Prédiction JSON | Endpoint Databricks Model Serving | Schéma, authentification, disponibilité, absence de prédiction sans résultat |
| Markdown + recherche lexicale | Azure AI Search | Index, ingestion, retrieval, citations et coût du niveau disponible |
| PostgreSQL local | PostgreSQL géré ou Cosmos DB facultatif | Transactions/idempotence adaptées, concurrence et sauvegardes |
| Rôles d’environnement | Identité vérifiée côté backend | Entra ID ou autre fournisseur, rôles et approbations authentifiées |
| Journal PostgreSQL | OpenTelemetry + Application Insights | Traces, requêtes, citations, jetons, latence et refus |
| Doubles déterministes | Évaluations avec modèle réel | Scénarios et mesures observées, sans pourcentages inventés |

## Arrêt avant Foundry

1. Réalisé : clé OpenRouter locale configurée et parcours réels Python/MCP exécutés avec GPT-5.6 Luna.
2. Réalisé : outils choisis, citations, brouillon et refus de création avant approbation examinés. Voir [les essais](essais-openrouter.md).
3. Choisir ensuite le compte/abonnement Azure, la région et le déploiement de modèle disponibles. Cette étape nécessitera l’accès utilisateur au portail si une connexion ou une création de compte est requise.
4. Implémenter la phase 3 après ces décisions. Les commandes et l’API Foundry seront vérifiées contre leur documentation actuelle lors de cette phase.
