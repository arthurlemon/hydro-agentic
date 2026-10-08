# Observabilité locale — phase 7

OpenTelemetry produit des spans `cli`, `investigation`, `model`, `tool` et `mcp.request`. Le contexte W3C `traceparent` passe dans les métadonnées MCP, jamais dans les arguments visibles au modèle. Les audits PostgreSQL ajoutent `trace_id` et `span_id` quand un span est actif.

Le journal JSONL est `.hydro/traces.jsonl` (`HYDRO_TRACE_PATH`). Chaque ligne contient identifiants, parent, durée, statut et attributs contrôlés. Le processus MCP écrit dans ce fichier, **pas dans stdout**, réservé au protocole. Les fichiers nouvellement créés sont privés (`0600`).

Les spans modèle enregistrent les compteurs de tokens disponibles. Les spans outil enregistrent le nom reconnu, le résultat et les citations. Pour une recherche, seuls `query_sha256` et `query_length` sont conservés : une empreinte permet de reconnaître une requête répétée, pas de relire son texte. Les exceptions marquent le span en erreur sans enregistrer leur message ni leur pile.

Les clés, URI PostgreSQL, arguments complets, prompts, résumés et documents ne sont pas exportés par cette instrumentation. Les empreintes ne rendent pas des requêtes prévisibles anonymes; traiter aussi ces journaux comme des données internes. L’audit métier existant contient les erreurs françaises contrôlées et les citations, pas les arguments.

## Export facultatif

`HYDRO_OTLP_ENDPOINT` peut désigner l’URL complète d’un collecteur OTLP HTTP, par exemple `http://localhost:4318/v1/traces`. Sans cette valeur, aucun export réseau de traces. Le collecteur doit gérer authentification, chiffrement, rétention et éventuel transfert vers Application Insights; aucun service Azure de supervision n’a été créé.

L’export est synchrone et peut ajouter de la latence; le délai OTLP est de cinq secondes. Une panne du fichier JSONL n’altère pas la décision métier. Il n’y a pas encore de rotation, d’alerte, de mesure tarifaire ni d’instrumentation automatique des SDK cloud. Les spans montrent les appels applicatifs, pas tous les traitements internes Foundry.

## Vérification

`tests/test_observability.py` vérifie les parents, la corrélation de l’audit, un refus de création, la propagation dans un vrai processus MCP et l’absence du texte sensible d’une requête/exception. Suite complète : **83 tests réussis**, Ruff et mypy réussis.
