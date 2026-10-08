# Démo Azure — design proposé

**Statut :** design à relire avant le plan d’implémentation et les nouveaux déploiements. Aucun composant de ce document n’est annoncé comme déployé sauf mention explicite « existant ».

## 1. Objectif et contraintes

Transformer le PoC en démonstration accessible dans un navigateur : lancer une investigation, suivre ses actions et preuves, soumettre une recommandation à un humain, puis consulter les traces et évaluations dans Azure. Le poste local devient un client de déclenchement et un environnement de développement; aucune exécution cloud ne doit dépendre d’un tunnel vers ce poste.

- Français pour les interfaces, prompts et docs; uv et Python 3.12+ pour le backend.
- Réutiliser Foundry GPT-5-mini, PostgreSQL et les contrats des dix outils. Databricks reporté.
- Données synthétiques ou publiques avec provenance et licence; ne pas attribuer à Hydro-Québec les procédures ou défaillances inventées.
- Objectif budgétaire de conception : **30 USD/mois, consommation couverte par les crédits comprise**, accepté comme orientation; ce n’est ni un devis ni une limite technique garantie.
- Services gratuits admissibles en priorité; vérifier disponibilité, quota et prix régional avant chaque groupe de ressources. Si le socle complet dépasse l’objectif, présenter l’écart et réduire le périmètre avant création.
- Tout composant ajouté possède une procédure d’export, d’arrêt quand disponible et de suppression ciblée. Voir [le cycle de vie](../azure/demo-lifecycle.md).

## 2. Approches et choix

| Approche | Avantage | Limite |
| --- | --- | --- |
| Traces/évaluations Azure, runtime local | Petit premier lot, peu de migrations | Démo dépend encore du poste |
| **Agent Foundry + backend/MCP cloud + interface légère** | Démo complète, réutilise les contrôles existants, ressources démontables | Identité, exécution durable et PostgreSQL cloud à traiter |
| Hosted agents/workflows et toutes les fonctions natives | Plus de surface pédagogique Foundry | Contraintes de préversion, orchestration et coûts supplémentaires à évaluer |

Choix proposé : deuxième approche, en commençant par le premier lot de la première. Tester les fonctions natives avancées dans des lots optionnels mesurables. Un seul agent métier au départ; multi-agent/A2A deviennent des expériences si une séparation de responsabilités justifie leur coût.

## 3. Deux parcours visibles

### Interface métier

Application web française, authentifiée avec Entra. Sélectionner un scénario ou poser une question dans un périmètre défini; voir un identifiant d’exécution, sa progression, les appels d’outils et citations, puis le résultat. Une file d’approbation permet au superviseur de consulter le brouillon exact et d’approuver/rejeter. Après validation, une action séparée crée l’ordre simulé de façon idempotente.

Le suivi affiche les événements observables (recherche, outil, document, résultat, erreur), pas une chaîne de pensée privée. Une déconnexion du navigateur n’interrompt pas l’investigation. La décision d’approbation porte sur la version du brouillon affichée; l’API refuse un brouillon modifié depuis cette lecture.

### Interface DS/AI engineer

Utiliser d’abord Foundry pour les agents/prompts versionnés, datasets, expériences, scores et traces. Une page interne légère lance un lot d’évaluation, choisit une version immuable d’agent/dataset et renvoie les liens vers le run Foundry et Application Insights. Ne pas reconstruire les visualiseurs Azure déjà disponibles.

Comparer qualité, validité des citations, succès des outils, refus d’autorisation, latence et tokens. Distinguer tests déterministes, investigations LLM et notes de juges LLM. Une panne d’infrastructure reste une panne, pas une mauvaise note du modèle.

## 4. Runtime et services

| Composant | Cible | Fonction |
| --- | --- | --- |
| Agent et modèle | Foundry existant | Agent natif versionné, GPT-5-mini; version épinglée par run |
| Interface et API | Container Apps Consumption | Une origine HTTP pour simplifier authentification et UX; conteneur web/API avec ressources plafonnées |
| Outils | Endpoint MCP Streamable HTTP sur Container Apps | Fonctions typées, contexte d’identité/incident fourni par le serveur; aucun rôle choisi par le modèle |
| Investigations/évaluations/ETL | Container Apps Jobs à la demande | Travail asynchrone durable; le déclenchement local ou web retourne immédiatement un run ID |
| État métier et événements | Azure Database for PostgreSQL | Incidents, transitions, ordres uniques, événements de progression et états de jobs |
| Sources et artefacts | Blob Storage privé | Sources brutes, manifests, données préparées, évaluations et exports |
| Recherche | Search Free existant | Corpus plafonné; textes et chunks sourcés, filtres déterministes |
| Traces | Application Insights + Log Analytics | Connexion au projet Foundry, spans client/serveur corrélés et vues de diagnostic |

