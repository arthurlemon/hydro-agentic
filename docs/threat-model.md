# Modèle de menaces du PoC

## Frontières de confiance

Le modèle, sa conversation et les documents récupérés ne déterminent jamais l’identité ni l’approbation. Le processus hôte, les fichiers synthétiques et PostgreSQL sont de confiance dans cette démonstration. Un utilisateur contrôlant l’environnement ou la base peut changer ces données : l’authentification réelle devra être ajoutée avant un déploiement multi-utilisateur.

| Menace | Contrôle actuel | Vérification |
|---|---|---|
| Document demandant de contourner l’approbation | Contenu marqué non fiable; approbation vérifiée côté service | `ATTACK-001` puis création refusée |
| Identité ou rôle inventé par le modèle | Champs supplémentaires interdits; identité liée à l’hôte | Arguments `role` / `approved_by` refusés |
| Référence à un autre incident | Registre lié à un incident et son actif | Accès croisé refusé |
| Citation inventée ou simple extrait | Source récupérée exigée; procédure complète requise | Brouillon non étayé refusé |
| Confusion huile historique / actuelle | Condition codée sur la télémétrie actuelle | Cas température seule refusé pour P1 |
| Rejeu ou concurrence de création | Transaction PostgreSQL, verrou de ligne et ordre conservé dans l’incident | Appels concurrents et reprise renvoient le même ordre |
| Modification après approbation | Brouillon/preuves figés; approbation liée à sa copie exacte | Modification et création après rejet refusées |
| Traversée de chemins | Identifiants de procédures limités | `../` refusé |
| Boucle ou panne modèle | Limite d’étapes, délai HTTP, état d’échec persisté | Limite et reprise testées |
| Secret dans les erreurs | Secret masqué en configuration; erreurs HTTP sans corps distant | 401/429/500 sans clé divulguée |

Les tests d’injection démontrent le refus du serveur même si le modèle appelle l’outil interdit. Ils ne démontrent pas que tous les modèles ignoreront tous les documents malveillants. Les textes libres du modèle doivent être évalués séparément; seules les actions structurées passent les contrôles métier.

Les journaux locaux ne sont pas inviolables et ne constituent pas un audit de conformité. Aucun secret ne doit être commité; `.env`, les bases et `.venv` sont exclus de Git.
