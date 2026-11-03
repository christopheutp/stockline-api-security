# StockLine — Démonstration 04 : limitation des ressources (OWASP API4:2023)

**Branche Git : `04-limitation-ressources` · Tag Git : `v0.4` · Docker : `christopheutp/stockline-api:0.4` · Port hôte : `8004`**

Cette branche reprend **toutes les protections des démos 01 à 03**, puis intègre les fichiers `demo.zip/ex4/` : `app/main.py`, `app/models.py`, `app/securite.py`, `tests/test_ex4_ressources.py`.

> **Laboratoire uniquement** : ne pas exposer publiquement. Le mécanisme de blocage des connexions est en mémoire, propre à chaque processus ; il ne remplace pas un rate limiting distribué ou une protection en passerelle.

## Pourquoi cette démonstration ?

**OWASP API4:2023 — Unrestricted Resource Consumption.** Sans limites, un client peut demander d'immenses réponses, soumettre des quantités aberrantes ou multiplier les essais d'authentification.

| Risque | Modification dans EX4 | Résultat attendu |
|---|---|---|
| Listes très volumineuses | `GET /produits` et `GET /mouvements` acceptent `limit` (1 à 100, défaut 20) et `offset` (≥ 0) | `limit=1000` → **422** ; page valide → **200** |
| Mouvements excessifs | `MouvementCreate.quantite` limitée à 10 000 | `quantite=1000000` → **422** |
| Tentatives répétées de connexion | 5 échecs récents pour un identifiant → blocage pendant la fenêtre de 5 minutes | Tentative suivante → **429** et `Retry-After: 300` |

Les règles de limitation de la connexion sont **par identifiant**, pas par adresse IP. Le blocage est simplifié pour la démo : après 5 échecs, même le mot de passe valide est temporairement refusé ; la réussite ne réinitialise pas explicitement un historique d'échecs antérieurs. Une défense réelle doit aussi considérer les risques de déni de service par blocage ciblé, plusieurs instances et la surveillance.

## Lancer sous Windows PowerShell

```powershell
$env:STOCKLINE_JWT_SECRET = ([guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N'))
docker pull christopheutp/stockline-api:0.4
docker run --rm --name stockline-04 -p 127.0.0.1:8004:8000 -e STOCKLINE_JWT_SECRET christopheutp/stockline-api:0.4
```

**Swagger :** <http://localhost:8004/docs> · **Santé :** <http://localhost:8004/sante>. Arrêter avec `Ctrl+C` ; les données SQLite du conteneur seront réinitialisées au prochain lancement.

La même image peut aussi lire son secret depuis un fichier via `STOCKLINE_JWT_SECRET_FILE` (prévoir un montage Docker approprié). Ne commite jamais de vrai secret dans Git.

## Démonstrations comparatives (versions 03 / 04)

Lancer la version 03 dans un autre terminal sur le port 8003, puis utiliser un **nouveau** PowerShell pour les appels ci-dessous :

```powershell
function Get-StocklineToken($port, $identifiant, $motDePasse) {
    $corps = @{ identifiant = $identifiant; mot_de_passe = $motDePasse } | ConvertTo-Json
    (Invoke-RestMethod -Uri "http://localhost:$port/auth/jeton" -Method Post -ContentType 'application/json' -Body $corps).access_token
}
$admin03 = Get-StocklineToken 8003 'admin' 'Admin-Stock-2026'
$admin04 = Get-StocklineToken 8004 'admin' 'Admin-Stock-2026'
$alice04 = Get-StocklineToken 8004 'alice' 'Paris-Stock-2026'
```

### A — Pagination

```powershell
# Version 03 : pas de paramètre de pagination, renvoie toute la liste
curl.exe -i -H "Authorization: Bearer $admin03" "http://localhost:8003/produits?limit=2&offset=2"
# Version 04 : uniquement les produits 3 et 4
curl.exe -i -H "Authorization: Bearer $admin04" "http://localhost:8004/produits?limit=2&offset=2"
# Version 04 : limite maximale dépassée (422)
curl.exe -i -H "Authorization: Bearer $admin04" "http://localhost:8004/produits?limit=1000"
```

