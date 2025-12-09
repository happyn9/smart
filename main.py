# main.py
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Body
from typing import Optional
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import shutil, os, qrcode, io, base64
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi.responses import HTMLResponse
from config import settings



import models, schemas, crud, utils, database, email_sender

app = FastAPI()

origins = [
    "https://smart-card.easytechcongo.com",
    "https://smart-10.onrender.com",
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- DB ---------------- #
models.Base.metadata.create_all(bind=database.engine)


FRONTEND_URL = settings.FRONTEND_URL
BACKEND_URL = settings.BACKEND_URL
ADMIN_EMAIL = settings.ADMIN_EMAIL
EMAIL_ADDRESS = settings.EMAIL_ADDRESS
EMAIL_PASSWORD = settings.EMAIL_PASSWORD
SENDGRID_API_KEY = settings.SENDGRID_API_KEY
SQLALCHEMY_DATABASE_URL = settings.SQLALCHEMY_DATABASE_URL



def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------- Auth ---------------- #
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, utils.SECRET_KEY, algorithms=[utils.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token invalide")
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide")

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return user

# ---------------- Uploads ---------------- #
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Sert les fichiers statiques pour que les images restent accessibles
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ---------------- Routes ---------------- #
@app.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    new_user = crud.create_user(db, user)
    
    # Envoi email de bienvenue
    email_sender.send_account_creation_email(new_user.name, new_user.email)
    
    return new_user

@app.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, user.email)
    if not db_user or not utils.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    
    token = utils.create_access_token({"sub": str(db_user.id)})
    
    # Envoi notification de connexion
    email_sender.send_login_notification_email(db_user.name, db_user.email)
    
    return {"access_token": token, "token_type": "bearer", "name": db_user.name, "role": db_user.role}

@app.get("/profile/me", response_model=schemas.UserOut)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.put("/profile/{user_id}", response_model=schemas.UserOut)
def update_profile(
    user_id: int,
    name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    adresse: Optional[str] = Form(None),
    pays: Optional[str] = Form(None),
    ville: Optional[str] = Form(None),
    telephone1: Optional[str] = Form(None),
    telephone2: Optional[str] = Form(None),
    facebook: Optional[str] = Form(None),
    whatsapp: Optional[str] = Form(None),
    profession: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès interdit")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    for field, value in {
        "name": name,
        "email": email,
        "adresse": adresse,
        "pays": pays,
        "ville": ville,
        "telephone1": telephone1,
        "telephone2": telephone2,
        "facebook": facebook,
        "whatsapp": whatsapp,
        "profession": profession
    }.items():
        if value is not None:
            setattr(user, field, value)
    if photo:
        file_ext = os.path.splitext(photo.filename)[1]
        file_name = f"user_{user.id}{file_ext}"
        file_path = UPLOAD_DIR / file_name
        with open(file_path, "wb") as f:
            shutil.copyfileobj(photo.file, f)
        user.photo = f"uploads/{file_name}"

    db.commit()
    db.refresh(user)
    return user

@app.put("/profile/{user_id}/password")
def change_password(user_id: int, passwords: schemas.PasswordChange, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    if not utils.verify_password(passwords.current, user.hashed_password):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")
    user.hashed_password = utils.get_password_hash(passwords.new)
    db.commit()
    return {"msg": "Mot de passe changé avec succès"}



@app.get("/profile/{user_id}/qrcode")
def generate_qr(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    # Lien qui sera ouvert quand on scanne le QR
    react_url = f"{FRONTEND_URL}/user/{user.id}"

    # Génération du QR
    qr = qrcode.make(react_url)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return {"qrcode": f"data:image/png;base64,{qr_str}", "link": react_url}

@app.get("/user/{user_id}", response_model=schemas.UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    if user.photo and not user.photo.startswith("http"):
        user.photo = f"{BACKEND_URL}/{user.photo}"

    return user

# Password reset (same logic que tu avais)
from datetime import datetime, timedelta
from jose import jwt as jose_jwt

RESET_SECRET_KEY = utils.SECRET_KEY
RESET_ALGORITHM = "HS256"
RESET_EXPIRE_MINUTES = 30

@app.post("/forgot-password")
def forgot_password(email: str = Body(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        return {"msg": "Si cet email existe, un lien de réinitialisation a été envoyé."}

    expire = datetime.utcnow() + timedelta(minutes=RESET_EXPIRE_MINUTES)
    reset_token = jose_jwt.encode({"sub": str(user.id), "exp": expire}, RESET_SECRET_KEY, algorithm=RESET_ALGORITHM)

    reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}"

    subject = "Réinitialisation du mot de passe 🔑"
    body = f"Bonjour {user.name},\n\nPour réinitialiser votre mot de passe, cliquez sur ce lien :\n{reset_link}\n\nCe lien expire dans {RESET_EXPIRE_MINUTES} minutes."
    email_sender.send_email(user.email, subject, body)

    return {"msg": "Vérifie ta boîte mail."}

@app.post("/reset-password")
def reset_password(
    body: dict = Body(...),
    db: Session = Depends(get_db)
):
    token = body.get("token")
    new_password = body.get("new_password")

    if not token or not new_password:
        raise HTTPException(status_code=400, detail="Token ou mot de passe manquant")

    try:
        payload = jose_jwt.decode(token, RESET_SECRET_KEY, algorithms=[RESET_ALGORITHM])
        user_id = int(payload.get("sub"))
    except ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Le lien a expiré.")
    except JWTError:
        raise HTTPException(status_code=400, detail="Lien invalide.")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    user.hashed_password = utils.get_password_hash(new_password)
    db.commit()
    return {"msg": "Mot de passe réinitialisé avec succès"}


# ---------------- Cartes ----------------
@app.post("/cartes", response_model=schemas.CarteOut)
def create_carte(carte: schemas.CarteCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès interdit")
    return crud.create_carte(db, carte)

@app.get("/cartes", response_model=list[schemas.CarteOut])
def list_cartes(db: Session = Depends(get_db)):
    return crud.get_cartes(db)

@app.put("/cartes/{carte_id}", response_model=schemas.CarteOut)
def update_carte(carte_id: int, data: schemas.CarteCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès interdit")
    updated = crud.update_carte(db, carte_id, data.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Carte introuvable")
    return updated

# ----------------- COMMANDES -----------------
@app.post("/commandes", response_model=schemas.CommandeOut)
def create_commande(commande: schemas.CommandeCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Assure que l'utilisateur commande pour lui-même
    if current_user.role != "user" and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès interdit")
    if current_user.id != commande.user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Vous ne pouvez commander pour un autre user")
    return crud.create_commande(db, commande)

@app.get("/commandes", response_model=list[schemas.CommandeOut])
def list_commandes(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role == "admin":
        return crud.get_commandes(db)
    else:
        return crud.get_commandes(db, user_id=current_user.id)

@app.put("/commandes/{commande_id}/status", response_model=schemas.CommandeOut)
def update_status(commande_id: int, status: str = Body(...), current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès interdit")
    updated = crud.update_commande_status(db, commande_id, status)
    if not updated:
        raise HTTPException(status_code=404, detail="Commande introuvable")
    return updated


ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")

@app.post("/profile/{user_id}/order_card", response_model=schemas.CommandeOut)
def order_card(
    user_id: int,
    carte_id: int = Body(..., embed=True),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # --- Sécurité ---
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Accès interdit")

    carte = db.query(models.Carte).filter(
        models.Carte.id == carte_id,
        models.Carte.disponible == True
    ).first()
    if not carte:
        raise HTTPException(status_code=404, detail="Carte introuvable ou indisponible")

    # --- Création de la commande ---
    new_commande = models.Commande(
        user_id=user_id,
        carte_id=carte_id,
        status="en attente",
        created_at=datetime.utcnow().isoformat()
    )
    db.add(new_commande)
    db.commit()
    db.refresh(new_commande)

    # --- Génération du QR code ---
    react_url = f"{FRONTEND_URL}/user/{current_user.id}"
    qr = qrcode.make(react_url)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    qr_image = f"data:image/png;base64,{qr_base64}"

    # --- Email HTML complet avec QR visible et téléchargeable ---
    subject = f"Nouvelle commande #{new_commande.id}"
    body = f"""
    <html>
      <body style="font-family: Arial, sans-serif;">
        <h3>Bonjour @Rinedi 👋</h3>
        <p>Une nouvelle commande a été passée :</p>

        <ul>
          <li><strong>Nom :</strong> {current_user.name}</li>
          <li><strong>Email :</strong> {current_user.email}</li>
          <li><strong>Carte :</strong> {carte.titre}</li>
          <li><strong>Prix :</strong> {carte.prix} €</li>
        </ul>

        <p>Voici le QR code associé à cette commande :</p>

        <a href="{qr_image}" download="QRCode_{current_user.name}.png">
          <img src="{qr_image}" alt="QR Code de {current_user.name}" style="width:150px;height:150px;border:1px solid #ccc;padding:5px;border-radius:8px;"/>
        </a>

        <p style="margin-top:15px;">
          🔗 Vous pouvez aussi <a href="{FRONTEND_URL}/commandes/{new_commande.id}/view">voir la carte complète</a> et l’imprimer depuis le navigateur.
        </p>

        <p>Merci 🙏</p>
      </body>
    </html>
    """

    # --- Envoi à l'admin ---
    email_sender.send_email(ADMIN_EMAIL, subject, body, html=True)

    return new_commande



# ---------------- Admin: aperçu imprimable + marquage imprimée ----------------
@app.get("/admin/commandes", response_model=list[schemas.CommandeOut])
def admin_list_commandes(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès interdit")
    return crud.get_commandes(db)

@app.get("/admin/commandes/{commande_id}/print", response_class=HTMLResponse)
def admin_print_commande(commande_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Retourne une page HTML prête à imprimer (aperçu de la carte avec QR).
    Cette route marque aussi la commande comme 'imprimée'.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Accès interdit")

    commande = db.query(models.Commande).filter(models.Commande.id == commande_id).first()
    if not commande:
        raise HTTPException(status_code=404, detail="Commande introuvable")

    user = commande.user
    carte = commande.carte

    # Générer le QR pour le user (base64)
    react_url = f"{FRONTEND_URL}/user/{user.id}"
    qr = qrcode.make(react_url)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    qr_data = f"data:image/png;base64,{qr_b64}"

    # HTML simple, stylable côté front si besoin.
    html = f"""
    <html>
      <head>
        <meta charset="utf-8"/>
        <title>Aperçu carte - Commande {commande.id}</title>
        <style>
          body {{ font-family: Arial, sans-serif; padding: 20px; }}
          .card {{ width: 600px; border: 1px solid #333; padding: 20px; border-radius: 8px; }}
          .top {{ display:flex; justify-content:space-between; align-items:center; }}
          .info {{ margin-left: 20px; }}
          .qr {{ width:150px; height:150px; }}
          .print-note {{ margin-top: 12px; font-size:12px;color:#555; }}
        </style>
      </head>
      <body>
        <div class="card">
          <div class="top">
            <div class="info">
              <h2>{carte.titre} - {carte.prix} €</h2>
              <p>{carte.description or ''}</p>
              <p><strong>Nom:</strong> {user.name}</p>
              <p><strong>Email:</strong> {user.email}</p>
            </div>
            <div>
              <img src="{qr_data}" class="qr"/>
            </div>
          </div>
          <div class="print-note">
            Imprimez cette page (Ctrl+P / Cmd+P). Après impression, la commande est marquée comme <strong>imprimée</strong>.
          </div>
        </div>
      </body>
    </html>
    """

    # Mettre à jour le statut -> 'imprimée'
    commande.status = "imprimée"
    db.commit()
    db.refresh(commande)

    return HTMLResponse(content=html, status_code=200)

# --- Optional: seed two cartes si aucune existe (au lancement) ---
@app.on_event("startup")
def seed_cartes():
    db = database.SessionLocal()
    try:
        cartes = db.query(models.Carte).count()
        if cartes == 0:
            c1 = models.Carte(titre="Carte Standard", description="Carte simple avec QR et nom", prix=5, disponible=True)
            c2 = models.Carte(titre="Carte Premium", description="Carte premium laminée + QR", prix=10, disponible=True)
            db.add_all([c1, c2])
            db.commit()
    finally:
        db.close()



@app.get("/commandes/{commande_id}/view")
def view_commande(commande_id: int, db: Session = Depends(get_db)):
    """
    Retourne les infos d'une commande (user + carte + QR code)
    pour affichage dans le front React (CardView.jsx)
    """
    commande = db.query(models.Commande).filter(models.Commande.id == commande_id).first()
    if not commande:
        raise HTTPException(status_code=404, detail="Commande introuvable")

    user = commande.user
    carte = commande.carte

    # Générer QR code
    react_url = f"{FRONTEND_URL}/user/{user.id}"
    qr = qrcode.make(react_url)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    qr_data = f"data:image/png;base64,{qr_b64}"

    return {
        "commande": {
            "id": commande.id,
            "status": commande.status,
            "created_at": commande.created_at
        },
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
        },
        "carte": {
            "id": carte.id,
            "titre": carte.titre,
            "description": carte.description,
            "prix": carte.prix
        },
        "qrcode": qr_data
    }





if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

