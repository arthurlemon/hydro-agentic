# Évaluations — phase 8

```bash
uv run python scripts/run_evals.py
# Facultatif, appels payants à un vrai agent; aucune substitution automatique :
uv run python scripts/run_evals.py --provider foundry --output .hydro/evals-foundry
uv run python scripts/run_evals.py --provider openrouter --output .hydro/evals-openrouter
```

Chaque commande exécute dix scénarios : faible risque, température seule, température + huile, actif inconnu, ML indisponible, procédure absente, document malveillant, création non autorisée, création approuvée et création répétée après reprise. Le rapport JSON donne résultats, citations, données manquantes, erreurs du vérificateur, durée et séquence d’outils observés. `model_calls` compte les appels terminés enregistrés dans l’audit, pas les tentatives interrompues avant réponse. `total_tokens` est la somme des usages retournés, ou `null` si indisponibles (notamment avec le double), jamais une estimation. Le rapport Markdown est dérivé du JSON. Une violation donne un code de sortie **1**.

## Environnement et effets

Les données sont copiées dans un répertoire temporaire. Les scénarios de panne suppriment seulement une source dans cette copie. Un schéma PostgreSQL `hydro_eval_<uuid>` est créé puis supprimé en `finally`. Les dix événements ont des identifiants distincts; aucune table applicative ni aucun incident de démonstration n’est modifié. Les deux derniers cas approuvent et créent des ordres **simulés dans ce schéma isolé** avec des identités de test.

La recherche est locale, avec les sept documents figés du dépôt, même si `.env` sélectionne Search Azure. Le transport est Python. En mode Foundry, les conversations distantes contiennent ces données synthétiques et sont fermées par l’adaptateur existant. Azure Search, MCP et leurs authentifications sont couverts séparément par les essais d’intégration documentés.

## Ce qui est mesuré

Le mode par défaut `regression` utilise un double programmé annoncé dans `evaluations/runner.py`. Il exerce la vraie boucle, les services et les contrôles PostgreSQL, mais ses choix et conclusions sont prédéterminés. **10/10 en régression ne signifie pas 100 % de réussite d’un LLM autonome.** Le rapport observé versionné est dans `evaluations/reports/regression/`.

Les modes `foundry` et `openrouter` utilisent la même boucle et un vrai modèle pour les investigations. Les actions d’approbation, tentatives interdites et répétitions sont exécutées explicitement par le harnais, jamais inventées par un adaptateur. Dans le cas malveillant, le harnais force également la consultation du document puis la tentative interdite : ce résultat démontre le refus du backend, pas une résistance sémantique universelle du LLM.

Le vérificateur contrôle les invariants structurels R1–R7 : actifs des preuves/ordres, y compris les observations imbriquées; schéma complet et strict de prédiction; consultation complète et citation de procédure; approbation du même brouillon non vide, rôle superviseur/admin, acteur et horodatage; absence d’effet non autorisé; données manquantes explicites et citations observées. Le backend valide les conditions métier des recommandations. Aucune analyse sémantique exhaustive du résumé ni juge LLM ne vérifie chaque phrase; une hallucination textuelle peut donc échapper à ces contrôles. Les pannes d’exécution ne sont pas des mesures de qualité du modèle.

Le test du vérificateur fournit une citation inventée et un ordre sans approbation, puis vérifie leur rejet; un cas valide est accepté. Un autre test impose un rapport échoué et vérifie le code de sortie 1. L’ensemble des dix cas est réellement exécuté dans la suite normale.

La solution suit le script léger prévu dans `PROJECT_PLAN.md`; elle n’ajoute pas un environnement Harbor ni un benchmark de développement généraliste. Les modes LLM de cette nouvelle suite sont disponibles mais **n’ont pas encore été exécutés**. Les essais réels antérieurs restent documentés séparément.
