# Cycle de vie de la démo — contrat à implémenter

Ces interfaces sont **prévues, pas encore disponibles**. Elles guideront les scripts d’infrastructure; aucune commande ci-dessous n’a été exécutée.

## Inventaire et groupes

Chaque environnement aura un identifiant unique et un manifest contenant abonnement, tenant, groupes, IDs des ressources créées, dépendances, profils, connexions Foundry, rôles et dates d’export. Les ressources réutilisées sont marquées `external` et ne sont jamais supprimées par une commande de profil.

| Groupe logique | Ressources | Suppression |
| --- | --- | --- |
| `observability` | Application Insights, Log Analytics | Exporter les résultats utiles; détacher la connexion Foundry avant suppression |
| `runtime` | Container Apps, jobs, environnement, registre éventuel | Arrêter l’entrée de nouvelles tâches puis terminer/annuler les runs |
| `data` | PostgreSQL, Blob des sources/artefacts | Export restaurable avant suppression; données distinctes du runtime |
| `experiments` | Services IQ/recherche supplémentaires éventuels | Ne concerne jamais automatiquement Search Free existant |

Les noms finaux sont dérivés d’un préfixe de démo et de l’environnement. Aucun script ne cible un abonnement entier. Le groupe existant `rg-hydro-agentic-poc` est exclu de la suppression automatique.

## Commandes prévues

```text
uv run python scripts/azure_demo.py status --environment <env>
uv run python scripts/azure_demo.py up --environment <env> --profile core
uv run python scripts/azure_demo.py down --environment <env> --profile demo
uv run python scripts/azure_demo.py export --environment <env> --destination <dossier-local>
uv run python scripts/azure_demo.py destroy --environment <env> --group runtime
uv run python scripts/azure_demo.py destroy --environment <env> --all-owned
```

- `status` : inventaire réel versus manifest, tâches actives, ressources externes, estimation/coûts disponibles et délais de facturation.
- `up` : vérifier compte/région/quota/prix, effectuer un aperçu Bicep, créer seulement les ressources approuvées du profil et mettre à jour le manifest.
- `down` : désactiver déclenchements et entrées d’exécution; attendre ou annuler les jobs selon option explicite; conserver les données. Afficher ce qui peut encore coûter.
- `export` : sauvegarde PostgreSQL, manifests de sources/datasets, versions de prompts et agents, rapports/traces sélectionnés; vérifier présence/checksums. L’export ne doit pas dépendre uniquement d’un bucket destiné à être supprimé.
- `destroy` : afficher les IDs ciblés et dépendances, exiger l’environnement exact et confirmation explicite, refuser ressources externes et dépendances actives, supprimer puis réinterroger l’inventaire. Opération répétable après suppression partielle.

Le manifest ne contient pas de secrets. Ne pas supprimer des objets préexistants seulement parce qu’ils partagent un tag. Les opérations sont limitées aux IDs possédés par le déploiement. Les identités applicatives Entra créées, rôles et connexions sont également inventoriés; ils ne disparaissent pas nécessairement avec un groupe.

## Arrêt ne signifie pas gratuité

| Composant | Après arrêt | Pour éliminer sa consommation future |
| --- | --- | --- |
| API/jobs | Réveil possible si ingress/schedules actifs; logs et stockage possibles | Désactiver déclencheurs ou supprimer le profil runtime |
| PostgreSQL | Stockage/sauvegardes possibles; arrêt temporaire selon service | Exporter puis supprimer le serveur et vérifier les éléments conservés |
| Blob/registre | Données stockées et opérations possibles | Supprimer contenu/ressource selon rétention et soft delete |
| Application Insights/Log Analytics | Rétention et collecte depuis d’autres producteurs possibles | Couper tous les producteurs puis supprimer selon politique de conservation |
| Modèle déployé | Global Standard à l’usage n’est pas du débit provisionné réservé | Révoquer l’accès/supprimer le déploiement possédé; ne pas toucher au modèle existant par défaut |

L’objectif est de rendre les coûts évitables et visibles, pas de promettre qu’un bouton « stop » ramène immédiatement toute facture à zéro. Les frais déjà consommés et délais de remontée demeurent.
