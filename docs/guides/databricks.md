# Analytique remplaçable — phase 9

`AnalyticsService.predict(asset_id) -> Prediction` sépare les prédictions des autres données de l’actif. `JsonAnalyticsService` fournit les valeurs synthétiques existantes, sans calcul statistique réel. `DatabricksAnalyticsService` appelle un service de modèle configuré explicitement. Les deux renvoient le même contrat Pydantic; `DataService` vérifie d’abord que l’actif existe.

## État réel

L’adaptateur et ses tests HTTP sont implémentés. **Aucun workspace, modèle MLflow ni endpoint Databricks n’a été créé ou testé réellement.** Le fonctionnement en cours reste `HYDRO_ANALYTICS_BACKEND=json`. Le service distant est facultatif; il n’est pas nécessaire pour les phases précédentes.

Pour l’essayer, il faut un compte/workspace, un modèle enregistré et un endpoint CPU compatible, puis une identité autorisée à l’interroger. Free Edition est destinée à l’apprentissage et aux usages personnels non commerciaux, sous quotas/fair use; sa disponibilité réelle de serving et ses restrictions réseau doivent être vérifiées dans le compte. Ne pas remplacer automatiquement cette offre par l’essai Azure Databricks payant après expiration. Voir [les offres et limites](../azure/offres-gratuites.md).

## Contrat du service à déployer

Le modèle doit accepter une seule ligne contenant `asset_id` et retourner un objet complet, pas seulement un score. Il doit obtenir ses caractéristiques et fournir sa version côté serveur; l’agent n’envoie ni code, ni SQL, ni instructions de modèle.

```json
{"dataframe_records": [{"asset_id": "TR-1042"}]}
```

Réponse attendue :

```json
{
  "predictions": [{
    "asset_id": "TR-1042",
    "failure_probability_30d": 0.68,
    "risk_level": "high",
    "main_factors": ["Exemple synthétique"],
    "model_version": "version-a-remplacer"
  }]
}
```

La probabilité, les facteurs et la version ci-dessus sont un **exemple de contrat**, pas une prédiction issue de Databricks. Le modèle réellement servi doit produire ses propres valeurs vérifiables. Pour un modèle attendant un tableau de caractéristiques plutôt qu’un identifiant, il faut adapter le service avant de l’utiliser; ce client ne prétend pas supporter tous les modèles Databricks.

## Configuration facultative

```dotenv
HYDRO_ANALYTICS_BACKEND=databricks
DATABRICKS_SERVING_ENDPOINT=https://<workspace>.cloud.databricks.com/serving-endpoints/<nom>/invocations
DATABRICKS_TOKEN=<jeton-autorise>
```

Un hostname Azure se terminant par `.azuredatabricks.net` est aussi accepté. HTTPS, chemin d’invocation précis et absence de paramètres/identifiants dans l’URL sont requis. Les endpoints route-optimized avec URL dédiée ne sont pas pris en charge. Le jeton peut être OAuth ou un jeton de développement valide; son renouvellement automatique n’est pas implémenté. En production, privilégier OAuth machine-à-machine et une identité de service à privilèges limités.

Le processus MCP reçoit le jeton uniquement lorsque Databricks est sélectionné; le modèle et les arguments d’outils ne le reçoivent pas. Il reste hors de Git et des traces. La liste des domaines admis limite les erreurs d’URL; elle ne remplace pas l’autorisation du workspace ni une politique réseau.

## Échecs et vérifications

Pas de redirection ni reprise automatique; délai de connexion cinq secondes et délai réseau vingt secondes par opération. HTTP 401/429/500, timeout, schéma invalide, plusieurs résultats ou actif différent donnent une erreur contrôlée. **Aucun retour vers JSON, score zéro ni probabilité inventée en cas de panne.**

Les tests utilisent HTTPX MockTransport, pas Databricks réel : payload étroit, schéma valide/invalide, autre actif, URL hostile, timeout, erreurs HTTP, absence de substitution et refus d’actif inconnu avant appel distant.

Référence consultée : [Databricks — interroger les services de modèles personnalisés](https://docs.databricks.com/aws/en/machine-learning/model-serving/score-custom-model-endpoints), mise à jour du 11 septembre 2026. Le format `dataframe_records` et l’enveloppe `predictions` sont documentés; le contenu métier reste notre contrat.
