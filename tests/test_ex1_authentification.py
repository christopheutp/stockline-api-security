"""Exercice 1 — API2 : authentification. Ces tests prouvent les protections."""

from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app import securite
from conftest import entetes

ROUTES_PROTEGEES = [
    ("get", "/moi"),
    ("get", "/produits"),
    ("get", "/produits/1"),
    ("delete", "/produits/1"),
    ("get", "/mouvements"),
    ("get", "/stocks/1"),
]


@pytest.mark.parametrize("methode,route", ROUTES_PROTEGEES)
def test_sans_jeton_401(client, methode, route):
    reponse = getattr(client, methode)(route)
    assert reponse.status_code == 401
    assert reponse.headers["www-authenticate"] == "Bearer"


def test_creation_sans_jeton_401(client):
    reponse = client.post("/mouvements", json={"produit_id": 1, "type": "entree", "quantite": 5})
    assert reponse.status_code == 401


def test_mauvais_mot_de_passe_meme_message_que_compte_inconnu(client):
    mauvais = client.post("/auth/jeton", json={"identifiant": "alice", "mot_de_passe": "faux"})
    inconnu = client.post("/auth/jeton", json={"identifiant": "zoe", "mot_de_passe": "faux"})
    assert mauvais.status_code == inconnu.status_code == 401
    assert mauvais.json() == inconnu.json()


def test_jeton_valide_identifie_l_utilisateur(client):
    reponse = client.get("/moi", headers=entetes(client, "alice"))
    assert reponse.status_code == 200
    assert reponse.json() == {"identifiant": "alice", "role": "gestionnaire", "entrepot": "paris"}


def test_jeton_de_courte_duree(client):
    reponse = client.post("/auth/jeton", json={"identifiant": "bruno", "mot_de_passe": "Lyon-Stock-2026"})
    assert reponse.json()["expire_dans"] <= 15 * 60


def _jeton(secret, expiration):
    return jwt.encode({"sub": "alice", "exp": expiration}, secret, algorithm="HS256")


def test_jeton_expire_refuse(client):
    passe = datetime.now(timezone.utc) - timedelta(minutes=1)
    jeton = _jeton(securite.SECRET, passe)
    assert client.get("/moi", headers={"Authorization": f"Bearer {jeton}"}).status_code == 401


def test_jeton_signe_avec_un_autre_secret_refuse(client):
    futur = datetime.now(timezone.utc) + timedelta(minutes=5)
    jeton = _jeton("un-autre-secret-de-32-caracteres-minimum", futur)
    assert client.get("/moi", headers={"Authorization": f"Bearer {jeton}"}).status_code == 401


def test_demarrage_refuse_sans_secret(monkeypatch):
    monkeypatch.setenv("STOCKLINE_JWT_SECRET", "trop-court")
    with pytest.raises(RuntimeError):
        securite._lire_secret()
