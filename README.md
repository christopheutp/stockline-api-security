# StockLine API — Démonstrations de sécurité des API

Ce dépôt accompagne une formation de **deux jours sur la sécurité des API REST**, basée sur les recommandations **OWASP API Security Top 10 (2023)**.

L'objectif est de suivre la sécurisation progressive de **StockLine**, une API de gestion de stocks multi-entrepôts. Chaque branche présente une version fonctionnelle de l'API et illustre une ou plusieurs protections ajoutées à l'étape précédente.

> **Usage pédagogique uniquement.** Certaines branches présentent volontairement des vulnérabilités. Elles doivent être exécutées dans un environnement de démonstration isolé, sans exposition publique ni données réelles.

## Technologies

- **Python / FastAPI** : API REST et documentation OpenAPI interactive
- **Pydantic** : validation et contrôle des données
- **SQLAlchemy / SQLite** : persistance et données de démonstration
- **Pytest** : tests fonctionnels et de sécurité
- **Docker** : exécution reproductible des différentes versions
- **GitHub** : suivi des évolutions de l'API

## Parcours des démonstrations

| Branche | Démonstration | Référence OWASP API Security Top 10 (2023) | Version Docker prévue |
| --- | --- | --- | --- |
| `00-api-vulnerable` | Découverte de l'API initiale non sécurisée | État initial présentant plusieurs risques | `0.0` |
| `01-authentification` | Ajout de l'authentification par jetons JWT | **API2:2023** — Broken Authentication | `0.1` |
| `02-autorisation` | Contrôle des rôles et des accès aux ressources | **API1:2023** — Broken Object Level Authorization ; **API5:2023** — Broken Function Level Authorization | `0.2` |
| `03-protection-donnees` | Contrôle des propriétés exposées et modifiables via les schémas Pydantic | **API3:2023** — Broken Object Property Level Authorization | `0.3` |
| `04-limitation-ressources` | Limitation des requêtes et de la consommation de ressources | **API4:2023** — Unrestricted Resource Consumption | `0.4` |

Chaque branche conserve les protections introduites dans les étapes précédentes. Les références OWASP indiquent les **risques étudiés**, et ne constituent pas une certification de conformité ni une garantie de couverture exhaustive.

## Organisation du dépôt

La branche **`main`** sert uniquement de page d'accueil et de guide de navigation.

Pour consulter le code d'une démonstration, sélectionner la branche correspondante dans le menu des branches GitHub, ou cloner le dépôt puis exécuter :

```bash
git switch 00-api-vulnerable
```

Les branches successives contiennent le code Python, les tests, et la documentation propre à chaque étape. Des tags Git permettront également de figer les versions présentées en formation.

## Exécution avec Docker

L'objectif est de distribuer les cinq étapes au moyen d'**un seul dépôt d'images Docker, décliné en tags numérotés**.

Une fois les images publiées, le principe de lancement sera le suivant :

```bash
docker run --rm -p 8000:8000 christopheutp/stockline-api:0.0
```

Pour lancer une étape ultérieure, remplacer `0.0` par `0.1`, `0.2`, `0.3` ou `0.4`.

La documentation interactive de FastAPI sera accessible sur : **http://localhost:8000/docs**.


## Démonstrations et évaluations

Les étapes de sécurisation sont des **démonstrations guidées** : elles permettent de comparer le comportement de l'API avant et après chaque correction. Les **quiz** constituent les évaluations des acquis de la formation.

## Déploiement AWS : démonstration distincte

Le support de formation prévoit également une étape relative à **AWS API Gateway et AWS Lambda**. Cette partie est traitée séparément du parcours principal de versions Docker : elle illustre une architecture de déploiement cloud plutôt qu'une nouvelle version cumulative de l'API.

## Référence

- [OWASP API Security Top 10 — 2023](https://owasp.org/API-Security/editions/2023/en/0x11-t10/)

---

**StockLine API** est un projet de démonstration destiné à l'apprentissage de la sécurité des API.
