"""StockLine v2 — API d'inventaire multi-entrepôts (produits, mouvements, stocks).

Exercice 1 : toutes les routes, sauf /sante et /auth/jeton, exigent un jeton.
Exercice 2 : un gestionnaire ne voit que son entrepôt ; supprimer est réservé à l'admin.
Exercice 3 : l'API choisit les champs qui entrent et qui sortent (models.py).
Exercice 4 : listes paginées et plafonnées, tentatives de connexion limitées.

Lancement en local :
    uvicorn app.main:app --reload

Documentation interactive : http://127.0.0.1:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app import models, securite
from app.db import MouvementDB, ProduitDB, get_session, init_db
from app.securite import Utilisateur, exiger_role, utilisateur_courant

VERSION = "2.4.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Au démarrage : création des tables et données de démonstration si nécessaire."""
    init_db()
    yield


app = FastAPI(
    title="StockLine",
    description="API d'inventaire multi-entrepôts — fil rouge du cursus Administrateur Cloud",
    version=VERSION,
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Santé
# ---------------------------------------------------------------------------

@app.get("/sante", response_model=models.Sante, tags=["exploitation"])
def sante(session: Session = Depends(get_session)) -> models.Sante:
    """Health check : l'API répond-elle et la base est-elle joignable ?"""
    try:
        session.execute(text("SELECT 1"))
        etat_bdd = "ok"
    except Exception:  # noqa: BLE001 — on veut un diagnostic, pas un crash
        etat_bdd = "indisponible"
    return models.Sante(statut="ok", base_de_donnees=etat_bdd, version=VERSION)


# ---------------------------------------------------------------------------
# Authentification (exercice 1)
# ---------------------------------------------------------------------------

@app.post("/auth/jeton", response_model=securite.Jeton, tags=["authentification"])
def obtenir_jeton(identifiants: securite.Identifiants) -> securite.Jeton:
    """Échange un identifiant et un mot de passe contre un jeton de 15 minutes."""
    securite.controler_tentatives(identifiants.identifiant)
    if not securite.verifier_mot_de_passe(identifiants.identifiant, identifiants.mot_de_passe):
        securite.noter_echec(identifiants.identifiant)
        # Même message que le compte existe ou non.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiant ou mot de passe incorrect.",
        )
    return securite.creer_jeton(identifiants.identifiant)


@app.get("/moi", response_model=Utilisateur, tags=["authentification"])
def moi(utilisateur: Utilisateur = Depends(utilisateur_courant)) -> Utilisateur:
    """Renvoie l'utilisateur correspondant au jeton."""
    return utilisateur


# ---------------------------------------------------------------------------
# Produits
# ---------------------------------------------------------------------------

@app.get("/produits", response_model=list[models.Produit], tags=["produits"])
def lister_produits(
    limit: int = Query(20, ge=1, le=100, description="Nombre d'éléments (100 au plus)"),
    offset: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    session: Session = Depends(get_session),
    utilisateur: Utilisateur = Depends(utilisateur_courant),
) -> list[ProduitDB]:
    """Liste les produits de l'entrepôt de l'utilisateur (tous pour l'admin), page par page."""
    requete = select(ProduitDB).order_by(ProduitDB.id)
    if utilisateur.role != "admin":
        requete = requete.where(ProduitDB.entrepot == utilisateur.entrepot)
    return list(session.execute(requete.limit(limit).offset(offset)).scalars())


@app.post(
    "/produits",
    response_model=models.Produit,
    status_code=status.HTTP_201_CREATED,
    tags=["produits"],
)
def creer_produit(
    produit: models.ProduitCreate,
    session: Session = Depends(get_session),
    utilisateur: Utilisateur = Depends(exiger_role("gestionnaire")),
) -> ProduitDB:
    """Crée un produit dans l'entrepôt du gestionnaire. La référence doit être unique."""
    existant = session.execute(
        select(ProduitDB).where(ProduitDB.reference == produit.reference)
    ).scalar_one_or_none()
    if existant is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"La référence '{produit.reference}' existe déjà.",
        )
    nouveau = ProduitDB(**produit.model_dump(), entrepot=utilisateur.entrepot)
    session.add(nouveau)
    session.commit()
    session.refresh(nouveau)
    return nouveau


