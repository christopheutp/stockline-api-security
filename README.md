# StockLine — Démonstration 05 : passerelle HTTPS et durcissement

**Branche Git :** `05-passerelle` · **Tag Git :** `v0.5` · **Docker Hub :** `christopheutp/stockline-api:0.5`.

> **Source de référence : `demo.zip/ex5/`**. Les fichiers `Dockerfile`, `compose.yaml`, `.dockerignore` (complété pour le développement) et `passerelle/nginx.conf` proviennent de l’EX5 fourni. Le code Python reste celui de l’EX4 : cette démonstration porte sur **l'infrastructure**, pas sur une nouvelle version de l'API métier. Les anciennes démonstrations restent cumulées.

## Nouveautés de l'EX5

- **HTTPS en frontal** : une passerelle Nginx écoute sur `https://localhost:8443`. Seule la passerelle publie un port ; l'API reste sur le réseau Docker interne.
- **Limitation des requêtes** : quotas par IP dans Nginx pour l'API et `/auth/jeton` (HTTP **429** en cas de dépassement) ; taille de corps maximale de 16 Ko (**413**).
- **Durcissement** : délais de connexion et de réponse, en-têtes de sécurité, méthodes HTTP filtrées, routes Swagger/OpenAPI masquées, journaux JSON.
- **Durcissement Docker** : API sans utilisateur root, système de fichiers en lecture seule, répertoire temporaire en mémoire, capacités Linux supprimées, limites CPU/mémoire/processus.
- **Secret JWT Docker Compose** : stocké dans un fichier local **non suivi par Git**, monté comme secret, lu par `STOCKLINE_JWT_SECRET_FILE`.
- **Dockerfile multi-étapes** : cibles `tests` et `production`.

**Correspondances pédagogiques :** OWASP API4:2023 (consommation excessive de ressources), API8:2023 (mauvaises configurations de sécurité), API9:2023 (gestion de l'inventaire des API, dont les interfaces exposées). Ces protections illustrent des mesures partielles, pas une conformité OWASP complète.

## Lancer la démonstration EX5 (Windows PowerShell + Docker Desktop)

Depuis **la racine de cette branche**, créer les répertoires locaux ignorés par Git :

```powershell
New-Item -ItemType Directory -Force secrets, passerelle/certs | Out-Null
$secret = ([guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N'))
[System.IO.File]::WriteAllText((Join-Path (Get-Location) 'secrets/jwt_secret.txt'), $secret)
```

Pour une formation, cette génération est suffisante ; en production, utiliser un générateur cryptographique dédié et un gestionnaire de secrets.

**Certificat local autosigné** : si OpenSSL est installé sur le poste, exécuter :

```powershell
openssl req -x509 -nodes -newkey rsa:2048 -days 30 -keyout passerelle/certs/stockline.key -out passerelle/certs/stockline.crt -subj '/CN=localhost' -addext 'subjectAltName=DNS:localhost'
```

Sinon, utiliser Docker (la première exécution télécharge Alpine et OpenSSL) :

```powershell
docker run --rm -v "${PWD}/passerelle/certs:/certs" alpine:3.20 sh -c "apk add --no-cache openssl >/dev/null && openssl req -x509 -nodes -newkey rsa:2048 -days 30 -keyout /certs/stockline.key -out /certs/stockline.crt -subj /CN=localhost -addext subjectAltName=DNS:localhost"
```

Démarrer l'ensemble **API + passerelle** :

```powershell
docker compose up --build -d
```

L'API est accessible **uniquement** par `https://localhost:8443/sante` depuis le poste. Le certificat est autosigné : pour un essai local en ligne de commande, `curl.exe -k` ignore sa validation. **Ne pas utiliser `-k` en production.**

```powershell
curl.exe -k -i https://localhost:8443/sante
curl.exe -k -i https://localhost:8443/docs
```

Résultats attendus : `/sante` → **200** ; `/docs` → **404**. Un accès direct `http://localhost:8000` à l'API **de ce Compose** n'est pas publié (sauf si tu as indépendamment lancé une autre version sur ce port).

Pour observer les logs ou arrêter :

```powershell
docker compose logs -f passerelle
docker compose down
```

`docker compose down -v` supprime **également les données SQLite** du volume : n'utiliser cette variante que pour remettre à zéro la démonstration.

> Remarque : l'EX5 livré utilise un certificat de laboratoire et des quotas Nginx en mémoire par instance. Il ne met pas en place de certificats publics, de gestion multi-instance du rate limiting, de WAF ni de déploiement AWS Lambda.

## Tester et publier sur GitHub

Les tests applicatifs des démos 00 à 04 sont conservés ; **l'EX5 ne fournit aucun nouveau fichier de test Python**. La CI lance les tests existants et construit l'image `production`. Le comportement Nginx/HTTPS doit être vérifié par les commandes ci-dessus.

```powershell
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
```

La publication Docker est déclenchée par le tag Git `v0.5` ou manuellement depuis la branche `05-passerelle` :

```powershell
git switch 04-limitation-ressources
git pull origin 04-limitation-ressources
git switch -c 05-passerelle
# Copier les fichiers de cette archive à la racine du dépôt
git add .
git commit -m "Demo 05 - Passerelle HTTPS Nginx (EX5)"
git push -u origin 05-passerelle
git tag v0.5
git push origin v0.5
```

L'image Docker `0.5` ne contient **que l'API** ; la passerelle Nginx et le réseau privé sont orchestrés par `compose.yaml`. Le simple `docker run` de `0.5` ne reproduit pas l'EX5 complet. Le dépôt Docker Hub conserve malgré tout un tag `0.5` cohérent avec la progression.

## Ports de la formation

| Version | Exécution | Port hôte |
|---|---|---:|
| 00 | `stockline-api:0.0` | 8000 |
| 01 | `stockline-api:0.1` | 8001 |
| 02 | `stockline-api:0.2` | 8002 |
| 03 | `stockline-api:0.3` | 8003 |
| 04 | `stockline-api:0.4` | 8004 |
| **05 — passerelle** | **`docker compose up --build -d`** | **8443 (HTTPS)** |

Les ports 8000–8004 concernent les conteneurs antérieurs lancés séparément. Le Compose de l'EX5 n'expose que la passerelle 8443.
