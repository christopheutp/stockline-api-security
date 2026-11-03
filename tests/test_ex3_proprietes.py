"""Exercice 3 — API3 : autorisation au niveau des propriétés (champs) des objets."""

from conftest import entetes

CHAMPS_PUBLICS = {"id", "reference", "nom", "prix_unitaire", "seuil_alerte", "entrepot", "cree_le"}
NOUVEAU = {"reference": "SSD-1000", "nom": "Disque SSD 1 To", "prix_unitaire": 89.90, "prix_achat": 48.00}


def test_le_prix_d_achat_ne_sort_pas(client):
    detail = client.get("/produits/1", headers=entetes(client, "alice")).json()
    liste = client.get("/produits", headers=entetes(client, "admin")).json()
    assert set(detail) == CHAMPS_PUBLICS
    assert all(set(p) == CHAMPS_PUBLICS for p in liste)


def test_l_entrepot_est_fixe_par_le_serveur(client):
    reponse = client.post("/produits", headers=entetes(client, "alice"), json=NOUVEAU)
    assert reponse.status_code == 201, reponse.text
    cree = reponse.json()
    assert cree["entrepot"] == "paris"
    assert set(cree) == CHAMPS_PUBLICS
    assert client.get(f"/produits/{cree['id']}", headers=entetes(client, "bruno")).status_code == 404


def test_un_champ_non_prevu_est_refuse(client):
    for champ, valeur in [("entrepot", "lyon"), ("id", 99), ("cree_le", "2020-01-01T00:00:00")]:
        reponse = client.post("/produits", headers=entetes(client, "alice"), json={**NOUVEAU, champ: valeur})
        assert reponse.status_code == 422, champ
    reponse = client.post(
        "/mouvements",
        headers=entetes(client, "alice"),
        json={"produit_id": 1, "type": "entree", "quantite": 5, "id": 1},
    )
    assert reponse.status_code == 422


def test_seul_un_gestionnaire_cree_des_produits(client):
    assert client.post("/produits", headers=entetes(client, "admin"), json=NOUVEAU).status_code == 403
