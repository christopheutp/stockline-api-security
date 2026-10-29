"""Configuration commune des tests : base SQLite dédiée, recréée pour chaque test.

Les variables d'environnement DOIVENT être définies AVANT l'import de
l'application, car app/db.py lit DATABASE_URL au moment de l'import.
"""

import os
import pathlib

TEST_DB = "test_stockline.db"
os.environ["DATABASE_URL"] = f"sqlite:///./{TEST_DB}"
# Secret réservé aux tests (utilisé à partir de l'exercice 1).
os.environ.setdefault("STOCKLINE_JWT_SECRET", "secret-de-test-uniquement-0123456789abcdef")

import pytest
from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app

# Comptes de démonstration du labo (créés à l'exercice 1).
MOTS_DE_PASSE = {
    "alice": "Paris-Stock-2026",
    "bruno": "Lyon-Stock-2026",
    "admin": "Admin-Stock-2026",
}
_jetons = {}


@pytest.fixture()
def client():
    """Client de test sur une base neuve (données de démonstration rechargées)."""
    Base.metadata.drop_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client


def entetes(client, identifiant):
    """En-têtes d'authentification de ce compte.

    Avant l'exercice 1, l'API n'a pas de route /auth/jeton : on renvoie
    des en-têtes vides. Le jeton obtenu est réutilisé d'un test à l'autre.
    """
    if identifiant not in _jetons:
        reponse = client.post(
            "/auth/jeton",
            json={"identifiant": identifiant, "mot_de_passe": MOTS_DE_PASSE[identifiant]},
        )
        if reponse.status_code in (404, 405):
            return {}
        assert reponse.status_code == 200, reponse.text
        _jetons[identifiant] = reponse.json()["access_token"]
    return {"Authorization": f"Bearer {_jetons[identifiant]}"}


def pytest_sessionfinish(session, exitstatus):
    """Supprime le fichier de base de test à la fin des tests."""
    engine.dispose()
    pathlib.Path(TEST_DB).unlink(missing_ok=True)
