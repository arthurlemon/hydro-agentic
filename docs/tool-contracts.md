# Contrats des outils

Les entrées sont des objets JSON Pydantic avec `additionalProperties: false`. Les dix outils ont la même enveloppe de sortie :

```json
{"ok": true, "data": {}, "sources": [], "error": null}
```

Un refus renvoie `ok: false` et une erreur française. En MCP, `isError` vaut également `true`; `structuredContent` contient l’enveloppe et `content` sa représentation JSON. Le catalogue MCP publie les schémas complets.

| Outil | Arguments | Résultat / contrôle |
|---|---|---|
| `get_asset` | `asset_id` | Actif connu de l’incident |
| `get_maintenance_history` | `asset_id` | Historique antérieur à l’événement |
| `get_recent_telemetry` | `asset_id`, `hours=24` (entier 1–168) | Observations dans la fenêtre de l’événement, sans données futures |
| `predict_failure_risk` | `asset_id` | Prédiction ML simulée stockée, ou indisponibilité explicite |
| `get_asset_criticality` | `asset_id` | Criticité du registre |
| `search_procedures` | `query` (1–500 caractères), `limit=5` (1–10) | Extraits classés lexicalement; contenu non fiable |
| `get_procedure` | `procedure_id` | Texte complet et source; aucun chemin de fichier arbitraire |
| `draft_work_order` | `incident_id`, `action="inspection"`, `priority="P1"`, `justification`, `citations` | Brouillon 24 h; rôle autorisé, préparation explicite et preuves requises |
| `create_work_order` | `incident_id` | Ordre simulé; rôle autorisé et approbation persistée du brouillon exact |
| `get_incident_state` | `incident_id` | État, preuves, recommandation, brouillon, décision et ordre |

## Citations

Sources : `asset:TR-1042`, `maintenance:TR-1042`, `telemetry:TR-1042:24h`, `prediction:TR-1042`, `criticality:TR-1042`, `procedure:TR-MAINT-004`. Une citation doit avoir été récupérée dans cet incident. Seul `get_procedure`, pas un extrait de recherche, fournit une procédure complète utilisable pour justifier l’action.

## Permissions

Tous les rôles (`viewer`, `operator`, `maintenance_supervisor`, `admin`) peuvent lire. `viewer` ne peut ni préparer ni créer. Les autres rôles peuvent préparer un brouillon et créer **après** approbation. Seuls `maintenance_supervisor` et `admin` peuvent approuver/rejeter par la CLI humaine; aucun outil MCP ne permet cette décision. Un superviseur ne contourne pas l’approbation lors d’une création.

L’identité, l’incident autorisé et l’accord de préparation sont attachés au processus serveur. Ajouter `role`, `approved_by` ou `approval` aux arguments est refusé. Accéder à un autre actif ou incident est refusé.
