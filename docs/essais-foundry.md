# Essais réels Foundry — GPT-5-mini

Agent natif `hydro-investigator`, version **3**, déploiement `hydro-gpt-5-mini-poc`, modèle `gpt-5-mini` version `2025-08-07`, GlobalStandard, East US 2. Authentification Azure CLI/Entra; aucune clé Azure. Outils et PostgreSQL locaux, documents et mesures entièrement synthétiques.

## Résultats observés

| Événement distinct | Transport | Incident | Résultat | Appels modèle | Tokens retournés |
|---|---|---|---|---:|---:|
| `EVT-48392-FOUNDRY-FINAL` | MCP, préparation demandée | `INC-1017` | Inspection P1 sous 24 h, huit citations, `awaiting_approval` | 5 | 22 426 |
| `EVT-LOW-FOUNDRY-V3` | MCP | `INC-1014` | `no_action`, aucune urgence | 3 | 11 819 |
| `EVT-TEMP-FOUNDRY-V3` | Python | `INC-1015` | `insufficient_evidence`, huile actuelle non confirmée | 4 | 14 082 |
| `EVT-UNKNOWN-FOUNDRY-V3` | Python | `INC-1016` | `insufficient_evidence`, outils de données refusés, aucune citation finale | 3 | 9 191 |

Compte des appels et tokens lu dans l’audit PostgreSQL. Total de **57 518 tokens** pour ces quatre investigations seulement : ce n’est ni toute la consommation des essais ni une facture. Les premiers essais, diagnostics et replay du P1 ont aussi consommé des tokens. Aucun pourcentage de qualité n’est calculé sur ces quatre cas.

Toutes les citations finales figurent dans les preuves réellement récupérées. Tous les états ont `approval=null` et `work_order=null`. Appel réel `create_work_order` via MCP sur `INC-1017` : refus « Approbation humaine persistée requise avant toute création. »; état identique avant/après. Aucun ordre approuvé ou créé pendant ces essais. Le brouillon OpenRouter `INC-1001` est toujours en attente, non modifié.

Les copies d’événements se trouvent dans `.hydro/foundry-data`, ignoré par Git; actifs, télémétrie et procédures identiques au jeu `data/`. Les identifiants distincts empêchent de réutiliser ou remplacer un incident déjà figé.

## Corrections vérifiées pendant la phase

1. **Quota d’inférence.** Premier déploiement capacité 1 : HTTP 429 après un premier tour réussi. Mise à jour de gestion à 50, mais en-têtes d’inférence encore à 1 requête/minute et 1 000 tokens/minute. Nouveau déploiement créé directement à 50, investigations suivantes réussies. Ancien déploiement supprimé. Aucun retry automatique d’inférence.
2. **Schéma final.** Revue : les consignes initiales renvoyaient à un schéma absent. Test en échec, puis schéma `Recommendation` ajouté à la publication; version 3 sélectionnée explicitement. Versions antérieures conservées dans l’historique, non utilisées par la configuration active.
3. **Arrêt après préparation.** Premier P1 version 3 : 24 appels modèle, car une nouvelle formulation ne pouvait remplacer la recommandation figée. Test reproduisant un troisième appel inutile en échec. La boucle termine maintenant après le lot d’outils qui produit un brouillon validé, avec la recommandation persistée. Le lot complet reste soumis aux contrôles : une création jointe au brouillon est refusée sans approbation. P1 final réussi en cinq appels.
4. **Erreurs et fermeture.** Tests RED→GREEN : HTTP lisible sans corps fournisseur/secret, erreur du modèle conservée à travers MCP, URL mal formée sans traceback, fermeture de tous les clients sans masquer l’erreur initiale. Publication configurée sans retries de POST, avec délais explicites.

## Limites constatées

Les champs d’action, les citations et les conditions P1 sont contrôlés par le backend, pas chaque phrase libre. Par exemple, le résumé P1 final contient l’expression contradictoire « température normale anormale » alors que les mesures citées et la décision structurée sont correctes. Le résumé du cas inconnu mentionne avoir retiré des citations non vérifiées; le résultat persisté n’en contient aucune. Ces observations ne justifient pas une affirmation d’absence générale d’erreurs narratives.

Les rôles métier restent déclarés par l’environnement local; Entra authentifie seulement l’accès au projet Azure. Les conversations cloud sont supprimées au mieux à la fermeture, mais les données envoyées restent soumises aux règles de rétention Azure. Les réponses brutes et traces cloud complètes ne sont pas conservées dans le journal local actuel.

Le playground Foundry ne peut pas joindre notre serveur MCP stdio : le parcours complet exige l’application locale. Pas de déploiement applicatif cloud, d’Azure AI Search, de Cosmos, de Databricks ni d’OpenTelemetry dans cette phase.