Les choix exacts de SKU et réseau PostgreSQL restent un contrôle de déploiement : l’offre gratuite applicable à ce compte n’est pas confirmée. Conserver PostgreSQL et ses garanties de transactions est prioritaire sur un changement de base destiné uniquement à réduire le prix. Ne pas exécuter PostgreSQL sur le disque éphémère de Container Apps.

Le worker exécute initialement notre boucle autour du prompt agent Foundry et appelle MCP distant. Cela conserve les contrôles d’évidence et les retours d’erreur déjà testés. Une variante Foundry → MCP natif sera expérimentée ensuite avec liaison sûre entre appel, utilisateur et incident; la permission technique d’appeler un outil n’est pas l’approbation métier d’un ordre.

## 5. Identité, reprise et interaction humaine

- API : validation Entra de l’émetteur, audience, signature et expiration. Rôles backend `viewer`, `operator`, `maintenance_supervisor`, `admin`, plus autorisation d’ingénierie pour les évaluations.
- Le client ne peut transmettre une identité d’approbateur arbitraire. Les variables de rôle de la CLI actuelle restent réservées au mode local de test.
- Services Azure : identités managées et droits limités; remplacer `AzureCliCredential` dans le runtime hébergé par la chaîne adaptée, tout en conservant la connexion CLI locale.
- MCP : identité technique authentifiée et contexte métier limité à un run, jamais confiance dans un simple `incident_id` fourni par le modèle. Aucun endpoint d’approbation exposé comme outil agent.
- Lancement durable : enregistrer le run avant déclenchement, dédoublonner les demandes et réconcilier les runs si la réponse de lancement se perd. Éviter le seul `background task` d’un serveur HTTP susceptible de s’arrêter.
- Concurrence : ajout d’une génération d’exécution et de mises à jour conditionnelles, car un verrou de session PostgreSQL peut disparaître après perte réseau alors qu’un worker continue. Toute écriture d’un ancien worker est rejetée.
- La timeline provient des événements métier persistés, pas de la disponibilité ou du délai d’ingestion Application Insights.

## 6. Prompts, conversations, traces et évaluations cloud

Extraire les prompts de `loop.py` vers des fichiers versionnés avec métadonnées : identifiant, version, schéma de sortie, hash et commit. Chaque publication crée une version Foundry; conserver le lien commit → prompt → agent → dataset → run → trace. Le rollback sélectionne une version antérieure, sans réécrire l’historique.

Connecter Application Insights à Foundry, puis exporter les spans applicatifs avec conventions GenAI compatibles. Conserver l’audit transactionnel en base. Capturer les contenus nécessaires à l’analyse sur les scénarios publics/synthétiques avec une politique explicite; ne jamais exporter secrets, jetons ou URI de connexion. La suppression automatique actuelle des conversations doit devenir une politique configurable : conserver celles de démo assez longtemps pour inspection, les supprimer lors du nettoyage prévu.

Première intégration d’évaluations : produire des résultats avec le véritable runtime puis soumettre un dataset de requêtes/réponses/preuves au service d’évaluation Foundry. Ce n’est pas la même chose qu’une exécution d’agent orchestrée par Foundry; le rapport l’indique. Ensuite, explorer l’évaluation de cible agent une fois les outils accessibles en cloud.

Le service héberge les évaluations et leurs résultats; les juges peuvent consommer des tokens. Les évaluations d’effets métier utilisent une base ou un schéma d’évaluation isolé sans accès aux incidents de démo. Les rapports indiquent modèle, juge, versions, taille d’échantillon, erreurs et limites; pas de pourcentage global mélangeant pannes et qualité.

## 7. Données et recherche

Ajouter un scénario public « expliquer une pointe de demande et préparer une note opérationnelle sourcée », distinct du scénario synthétique transformateur. Sources candidates et volumes observés dans [le catalogue](../data/public-sources.md).