### B — Quantité de mouvement plafonnée

```powershell
$corps = '{"produit_id":1,"type":"entree","quantite":1000000}'
curl.exe -i -X POST "http://localhost:8004/mouvements" -H "Authorization: Bearer $alice04" -H "Content-Type: application/json" --data-raw $corps
```

**Résultat attendu : 422** (quantité supérieure à 10 000).

### C — Blocage après cinq échecs d'authentification

```powershell
$uri = 'http://localhost:8004/auth/jeton'
$erreur = @{ identifiant = 'bruno'; mot_de_passe = 'mauvais' } | ConvertTo-Json
1..5 | ForEach-Object {
  $r = Invoke-WebRequest -Uri $uri -Method Post -ContentType 'application/json' -Body $erreur -SkipHttpErrorCheck
  "Tentative $_ : $($r.StatusCode)"
}
$valide = @{ identifiant = 'bruno'; mot_de_passe = 'Lyon-Stock-2026' } | ConvertTo-Json
$r = Invoke-WebRequest -Uri $uri -Method Post -ContentType 'application/json' -Body $valide -SkipHttpErrorCheck
"Compte bloqué : $($r.StatusCode) — Retry-After : $($r.Headers['Retry-After'])"
```

Cette variante utilise **PowerShell 7+** (`-SkipHttpErrorCheck`). Sous Windows PowerShell 5.1, utiliser Swagger ou `curl.exe` pour observer les codes 401 puis 429. Le blocage est **indépendant pour chaque identifiant** : Alice reste accessible.

> Attention : après ces cinq échecs, le compte `bruno` reste bloqué pendant la fenêtre de cinq minutes dans le conteneur 04. Pour recommencer immédiatement la démo, arrêter et recréer le conteneur.

## Identifiants du laboratoire

| Compte | Mot de passe | Rôle |
|---|---|---|
| `alice` | `Paris-Stock-2026` | Gestionnaire Paris |
| `bruno` | `Lyon-Stock-2026` | Gestionnaire Lyon |
| `admin` | `Admin-Stock-2026` | Administrateur |

## Toutes les versions en parallèle

| Démo | Tag Docker | Port hôte | Swagger |
|---|---|---:|---|
| 00 — Initiale | `0.0` | 8000 | <http://localhost:8000/docs> |
| 01 — JWT | `0.1` | 8001 | <http://localhost:8001/docs> |
| 02 — Autorisations | `0.2` | 8002 | <http://localhost:8002/docs> |
| 03 — Propriétés | `0.3` | 8003 | <http://localhost:8003/docs> |
| **04 — Ressources** | **`0.4`** | **8004** | <http://localhost:8004/docs> |

Chaque conteneur écoute sur **8000 à l'intérieur**. Utiliser un nom distinct pour chaque `docker run`. Chaque instance dispose de sa base SQLite propre et de son état de limitation des connexions.

## Tests et publication automatique

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
```

À chaque push sur `04-limitation-ressources`, GitHub Actions lance les tests. Le tag Git `v0.4` déclenche ensuite la construction et la publication de **`christopheutp/stockline-api:0.4`** pour `linux/amd64` et `linux/arm64`, avec le secret GitHub existant `DOCKERHUB_TOKEN`.

```powershell
git switch 03-protection-donnees
git pull origin 03-protection-donnees
git switch -c 04-limitation-ressources
# À ce stade, remplacer les fichiers de la racine du dépôt par ceux de cette archive.
git add .
git commit -m "Demo 04 - Limitation des ressources OWASP API4"
git push -u origin 04-limitation-ressources
# Une fois le workflow de tests validé :
git tag v0.4
git push origin v0.4
```

## Suite de la formation

L'EX5 de `demo.zip` concerne **une passerelle Nginx avec un Dockerfile et un fichier Compose**, et non la protection supplémentaire du code Python. Il pourra constituer une démonstration distincte, séparée du périmètre 00–04.
