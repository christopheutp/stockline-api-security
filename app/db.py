"""StockLine — couche base de données (SQLAlchemy).

Par défaut, l'application utilise une base SQLite locale (fichier
``stockline.db`` dans le répertoire courant) : aucune configuration
n'est nécessaire pour démarrer. DATABASE_URL permet d'en choisir une autre.
"""

import os
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
    select,
)
from sqlalchemy.orm import Session, declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./stockline.db")

# SQLite impose par défaut un accès mono-thread : on assouplit ce réglage
# car FastAPI peut traiter les requêtes dans plusieurs threads.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


def maintenant_utc() -> datetime:
    """Horodatage UTC (les serveurs travaillent toujours en UTC)."""
    return datetime.now(timezone.utc)


class ProduitDB(Base):
    """Table des produits, chacun rattaché à un entrepôt."""

    __tablename__ = "produits"

    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String(50), unique=True, index=True, nullable=False)
    nom = Column(String(200), nullable=False)
    prix_unitaire = Column(Float, nullable=False)
    prix_achat = Column(Float, nullable=False)
    seuil_alerte = Column(Integer, nullable=False, default=5)
    entrepot = Column(String(20), nullable=False, index=True)
    cree_le = Column(DateTime, default=maintenant_utc, nullable=False)


class MouvementDB(Base):
    """Table des mouvements de stock (entrées et sorties)."""

    __tablename__ = "mouvements"

    id = Column(Integer, primary_key=True, index=True)
    produit_id = Column(Integer, ForeignKey("produits.id"), nullable=False, index=True)
    type = Column(String(10), nullable=False)  # "entree" ou "sortie"
    quantite = Column(Integer, nullable=False)
    commentaire = Column(String(300), nullable=True)
    cree_le = Column(DateTime, default=maintenant_utc, nullable=False)


# Jeu de données de démonstration : deux entrepôts, Paris et Lyon.
PRODUITS_DEMO = [
    ("SSD-500", "Disque SSD 500 Go", 59.90, 31.20, 5, "paris"),
    ("RAM-16", "Barrette mémoire 16 Go", 45.00, 22.50, 10, "paris"),
    ("ECR-27", "Écran 27 pouces", 229.00, 141.00, 3, "paris"),
    ("CLA-FR", "Clavier AZERTY", 24.90, 9.80, 8, "lyon"),
    ("SOU-01", "Souris optique", 12.50, 4.10, 15, "lyon"),
    ("CAB-HD", "Câble HDMI 2 m", 9.90, 2.30, 20, "lyon"),
]


def init_db() -> None:
    """Crée les tables si besoin et charge les données de démonstration si la base est vide."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        if session.execute(select(ProduitDB.id).limit(1)).first() is None:
            for reference, nom, prix, achat, seuil, entrepot in PRODUITS_DEMO:
                session.add(
                    ProduitDB(
                        reference=reference,
                        nom=nom,
                        prix_unitaire=prix,
                        prix_achat=achat,
                        seuil_alerte=seuil,
                        entrepot=entrepot,
                    )
                )
            session.commit()


def get_session():
    """Fournit une session de base de données à chaque requête (dépendance FastAPI)."""
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
