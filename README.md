# StockLine — Démonstration 02 : autorisations (BOLA / BFLA)

**Branche Git : `02-autorisation` · Tag Git : `v0.2` · Image Docker : `christopheutp/stockline-api:0.2` · Port hôte : `8002`**

Cette version reprend les étapes **00 — API non sécurisée** et **01 — authentification JWT**, puis ajoute les contrôles d'accès par rôle et par objet. Les changements applicatifs proviennent des fichiers de l'exercice 2 de `securite-api-2j.zip` : `app/main.py`, `app/securite.py` et `tests/test_ex2_autorisation.py`.

> **Usage pédagogique exclusivement.** Comptes et mots de passe de démonstration, autres faiblesses volontairement conservées. Ne pas exposer sur Internet ni utiliser de données réelles.

## Correspondance OWASP

- **API1:2023 — Broken Object Level Authorization (BOLA)** : un gestionnaire ne doit pouvoir consulter et modifier que les produits, mouvements et stocks de **son entrepôt**. Les ressources d'un autre entrepôt retournent `404`, comme les ressources inexistantes.
- **API5:2023 — Broken Function Level Authorization (BFLA)** : la suppression de produits (`DELETE /produits/{produit_id}`) est réservée au rôle **admin**. Un gestionnaire authentifié reçoit `403 Forbidden`.

L'authentification seule (étape 01) prouvait *qui* était l'utilisateur ; cette étape contrôle *ce qu'il peut faire* et *à quelles données il peut accéder*.

## Lancement sur Windows (PowerShell)

Docker Desktop doit être démarré. La clé JWT est générée localement et transmise au conteneur à l'exécution. Dans un terminal PowerShell :

```powershell
$env:STOCKLINE_JWT_SECRET = ([guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N'))
docker pull christopheutp/stockline-api:0.2
docker run --rm --name stockline-02 -p 127.0.0.1:8002:8000 -e STOCKLINE_JWT_SECRET christopheutp/stockline-api:0.2
```

- Swagger : <http://localhost:8002/docs>
- Santé : <http://localhost:8002/sante>
- Produits : <http://localhost:8002/produits> (nécessite un JWT)

Arrêter avec `Ctrl+C`. La base SQLite du conteneur est indépendante des autres versions ; sans volume Docker, elle est réinitialisée lors de la création d'un nouveau conteneur.

## Démonstration comparative : 01 contre 02

Exécuter l'API `0.1` sur le port **8001** (dans un terminal distinct, avec une clé JWT générée de la même manière), et l'API `0.2` sur **8002**. Les deux bases contiennent les mêmes données initiales.

```powershell
$env:STOCKLINE_JWT_SECRET = ([guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N'))
docker run --rm --name stockline-01 -p 127.0.0.1:8001:8000 -e STOCKLINE_JWT_SECRET christopheutp/stockline-api:0.1
```

Ouvrir un **troisième terminal PowerShell** pour les tests ci-dessous. Les requêtes récupèrent un jeton pour chaque version, car leurs clés peuvent être différentes.

```powershell
function Get-StocklineToken($port, $identifiant, $motDePasse) {
    $corps = @{ identifiant = $identifiant; mot_de_passe = $motDePasse } | ConvertTo-Json
    (Invoke-RestMethod -Uri "http://localhost:$port/auth/jeton" -Method Post -ContentType 'application/json' -Body $corps).access_token
}
$alice01 = Get-StocklineToken 8001 'alice' 'Paris-Stock-2026'
$alice02 = Get-StocklineToken 8002 'alice' 'Paris-Stock-2026'
$admin02 = Get-StocklineToken 8002 'admin' 'Admin-Stock-2026'
```

### A. Contrôle d'accès aux objets — API1 / BOLA

```powershell
# Version 01 : Alice peut consulter un produit de Lyon (faille)
curl.exe -i -H "Authorization: Bearer $alice01" http://localhost:8001/produits/4

# Version 02 : le même accès est refusé (404)
curl.exe -i -H "Authorization: Bearer $alice02" http://localhost:8002/produits/4

# Version 02 : Alice consulte les produits de Paris uniquement
curl.exe -i -H "Authorization: Bearer $alice02" http://localhost:8002/produits
```

### B. Contrôle d'accès aux fonctions — API5 / BFLA

```powershell
# Version 02 : Alice n'est pas autorisée à supprimer (403)
curl.exe -i -X DELETE -H "Authorization: Bearer $alice02" http://localhost:8002/produits/1

# Version 02 : l'admin peut supprimer (204) — modifie seulement la base de 02
curl.exe -i -X DELETE -H "Authorization: Bearer $admin02" http://localhost:8002/produits/1
```

**Attention :** le dernier appel supprime réellement le produit de la base de démonstration de la version 02 ; redémarrer le conteneur pour retrouver le jeu de données initial.

## Comptes de démonstration

| Identifiant | Mot de passe | Rôle | Entrepôt |
|---|---|---|---|
| `alice` | `Paris-Stock-2026` | gestionnaire | Paris |
| `bruno` | `Lyon-Stock-2026` | gestionnaire | Lyon |
| `admin` | `Admin-Stock-2026` | admin | Tous |

## Ports de toutes les versions

| Démonstration | Tag Docker | Port hôte | Swagger |
|---|---|---:|---|
| 00 — Initiale | `0.0` | 8000 | <http://localhost:8000/docs> |
| 01 — JWT | `0.1` | 8001 | <http://localhost:8001/docs> |
| 02 — Autorisations | `0.2` | 8002 | <http://localhost:8002/docs> |
| 03 — Propriétés (à venir) | `0.3` | 8003 | <http://localhost:8003/docs> |
| 04 — Ressources (à venir) | `0.4` | 8004 | <http://localhost:8004/docs> |

Le port **interne** reste toujours `8000`. Chaque conteneur a un nom et un port hôte différents, sans partage de la base SQLite.

## Tests et publication sur Docker Hub

`pytest -q` exécute les tests historiques, JWT et autorisation ; GitHub Actions lance les tests sur les pushes de la branche `02-autorisation`. La publication sur Docker Hub n'est déclenchée que pour le tag Git `v0.2` (ou le workflow manuel sur cette branche) et produit les images `linux/amd64` et `linux/arm64` sous le tag `christopheutp/stockline-api:0.2`.

```powershell
git switch 02-autorisation
git tag v0.2
git push origin v0.2
```

Le secret GitHub `DOCKERHUB_TOKEN` existant est réutilisé.

## Étape suivante

**03 — Protection des propriétés**, en lien avec **API3:2023 — Broken Object Property Level Authorization** : filtrer explicitement les champs acceptés en entrée et ceux renvoyés en sortie via des DTO / schémas Pydantic.
