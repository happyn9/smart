# crud.py
from sqlalchemy.orm import Session
import models, schemas, utils
from datetime import datetime

# ----------------- USERS -----------------
def create_user(db: Session, user: schemas.UserCreate):
    hashed_pw = utils.hash_password(user.password)
    db_user = models.User(
        name=user.name,
        email=user.email,
        hashed_password=hashed_pw,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def update_user(db: Session, user_id: int, update: schemas.UserUpdate):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None
    for key, value in update.dict(exclude_unset=True).items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user

# ----------------- CARTES -----------------
def create_carte(db: Session, carte: schemas.CarteCreate):
    db_carte = models.Carte(**carte.dict())
    db.add(db_carte)
    db.commit()
    db.refresh(db_carte)
    return db_carte

def get_cartes(db: Session):
    return db.query(models.Carte).all()

def get_carte(db: Session, carte_id: int):
    return db.query(models.Carte).filter(models.Carte.id == carte_id).first()

def update_carte(db: Session, carte_id: int, data: dict):
    carte = get_carte(db, carte_id)
    if not carte:
        return None
    for key, value in data.items():
        setattr(carte, key, value)
    db.commit()
    db.refresh(carte)
    return carte

# ----------------- COMMANDES -----------------
def create_commande(db: Session, commande: schemas.CommandeCreate):
    db_commande = models.Commande(
        user_id=commande.user_id,
        carte_id=commande.carte_id,
        status="en attente",
        created_at=datetime.utcnow().isoformat()
    )
    db.add(db_commande)
    db.commit()
    db.refresh(db_commande)
    return db_commande

def get_commandes(db: Session, user_id: int = None):
    query = db.query(models.Commande)
    if user_id:
        query = query.filter(models.Commande.user_id == user_id)
    return query.all()

def update_commande_status(db: Session, commande_id: int, status: str):
    commande = db.query(models.Commande).filter(models.Commande.id == commande_id).first()
    if not commande:
        return None
    commande.status = status
    db.commit()
    db.refresh(commande)
    return commande

def delete_commande(db: Session, commande_id: int):
    commande = db.query(models.Commande).filter(models.Commande.id == commande_id).first()
    if not commande:
        return None
    db.delete(commande)
    db.commit()
    return commande     