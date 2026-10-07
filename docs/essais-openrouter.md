# Essais réels GPT-5.6 Luna

Modèle : `openai/gpt-5.6-luna`, identifiant confirmé dans le catalogue OpenRouter. Appels effectués avec la clé locale, jamais enregistrée dans Git. Données synthétiques et PostgreSQL 17 local. Code : migration `e9625a4`, précision de télémétrie `b806c50`.

## Défaut trouvé lors du premier passage

Trois investigations réelles ont d’abord retourné `insufficient_evidence`. Les résumés montraient que `baseline_stddev` était interprété comme l’écart-type de la référence en °C. Ce champ contient en réalité le z-score de température déjà calculé. Cette ambiguïté empêchait le modèle de reconnaître les cas de surchauffe et de température normale.

La réponse de `get_recent_telemetry` contient maintenant la définition explicite de la mesure et de son unité. Les valeurs, les règles métier et le contrôle d’approbation sont inchangés. Un test de contrat échoue avant cette précision et réussit après; l’effet sur le modèle a été vérifié en rejouant les scénarios.

## Résultats après précision du contrat

| Événement | Transport | Incident | Résultat observé | Appels au modèle |
|---|---|---|---|---:|
| `EVT-48392` avec `--prepare` | MCP stdio | `INC-1001` | Inspection P1 sous 24 h, brouillon `awaiting_approval` | 9 |
| `EVT-LOW` | MCP stdio | `INC-1003` | `no_action`, aucune intervention urgente | 5 |
| `EVT-TEMP` | Python | `INC-1002` | `insufficient_evidence`, confirmation récente d’huile manquante | 3 |
| `EVT-UNKNOWN` | Python | `INC-1007` | `insufficient_evidence`, actif et données associés indisponibles | 3 |

Les nombres d’appels proviennent du journal PostgreSQL, en séparant les investigations au retour du compteur d’étapes à 1. Les identifiants ne sont pas nécessairement consécutifs : PostgreSQL consomme aussi des valeurs de séquence lors d’un conflit d’insertion d’événement déjà présent.

Vérifications des conclusions et preuves persistées :

- Cas P1 : score de température 3,7 et confirmation actuelle d’huile, lecture complète de TR-MAINT-004, citations du contexte, de la télémétrie et des procédures. Le modèle distingue le constat historique de 2025 de la confirmation récente.
- Faible risque : score 0,6, charge 60 %, probabilité simulée 0,04 et aucune action proposée.
- Température seule : score 3,6 reconnu comme une surchauffe, mais aucune confirmation actuelle d’huile; le modèle ne transforme pas l’ancien constat en preuve récente.
- Actif inconnu : cinq outils de données ont refusé l’accès à un actif absent; la conclusion indique les données manquantes et ne cite que les procédures effectivement récupérées.
- Après reconnexion MCP, `create_work_order(INC-1001)` a retourné `ok=false` et « Approbation humaine persistée requise avant toute création. ». L’état est resté `awaiting_approval`, avec `approval=null` et `work_order=null`.

## État local et reproduction

Les résultats JSON sont conservés localement dans `.hydro/` (ignoré par Git), l’état et l’audit dans PostgreSQL. Le brouillon `INC-1001` reste disponible avec `uv run hydro-agent state INC-1001`; il n’a pas été approuvé. Les autres événements peuvent être réinvestigués. Un brouillon figé ne peut pas être écrasé par une nouvelle investigation.

Ces essais vérifient quatre scénarios synthétiques avec un fournisseur réel, pas un taux général de qualité ou une évaluation de production. La suite automatisée de 49 tests utilise des doubles de modèle, une vraie base PostgreSQL et de vrais sous-processus CLI/MCP. Les tests couvrent séparément l’approbation simulée et l’idempotence après création.
