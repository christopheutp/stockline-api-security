"""StockLine — authentification par jeton JWT (exercice 1).

Les comptes ci-dessous sont ceux du labo. En production, les comptes vivent
dans un annuaire (Amazon Cognito, Microsoft Entra ID), jamais dans le code.
"""

import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

ALGORITHME = "HS256"
DUREE_JETON = timedelta(minutes=15)
ITERATIONS = 600_000  # PBKDF2-SHA256 : valeur recommandée par l'OWASP


def _lire_secret() -> str:
    """Le secret de signature vient de l'environnement, jamais du code."""
    secret = os.environ.get("STOCKLINE_JWT_SECRET", "")
    if len(secret) < 32:
        raise RuntimeError(
            "STOCKLINE_JWT_SECRET absent ou trop court (32 caractères minimum) : démarrage refusé."
        )
    return secret


SECRET = _lire_secret()

# Mots de passe stockés hachés (PBKDF2-SHA256, sel propre à chaque compte).
UTILISATEURS = {
    "alice": {
        "role": "gestionnaire",
        "entrepot": "paris",
        "sel": "4fffb3df6bee94ab0259bd710eecbe0a",
        "empreinte": "b48cae3e023ceebd1612367570e1eea024755b89c418961762a98206befc46e2",
    },
    "bruno": {
        "role": "gestionnaire",
        "entrepot": "lyon",
        "sel": "c6202d7fad512feeb03846cf7f351689",
        "empreinte": "ea8a203a5d7c0622a16e398cb714a8639ab4094f17d8d530df71907bd43bedfc",
    },
    "admin": {
        "role": "admin",
        "entrepot": None,
        "sel": "489de3fc15b06dadf92910208d49d4ea",
        "empreinte": "19bf9de7892868b96b0f680ad03b220ed0dc38a35e25aaea796997ea97158e7e",
    },
}
_SEL_FACTICE = "00" * 16


class Identifiants(BaseModel):
    """Corps de la requête POST /auth/jeton."""

    identifiant: str = Field(min_length=1, max_length=50)
    mot_de_passe: str = Field(min_length=1, max_length=200)


class Jeton(BaseModel):
    """Réponse de POST /auth/jeton."""

    access_token: str
    token_type: str = "bearer"
    expire_dans: int = Field(description="Durée de validité en secondes")


class Utilisateur(BaseModel):
    """Utilisateur authentifié, déduit du jeton."""

    identifiant: str
    role: str
    entrepot: Optional[str]


def verifier_mot_de_passe(identifiant: str, mot_de_passe: str) -> bool:
    """Compare le mot de passe à l'empreinte stockée, en temps constant."""
    compte = UTILISATEURS.get(identifiant)
    # Même calcul si le compte n'existe pas : le temps de réponse ne révèle rien.
    sel = compte["sel"] if compte else _SEL_FACTICE
    calcul = hashlib.pbkdf2_hmac(
        "sha256", mot_de_passe.encode(), bytes.fromhex(sel), ITERATIONS
    ).hex()
    return compte is not None and hmac.compare_digest(calcul, compte["empreinte"])


def creer_jeton(identifiant: str) -> Jeton:
    """Signe un jeton JWT de courte durée pour ce compte."""
    maintenant = datetime.now(timezone.utc)
    charge = {"sub": identifiant, "iat": maintenant, "exp": maintenant + DUREE_JETON}
    return Jeton(
        access_token=jwt.encode(charge, SECRET, algorithm=ALGORITHME),
        expire_dans=int(DUREE_JETON.total_seconds()),
    )


_schema_bearer = HTTPBearer(auto_error=False)


def utilisateur_courant(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_schema_bearer),
) -> Utilisateur:
    """Dépendance FastAPI : exige un jeton valide, sinon 401."""
    refus = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentification requise.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise refus
    try:
        # algorithms est imposé : un jeton signé autrement est refusé.
        charge = jwt.decode(
            credentials.credentials,
            SECRET,
            algorithms=[ALGORITHME],
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError:
        raise refus from None
    compte = UTILISATEURS.get(charge["sub"])
    if compte is None:
        raise refus
    # Le rôle et l'entrepôt viennent du serveur, pas du jeton.
    return Utilisateur(identifiant=charge["sub"], role=compte["role"], entrepot=compte["entrepot"])
