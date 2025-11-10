# schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List

# --- Users ---
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    photo: Optional[str] = None
    role: Optional[str] = "user"  # role par défaut


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    adresse: Optional[str]
    pays: Optional[str]
    ville: Optional[str]
    telephone1: Optional[str]
    telephone2: Optional[str]
    facebook: Optional[str]
    whatsapp: Optional[str]
    profession: Optional[str]
    photo: Optional[str]


class UserOut(BaseModel):
    id: int
    name: Optional[str]
    email: Optional[EmailStr]
    adresse: Optional[str]
    pays: Optional[str]
    ville: Optional[str]
    telephone1: Optional[str]
    telephone2: Optional[str]
    facebook: Optional[str]
    whatsapp: Optional[str]
    profession: Optional[str]
    photo: Optional[str]
    role: str

    class Config:
        orm_mode = True


class PasswordChange(BaseModel):
    current: str
    new: str

class ResetPasswordSchema(BaseModel):
    new_password: str

# --- Cartes ---
class CarteCreate(BaseModel):
    titre: str
    description: Optional[str] = None
    prix: int
    disponible: Optional[bool] = True
    image: Optional[str] = None


class CarteOut(BaseModel):
    id: int
    titre: str
    description: Optional[str]
    prix: int
    disponible: bool
    image: Optional[str]

    class Config:
        orm_mode = True


# --- Commandes ---
class CommandeCreate(BaseModel):
    user_id: int
    carte_id: int


class CommandeOut(BaseModel):
    id: int
    user: UserOut
    carte: CarteOut
    status: str

    class Config:
        orm_mode = True
