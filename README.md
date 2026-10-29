# StockLine — Démonstration 00 : API initiale non sécurisée

**Version pédagogique : 00** · **Branche : `00-api-vulnerable`** · **Image Docker : `christopheutp/stockline-api:0.0`**

Cette branche contient le **code initial fourni dans `stockline-api.zip`**, sans modification des routes ni des règles métier. L'application FastAPI gère les produits et mouvements de stocks de deux entrepôts (`paris` et `lyon`), avec SQLite et SQLAlchemy. Cette version n'implémente **aucune authentification ni autorisation** : elle sert de point de comparaison pour les démonstrations suivantes.

> **Laboratoire uniquement.** Ne pas publier ce service sur Internet, le relier à des données réelles ni réutiliser ses configurations en production. Le port Docker est lié à `127.0.0.1` dans les commandes proposées.

## Objectifs de la démonstration

1. Découvrir `/docs` et les routes FastAPI.
2. Interroger les produits et les stocks sans identité.
3. Constater que les opérations de modification ne requièrent aucune authentification.
4. Relever les risques qui seront étudiés aux étapes suivantes.

## Références OWASP API Security Top 10 (2023)

- **API2:2023 — Broken Authentication** : ici, aucune authentification n'est imposée.
- **API1:2023 — Broken Object Level Authorization** et **API5:2023 — Broken Function Level Authorization** : aucun contrôle de droits utilisateur n'est effectué.
- **API3:2023 — Broken Object Property Level Authorization** : la protection des propriétés sera étudiée à l'étape 03.
- **API4:2023 — Unrestricted Resource Consumption** : la limitation des appels sera étudiée à l'étape 04.

Ces correspondances désignent des thèmes pédagogiques, pas un audit OWASP exhaustif.

## Lancer avec Docker

Prérequis : Docker installé et démarré. Après publication de l'image :

```bash
docker run --rm --name stockline -p 127.0.0.1:8000:8000 christopheutp/stockline-api:0.0
```

- Documentation interactive : <http://localhost:8000/docs>
- Vérification de santé : <http://localhost:8000/sante>
- Liste des produits : <http://localhost:8000/produits>

Pour arrêter : `Ctrl+C` dans le terminal Docker. Sans volume, la base de démonstration est recréée pour chaque nouveau conteneur. Pour conserver la base : ajouter `-v stockline-data:/data` à la commande `docker run` (attention : les données restent alors persistantes entre les étapes).

Pour construire localement au lieu de télécharger l'image :

```bash
docker build -t stockline-api:0.0 .
docker run --rm --name stockline -p 127.0.0.1:8000:8000 stockline-api:0.0
```

## Lancer sans Docker (CloudShell ou ordinateur)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Sur Windows, l'activation du venv s'effectue différemment ; sur CloudShell, `relancer-api.sh` reste disponible pour un démarrage en arrière-plan.

## Vérification de la démonstration

Depuis `/docs`, lancer `GET /produits`, puis tester une opération d'écriture sur des données fictives. Observer qu'aucun jeton d'accès n'est exigé. Refaire ensuite les appels sur les branches suivantes pour visualiser les protections ajoutées.

## Fichiers

- `app/` : code source initial (inchangé).
- `tests/` et `pytest.ini` : tests fonctionnels fournis.
- `requirements.txt` : dépendances fournies.
- `relancer-api.sh` : script initial pour CloudShell, **non utilisé dans Docker**.
- `Dockerfile`, `.dockerignore` : construction du conteneur.
- `.github/workflows/docker-publish.yml` : tests automatiques et publication Docker.

## Publication automatique

Créer dans les **Secrets and variables → Actions** du dépôt GitHub un secret `DOCKERHUB_TOKEN` contenant un **access token Docker Hub** autorisé à publier dans `christopheutp/stockline-api`. Ne jamais mettre ce jeton dans un fichier versionné.

Le workflow lance les tests à chaque push sur `00-api-vulnerable`. Il publie l'image `0.0` **uniquement** quand le tag Git `v0.0` est poussé (ou lors d'un déclenchement manuel du workflow sur cette branche). Le tag doit être créé à partir de cette branche :

```bash
git switch 00-api-vulnerable
git tag v0.0
git push origin v0.0
```

Vérifier ensuite l'exécution dans l'onglet **Actions** du dépôt et la présence de `christopheutp/stockline-api:0.0` sur Docker Hub.

## Étape suivante

Branche `01-authentification` : ajout de l'authentification JWT pour illustrer **API2:2023 — Broken Authentication**.
