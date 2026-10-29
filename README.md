# StockLine — Démonstration 01 : authentification JWT

**Branche : `01-authentification` · Tag Git : `v0.1` · Image Docker : `christopheutp/stockline-api:0.1` · Port hôte : `8001`**

Cette version reprend **l'intégralité de la démonstration 00** et ajoute une authentification par jeton JWT. Elle est construite à partir des **fichiers officiels de l'exercice 1** fournis dans `securite-api-2j.zip` (`ex1/app/main.py`, `ex1/app/securite.py`, `ex1/tests/test_ex1_authentification.py`). Les autres routes, modèles et données restent inchangés.

> **Laboratoire uniquement.** Les comptes de test et mots de passe sont publics et les versions successives conservent volontairement des faiblesses à corriger. Ne pas exposer directement ces conteneurs à Internet ni les utiliser avec de vraies données.

## Risque OWASP couvert

**OWASP API Security Top 10 (2023) — API2:2023, Broken Authentication (authentification défaillante).**

- `POST /auth/jeton` vérifie un identifiant et son mot de passe, puis émet un JWT signé (HS256), valable 15 minutes.
- Les routes métier utilisent `Depends(utilisateur_courant)` et renvoient **401** si le jeton Bearer est absent, invalide ou expiré.
- `GET /sante` et `POST /auth/jeton` restent publics.
- `GET /moi` permet de consulter l'identité associée au jeton.
- Les mots de passe des comptes du laboratoire sont représentés par des empreintes PBKDF2 salées. La clé JWT doit être fournie **hors du code** via `STOCKLINE_JWT_SECRET` (32 caractères minimum).

**Limite pédagogique :** cette étape authentifie les utilisateurs, mais ne vérifie **pas encore** quels produits, entrepôts ou opérations chacun a le droit d'utiliser. L'autorisation sera ajoutée dans la démonstration 02 (API1 et API5).

## Lancement Docker sur Windows (PowerShell)

Prérequis : Docker Desktop démarré. Créer une clé de signature temporaire propre à cette exécution :

```powershell
$env:STOCKLINE_JWT_SECRET = ([guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N'))
```

Télécharger l'image si nécessaire :

```powershell
docker pull christopheutp/stockline-api:0.1
```

Lancer le conteneur sur le **port 8001 du PC**, le port interne restant `8000` :

```powershell
docker run --rm --name stockline-01 -p 127.0.0.1:8001:8000 -e STOCKLINE_JWT_SECRET christopheutp/stockline-api:0.1
```

- Swagger : <http://localhost:8001/docs>
- Santé (sans authentification) : <http://localhost:8001/sante>
- Produits (sans jeton : `401`) : <http://localhost:8001/produits>

Pour arrêter : `Ctrl+C` dans le terminal du conteneur. La variable d'environnement PowerShell n'est nécessaire que pour le lancement, pas pour télécharger l'image.

## Démonstration avant / après

Faire tourner les deux versions simultanément, dans **deux terminaux** PowerShell. Pour la version 00 :

```powershell
docker run --rm --name stockline-00 -p 127.0.0.1:8000:8000 christopheutp/stockline-api:0.0
```

Pour la version 01 :

```powershell
$env:STOCKLINE_JWT_SECRET = ([guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N'))
docker run --rm --name stockline-01 -p 127.0.0.1:8001:8000 -e STOCKLINE_JWT_SECRET christopheutp/stockline-api:0.1
```

Tester sans jeton :

```powershell
curl.exe -i http://localhost:8000/produits
curl.exe -i http://localhost:8001/produits
```

**Résultat attendu :** `200 OK` pour la version 00, `401 Unauthorized` pour la version 01.

Obtenir ensuite un jeton (PowerShell) et effectuer le même appel avec authentification :

```powershell
$corps = @{ identifiant = 'alice'; mot_de_passe = 'Paris-Stock-2026' } | ConvertTo-Json
$reponse = Invoke-RestMethod -Uri 'http://localhost:8001/auth/jeton' -Method Post -ContentType 'application/json' -Body $corps
$jeton = $reponse.access_token
Invoke-RestMethod -Uri 'http://localhost:8001/moi' -Headers @{ Authorization = "Bearer $jeton" }
Invoke-RestMethod -Uri 'http://localhost:8001/produits' -Headers @{ Authorization = "Bearer $jeton" }
```

**Résultat attendu :** identité d'Alice et liste des produits. On peut aussi utiliser Swagger et son bouton **Authorize** : saisir le jeton Bearer.

### Comptes du laboratoire

| Identifiant | Mot de passe | Rôle | Entrepôt |
|---|---|---|---|
| `alice` | `Paris-Stock-2026` | gestionnaire | paris |
| `bruno` | `Lyon-Stock-2026` | gestionnaire | lyon |
| `admin` | `Admin-Stock-2026` | admin | — |

Ces identifiants ne conviennent **qu'à cette démonstration locale**.

## Plan de ports pour toutes les versions

Chaque conteneur écoute toujours le port **8000 en interne**, mais expose un port **différent sur le PC**. Les noms de conteneurs doivent aussi être uniques.

| Branche | Tag Docker | Port PC | Swagger |
|---|---|---:|---|
| `00-api-vulnerable` | `0.0` | 8000 | <http://localhost:8000/docs> |
| `01-authentification` | `0.1` | 8001 | <http://localhost:8001/docs> |
| `02-autorisation` | `0.2` | 8002 | <http://localhost:8002/docs> |
| `03-protection-donnees` | `0.3` | 8003 | <http://localhost:8003/docs> |
| `04-limitation-ressources` | `0.4` | 8004 | <http://localhost:8004/docs> |

Les trois dernières images seront accessibles **après** leur publication. Chacun des conteneurs utilisera sa **propre base SQLite** dans `/data` (aucun volume partagé), donc les données sont indépendantes. Prévoir suffisamment de mémoire pour les exécuter simultanément.

## Démarrer et vérifier localement (sans Docker)

À partir de la racine du dépôt :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export STOCKLINE_JWT_SECRET="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
pytest -q
uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Sur AWS CloudShell, `relancer-api.sh` reste disponible et génère un secret dans `.secret-jwt` (à ne pas committer). Le script lance l'API sur le port 8000.

## Tests

Le workflow GitHub Actions exécute `pytest -q` à chaque push sur cette branche. Le fichier `tests/test_ex1_authentification.py` contrôle notamment :

- Le refus des accès sans jeton (`401`).
- Le refus d'un mauvais mot de passe.
- L'identification par un jeton valide.
- Le refus des jetons expirés et des signatures incorrectes.
- L'obligation de fournir une clé suffisamment longue.

Les tests fonctionnels historiques sont conservés.

## Publication automatisée sur Docker Hub

Le workflow `.github/workflows/docker-publish.yml` exécute les tests sur la branche `01-authentification` et publie `christopheutp/stockline-api:0.1` **uniquement lorsque le tag Git `v0.1` est poussé**, ou lors d'un déclenchement manuel sur cette branche.

Le secret GitHub `DOCKERHUB_TOKEN` créé pour la version 00 est réutilisé : aucun nouveau secret n'est nécessaire.

```bash
git switch 01-authentification
git tag v0.1
git push origin v0.1
```

Ne créer le tag **qu'après** avoir vérifié les tests de la branche. Ne pas réutiliser `v0.0` : il correspond déjà à l'image précédente.

## Étape suivante

`02-autorisation` : contrôle des droits par rôle et par objet / entrepôt (API1:2023 BOLA et API5:2023 BFLA).
