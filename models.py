# models.py
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    telephone1 = Column(String, nullable=True)
    telephone2 = Column(String, nullable=True)
    adresse = Column(String, nullable=True)
    pays = Column(String, nullable=True)
    ville = Column(String, nullable=True)
    photo = Column(String, nullable=True)
    facebook = Column(String, nullable=True)
    whatsapp = Column(String, nullable=True)
    profession = Column(String, nullable=True)
    role = Column(String, default="user")  # "user" ou "admin"

    # Relations
    commandes = relationship("Commande", back_populates="user")


class Carte(Base):
    __tablename__ = "cartes"

    id = Column(Integer, primary_key=True, index=True)
    titre = Column(String, nullable=False)
    description = Column(String, nullable=True)
    prix = Column(Integer, nullable=False)
    disponible = Column(Boolean, default=True)
    image = Column(String, nullable=True)  # URL / path optionnel

    # Relations
    commandes = relationship("Commande", back_populates="carte")


class Commande(Base):
    __tablename__ = "commandes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    carte_id = Column(Integer, ForeignKey("cartes.id"))
    status = Column(String, default="en attente")  # "en attente", "imprimée", "annulée", etc.
    created_at = Column(String, nullable=True)

    # Relations
    user = relationship("User", back_populates="commandes")
    carte = relationship("Carte", back_populates="commandes")