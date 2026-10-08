# Sources publiques candidates

## Hydro-Québec

Le [site officiel](https://www.hydroquebec.com/documents-donnees/donnees-ouvertes/) renvoie vers le [catalogue de données](https://donnees.hydroquebec.com/pages/accueil/). Métadonnées consultées le 8 octobre 2026 via [API de catalogue](https://donnees.hydroquebec.com/api/explore/v2.1/catalog/datasets?limit=20) : 26 jeux annoncés au total; volumes ci-dessous issus de `metas.default.records_count`, pas d’un téléchargement intégral.

| Identifiant du jeu | Volume annoncé | Utilité possible |
| --- | ---: | --- |
| `historique-demande-electricite-quebec` | 52 608 | Détecter et expliquer des pointes de demande |
| `historique-donnees-meteo` | 2 326 547 | Contextualiser les variations, avec sélection géographique/temporelle |
| `historique-production-consommation-proxy-horaire` | 61 371 | Comparer production/consommation selon la méthode du producteur |
| `historique-production-consommation-ec-horaire` | 61 375 | Autre méthode : ne pas fusionner sans examiner sa définition |
| `calendrier-travaux-degagement-transport-json` | 13 079 | Démonstration de recherche sur planification publique |
| `donnees-hydrometriques` | 51 454 | Débits/apports, scénario futur distinct |

Ces entrées annoncent **CC BY-NC 4.0**. Conserver auteur, URL, licence, date et transformations. Usage non commercial requis; une utilisation commerciale demande une autre base d’autorisation. Les PDF et pages publiques ne sont pas automatiquement couverts par la licence des datasets : vérifier document par document avant ingestion et redistribution.

Les compteurs peuvent évoluer et les formats/endpoints détaillés restent à inspecter avant ETL. Aucun jeu ne constitue ici une source vérifiée de défaillances, d’huile ou de maintenance de transformateurs individuels. Conserver les données d’actifs fictives dans un espace explicitement synthétique.

## Premier scénario proposé

« Analyse cette pointe de demande, compare les jours proches, examine le contexte météo et prépare une note sourcée pour validation humaine. »

Choisir une période commune, contrôler fuseaux et unités, puis interroger les séries par outils bornés. Indexer les fiches de jeux, méthodologies et documents autorisés dans Search, pas chaque cellule du dataset. Une corrélation météo/demande ne prouve pas une cause; distinguer observation et interprétation dans le résultat.

## ETL minimal proposé

1. Manifest des sources avec licence, URL, intervalle, schéma et taille maximale.
2. Téléchargement borné et stockage brut immuable, checksum, date d’extraction.
3. Validation, dédoublonnage, normalisation unités/fuseaux; conserver les lignes rejetées avec motif.
4. Tables de séries et documents/chunks sourcés dans deux représentations distinctes.
5. Upsert idempotent dans Search, suivi des retraits, contrôle de taille avant dépassement de Free.
6. Snapshot de dataset d’évaluation séparé de la source actualisée.

Alternative à explorer si les documents utilisables sont insuffisants : corpus publics d’autres opérateurs, par exemple RTE/ODRÉ. Aucun volume ni droit de réutilisation de cette alternative n’a encore été vérifié.
