# Documentation

## État actuel et prochaine évolution

- [Design de la démo Azure](architecture/cloud-demo.md) — proposition à valider avant les nouveaux déploiements.
- [Arrêter, exporter et supprimer la démo](azure/demo-lifecycle.md) — contrat prévu; commandes à implémenter.
- [Historique des livraisons et vérifications](history/progress.md).
- [Plan initial](../PROJECT_PLAN.md) — périmètre des phases 0–9 déjà réalisées.

## Architecture

- [Socle local et Foundry](architecture/local-foundry.md)
- [Contrats des outils](architecture/tool-contracts.md)
- [Modèle de menaces](architecture/threat-model.md)
- [Correspondance avec les services cloud](architecture/production-mapping.md)

## Azure et exploitation

- [Foundry : configuration existante](azure/foundry-setup.md)
- [Search Free : configuration existante](azure/search-setup.md)
- [Offres gratuites et crédits](azure/offres-gratuites.md)
- [Approbation, rejet et reprise](guides/approbation-reprise.md)
- [Observabilité actuelle](guides/observabilite.md)
- [Databricks facultatif, reporté](guides/databricks.md)

## Données, évaluations et apprentissage

- [Sources publiques candidates et ETL proposé](data/public-sources.md)
- [Évaluateur actuel : exécution et limites](evaluations/runner.md)
- [Correspondance avec Microsoft Learn](learning/microsoft-learn.md)

## Plans et résultats historiques

- [Phases 0–2](plans/plan-phases-0-2.md), [migration PostgreSQL](plans/plan-postgresql.md), [phase 3](plans/phase-3-foundry.md), [phases 4–9](plans/plan-phases-4-9.md)
- [Essais OpenRouter](history/essais-openrouter.md) et [essais Foundry](history/essais-foundry.md)

Les chemins présentés entre backticks dans les documents sont relatifs à la racine du dépôt, sauf indication contraire. Les bilans historiques décrivent l’état au moment de leurs vérifications; ils ne certifient pas les nouveaux composants proposés.