ETL Python initial à la demande : téléchargement d’un périmètre borné → archive brute Blob avec checksum et licence → validation schéma/unités/fuseaux → normalisation des séries et extraction de textes → découpage avec URL/page/version → indexation idempotente. Un manifest versionné permet d’auditer ce qui a été ingéré et retiré. Un changement de source n’altère pas silencieusement un dataset d’évaluation figé.

Les séries numériques sont accessibles par outils de requête/agrégation bornés (pas de SQL libre). Les descriptions, guides et extraits documentaires alimentent Search. Premier objectif : 10 000–50 000 observations et 200–1 000 chunks, plafonnés par taille réelle et licence; ce sont des objectifs de sélection, pas des volumes déjà ingérés.

Foundry IQ est un lot optionnel comparant la même question et les mêmes preuves avec Search classique. Vérifier séparément tier du service, région, quotas du plan de retrieval et coût LLM : « allocation gratuite de retrieval » ne signifie pas « n’importe quel service Search gratuit compatible ».

## 8. Microsoft 365 simulé puis réel

Créer une bibliothèque fictive de notes et procédures avec métadonnées de site/dossier/version et ACL, hébergée dans Blob/Search et exposée par MCP. Deux utilisateurs de test avec permissions différentes démontrent un filtrage backend. Nommer l’intégration « bibliothèque M365 simulée » dans l’interface.

Le vrai SharePoint est un lot séparé : licence Copilot ou option pay-as-you-go, site et agent dans le même tenant, identité déléguée OBO; l’identité managée ne remplace pas l’utilisateur pour ce connecteur. Aucun abonnement Microsoft 365 ni Databricks ajouté dans le socle.

## 9. Coûts et cycle de vie

Déployer les nouveaux composants dans des groupes dédiés, avec manifest de propriété et dépendances. Les ressources existantes `rg-hydro-agentic-poc` sont référencées en lecture d’inventaire et protégées des scripts de suppression par défaut. Ni migration ni suppression implicite de ce groupe.

Trois profils : `core` (visibilité cloud), `demo` (runtime + UX + état distant), `experiments` (IQ et intégrations optionnelles). Le profil doit pouvoir être supprimé indépendamment dans un ordre de dépendances défini. Infrastructure Bicep, paramètres explicites, inventaire des connexions/RBAC et commandes reproductibles.

Arrêt logique : refuser de nouveaux runs, arrêter les planifications, attendre/annuler les jobs selon demande, puis désactiver l’exécution. `minReplicas=0` seul n’est pas un arrêt : une requête peut réveiller l’application. PostgreSQL arrêté peut continuer à facturer du stockage et peut redémarrer automatiquement selon les règles du service. Les commandes affichent toujours les frais résiduels possibles.

Les budgets Azure servent à alerter et ne bloquent pas automatiquement les dépenses. Utiliser en plus plafonds de concurrence, taille de lots, tokens/étapes et ressources; prévoir une commande de suppression après export. La rétention et les suppressions différées du stockage doivent figurer dans le bilan de nettoyage.

## 10. Livraison et critères d’acceptation

1. **Visibilité cloud** : une investigation déclenchée localement apparaît dans Foundry avec version de prompt, trace et évaluation retrouvables par run ID.
2. **Backend hébergé** : lancer un run puis fermer le client; le run se termine, le résultat est consultable depuis un autre client. Reprise et idempotence vérifiées après arrêt du worker.
3. **UX et humain** : opérateur lance, superviseur approuve, rôle insuffisant refusé; rechargement de page et double clic ne créent pas de doublon.
4. **Données** : corpus public borné ingéré avec provenance, deux imports identiques sans doublons, citations retrouvables et tests d’ACL pour la bibliothèque simulée.
5. **Expériences** : comparer au moins deux versions de prompt sur un dataset figé; tests structurels et notes sémantiques affichés séparément.
6. **Réversibilité** : en environnement jetable, déployer, exporter, supprimer un profil, vérifier les ressources restantes, puis redéployer et restaurer. Documenter les objets hors resource group (connexions Foundry, rôles, applications Entra).

Le premier plan d’implémentation portera uniquement sur le lot 1 et l’outillage de cycle de vie commun. Chaque lot suivant aura son propre périmètre, vérification de coût et résultat démontrable.
