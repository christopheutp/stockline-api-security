# StockLine — Démonstration 03 : protection des propriétés (OWASP API3:2023)

**Branche Git : `03-protection-donnees` · Tag Git : `v0.3` · Docker : `christopheutp/stockline-api:0.3` · Port hôte : `8003`**

Cette branche dérive de `02-autorisation` et ajoute les fichiers officiels de l'exercice 3 : `app/main.py`, `app/models.py`, `tests/test_ex3_proprietes.py`. Les protections JWT et les contrôles par rôle / entrepôt des étapes 01 et 02 restent actifs.

> **Laboratoire uniquement** : utilisateurs et mots de passe fictifs, vulnérabilités résiduelles volontaires. Ne pas exposer cette API à Internet et ne pas utiliser de données réelles.

## Objectif OWASP

**API3:2023 — Broken Object Property Level Authorization**. L'API doit contrôler **quelles propriétés le client peut modifier** (mass assignment) et **quelles propriétés peuvent être révélées** en sortie (excessive data exposure).

- `ProduitCreate` énumère explicitement les champs autorisés en entrée et interdit les champs supplémentaires (`extra="forbid"`) : un client ne peut pas forcer `entrepot`, `id` ou des champs internes.
- `Produit` (modèle de sortie) ne révèle pas `prix_achat`, information interne, tout en conservant les champs publics.
- Les contraintes Pydantic valident les prix, quantités, longueurs et formats.
- Les contrôles d'autorisation de la version 02 restent nécessaires : les DTO ne remplacent pas BOLA/BFLA.

## Lancer la version 03 sous Windows PowerShell

```powershell
$env:STOCKLINE_JWT_SECRET = ([guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N'))
docker pull christopheutp/stockline-api:0.3
docker run --rm --name stockline-03 -p 127.0.0.1:8003:8000 -e STOCKLINE_JWT_SECRET christopheutp/stockline-api:0.3
```

Swagger : <http://localhost:8003/docs> · Santé : <http://localhost:8003/sante>. Pour arrêter : `Ctrl+C`. La base SQLite est éphémère et isolée par conteneur.

## Comparer les versions 02 et 03

Lancer la version 02 sur le port 8002 dans **un autre terminal** (avec sa variable `STOCKLINE_JWT_SECRET` définie). Dans un troisième PowerShell, demander un JWT à chaque API :

```powershell
function Get-StocklineToken($port, $identifiant, $motDePasse) {
    $corps = @{ identifiant = $identifiant; mot_de_passe = $motDePasse } | ConvertTo-Json
    (Invoke-RestMethod -Uri "http://localhost:$port/auth/jeton" -Method Post -ContentType 'application/json' -Body $corps).access_token
}
$alice02 = Get-StocklineToken 8002 'alice' 'Paris-Stock-2026'
$alice03 = Get-StocklineToken 8003 'alice' 'Paris-Stock-2026'
```

### 1. Vérifier la confidentialité en lecture

```powershell
# Sur 02, inspecter si le champ interne prix_achat est présent
curl.exe -s -H "Authorization: Bearer $alice02" http://localhost:8002/produits/1
# Sur 03, le champ prix_achat ne doit plus apparaître
curl.exe -s -H "Authorization: Bearer $alice03" http://localhost:8003/produits/1
```

### 2. Vérifier les propriétés autorisées en écriture

Consulter dans Swagger les champs acceptés par `POST /produits` en 02 et 03. Avec l'étape 03, envoyer un champ supplémentaire (`entrepot`) provoque une erreur de validation `422` :

```powershell
$payload = '{"reference":"DEMO-03","nom":"Produit test","prix_unitaire":10,"prix_achat":5,"seuil_alerte":2,"entrepot":"Lyon"}'
curl.exe -i -X POST http://localhost:8003/produits -H "Authorization: Bearer $alice03" -H "Content-Type: application/json" --data-raw $payload
```

**Important :** le prix d'achat est accepté à la création (champ métier) mais masqué dans les réponses. L'entrepôt est imposé côté serveur selon le JWT.

## Comptes de laboratoire

| Identifiant | Mot de passe | Profil |
|---|---|---|
| `alice` | `Paris-Stock-2026` | Gestionnaire Paris |
| `bruno` | `Lyon-Stock-2026` | Gestionnaire Lyon |
| `admin` | `Admin-Stock-2026` | Administrateur |

## Plusieurs versions sur le même ordinateur

| Version | Tag Docker | Port hôte | Swagger |
|---|---|---:|---|
| 00 — Vulnérable | `0.0` | 8000 | <http://localhost:8000/docs> |
| 01 — JWT | `0.1` | 8001 | <http://localhost:8001/docs> |
| 02 — Autorisations | `0.2` | 8002 | <http://localhost:8002/docs> |
| **03 — Propriétés** | **`0.3`** | **8003** | <http://localhost:8003/docs> |
| 04 — Ressources (future) | `0.4` | 8004 | <http://localhost:8004/docs> |

Tous les conteneurs utilisent le port **8000 à l'intérieur** et un nom différent. Les images 00 à 02 doivent avoir été publiées auparavant.

## Tests et publication automatique

```powershell
python -m pip install -r requirements.txt
pytest -q
```

GitHub Actions lance les tests sur chaque push de la branche `03-protection-donnees`. Le push du tag Git `v0.3` déclenche, après réussite des tests, la publication Docker Hub `christopheutp/stockline-api:0.3` pour `linux/amd64` et `linux/arm64`. Le secret GitHub `DOCKERHUB_TOKEN` est réutilisé.

```powershell
git switch 03-protection-donnees
git tag v0.3
git push origin v0.3
```

## Prochaine démonstration

**04 — Limitation des ressources** : OWASP API4:2023 — Unrestricted Resource Consumption.
