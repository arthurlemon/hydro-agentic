# Correspondance avec Microsoft Learn

Sources : [Operationalize generative AI applications](https://learn.microsoft.com/en-us/training/paths/operationalize-gen-ai-apps/) (6 modules) et [Develop AI agents on Azure](https://learn.microsoft.com/en-us/training/paths/develop-ai-agents-azure/) (9 modules), consultés le 8 octobre 2026.

| Concept | Démonstration prévue | État |
| --- | --- | --- |
| Planification GenAIOps | Spec, coûts, versions, critères et cycle de suppression | Design écrit |
| Prompts versionnés avec GitHub | Prompt séparé, commit lié à la version Foundry, rollback | Agent versionné existant; extraction/liaison à ajouter |
| Expériences structurées | Comparaison A/B sur snapshot et critères explicites | Régression existante; comparaison cloud à ajouter |
| Évaluation automatisée | Datasets/runs Foundry, déclenchement local puis CI | Nouvelle intégration à ajouter |
| Monitoring et traces | Traces Foundry/Application Insights, usage et latence | OpenTelemetry local existant; connexion cloud à ajouter |
| Agent Foundry et outils personnalisés | Investigation avec dix outils et contrôle backend | Existant en relais local |
| MCP | Endpoint distant authentifié et contexte par run | stdio existant; HTTP cloud à ajouter |
| Foundry IQ | Comparer retrieval classique et base de connaissances | Expérience optionnelle selon coût/tier/région |
| Microsoft 365 | Bibliothèque simulée avec ACL, puis vrai SharePoint/OBO | À concevoir; licences réelles séparées |
| Workflows et humain | Investigation asynchrone, approbation, reprise sans doublon | Backend local existant; UX/cloud à ajouter |
| Microsoft Agent Framework | Évaluer l’intérêt d’un adaptateur conservant les contrats | Option future, aucun changement de framework annoncé |
| Multi-agent et A2A | Expérience isolée si une collaboration apporte une valeur mesurable | Hors premier socle |

Le projet illustre les concepts par un cas cohérent; il ne cherche pas à déployer toutes les options simultanément.

## Références de faisabilité

- [Traces Foundry et connexion Application Insights](https://learn.microsoft.com/en-us/azure/foundry/observability/how-to/trace-agent-setup) : traces serveur après connexion, instrumentation client pour notre code, vues de conversations et règles de rétention.
- [Évaluations cloud](https://learn.microsoft.com/en-us/azure/foundry/observability/how-to/cloud-evaluation) : datasets, cibles et conversations, résultats dans le projet et inspection SDK/portail.
- [Agentic retrieval](https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-overview) : Foundry IQ repose sur Search; coûts retrieval et modèle distincts; fonctionnalités GA/préversion à distinguer.
- [SharePoint Foundry](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/sharepoint) : identité utilisateur déléguée, même tenant, licence admissible ou pay-as-you-go; ne pas confondre avec une simulation d’ACL.
- [Tarification Container Apps](https://azure.microsoft.com/en-us/pricing/details/container-apps/) : allocation mensuelle Consumption annoncée de 180 000 vCPU-secondes, 360 000 GiB-secondes et 2 millions de requêtes par abonnement; stockage et services annexes à compter séparément.