def _produit_autorise(session: Session, produit_id: int, utilisateur: Utilisateur) -> ProduitDB:
    """Renvoie le produit s'il existe ET si l'utilisateur y a droit, sinon 404.

    Un produit d'un autre entrepôt donne la même réponse qu'un produit
    inexistant : l'API ne révèle pas ce qui existe ailleurs.
    """
    produit = session.get(ProduitDB, produit_id)
    autorise = produit is not None and (
        utilisateur.role == "admin" or produit.entrepot == utilisateur.entrepot
    )
    if not autorise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Produit {produit_id} introuvable.",
        )
    return produit


@app.get("/produits/{produit_id}", response_model=models.Produit, tags=["produits"])
def lire_produit(
    produit_id: int,
    session: Session = Depends(get_session),
    utilisateur: Utilisateur = Depends(utilisateur_courant),
) -> ProduitDB:
    """Renvoie un produit par son identifiant."""
    return _produit_autorise(session, produit_id, utilisateur)


@app.delete(
    "/produits/{produit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["produits"],
)
def supprimer_produit(
    produit_id: int,
    session: Session = Depends(get_session),
    utilisateur: Utilisateur = Depends(exiger_role("admin")),
) -> None:
    """Supprime un produit et ses mouvements (admin uniquement)."""
    produit = _produit_autorise(session, produit_id, utilisateur)
    session.query(MouvementDB).filter(MouvementDB.produit_id == produit.id).delete()
    session.delete(produit)
    session.commit()


# ---------------------------------------------------------------------------
# Mouvements
# ---------------------------------------------------------------------------

def _quantite_en_stock(session: Session, produit_id: int) -> int:
    """Calcule le stock courant : somme des entrées moins somme des sorties."""
    total = 0
    lignes = session.execute(
        select(MouvementDB.type, func.sum(MouvementDB.quantite))
        .where(MouvementDB.produit_id == produit_id)
        .group_by(MouvementDB.type)
    ).all()
    for type_mouvement, somme in lignes:
        if type_mouvement == models.TypeMouvement.ENTREE.value:
            total += int(somme)
        else:
            total -= int(somme)
    return total


@app.get("/mouvements", response_model=list[models.Mouvement], tags=["mouvements"])
def lister_mouvements(
    limit: int = Query(20, ge=1, le=100, description="Nombre d'éléments (100 au plus)"),
    offset: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    session: Session = Depends(get_session),
    utilisateur: Utilisateur = Depends(utilisateur_courant),
) -> list[MouvementDB]:
    """Liste les mouvements des produits de l'entrepôt de l'utilisateur, page par page."""
    requete = select(MouvementDB).order_by(MouvementDB.id)
    if utilisateur.role != "admin":
        requete = requete.join(ProduitDB).where(ProduitDB.entrepot == utilisateur.entrepot)
    return list(session.execute(requete.limit(limit).offset(offset)).scalars())


@app.post(
    "/mouvements",
    response_model=models.Mouvement,
    status_code=status.HTTP_201_CREATED,
    tags=["mouvements"],
)
def creer_mouvement(
    mouvement: models.MouvementCreate,
    session: Session = Depends(get_session),
    utilisateur: Utilisateur = Depends(utilisateur_courant),
) -> MouvementDB:
    """Enregistre un mouvement. Une sortie ne peut pas dépasser le stock courant."""
    produit = _produit_autorise(session, mouvement.produit_id, utilisateur)
    if mouvement.type == models.TypeMouvement.SORTIE:
        stock = _quantite_en_stock(session, produit.id)
        if mouvement.quantite > stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuffisant : {stock} en stock, sortie de {mouvement.quantite}.",
            )
    nouveau = MouvementDB(
        produit_id=produit.id,
        type=mouvement.type.value,
        quantite=mouvement.quantite,
        commentaire=mouvement.commentaire,
    )
    session.add(nouveau)
    session.commit()
    session.refresh(nouveau)
    return nouveau


# ---------------------------------------------------------------------------
# Stocks
# ---------------------------------------------------------------------------

@app.get("/stocks/{produit_id}", response_model=models.Stock, tags=["stocks"])
def lire_stock(
    produit_id: int,
    session: Session = Depends(get_session),
    utilisateur: Utilisateur = Depends(utilisateur_courant),
) -> models.Stock:
    """Renvoie l'état du stock d'un produit, avec indicateur d'alerte."""
    produit = _produit_autorise(session, produit_id, utilisateur)
    quantite = _quantite_en_stock(session, produit.id)
    return models.Stock(
        produit_id=produit.id,
        reference=produit.reference,
        nom=produit.nom,
        quantite=quantite,
        seuil_alerte=produit.seuil_alerte,
        alerte=quantite < produit.seuil_alerte,
    )
