# Persistance et approbation — phases 5 et 6

Ces contrôles ont été implémentés avant l’intégration cloud : ils sont nécessaires dès qu’un outil peut préparer ou créer un ordre. PostgreSQL reste la seule base d’état; Cosmos DB n’est pas nécessaire pour ce PoC et n’a pas été déployé.

## Parcours humain

```bash
# Lire le brouillon, les preuves et la décision, sans modifier l’incident.
uv run hydro-agent state <INC-identifiant>

# Action humaine explicite : identité locale SIMULÉE de superviseur.
HYDRO_ROLE=maintenance_supervisor HYDRO_ACTOR=superviseure-locale \
  uv run hydro-agent approve <INC-identifiant>

# Ou refuser; aucun ordre ne pourra être créé pour cet incident rejeté.
HYDRO_ROLE=maintenance_supervisor HYDRO_ACTOR=superviseure-locale \
  uv run hydro-agent reject <INC-identifiant>

# Après approbation seulement; aucune inférence LLM ni connexion Azure nécessaire.
uv run hydro-agent resume <INC-identifiant>
uv run hydro-agent resume <INC-identifiant>  # Même ordre simulé.
```

L’approbation ne crée pas d’ordre. Elle conserve l’identité, la date et une copie exacte du brouillon. Même un admin doit faire approuver le brouillon avant création. Les opérateurs ne peuvent pas approuver; les lecteurs ne peuvent pas rédiger ou créer. L’agent ne dispose d’aucun outil d’approbation et ne peut pas fournir son propre rôle comme argument.

`--prepare` autorise la préparation, jamais l’approbation. Le brouillon soumis est figé. Une modification doit passer par un nouveau processus métier, non par une reformulation du modèle. Un rejet est terminal dans cette démonstration.

## Reprise et concurrence

- `event_id` unique : les réessais retrouvent le même incident; les séquences peuvent avoir des trous.
- État et preuves en JSONB, indépendants de la conversation Foundry et de la mémoire Python.
- Verrou de session PostgreSQL : une seule investigation simultanée du même incident entre processus.
- Verrou de ligne et transaction : validation, approbation et création cohérentes; une création concurrente renvoie l’ordre déjà persisté.
- Une coupure après commit mais avant réception du résultat se traite en relançant `state` puis `resume`, jamais en inventant un nouvel ordre.
- La connexion PostgreSQL du verrou doit rester attachée à la session : ne pas utiliser un pool en mode transaction pour cette connexion. Le PoC ne fournit pas de jeton de génération contre une perte de connexion pendant une exécution distribuée.

Le volume Compose conserve les données. `docker compose stop` puis `docker compose up -d --wait postgres` permet un arrêt sans supprimer le volume. **Ne pas utiliser `down --volumes`** sur une base à conserver. Aucun arrêt du PostgreSQL applicatif ni suppression d’incident n’a été nécessaire à cette validation.

## Preuves exécutées

Les tests ouvrent une vraie base PostgreSQL dans des schémas isolés, puis redémarrent CLI et sous-processus MCP. Ils vérifient l’approbation persistée, la reprise sans LLM, les créations répétées/concurrentes, le brouillon figé et le rejet persistant avec refus de reprise. Les tests interprocessus vérifient aussi la libération du verrou après fermeture de la session.

Les incidents de démonstration `INC-1001`, `INC-1017` et `INC-1018` restent en attente : **aucune approbation ni création n’a été exécutée sur ces incidents**. Les seuls ordres créés pour ces vérifications sont simulés, dans les schémas de test.

En production, remplacer les variables d’identité par une identité Entra vérifiée et un véritable écran/API d’approbation; la lecture d’un brouillon et l’approbation ne doivent pas reposer sur la confiance envers un processus local.
