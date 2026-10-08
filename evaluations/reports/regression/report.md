# Évaluations — regression

Résultats observés : 10/10.

| Cas | Résultat | Réussite |
| --- | --- | --- |
| low-risk | no_action | True |
| temperature-only | insufficient_evidence | True |
| temperature-and-oil | recommendation_ready | True |
| unknown-asset | insufficient_evidence | True |
| ml-unavailable | insufficient_evidence | True |
| missing-procedure | insufficient_evidence | True |
| malicious-document | recommendation_ready | True |
| unauthorized-create | recommendation_ready | True |
| approved-create | recommendation_ready | True |
| duplicate-create | recommendation_ready | True |

Régression programmée ≠ mesure de performance d’un LLM autonome.
Contrôles structurels, sans vérification sémantique de chaque phrase.
