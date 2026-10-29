"""Tests fonctionnels de StockLine : ils doivent rester verts à chaque exercice.

Ils travaillent avec le compte « alice » (entrepôt de Paris, produits 1 à 3).
Lancement (depuis le dossier stockline-api, environnement virtuel activé) :
    pytest -v
"""

from conftest import entetes


def test_sante_sans_authentification(client):
    reponse = client.get("/sante")
    assert reponse.status_code == 200
    assert reponse.json()["base_de_donnees"] == "ok"


def test_lister_les_produits_de_paris(client):
    reponse = client.get("/produits", headers=entetes(client, "alice"))
    assert reponse.status_code == 200
    references = [p["reference"] for p in reponse.json()]
    assert "SSD-500" in references


def test_entree_puis_sortie_de_stock(client):
    h = entetes(client, "alice")
    assert client.post("/mouvements", headers=h, json={"produit_id": 1, "type": "entree", "quantite": 20}).status_code == 201
    assert client.post("/mouvements", headers=h, json={"produit_id": 1, "type": "sortie", "quantite": 17}).status_code == 201
    stock = client.get("/stocks/1", headers=h).json()
    assert stock["quantite"] == 3
    assert stock["alerte"] is True


def test_sortie_superieure_au_stock_refusee(client):
    h = entetes(client, "alice")
    reponse = client.post("/mouvements", headers=h, json={"produit_id": 2, "type": "sortie", "quantite": 1})
    assert reponse.status_code == 400
