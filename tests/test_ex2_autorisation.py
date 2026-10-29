"""Exercice 2 — API1 (autorisation par objet) et API5 (autorisation par fonction).

Données de démonstration : produits 1 à 3 à Paris (alice), 4 à 6 à Lyon (bruno).
"""

from conftest import entetes


def _references(reponse):
    return sorted(p["reference"] for p in reponse.json())


def test_chacun_ne_liste_que_son_entrepot(client):
    paris = client.get("/produits", headers=entetes(client, "alice"))
    lyon = client.get("/produits", headers=entetes(client, "bruno"))
    assert _references(paris) == ["ECR-27", "RAM-16", "SSD-500"]
    assert _references(lyon) == ["CAB-HD", "CLA-FR", "SOU-01"]


def test_l_admin_liste_tout(client):
    assert len(client.get("/produits", headers=entetes(client, "admin")).json()) == 6


def test_produit_d_un_autre_entrepot_404(client):
    assert client.get("/produits/4", headers=entetes(client, "alice")).status_code == 404
    assert client.get("/produits/1", headers=entetes(client, "bruno")).status_code == 404
    assert client.get("/stocks/4", headers=entetes(client, "alice")).status_code == 404


def test_meme_reponse_que_pour_un_produit_inexistant(client):
    autre_entrepot = client.get("/produits/4", headers=entetes(client, "alice"))
    inexistant = client.get("/produits/999", headers=entetes(client, "alice"))
    assert autre_entrepot.status_code == inexistant.status_code == 404


def test_mouvement_sur_un_produit_d_un_autre_entrepot_404(client):
    reponse = client.post(
        "/mouvements",
        headers=entetes(client, "alice"),
        json={"produit_id": 4, "type": "entree", "quantite": 5},
    )
    assert reponse.status_code == 404


def test_les_mouvements_de_lyon_sont_invisibles_pour_paris(client):
    client.post("/mouvements", headers=entetes(client, "bruno"), json={"produit_id": 4, "type": "entree", "quantite": 7})
    mouvements_alice = client.get("/mouvements", headers=entetes(client, "alice")).json()
    assert all(m["produit_id"] in (1, 2, 3) for m in mouvements_alice)
    assert len(client.get("/mouvements", headers=entetes(client, "bruno")).json()) == 1


def test_suppression_reservee_a_l_admin(client):
    assert client.delete("/produits/1", headers=entetes(client, "alice")).status_code == 403
    assert client.get("/produits/1", headers=entetes(client, "alice")).status_code == 200
    assert client.delete("/produits/1", headers=entetes(client, "admin")).status_code == 204
    assert client.get("/produits/1", headers=entetes(client, "alice")).status_code == 404
