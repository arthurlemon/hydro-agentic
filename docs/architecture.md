# Architecture locale — phases 0 à 2

```text
CLI humaine → boucle agentique → modèle OpenRouter
                    ↓ appels d’outils choisis par le modèle
           registre Python OU client MCP → serveur MCP stdio
                                           ↓ même registre
                         services métier typés et contrôles
                           ↓           ↓             ↓
                       JSON local   procédures     PostgreSQL
                                    Markdown       incidents / audit

CLI approve / reject → contrôle du rôle → décision persistée
CLI resume ou create_work_order → contrôle de l’approbation → ordre simulé unique
```

## Responsabilités

- `agent/model.py` : adaptateur HTTP OpenRouter; aucune clé dans les erreurs ou traces.
- `agent/loop.py` : consignes françaises, outils sélectionnés par le modèle, recherches répétables, résultats d’outils réinjectés, conclusion JSON validée, plafond d’étapes.
- `tools/registry.py` : dix contrats Pydantic communs aux deux transports; identité et incident attachés par l’hôte. Les arguments ne peuvent changer ni rôle ni incident.
- `services/data.py` : registre, historique, télémétrie et prédiction ML simulée. La fenêtre de télémétrie est relative à l’événement, pas à l’horloge de la machine.
- `services/search.py` : recherche lexicale insensible aux accents; lecture complète par identifiant. Les extraits de recherche ne valident pas une intervention.
- `state/postgres.py` : preuves récupérées, validation déterministe, brouillon figé, approbation et création transactionnelle en JSONB. Un événement correspond à un incident; un incident à au plus un ordre simulé.
- `mcp/` : serveur SDK MCP officiel et client stdio; schémas d’entrée/sortie explicites, erreurs métier structurées.
- `cli.py` : commandes humaines; approbation hors des outils du modèle.

## État et reprise

`new → investigating → recommendation_ready | insufficient_evidence | failed`

Une recommandation justifiée peut devenir `awaiting_approval` uniquement si la préparation est autorisée. Ensuite : `approved → work_order_created`, ou `rejected`. Une conclusion `no_action` est stockée dans `recommendation.outcome` avec l’état `recommendation_ready`.

Une investigation non figée peut être relancée : les preuves et la recommandation sont recalculées. Après préparation, les preuves et le brouillon sont figés; l’approbation conserve une copie exacte du brouillon. `resume` crée l’ordre approuvé sans dépendre de la conversation ni du LLM. Les décisions métier sont vérifiées dans une transaction PostgreSQL avec verrou de ligne `SELECT ... FOR UPDATE`. `event_id` est unique; `INSERT ... ON CONFLICT` évite de créer plusieurs incidents pour le même événement.

## Observabilité déjà présente

Table PostgreSQL `audit` : outil, succès/refus, erreur métier, identifiants de sources et latence; pour le modèle, numéro d’étape, latence et usage retourné par OpenRouter. L’état conserve les données des preuves et la décision d’approbation. Ce journal minimal n’est pas encore le dispositif OpenTelemetry/Application Insights de la phase 7.

## Limites actuelles

- Les tests automatisés utilisent des doubles du modèle. Les essais réels OpenRouter sont consignés séparément dans le suivi.
- Recherche lexicale, sans embeddings ni classement sémantique.
- Une seule règle d’intervention synthétique : inspection P1 sous 24 h selon TR-MAINT-004. La logique est codée côté service, pas interprétée depuis un document.
- Le serveur valide les citations et les champs d’action. Il ne prouve pas automatiquement chaque phrase libre du résumé; une évaluation réelle reste nécessaire pour mesurer les inventions narratives.
- Identités déclarées localement, fichiers et PostgreSQL de confiance. Le PoC n’est pas un service multi-utilisateur authentifié.
- Une seule investigation active par incident : verrou consultatif PostgreSQL de session, partagé entre processus connectés à la même base et au même schéma. Une seconde investigation est refusée sans effacer les preuves. Le verrou est libéré à la fermeture de connexion; une coupure réseau peut retarder sa libération côté serveur. Utiliser une connexion directe ou un pool en mode session, pas un pool en mode transaction. Il n’y a pas encore de mécanisme de reprise distribuée avec jeton de génération après perte de connexion.
- Aucune action sur un équipement, aucun CMMS externe, aucun arrêt automatisé.
