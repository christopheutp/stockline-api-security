"""StockLine — schémas Pydantic (validation des entrées et des sorties de l'API).

- les modèles ``...Create`` : ce que le client a le droit d'envoyer (POST) ;
- les modèles de lecture : ce que l'API a le droit de renvoyer.

Exercice 3 : ces deux listes de champs sont écrites explicitement.
Un champ absent d'un modèle n'entre pas (refus 422) et ne sort pas.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TypeMouvement(str, Enum):
    """Un mouvement de stock est soit une entrée, soit une sortie."""

    ENTREE = "entree"
    SORTIE = "sortie"


# ---------------------------------------------------------------------------
# Produits
# ---------------------------------------------------------------------------

class ProduitCreate(BaseModel):
    """Champs qu'un client peut fournir pour créer un produit.

    Pas d'entrepôt : c'est le serveur qui le fixe, d'après le jeton.
    """

    model_config = ConfigDict(extra="forbid")

    reference: str = Field(min_length=1, max_length=50, examples=["SSD-1000"])
    nom: str = Field(min_length=1, max_length=200, examples=["Disque SSD 1 To"])
    prix_unitaire: float = Field(gt=0, examples=[89.90])
    prix_achat: float = Field(gt=0, description="Prix payé au fournisseur", examples=[48.00])
    seuil_alerte: int = Field(default=5, ge=0, description="Stock minimal avant alerte")


class Produit(BaseModel):
    """Champs qu'un client peut lire. Le prix d'achat, donnée interne, n'en fait pas partie."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    reference: str
    nom: str
    prix_unitaire: float
    seuil_alerte: int
    entrepot: str
    cree_le: datetime


# ---------------------------------------------------------------------------
# Mouvements
# ---------------------------------------------------------------------------

class MouvementCreate(BaseModel):
    """Champs qu'un client peut fournir pour enregistrer un mouvement de stock."""

    model_config = ConfigDict(extra="forbid")

    produit_id: int = Field(gt=0)
    type: TypeMouvement
    quantite: int = Field(gt=0, examples=[10])
    commentaire: Optional[str] = Field(default=None, max_length=300)


class Mouvement(MouvementCreate):
    """Mouvement tel que renvoyé par l'API."""

    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: int
    cree_le: datetime


# ---------------------------------------------------------------------------
# Stocks et santé
# ---------------------------------------------------------------------------

class Stock(BaseModel):
    """État du stock d'un produit (calculé à partir des mouvements)."""

    produit_id: int
    reference: str
    nom: str
    quantite: int
    seuil_alerte: int
    alerte: bool = Field(description="True si la quantité est sous le seuil d'alerte")


class Sante(BaseModel):
    """Réponse du health check GET /sante."""

    statut: str
    base_de_donnees: str
    version: str
