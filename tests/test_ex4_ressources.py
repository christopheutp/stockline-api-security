"""Exercice 4 — API4 : consommation de ressources sans limite."""

import pytest

from app import securite
from conftest import entetes


@pytest.fixture(autouse=True)
def compteurs_a_zero():
    """Chaque test démarre sans tentative échouée en mémoire."""
    securite._echecs.clear()
    yield
    securite._echecs.clear()


def test_liste_paginee_par_defaut(client):
    h = entetes(client, "admin")
    assert len(client.get("/produits", headers=h).json()) == 6  # moins de 20 : tout tient
    page = client.get("/produits?limit=2&offset=2", headers=h).json()
    assert [p["id"] for p in page] == [3, 4]


def test_page_trop_grande_refusee(client):
    h = entetes(client, "admin")
    assert client.get("/produits?limit=1000", headers=h).status_code == 422
    assert client.get("/mouvements?limit=1000", headers=h).status_code == 422
    assert client.get("/produits?limit=100", headers=h).status_code == 200


def test_quantite_plafonnee(client):
    reponse = client.post(
        "/mouvements",
        headers=entetes(client, "alice"),
        json={"produit_id": 1, "type": "entree", "quantite": 1_000_000},
    )
    assert reponse.status_code == 422


def _connexion(client, mot_de_passe):
    return client.post("/auth/jeton", json={"identifiant": "bruno", "mot_de_passe": mot_de_passe})


def test_trop_d_echecs_bloque_le_compte_5_minutes(client):
    for _ in range(securite.ECHECS_MAX):
        assert _connexion(client, "mauvais").status_code == 401
    bloque = _connexion(client, "Lyon-Stock-2026")  # même le bon mot de passe
    assert bloque.status_code == 429
    assert bloque.headers["retry-after"] == "300"


def test_le_blocage_ne_touche_que_ce_compte(client):
    for _ in range(securite.ECHECS_MAX):
        _connexion(client, "mauvais")
    alice = client.post("/auth/jeton", json={"identifiant": "alice", "mot_de_passe": "Paris-Stock-2026"})
    assert alice.status_code == 200


def test_quelques_erreurs_ne_bloquent_pas(client):
    for _ in range(securite.ECHECS_MAX - 1):
        _connexion(client, "mauvais")
    assert _connexion(client, "Lyon-Stock-2026").status_code == 200
