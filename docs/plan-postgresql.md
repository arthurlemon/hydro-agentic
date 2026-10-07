# PostgreSQL et vérification réelle OpenRouter

Demande : remplacer SQLite par PostgreSQL, utiliser `openai/gpt-5.6-luna`, tester avec la clé configurée et pousser les étapes validées sur `main`.

1. Modèle par défaut : vérifier le catalogue OpenRouter, tester la configuration, commit et push.
2. PostgreSQL : service Compose local sur `127.0.0.1:55432`, persistance JSONB, transactions et verrouillage de ligne pour les mutations. Verrou consultatif de session pour exclure deux investigations d’un incident; libération à la fermeture de connexion. Conserver les contrôles de preuves et d’approbation.
3. Vérification : suite existante sur une vraie base, schémas temporaires isolés, tests d’initialisation concurrente, d’événement unique, de rollback et de verrous interprocessus. Reconnexion MCP et CLI. Mise à jour de la documentation, commit et push.
4. Essais réels Python et MCP avec GPT-5.6 Luna. Examiner résultats, citations, brouillon et blocage sans approbation; consigner les observations sans inventer de métriques. Commit et push du bilan.

Configuration : `HYDRO_DATABASE_URL` est un secret masqué, transmis au serveur MCP par l’hôte. Aucune base SQLite locale contenant des incidents n’a été trouvée; aucune conversion de données existantes n’est nécessaire.

Pas de ressource Foundry à créer dans cette étape.
