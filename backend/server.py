from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, UploadFile, File, Response
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import aiofiles
import uuid
import mimetypes
import pandas as pd
import io
import secrets
import string
from pathlib import Path
from datetime import datetime, timedelta
from bson import ObjectId

# Import our models and dependencies
from models import *
from auth import get_password_hash, verify_password, create_access_token, decode_access_token
import dependencies
from dependencies import get_current_user, get_current_admin_user
import email_service

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'gmao_iris')]

# Initialize dependencies with database
dependencies.set_database(db)

# Create the main app
app = FastAPI(title="GMAO Atlas API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Helper functions
def serialize_doc(doc):
    """Convert MongoDB document to JSON serializable format"""
    if doc is None:
        return None
    
    # Convertir le _id principal
    if "_id" in doc:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    
    # Supprimer le password si présent
    if "password" in doc:
        del doc["password"]
    
    # Convertir récursivement tous les ObjectId et types non sérialisables
    for key, value in list(doc.items()):
        if isinstance(value, ObjectId):
            doc[key] = str(value)
        elif isinstance(value, (int, float)) and key in ["telephone", "phone", "numero"]:
            # Convertir les numéros de téléphone et numéros en strings
            doc[key] = str(value)
        elif isinstance(value, list):
            doc[key] = [
                str(item) if isinstance(item, ObjectId) 
                else serialize_doc(item) if isinstance(item, dict) 
                else str(item) if isinstance(item, (int, float)) and key in ["telephone", "phone", "numero"]
                else item 
                for item in value
            ]
        elif isinstance(value, dict):
            doc[key] = serialize_doc(value)
    
    # Ajouter dateCreation si manquant (pour compatibilité)
    if "dateCreation" not in doc:
        doc["dateCreation"] = datetime.utcnow()
    
    # S'assurer que attachments existe
    if "attachments" not in doc:
        doc["attachments"] = []
    
    return doc

async def get_user_by_id(user_id: str):
    """Get user details by ID"""
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if user:
            return {
                "id": str(user["_id"]),
                "nom": user.get("nom"),
                "prenom": user.get("prenom"),
                "email": user.get("email"),
                "role": user.get("role")
            }
    except:
        return None

async def get_location_by_id(location_id: str):
    """Get location details by ID"""
    try:
        location = await db.locations.find_one({"_id": ObjectId(location_id)})
        if location:
            return {
                "id": str(location["_id"]),
                "nom": location.get("nom")
            }
    except:
        return None

async def get_equipment_by_id(equipment_id: str):
    """Get equipment details by ID"""
    try:
        equipment = await db.equipments.find_one({"_id": ObjectId(equipment_id)})
        if equipment:
            return {
                "id": str(equipment["_id"]),
                "nom": equipment.get("nom")
            }
    except:
        return None

# ==================== AUTH ROUTES ====================
@api_router.post("/auth/register", response_model=User)
async def register(user_create: UserCreate):
    """Créer un nouveau compte utilisateur"""
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_create.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un utilisateur avec cet email existe déjà"
        )
    
    # Hash password
    hashed_password = get_password_hash(user_create.password)
    
    # Définir les permissions par défaut selon le rôle
    if user_create.role == UserRole.ADMIN:
        permissions = {
            "dashboard": {"view": True, "edit": True, "delete": True},
            "workOrders": {"view": True, "edit": True, "delete": True},
            "assets": {"view": True, "edit": True, "delete": True},
            "preventiveMaintenance": {"view": True, "edit": True, "delete": True},
            "inventory": {"view": True, "edit": True, "delete": True},
            "locations": {"view": True, "edit": True, "delete": True},
            "vendors": {"view": True, "edit": True, "delete": True},
            "reports": {"view": True, "edit": True, "delete": True}
        }
    elif user_create.role == UserRole.TECHNICIEN:
        permissions = {
            "dashboard": {"view": True, "edit": False, "delete": False},
            "workOrders": {"view": True, "edit": True, "delete": False},
            "assets": {"view": True, "edit": True, "delete": False},
            "preventiveMaintenance": {"view": True, "edit": True, "delete": False},
            "inventory": {"view": True, "edit": True, "delete": False},
            "locations": {"view": True, "edit": False, "delete": False},
            "vendors": {"view": True, "edit": False, "delete": False},
            "reports": {"view": True, "edit": False, "delete": False}
        }
    else:  # VISUALISEUR
        permissions = {
            "dashboard": {"view": True, "edit": False, "delete": False},
            "workOrders": {"view": True, "edit": False, "delete": False},
            "assets": {"view": True, "edit": False, "delete": False},
            "preventiveMaintenance": {"view": True, "edit": False, "delete": False},
            "inventory": {"view": True, "edit": False, "delete": False},
            "locations": {"view": True, "edit": False, "delete": False},
            "vendors": {"view": True, "edit": False, "delete": False},
            "reports": {"view": True, "edit": False, "delete": False}
        }
    
    # Create user
    user_dict = user_create.model_dump()
    del user_dict["password"]
    user_dict["password"] = hashed_password
    user_dict["statut"] = "actif"
    user_dict["dateCreation"] = datetime.utcnow()
    user_dict["derniereConnexion"] = None
    user_dict["permissions"] = permissions
    user_dict["_id"] = ObjectId()
    
    await db.users.insert_one(user_dict)
    
    return User(**serialize_doc(user_dict))

@api_router.post("/auth/login", response_model=Token)
async def login(login_request: LoginRequest):
    """Se connecter et obtenir un token JWT"""
    # Debug logging
    logger.info(f"🔍 LOGIN ATTEMPT - Email: {login_request.email}")
    
    # Find user
    user = await db.users.find_one({"email": login_request.email})
    logger.info(f"🔍 User found in DB: {user is not None}")
    
    if not user:
        logger.warning(f"❌ User not found for email: {login_request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    # Verify password
    password_valid = verify_password(login_request.password, user["password"])
    logger.info(f"🔍 Password valid: {password_valid}")
    
    if not password_valid:
        logger.warning(f"❌ Invalid password for email: {login_request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    # Update last login
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"derniereConnexion": datetime.utcnow()}}
    )
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user["_id"])})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=User(**serialize_doc(user))
    )

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Obtenir l'utilisateur connecté"""
    return User(**current_user)


@api_router.post("/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Demander une réinitialisation de mot de passe"""
    # Vérifier si l'utilisateur existe
    user = await db.users.find_one({"email": request.email})
    
    if user:
        # Créer un token de réinitialisation (valide 1 heure)
        reset_token = create_access_token(
            data={"sub": str(user["_id"]), "type": "reset"},
            expires_delta=timedelta(hours=1)
        )
        
        # Dans une vraie application, on enverrait un email ici
        # Pour l'instant, on log le token (pour dev/test uniquement)
        print(f"Reset token for {request.email}: {reset_token}")
        print(f"Reset URL: http://localhost:3000/reset-password?token={reset_token}")
        
        # Sauvegarder le token dans la base (optionnel, pour invalider après usage)
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"reset_token": reset_token, "reset_token_created": datetime.utcnow()}}
        )
    
    # Toujours retourner succès pour ne pas révéler si l'email existe
    return {"message": "Si cet email existe, un lien de réinitialisation a été envoyé"}

@api_router.post("/auth/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """Réinitialiser le mot de passe avec un token"""
    try:
        # Vérifier le token
        payload = jwt.decode(request.token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        token_type = payload.get("type")
        
        if token_type != "reset":
            raise HTTPException(status_code=400, detail="Token invalide")
        
        # Trouver l'utilisateur
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        # Vérifier que le token correspond (si sauvegardé)
        if user.get("reset_token") != request.token:
            raise HTTPException(status_code=400, detail="Token invalide ou déjà utilisé")
        
        # Hacher le nouveau mot de passe
        hashed_password = get_password_hash(request.new_password)
        
        # Mettre à jour le mot de passe et supprimer le token
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {"password": hashed_password},
                "$unset": {"reset_token": "", "reset_token_created": ""}
            }
        )
        
        return {"message": "Mot de passe réinitialisé avec succès"}
        
    except JWTError:
        raise HTTPException(status_code=400, detail="Token invalide ou expiré")


# ==================== INVITATION & REGISTRATION ROUTES ====================

def generate_temp_password(length: int = 12) -> str:
    """Génère un mot de passe temporaire aléatoire"""
    characters = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(secrets.choice(characters) for _ in range(length))

@api_router.post("/users/invite-member")
async def invite_member(request: InviteMemberRequest, current_user: dict = Depends(get_current_admin_user)):
    """
    Envoyer une invitation par email (Admin uniquement)
    L'utilisateur recevra un lien pour compléter son inscription
    """
    # Vérifier si l'email existe déjà
    existing_user = await db.users.find_one({"email": request.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un utilisateur avec cet email existe déjà"
        )
    
    # Créer un token d'invitation (valide 7 jours)
    invitation_data = {
        "sub": request.email,
        "type": "invitation",
        "role": request.role,
        "invited_by": current_user.get("_id")
    }
    invitation_token = create_access_token(
        data=invitation_data,
        expires_delta=timedelta(days=7)
    )
    
    # Envoyer l'email d'invitation
    email_sent = email_service.send_invitation_email(
        to_email=request.email,
        token=invitation_token,
        role=request.role
    )
    
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'envoi de l'email d'invitation"
        )
    
    # Log l'invitation
    logger.info(f"Invitation envoyée à {request.email} par {current_user.get('email')}")
    
    return {
        "message": f"Invitation envoyée à {request.email}",
        "email": request.email,
        "role": request.role
    }

@api_router.post("/users/create-member", response_model=User)
async def create_member(request: CreateMemberRequest, current_user: dict = Depends(get_current_admin_user)):
    """
    Créer un membre directement avec mot de passe temporaire (Admin uniquement)
    L'utilisateur recevra un email avec ses identifiants
    """
    # Vérifier si l'email existe déjà
    existing_user = await db.users.find_one({"email": request.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un utilisateur avec cet email existe déjà"
        )
    
    # Hasher le mot de passe fourni
    hashed_password = get_password_hash(request.password)
    
    # Définir les permissions par défaut selon le rôle
    if request.role == UserRole.ADMIN:
        permissions = {
            "dashboard": {"view": True, "edit": True, "delete": True},
            "workOrders": {"view": True, "edit": True, "delete": True},
            "assets": {"view": True, "edit": True, "delete": True},
            "preventiveMaintenance": {"view": True, "edit": True, "delete": True},
            "inventory": {"view": True, "edit": True, "delete": True},
            "locations": {"view": True, "edit": True, "delete": True},
            "vendors": {"view": True, "edit": True, "delete": True},
            "reports": {"view": True, "edit": True, "delete": True}
        }
    elif request.role == UserRole.TECHNICIEN:
        permissions = {
            "dashboard": {"view": True, "edit": False, "delete": False},
            "workOrders": {"view": True, "edit": True, "delete": False},
            "assets": {"view": True, "edit": True, "delete": False},
            "preventiveMaintenance": {"view": True, "edit": True, "delete": False},
            "inventory": {"view": True, "edit": True, "delete": False},
            "locations": {"view": True, "edit": False, "delete": False},
            "vendors": {"view": True, "edit": False, "delete": False},
            "reports": {"view": True, "edit": False, "delete": False}
        }
    else:  # VISUALISEUR
        permissions = {
            "dashboard": {"view": True, "edit": False, "delete": False},
            "workOrders": {"view": True, "edit": False, "delete": False},
            "assets": {"view": True, "edit": False, "delete": False},
            "preventiveMaintenance": {"view": True, "edit": False, "delete": False},
            "inventory": {"view": True, "edit": False, "delete": False},
            "locations": {"view": True, "edit": False, "delete": False},
            "vendors": {"view": True, "edit": False, "delete": False},
            "reports": {"view": True, "edit": False, "delete": False}
        }
    
    # Créer l'utilisateur
    user_dict = {
        "id": str(uuid.uuid4()),
        "nom": request.nom,
        "prenom": request.prenom,
        "email": request.email,
        "telephone": request.telephone or "",
        "role": request.role,
        "service": request.service,
        "password": hashed_password,
        "statut": "actif",
        "dateCreation": datetime.utcnow(),
        "derniereConnexion": datetime.utcnow(),
        "permissions": permissions,
        "firstLogin": True  # Doit changer son mot de passe à la première connexion
    }
    
    await db.users.insert_one(user_dict)
    
    # Envoyer l'email avec les identifiants
    email_sent = email_service.send_account_created_email(
        to_email=request.email,
        temp_password=request.password,
        prenom=request.prenom
    )
    
    if not email_sent:
        logger.warning(f"Email non envoyé à {request.email}, mais compte créé")
    
    logger.info(f"Membre créé: {request.email} par {current_user.get('email')}")
    
    return User(**serialize_doc(user_dict))

@api_router.get("/auth/validate-invitation/{token}")
async def validate_invitation(token: str):
    """
    Valider un token d'invitation et retourner les informations
    """
    try:
        payload = decode_access_token(token)
        if not payload or payload.get("type") != "invitation":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token d'invitation invalide"
            )
        
        # Vérifier que l'utilisateur n'existe pas déjà
        email = payload.get("sub")
        existing_user = await db.users.find_one({"email": email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cet utilisateur existe déjà"
            )
        
        return {
            "valid": True,
            "email": email,
            "role": payload.get("role")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token d'invitation invalide ou expiré"
        )

@api_router.post("/auth/complete-registration", response_model=User)
async def complete_registration(request: CompleteRegistrationRequest):
    """
    Compléter l'inscription après avoir reçu une invitation
    """
    try:
        # Valider le token
        payload = decode_access_token(request.token)
        if not payload or payload.get("type") != "invitation":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token d'invitation invalide"
            )
        
        email = payload.get("sub")
        role = payload.get("role")
        
        # Vérifier que l'utilisateur n'existe pas déjà
        existing_user = await db.users.find_one({"email": email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cet utilisateur existe déjà"
            )
        
        # Hasher le mot de passe
        hashed_password = get_password_hash(request.password)
        
        # Définir les permissions par défaut selon le rôle
        if role == UserRole.ADMIN:
            permissions = {
                "dashboard": {"view": True, "edit": True, "delete": True},
                "workOrders": {"view": True, "edit": True, "delete": True},
                "assets": {"view": True, "edit": True, "delete": True},
                "preventiveMaintenance": {"view": True, "edit": True, "delete": True},
                "inventory": {"view": True, "edit": True, "delete": True},
                "locations": {"view": True, "edit": True, "delete": True},
                "vendors": {"view": True, "edit": True, "delete": True},
                "reports": {"view": True, "edit": True, "delete": True}
            }
        elif role == UserRole.TECHNICIEN:
            permissions = {
                "dashboard": {"view": True, "edit": False, "delete": False},
                "workOrders": {"view": True, "edit": True, "delete": False},
                "assets": {"view": True, "edit": True, "delete": False},
                "preventiveMaintenance": {"view": True, "edit": True, "delete": False},
                "inventory": {"view": True, "edit": True, "delete": False},
                "locations": {"view": True, "edit": False, "delete": False},
                "vendors": {"view": True, "edit": False, "delete": False},
                "reports": {"view": True, "edit": False, "delete": False}
            }
        else:  # VISUALISEUR
            permissions = {
                "dashboard": {"view": True, "edit": False, "delete": False},
                "workOrders": {"view": True, "edit": False, "delete": False},
                "assets": {"view": True, "edit": False, "delete": False},
                "preventiveMaintenance": {"view": True, "edit": False, "delete": False},
                "inventory": {"view": True, "edit": False, "delete": False},
                "locations": {"view": True, "edit": False, "delete": False},
                "vendors": {"view": True, "edit": False, "delete": False},
                "reports": {"view": True, "edit": False, "delete": False}
            }
        
        # Créer l'utilisateur
        user_dict = {
            "id": str(uuid.uuid4()),
            "nom": request.nom,
            "prenom": request.prenom,
            "email": email,
            "telephone": request.telephone or "",
            "role": role,
            "service": None,
            "password": hashed_password,
            "statut": "actif",
            "dateCreation": datetime.utcnow(),
            "derniereConnexion": datetime.utcnow(),
            "permissions": permissions,
            "firstLogin": False  # A déjà défini son mot de passe
        }
        
        await db.users.insert_one(user_dict)
        
        logger.info(f"Inscription complétée pour {email}")
        
        return User(**serialize_doc(user_dict))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la completion de l'inscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erreur lors de l'inscription"
        )

@api_router.post("/auth/change-password-first-login")
async def change_password_first_login(request: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    """
    Changer le mot de passe lors de la première connexion
    """
    user_id = current_user.get("id")  # Changé de "_id" à "id"
    
    # Vérifier l'ancien mot de passe
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    if not verify_password(request.old_password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mot de passe actuel incorrect"
        )
    
    # Hasher le nouveau mot de passe
    new_hashed_password = get_password_hash(request.new_password)
    
    # Mettre à jour le mot de passe et marquer firstLogin comme False
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "password": new_hashed_password,
                "firstLogin": False
            }
        }
    )
    
    logger.info(f"Mot de passe changé pour {user.get('email')}")
    
    return {"message": "Mot de passe changé avec succès"}


@api_router.get("/auth/me", response_model=User)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Récupérer le profil de l'utilisateur connecté
    """
    user_id = current_user.get("id")
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return User(**serialize_doc(user))


@api_router.put("/auth/me")
async def update_current_user_profile(user_update: UserProfileUpdate, current_user: dict = Depends(get_current_user)):
    """
    Mettre à jour le profil de l'utilisateur connecté
    """
    user_id = current_user.get("id")
    
    # Préparer les données à mettre à jour (exclure None)
    update_data = {k: v for k, v in user_update.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")
    
    # Mettre à jour l'utilisateur
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    # Récupérer l'utilisateur mis à jour
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    logger.info(f"Profil mis à jour pour {user.get('email')}")
    
    return {"message": "Profil mis à jour avec succès", "user": serialize_doc(user)}


@api_router.post("/auth/change-password")
async def change_password(request: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    """
    Changer le mot de passe de l'utilisateur connecté
    """
    user_id = current_user.get("id")
    
    # Vérifier l'ancien mot de passe
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    if not verify_password(request.old_password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mot de passe actuel incorrect"
        )
    
    # Hasher le nouveau mot de passe
    new_hashed_password = get_password_hash(request.new_password)
    
    # Mettre à jour le mot de passe
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password": new_hashed_password}}
    )
    
    logger.info(f"Mot de passe changé pour {user.get('email')}")
    
    return {"message": "Mot de passe changé avec succès"}

# ==================== WORK ORDERS ROUTES ====================
@api_router.get("/work-orders", response_model=List[WorkOrder])
async def get_work_orders(
    date_debut: str = None,
    date_fin: str = None,
    date_type: str = "creation",  # "creation" ou "echeance"
    current_user: dict = Depends(get_current_user)
):
    """Liste tous les ordres de travail avec filtrage par date"""
    query = {}
    
    # Filtrage par date
    if date_debut and date_fin:
        date_field = "dateCreation" if date_type == "creation" else "dateLimite"
        query[date_field] = {
            "$gte": datetime.fromisoformat(date_debut),
            "$lte": datetime.fromisoformat(date_fin)
        }
    
    work_orders = await db.work_orders.find(query).to_list(1000)
    
    # Populate references
    for wo in work_orders:
        # Serialiser le document pour convertir tous les types non JSON
        wo = serialize_doc(wo)
        
        # S'assurer que attachments existe et convertir les ObjectId
        if "attachments" not in wo:
            wo["attachments"] = []
        else:
            # Convertir tous les ObjectId dans attachments
            for att in wo["attachments"]:
                if "_id" in att and isinstance(att["_id"], ObjectId):
                    att["_id"] = str(att["_id"])
                for key, value in att.items():
                    if isinstance(value, ObjectId):
                        att[key] = str(value)
        
        if wo.get("assigne_a_id"):
            wo["assigneA"] = await get_user_by_id(wo["assigne_a_id"])
        if wo.get("emplacement_id"):
            wo["emplacement"] = await get_location_by_id(wo["emplacement_id"])
        if wo.get("equipement_id"):
            wo["equipement"] = await get_equipment_by_id(wo["equipement_id"])
    
    return [WorkOrder(**wo) for wo in work_orders]

@api_router.get("/work-orders/{wo_id}", response_model=WorkOrder)
async def get_work_order(wo_id: str, current_user: dict = Depends(get_current_user)):
    """Détails d'un ordre de travail"""
    try:
        wo = await db.work_orders.find_one({"_id": ObjectId(wo_id)})
        if not wo:
            raise HTTPException(status_code=404, detail="Ordre de travail non trouvé")
        
        wo = serialize_doc(wo)
        if wo.get("assigne_a_id"):
            wo["assigneA"] = await get_user_by_id(wo["assigne_a_id"])
        if wo.get("emplacement_id"):
            wo["emplacement"] = await get_location_by_id(wo["emplacement_id"])
        if wo.get("equipement_id"):
            wo["equipement"] = await get_equipment_by_id(wo["equipement_id"])
        
        return WorkOrder(**wo)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/work-orders", response_model=WorkOrder)
async def create_work_order(wo_create: WorkOrderCreate, current_user: dict = Depends(get_current_user)):
    """Créer un nouvel ordre de travail"""
    # Generate numero
    count = await db.work_orders.count_documents({})
    numero = str(5800 + count + 1)
    
    wo_dict = wo_create.model_dump()
    wo_dict["numero"] = numero
    wo_dict["dateCreation"] = datetime.utcnow()
    wo_dict["tempsReel"] = None
    wo_dict["dateTermine"] = None
    wo_dict["attachments"] = []
    wo_dict["_id"] = ObjectId()
    
    await db.work_orders.insert_one(wo_dict)
    
    wo = serialize_doc(wo_dict)
    if wo.get("assigne_a_id"):
        wo["assigneA"] = await get_user_by_id(wo["assigne_a_id"])
    if wo.get("emplacement_id"):
        wo["emplacement"] = await get_location_by_id(wo["emplacement_id"])
    if wo.get("equipement_id"):
        wo["equipement"] = await get_equipment_by_id(wo["equipement_id"])
    
    return WorkOrder(**wo)

@api_router.put("/work-orders/{wo_id}", response_model=WorkOrder)
async def update_work_order(wo_id: str, wo_update: WorkOrderUpdate, current_user: dict = Depends(get_current_user)):
    """Modifier un ordre de travail"""
    try:
        update_data = {k: v for k, v in wo_update.model_dump().items() if v is not None}
        
        if wo_update.statut == WorkOrderStatus.TERMINE and "dateTermine" not in update_data:
            update_data["dateTermine"] = datetime.utcnow()
        
        await db.work_orders.update_one(
            {"_id": ObjectId(wo_id)},
            {"$set": update_data}
        )
        
        wo = await db.work_orders.find_one({"_id": ObjectId(wo_id)})
        wo = serialize_doc(wo)
        
        if wo.get("assigne_a_id"):
            wo["assigneA"] = await get_user_by_id(wo["assigne_a_id"])
        if wo.get("emplacement_id"):
            wo["emplacement"] = await get_location_by_id(wo["emplacement_id"])
        if wo.get("equipement_id"):
            wo["equipement"] = await get_equipment_by_id(wo["equipement_id"])
        
        return WorkOrder(**wo)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.delete("/work-orders/{wo_id}")
async def delete_work_order(wo_id: str, current_user: dict = Depends(get_current_user)):
    """Supprimer un ordre de travail"""
    try:
        result = await db.work_orders.delete_one({"_id": ObjectId(wo_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Ordre de travail non trouvé")
        return {"message": "Ordre de travail supprimé"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== WORK ORDER ATTACHMENTS ====================
UPLOAD_DIR = Path("/app/backend/uploads/work-orders")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB

@api_router.post("/work-orders/{wo_id}/attachments")
async def upload_attachment(
    wo_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Uploader une pièce jointe (max 25MB)"""
    try:
        # Vérifier que l'ordre de travail existe
        wo = await db.work_orders.find_one({"_id": ObjectId(wo_id)})
        if not wo:
            raise HTTPException(status_code=404, detail="Ordre de travail non trouvé")
        
        # Vérifier la taille du fichier
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 25MB)")
        
        # Générer un nom de fichier unique
        file_ext = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Sauvegarder le fichier
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Créer l'entrée attachment
        attachment = {
            "_id": ObjectId(),
            "filename": unique_filename,
            "original_filename": file.filename,
            "size": len(content),
            "mime_type": file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream",
            "uploaded_at": datetime.utcnow()
        }
        
        # Ajouter à la base de données
        await db.work_orders.update_one(
            {"_id": ObjectId(wo_id)},
            {"$push": {"attachments": attachment}}
        )
        
        attachment_response = {
            "id": str(attachment["_id"]),
            "filename": attachment["filename"],
            "original_filename": attachment["original_filename"],
            "size": attachment["size"],
            "mime_type": attachment["mime_type"],
            "uploaded_at": attachment["uploaded_at"],
            "url": f"/api/work-orders/{wo_id}/attachments/{str(attachment['_id'])}"
        }
        
        return attachment_response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/work-orders/{wo_id}/attachments")
async def get_attachments(wo_id: str, current_user: dict = Depends(get_current_user)):
    """Lister les pièces jointes d'un ordre de travail"""
    try:
        wo = await db.work_orders.find_one({"_id": ObjectId(wo_id)})
        if not wo:
            raise HTTPException(status_code=404, detail="Ordre de travail non trouvé")
        
        attachments = wo.get("attachments", [])
        result = []
        for att in attachments:
            result.append({
                "id": str(att["_id"]),
                "filename": att["filename"],
                "original_filename": att["original_filename"],
                "size": att["size"],
                "mime_type": att["mime_type"],
                "uploaded_at": att["uploaded_at"],
                "url": f"/api/work-orders/{wo_id}/attachments/{str(att['_id'])}"
            })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/work-orders/{wo_id}/attachments/{attachment_id}")
async def download_attachment(
    wo_id: str,
    attachment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Télécharger une pièce jointe"""
    try:
        wo = await db.work_orders.find_one({"_id": ObjectId(wo_id)})
        if not wo:
            raise HTTPException(status_code=404, detail="Ordre de travail non trouvé")
        
        # Trouver l'attachment
        attachment = None
        for att in wo.get("attachments", []):
            if str(att["_id"]) == attachment_id:
                attachment = att
                break
        
        if not attachment:
            raise HTTPException(status_code=404, detail="Pièce jointe non trouvée")
        
        file_path = UPLOAD_DIR / attachment["filename"]
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Fichier non trouvé sur le serveur")
        
        return FileResponse(
            path=file_path,
            filename=attachment["original_filename"],
            media_type=attachment["mime_type"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.delete("/work-orders/{wo_id}/attachments/{attachment_id}")
async def delete_attachment(
    wo_id: str,
    attachment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Supprimer une pièce jointe"""
    try:
        wo = await db.work_orders.find_one({"_id": ObjectId(wo_id)})
        if not wo:
            raise HTTPException(status_code=404, detail="Ordre de travail non trouvé")
        
        # Trouver l'attachment
        attachment = None
        for att in wo.get("attachments", []):
            if str(att["_id"]) == attachment_id:
                attachment = att
                break
        
        if not attachment:
            raise HTTPException(status_code=404, detail="Pièce jointe non trouvée")
        
        # Supprimer le fichier physique
        file_path = UPLOAD_DIR / attachment["filename"]
        if file_path.exists():
            file_path.unlink()
        
        # Retirer de la base de données
        await db.work_orders.update_one(
            {"_id": ObjectId(wo_id)},
            {"$pull": {"attachments": {"_id": ObjectId(attachment_id)}}}
        )
        
        return {"message": "Pièce jointe supprimée"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== EQUIPMENTS ROUTES ====================
@api_router.get("/equipments", response_model=List[Equipment])
async def get_equipments(current_user: dict = Depends(get_current_user)):
    """Liste tous les équipements"""
    equipments = await db.equipments.find().to_list(1000)
    
    for eq in equipments:
        eq["id"] = str(eq["_id"])
        del eq["_id"]
        if eq.get("emplacement_id"):
            eq["emplacement"] = await get_location_by_id(eq["emplacement_id"])
        
        # Ajouter les informations du parent si présent
        if eq.get("parent_id"):
            eq["parent"] = await get_equipment_by_id(eq["parent_id"])
        
        # Vérifier si l'équipement a des enfants
        children_count = await db.equipments.count_documents({"parent_id": eq["id"]})
        eq["hasChildren"] = children_count > 0
    
    return [Equipment(**eq) for eq in equipments]

@api_router.post("/equipments", response_model=Equipment)
async def create_equipment(eq_create: EquipmentCreate, current_user: dict = Depends(get_current_user)):
    """Créer un nouvel équipement"""
    eq_dict = eq_create.model_dump()
    
    # Si un parent est spécifié et qu'aucun emplacement n'est fourni, hériter de l'emplacement du parent
    if eq_dict.get("parent_id"):
        parent = await db.equipments.find_one({"_id": ObjectId(eq_dict["parent_id"])})
        if parent:
            # Hériter de l'emplacement du parent
            if not eq_dict.get("emplacement_id"):
                eq_dict["emplacement_id"] = parent.get("emplacement_id")
        else:
            raise HTTPException(status_code=404, detail="Équipement parent non trouvé")
    
    # Vérifier qu'on a un emplacement_id valide après héritage
    if not eq_dict.get("emplacement_id"):
        raise HTTPException(status_code=400, detail="Un emplacement est requis (directement ou hérité du parent)")
    
    eq_dict["dateCreation"] = datetime.utcnow()
    eq_dict["derniereMaintenance"] = None
    eq_dict["_id"] = ObjectId()
    
    await db.equipments.insert_one(eq_dict)
    
    eq = serialize_doc(eq_dict)
    if eq.get("emplacement_id"):
        eq["emplacement"] = await get_location_by_id(eq["emplacement_id"])
    
    if eq.get("parent_id"):
        eq["parent"] = await get_equipment_by_id(eq["parent_id"])
    
    eq["hasChildren"] = False
    
    return Equipment(**eq)

@api_router.get("/equipments/{eq_id}", response_model=Equipment)
async def get_equipment_detail(eq_id: str, current_user: dict = Depends(get_current_user)):
    """Récupérer les détails d'un équipement"""
    try:
        eq = await db.equipments.find_one({"_id": ObjectId(eq_id)})
        if not eq:
            raise HTTPException(status_code=404, detail="Équipement non trouvé")
        
        eq = serialize_doc(eq)
        
        if eq.get("emplacement_id"):
            eq["emplacement"] = await get_location_by_id(eq["emplacement_id"])
        
        if eq.get("parent_id"):
            eq["parent"] = await get_equipment_by_id(eq["parent_id"])
        
        # Vérifier si l'équipement a des enfants
        children_count = await db.equipments.count_documents({"parent_id": eq["id"]})
        eq["hasChildren"] = children_count > 0
        
        return Equipment(**eq)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/equipments/{eq_id}/children", response_model=List[Equipment])
async def get_equipment_children(eq_id: str, current_user: dict = Depends(get_current_user)):
    """Récupérer tous les sous-équipements d'un équipement"""
    try:
        # Vérifier que le parent existe
        parent = await db.equipments.find_one({"_id": ObjectId(eq_id)})
        if not parent:
            raise HTTPException(status_code=404, detail="Équipement parent non trouvé")
        
        # Récupérer tous les enfants
        children = await db.equipments.find({"parent_id": eq_id}).to_list(1000)
        
        result = []
        for child in children:
            child = serialize_doc(child)
            
            if child.get("emplacement_id"):
                child["emplacement"] = await get_location_by_id(child["emplacement_id"])
            
            if child.get("parent_id"):
                child["parent"] = await get_equipment_by_id(child["parent_id"])
            
            # Vérifier si cet enfant a lui-même des enfants
            grandchildren_count = await db.equipments.count_documents({"parent_id": child["id"]})
            child["hasChildren"] = grandchildren_count > 0
            
            result.append(Equipment(**child))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/equipments/{eq_id}/hierarchy")
async def get_equipment_hierarchy(eq_id: str, current_user: dict = Depends(get_current_user)):
    """Récupérer toute la hiérarchie d'un équipement (récursif)"""
    try:
        async def build_hierarchy(equipment_id: str):
            eq = await db.equipments.find_one({"_id": ObjectId(equipment_id)})
            if not eq:
                return None
            
            eq = serialize_doc(eq)
            
            if eq.get("emplacement_id"):
                eq["emplacement"] = await get_location_by_id(eq["emplacement_id"])
            
            # Récupérer les enfants
            children = await db.equipments.find({"parent_id": eq["id"]}).to_list(1000)
            eq["children"] = []
            
            for child in children:
                child_hierarchy = await build_hierarchy(str(child["_id"]))
                if child_hierarchy:
                    eq["children"].append(child_hierarchy)
            
            eq["hasChildren"] = len(eq["children"]) > 0
            
            return eq
        
        hierarchy = await build_hierarchy(eq_id)
        if not hierarchy:
            raise HTTPException(status_code=404, detail="Équipement non trouvé")
        
        return hierarchy
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.put("/equipments/{eq_id}", response_model=Equipment)
async def update_equipment(eq_id: str, eq_update: EquipmentUpdate, current_user: dict = Depends(get_current_user)):
    """Modifier un équipement"""
    try:
        update_data = {k: v for k, v in eq_update.model_dump().items() if v is not None}
        
        await db.equipments.update_one(
            {"_id": ObjectId(eq_id)},
            {"$set": update_data}
        )
        
        eq = await db.equipments.find_one({"_id": ObjectId(eq_id)})
        eq = serialize_doc(eq)
        
        if eq.get("emplacement_id"):
            eq["emplacement"] = await get_location_by_id(eq["emplacement_id"])
        
        if eq.get("parent_id"):
            eq["parent"] = await get_equipment_by_id(eq["parent_id"])
        
        children_count = await db.equipments.count_documents({"parent_id": eq["id"]})
        eq["hasChildren"] = children_count > 0
        
        return Equipment(**eq)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def check_and_update_parent_status(equipment_id: str):
    """Vérifier et mettre à jour le statut du parent en fonction des enfants"""
    # Récupérer l'équipement
    equipment = await db.equipments.find_one({"_id": ObjectId(equipment_id)})
    if not equipment:
        return
    
    # Si cet équipement a un parent, vérifier le statut du parent
    if equipment.get("parent_id"):
        await update_parent_alert_status(equipment["parent_id"])

async def update_parent_alert_status(parent_id: str):
    """Mettre à jour le statut du parent en fonction des statuts des enfants"""
    # Récupérer tous les enfants
    children = await db.equipments.find({"parent_id": parent_id}).to_list(1000)
    
    if not children:
        return
    
    # Vérifier si au moins un enfant est EN_MAINTENANCE ou HORS_SERVICE
    has_problematic_child = any(
        child.get("statut") in ["EN_MAINTENANCE", "HORS_SERVICE"] 
        for child in children
    )
    
    parent = await db.equipments.find_one({"_id": ObjectId(parent_id)})
    if not parent:
        return
    
    if has_problematic_child:
        # Mettre le parent en ALERTE_S_EQUIP
        await db.equipments.update_one(
            {"_id": ObjectId(parent_id)},
            {"$set": {"statut": "ALERTE_S_EQUIP"}}
        )
    else:
        # Si tous les enfants sont OPERATIONNEL et le parent est en ALERTE, remettre à OPERATIONNEL
        if parent.get("statut") == "ALERTE_S_EQUIP":
            all_operational = all(
                child.get("statut") == "OPERATIONNEL" 
                for child in children
            )
            if all_operational:
                await db.equipments.update_one(
                    {"_id": ObjectId(parent_id)},
                    {"$set": {"statut": "OPERATIONNEL"}}
                )

@api_router.patch("/equipments/{eq_id}/status")
async def update_equipment_status(eq_id: str, statut: EquipmentStatus, current_user: dict = Depends(get_current_user)):
    """Mettre à jour rapidement le statut d'un équipement"""
    try:
        equipment = await db.equipments.find_one({"_id": ObjectId(eq_id)})
        if not equipment:
            raise HTTPException(status_code=404, detail="Équipement non trouvé")
        
        # Vérifier si l'équipement a des enfants
        children = await db.equipments.find({"parent_id": eq_id}).to_list(1000)
        
        # Si l'équipement a des enfants et qu'on essaie de changer depuis ALERTE_S_EQUIP
        if children and equipment.get("statut") == "ALERTE_S_EQUIP":
            # Vérifier si tous les enfants sont opérationnels
            all_operational = all(child.get("statut") == "OPERATIONNEL" for child in children)
            if not all_operational:
                raise HTTPException(
                    status_code=400, 
                    detail="Impossible de changer le statut : des sous-équipements ne sont pas opérationnels"
                )
        
        # Interdire de mettre manuellement en ALERTE_S_EQUIP
        if statut == EquipmentStatus.ALERTE_S_EQUIP:
            raise HTTPException(
                status_code=400,
                detail="Le statut 'Alerte S.Equip' est automatique et ne peut pas être défini manuellement"
            )
        
        # Mettre à jour le statut
        result = await db.equipments.update_one(
            {"_id": ObjectId(eq_id)},
            {"$set": {"statut": statut}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Équipement non trouvé")
        
        # Mettre à jour le statut du parent si nécessaire
        await check_and_update_parent_status(eq_id)
        
        return {"message": "Statut mis à jour", "statut": statut}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.delete("/equipments/{eq_id}")
async def delete_equipment(eq_id: str, current_user: dict = Depends(get_current_user)):
    """Supprimer un équipement"""
    try:
        result = await db.equipments.delete_one({"_id": ObjectId(eq_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Équipement non trouvé")
        return {"message": "Équipement supprimé"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== AVAILABILITY ROUTES ====================
@api_router.get("/availabilities")
async def get_availabilities(
    start_date: str = None,
    end_date: str = None,
    user_id: str = None,
    current_user: dict = Depends(get_current_user)
):
    """Récupérer les disponibilités du personnel"""
    query = {}
    
    if user_id:
        query["user_id"] = user_id
    
    if start_date and end_date:
        query["date"] = {
            "$gte": datetime.fromisoformat(start_date),
            "$lte": datetime.fromisoformat(end_date)
        }
    
    availabilities = await db.availabilities.find(query).to_list(1000)
    
    for avail in availabilities:
        avail["id"] = str(avail["_id"])
        del avail["_id"]
        if avail.get("user_id"):
            avail["user"] = await get_user_by_id(avail["user_id"])
    
    return availabilities

@api_router.post("/availabilities")
async def create_availability(
    availability: UserAvailabilityCreate,
    current_user: dict = Depends(get_current_admin_user)
):
    """Créer une disponibilité (admin uniquement)"""
    avail_dict = availability.model_dump()
    avail_dict["_id"] = ObjectId()
    
    await db.availabilities.insert_one(avail_dict)
    
    avail = serialize_doc(avail_dict)
    if avail.get("user_id"):
        avail["user"] = await get_user_by_id(avail["user_id"])
    
    return avail

@api_router.put("/availabilities/{avail_id}")
async def update_availability(
    avail_id: str,
    availability_update: UserAvailabilityUpdate,
    current_user: dict = Depends(get_current_admin_user)
):
    """Mettre à jour une disponibilité (admin uniquement)"""
    try:
        update_data = {k: v for k, v in availability_update.model_dump().items() if v is not None}
        
        await db.availabilities.update_one(
            {"_id": ObjectId(avail_id)},
            {"$set": update_data}
        )
        
        avail = await db.availabilities.find_one({"_id": ObjectId(avail_id)})
        avail = serialize_doc(avail)
        
        if avail.get("user_id"):
            avail["user"] = await get_user_by_id(avail["user_id"])
        
        return avail
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.delete("/availabilities/{avail_id}")
async def delete_availability(
    avail_id: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """Supprimer une disponibilité (admin uniquement)"""
    try:
        result = await db.availabilities.delete_one({"_id": ObjectId(avail_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Disponibilité non trouvée")
        return {"message": "Disponibilité supprimée"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== LOCATIONS ROUTES ====================
@api_router.get("/locations", response_model=List[Location])
async def get_locations(current_user: dict = Depends(get_current_user)):
    """Liste toutes les zones avec hiérarchie"""
    locations = await db.locations.find().to_list(1000)
    
    # Enrichir avec les informations de hiérarchie
    result = []
    for loc in locations:
        loc_data = serialize_doc(loc)
        
        # Calculer le niveau dans la hiérarchie
        level = 0
        parent_id = loc.get('parent_id')
        while parent_id and level < 3:
            parent = await db.locations.find_one({"_id": ObjectId(parent_id)})
            if parent:
                level += 1
                parent_id = parent.get('parent_id')
            else:
                break
        loc_data['level'] = level
        
        # Vérifier si cette zone a des enfants
        has_children = await db.locations.count_documents({"parent_id": loc_data['id']}) > 0
        loc_data['hasChildren'] = has_children
        
        # Ajouter les infos du parent si présent
        if loc.get('parent_id'):
            parent = await db.locations.find_one({"_id": ObjectId(loc.get('parent_id'))})
            if parent:
                loc_data['parent'] = {
                    "id": str(parent["_id"]),
                    "nom": parent.get("nom")
                }
        
        result.append(Location(**loc_data))
    
    return result

@api_router.get("/locations/{loc_id}/children", response_model=List[Location])
async def get_location_children(loc_id: str, current_user: dict = Depends(get_current_user)):
    """Récupérer les sous-zones d'une zone"""
    children = await db.locations.find({"parent_id": loc_id}).to_list(100)
    result = []
    for child in children:
        child_data = serialize_doc(child)
        child_data['level'] = 1  # Simplifié pour l'instant
        child_data['hasChildren'] = await db.locations.count_documents({"parent_id": child_data['id']}) > 0
        result.append(Location(**child_data))
    return result

@api_router.post("/locations", response_model=Location)
async def create_location(loc_create: LocationCreate, current_user: dict = Depends(get_current_user)):
    """Créer une nouvelle zone"""
    loc_dict = loc_create.model_dump()
    loc_dict["dateCreation"] = datetime.utcnow()
    loc_dict["_id"] = ObjectId()
    
    # Vérifier le niveau de hiérarchie si parent_id est fourni
    if loc_dict.get('parent_id'):
        parent_id = loc_dict['parent_id']
        level = 0
        
        # Remonter la hiérarchie pour calculer le niveau
        while parent_id and level < 3:
            parent = await db.locations.find_one({"_id": ObjectId(parent_id)})
            if parent:
                level += 1
                parent_id = parent.get('parent_id')
            else:
                break
        
        # Limiter à 3 niveaux (0, 1, 2)
        if level >= 3:
            raise HTTPException(
                status_code=400, 
                detail="Limite de hiérarchie atteinte. Maximum 3 niveaux de sous-zones."
            )
    
    await db.locations.insert_one(loc_dict)
    
    loc_data = serialize_doc(loc_dict)
    loc_data['level'] = 0
    loc_data['hasChildren'] = False
    
    return Location(**loc_data)

@api_router.put("/locations/{loc_id}", response_model=Location)
async def update_location(loc_id: str, loc_update: LocationUpdate, current_user: dict = Depends(get_current_user)):
    """Modifier une zone"""
    try:
        update_data = {k: v for k, v in loc_update.model_dump().items() if v is not None}
        
        # Si on change le parent_id, vérifier la hiérarchie
        if 'parent_id' in update_data and update_data['parent_id']:
            parent_id = update_data['parent_id']
            level = 0
            
            while parent_id and level < 3:
                parent = await db.locations.find_one({"_id": ObjectId(parent_id)})
                if parent:
                    level += 1
                    parent_id = parent.get('parent_id')
                else:
                    break
            
            if level >= 3:
                raise HTTPException(
                    status_code=400,
                    detail="Limite de hiérarchie atteinte. Maximum 3 niveaux de sous-zones."
                )
        
        await db.locations.update_one(
            {"_id": ObjectId(loc_id)},
            {"$set": update_data}
        )
        
        loc = await db.locations.find_one({"_id": ObjectId(loc_id)})
        loc_data = serialize_doc(loc)
        
        # Calculer le niveau
        level = 0
        parent_id = loc.get('parent_id')
        while parent_id and level < 3:
            parent = await db.locations.find_one({"_id": ObjectId(parent_id)})
            if parent:
                level += 1
                parent_id = parent.get('parent_id')
            else:
                break
        loc_data['level'] = level
        loc_data['hasChildren'] = await db.locations.count_documents({"parent_id": loc_id}) > 0
        
        if loc.get('parent_id'):
            parent = await db.locations.find_one({"_id": ObjectId(loc.get('parent_id'))})
            if parent:
                loc_data['parent'] = {
                    "id": str(parent["_id"]),
                    "nom": parent.get("nom")
                }
        
        return Location(**loc_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.delete("/locations/{loc_id}")
async def delete_location(loc_id: str, current_user: dict = Depends(get_current_user)):
    """Supprimer une zone et ses sous-zones"""
    try:
        # Vérifier s'il y a des sous-zones
        children_count = await db.locations.count_documents({"parent_id": loc_id})
        if children_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Impossible de supprimer cette zone car elle contient {children_count} sous-zone(s). Supprimez d'abord les sous-zones."
            )
        
        # Vérifier s'il y a des équipements liés
        equipment_count = await db.equipments.count_documents({"emplacement_id": loc_id})
        if equipment_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Impossible de supprimer cette zone car elle contient {equipment_count} équipement(s)."
            )
        
        result = await db.locations.delete_one({"_id": ObjectId(loc_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Zone non trouvée")
        return {"message": "Zone supprimée"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== INVENTORY ROUTES ====================
@api_router.get("/inventory", response_model=List[Inventory])
async def get_inventory(current_user: dict = Depends(get_current_user)):
    """Liste tous les articles de l'inventaire"""
    inventory = await db.inventory.find().to_list(1000)
    return [Inventory(**serialize_doc(item)) for item in inventory]

@api_router.post("/inventory", response_model=Inventory)
async def create_inventory_item(inv_create: InventoryCreate, current_user: dict = Depends(get_current_user)):
    """Créer un nouvel article dans l'inventaire"""
    inv_dict = inv_create.model_dump()
    inv_dict["dateCreation"] = datetime.utcnow()
    inv_dict["derniereModification"] = datetime.utcnow()
    inv_dict["_id"] = ObjectId()
    
    await db.inventory.insert_one(inv_dict)
    
    return Inventory(**serialize_doc(inv_dict))

@api_router.put("/inventory/{inv_id}", response_model=Inventory)
async def update_inventory_item(inv_id: str, inv_update: InventoryUpdate, current_user: dict = Depends(get_current_user)):
    """Modifier un article de l'inventaire"""
    try:
        update_data = {k: v for k, v in inv_update.model_dump().items() if v is not None}
        update_data["derniereModification"] = datetime.utcnow()
        
        await db.inventory.update_one(
            {"_id": ObjectId(inv_id)},
            {"$set": update_data}
        )
        
        inv = await db.inventory.find_one({"_id": ObjectId(inv_id)})
        return Inventory(**serialize_doc(inv))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.delete("/inventory/{inv_id}")
async def delete_inventory_item(inv_id: str, current_user: dict = Depends(get_current_user)):
    """Supprimer un article de l'inventaire"""
    try:
        result = await db.inventory.delete_one({"_id": ObjectId(inv_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Article non trouvé")
        return {"message": "Article supprimé"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== PREVENTIVE MAINTENANCE ROUTES ====================
@api_router.get("/preventive-maintenance", response_model=List[PreventiveMaintenance])
async def get_preventive_maintenance(current_user: dict = Depends(get_current_user)):
    """Liste toutes les maintenances préventives"""
    pm_list = await db.preventive_maintenance.find().to_list(1000)
    
    for pm in pm_list:
        pm["id"] = str(pm["_id"])
        del pm["_id"]
        
        if pm.get("equipement_id"):
            pm["equipement"] = await get_equipment_by_id(pm["equipement_id"])
        if pm.get("assigne_a_id"):
            pm["assigneA"] = await get_user_by_id(pm["assigne_a_id"])
    
    return [PreventiveMaintenance(**pm) for pm in pm_list]

@api_router.post("/preventive-maintenance", response_model=PreventiveMaintenance)
async def create_preventive_maintenance(pm_create: PreventiveMaintenanceCreate, current_user: dict = Depends(get_current_user)):
    """Créer une nouvelle maintenance préventive"""
    pm_dict = pm_create.model_dump()
    pm_dict["dateCreation"] = datetime.utcnow()
    pm_dict["derniereMaintenance"] = None
    pm_dict["_id"] = ObjectId()
    
    await db.preventive_maintenance.insert_one(pm_dict)
    
    pm = serialize_doc(pm_dict)
    if pm.get("equipement_id"):
        pm["equipement"] = await get_equipment_by_id(pm["equipement_id"])
    if pm.get("assigne_a_id"):
        pm["assigneA"] = await get_user_by_id(pm["assigne_a_id"])
    
    return PreventiveMaintenance(**pm)

@api_router.put("/preventive-maintenance/{pm_id}", response_model=PreventiveMaintenance)
async def update_preventive_maintenance(pm_id: str, pm_update: PreventiveMaintenanceUpdate, current_user: dict = Depends(get_current_user)):
    """Modifier une maintenance préventive"""
    try:
        update_data = {k: v for k, v in pm_update.model_dump().items() if v is not None}
        
        await db.preventive_maintenance.update_one(
            {"_id": ObjectId(pm_id)},
            {"$set": update_data}
        )
        
        pm = await db.preventive_maintenance.find_one({"_id": ObjectId(pm_id)})
        pm = serialize_doc(pm)
        
        if pm.get("equipement_id"):
            pm["equipement"] = await get_equipment_by_id(pm["equipement_id"])
        if pm.get("assigne_a_id"):
            pm["assigneA"] = await get_user_by_id(pm["assigne_a_id"])
        
        return PreventiveMaintenance(**pm)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.delete("/preventive-maintenance/{pm_id}")
async def delete_preventive_maintenance(pm_id: str, current_user: dict = Depends(get_current_user)):
    """Supprimer une maintenance préventive"""
    try:
        result = await db.preventive_maintenance.delete_one({"_id": ObjectId(pm_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Maintenance préventive non trouvée")
        return {"message": "Maintenance préventive supprimée"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== USERS ROUTES ====================
@api_router.get("/users", response_model=List[User])
async def get_users(current_user: dict = Depends(get_current_user)):
    """Liste tous les utilisateurs"""
    users = await db.users.find().to_list(1000)
    return [User(**serialize_doc(user)) for user in users]

@api_router.put("/users/{user_id}", response_model=User)
async def update_user(user_id: str, user_update: UserUpdate, current_user: dict = Depends(get_current_admin_user)):
    """Modifier un utilisateur (admin uniquement)"""
    try:
        update_data = {k: v for k, v in user_update.model_dump().items() if v is not None}
        
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        return User(**serialize_doc(user))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_admin_user)):
    """Supprimer un utilisateur (admin uniquement)"""
    try:
        # Empêcher de se supprimer soi-même
        if str(user_id) == str(current_user.get('id')):
            raise HTTPException(status_code=400, detail="Vous ne pouvez pas vous supprimer vous-même")
        
        result = await db.users.delete_one({"_id": ObjectId(user_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        return {"message": "Utilisateur supprimé"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/users/invite", response_model=User)
async def invite_user(user_invite: UserInvite, current_user: dict = Depends(get_current_admin_user)):
    """Inviter un nouveau membre (admin uniquement)"""
    # Vérifier si l'utilisateur existe déjà
    existing_user = await db.users.find_one({"email": user_invite.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un utilisateur avec cet email existe déjà"
        )
    
    # Générer un mot de passe temporaire
    import secrets
    import string
    temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
    hashed_password = get_password_hash(temp_password)
    
    # Définir les permissions par défaut selon le rôle
    if user_invite.permissions is None:
        if user_invite.role == UserRole.ADMIN:
            permissions = {
                "dashboard": {"view": True, "edit": True, "delete": True},
                "workOrders": {"view": True, "edit": True, "delete": True},
                "assets": {"view": True, "edit": True, "delete": True},
                "preventiveMaintenance": {"view": True, "edit": True, "delete": True},
                "inventory": {"view": True, "edit": True, "delete": True},
                "locations": {"view": True, "edit": True, "delete": True},
                "vendors": {"view": True, "edit": True, "delete": True},
                "reports": {"view": True, "edit": True, "delete": True}
            }
        elif user_invite.role == UserRole.TECHNICIEN:
            permissions = {
                "dashboard": {"view": True, "edit": False, "delete": False},
                "workOrders": {"view": True, "edit": True, "delete": False},
                "assets": {"view": True, "edit": True, "delete": False},
                "preventiveMaintenance": {"view": True, "edit": True, "delete": False},
                "inventory": {"view": True, "edit": True, "delete": False},
                "locations": {"view": True, "edit": False, "delete": False},
                "vendors": {"view": True, "edit": False, "delete": False},
                "reports": {"view": True, "edit": False, "delete": False}
            }
        else:  # VISUALISEUR
            permissions = {
                "dashboard": {"view": True, "edit": False, "delete": False},
                "workOrders": {"view": True, "edit": False, "delete": False},
                "assets": {"view": True, "edit": False, "delete": False},
                "preventiveMaintenance": {"view": True, "edit": False, "delete": False},
                "inventory": {"view": True, "edit": False, "delete": False},
                "locations": {"view": True, "edit": False, "delete": False},
                "vendors": {"view": True, "edit": False, "delete": False},
                "reports": {"view": True, "edit": False, "delete": False}
            }
    else:
        permissions = user_invite.permissions.model_dump()
    
    # Créer l'utilisateur
    user_dict = {
        "nom": user_invite.nom,
        "prenom": user_invite.prenom,
        "email": user_invite.email,
        "telephone": user_invite.telephone,
        "role": user_invite.role,
        "password": hashed_password,
        "statut": "actif",
        "dateCreation": datetime.utcnow(),
        "derniereConnexion": None,
        "permissions": permissions,
        "_id": ObjectId()
    }
    
    await db.users.insert_one(user_dict)
    
    # TODO: Envoyer un email avec le mot de passe temporaire
    # Pour l'instant, on log juste le mot de passe (À REMPLACER EN PRODUCTION)
    logger.info(f"Utilisateur {user_invite.email} créé avec mot de passe temporaire: {temp_password}")
    
    return User(**serialize_doc(user_dict))

@api_router.get("/users/{user_id}/permissions", response_model=UserPermissions)
async def get_user_permissions(user_id: str, current_user: dict = Depends(get_current_user)):
    """Obtenir les permissions d'un utilisateur"""
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        permissions = user.get("permissions", {})
        return UserPermissions(**permissions)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.put("/users/{user_id}/permissions", response_model=User)
async def update_user_permissions(
    user_id: str, 
    permissions_update: UserPermissionsUpdate, 
    current_user: dict = Depends(get_current_admin_user)
):
    """Mettre à jour les permissions d'un utilisateur (admin uniquement)"""
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        # Empêcher de modifier ses propres permissions
        if str(user_id) == str(current_user.get('id')):
            raise HTTPException(status_code=400, detail="Vous ne pouvez pas modifier vos propres permissions")
        
        permissions_dict = permissions_update.permissions.model_dump()
        
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"permissions": permissions_dict}}
        )
        
        updated_user = await db.users.find_one({"_id": ObjectId(user_id)})
        return User(**serialize_doc(updated_user))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==================== VENDORS ROUTES ====================
@api_router.get("/vendors", response_model=List[Vendor])
async def get_vendors(current_user: dict = Depends(get_current_user)):
    """Liste tous les fournisseurs"""
    vendors = await db.vendors.find().to_list(1000)
    return [Vendor(**serialize_doc(vendor)) for vendor in vendors]

@api_router.post("/vendors", response_model=Vendor)
async def create_vendor(vendor_create: VendorCreate, current_user: dict = Depends(get_current_user)):
    """Créer un nouveau fournisseur"""
    vendor_dict = vendor_create.model_dump()
    vendor_dict["dateCreation"] = datetime.utcnow()
    vendor_dict["_id"] = ObjectId()
    
    await db.vendors.insert_one(vendor_dict)
    
    return Vendor(**serialize_doc(vendor_dict))

@api_router.put("/vendors/{vendor_id}", response_model=Vendor)
async def update_vendor(vendor_id: str, vendor_update: VendorUpdate, current_user: dict = Depends(get_current_user)):
    """Modifier un fournisseur"""
    try:
        update_data = {k: v for k, v in vendor_update.model_dump().items() if v is not None}
        
        await db.vendors.update_one(
            {"_id": ObjectId(vendor_id)},
            {"$set": update_data}
        )
        
        vendor = await db.vendors.find_one({"_id": ObjectId(vendor_id)})
        return Vendor(**serialize_doc(vendor))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.delete("/vendors/{vendor_id}")
async def delete_vendor(vendor_id: str, current_user: dict = Depends(get_current_user)):
    """Supprimer un fournisseur"""
    try:
        result = await db.vendors.delete_one({"_id": ObjectId(vendor_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Fournisseur non trouvé")
        return {"message": "Fournisseur supprimé"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== PURCHASE HISTORY ROUTES ====================
@api_router.get("/purchase-history/grouped")
async def get_purchase_history_grouped(current_user: dict = Depends(get_current_user)):
    """Liste tous les achats groupés par N° Commande"""
    purchases = await db.purchase_history.find().sort("dateCreation", -1).to_list(5000)
    
    # Grouper par numeroCommande
    grouped = {}
    for p in purchases:
        num_cmd = p.get('numeroCommande')
        if not num_cmd:
            continue
            
        if num_cmd not in grouped:
            # Utiliser Fournisseur2 (colonne M) si disponible, sinon fournisseur
            fournisseur_display = p.get('Fournisseur2') or p.get('fournisseur', 'Inconnu')
            
            grouped[num_cmd] = {
                'numeroCommande': num_cmd,
                'fournisseur': fournisseur_display,
                'dateCreation': p.get('dateCreation'),
                'site': p.get('site'),
                'items': [],
                'montantTotal': 0.0,
                'itemCount': 0
            }
        
        # Ajouter l'item au groupe
        item_data = {
            'article': p.get('article'),
            'description': p.get('description'),
            'quantite': p.get('quantite', 0.0),
            'montantLigneHT': p.get('montantLigneHT', 0.0),
            'numeroReception': p.get('numeroReception'),
            'groupeStatistique': p.get('groupeStatistique')
        }
        
        grouped[num_cmd]['items'].append(item_data)
        grouped[num_cmd]['montantTotal'] += item_data['montantLigneHT']
        grouped[num_cmd]['itemCount'] += 1
    
    # Convertir en liste
    result = list(grouped.values())
    return result


@api_router.delete("/purchase-history/all")
async def delete_all_purchase_history(current_user: dict = Depends(get_current_admin_user)):
    """Supprimer tout l'historique d'achat (admin uniquement)"""
    result = await db.purchase_history.delete_many({})
    return {
        "message": f"{result.deleted_count} achats supprimés",
        "deleted_count": result.deleted_count
    }


@api_router.get("/purchase-history", response_model=List[PurchaseHistory])
async def get_purchase_history(current_user: dict = Depends(get_current_user)):
    """Liste tous les achats"""
    purchases = await db.purchase_history.find().sort("dateCreation", -1).to_list(5000)
    
    # Filtrer pour ne garder que les champs du modèle PurchaseHistory
    allowed_fields = {
        '_id', 'id', 'fournisseur', 'numeroCommande', 'numeroReception', 
        'dateCreation', 'article', 'description', 'groupeStatistique',
        'quantite', 'montantLigneHT', 'quantiteRetournee', 'site', 
        'creationUser', 'dateEnregistrement'
    }
    
    result = []
    for p in purchases:
        # Ne garder que les champs autorisés
        filtered_doc = {k: v for k, v in p.items() if k in allowed_fields}
        
        # S'assurer que les champs obligatoires existent avec des valeurs par défaut
        if 'montantLigneHT' not in filtered_doc or filtered_doc['montantLigneHT'] is None:
            filtered_doc['montantLigneHT'] = 0.0
        if 'quantite' not in filtered_doc or filtered_doc['quantite'] is None:
            filtered_doc['quantite'] = 0.0
        if 'quantiteRetournee' not in filtered_doc:
            filtered_doc['quantiteRetournee'] = 0.0
        
        try:
            result.append(PurchaseHistory(**serialize_doc(filtered_doc)))
        except Exception as e:
            logger.error(f"Erreur serialization purchase {filtered_doc.get('numeroCommande')}: {e}")
            continue
    
    return result

@api_router.get("/purchase-history/stats")
async def get_purchase_stats(current_user: dict = Depends(get_current_user)):
    """Statistiques détaillées des achats"""
    
    # Total des achats
    all_purchases = await db.purchase_history.find().to_list(10000)
    
    if not all_purchases:
        return {
            "totalAchats": 0,
            "montantTotal": 0,
            "quantiteTotale": 0,
            "parFournisseur": [],
            "parMois": [],
            "parSite": [],
            "parGroupeStatistique": [],
            "articlesTop": []
        }
    
    total_achats = len(all_purchases)
    montant_total = sum(p.get("montantLigneHT", 0) for p in all_purchases)
    
    # Compter les commandes uniques (pas les lignes)
    commandes_uniques = set()
    for p in all_purchases:
        num_cmd = p.get("numeroCommande")
        if num_cmd:
            commandes_uniques.add(num_cmd)
    
    commandes_totales = len(commandes_uniques)
    
    # Par fournisseur (utiliser Fournisseur2 si disponible)
    fournisseurs = {}
    for p in all_purchases:
        fournisseur = p.get("Fournisseur2") or p.get("fournisseur", "Inconnu")
        if fournisseur not in fournisseurs:
            fournisseurs[fournisseur] = {"montant": 0, "quantite": 0, "count": 0}
        fournisseurs[fournisseur]["montant"] += p.get("montantLigneHT", 0)
        fournisseurs[fournisseur]["quantite"] += p.get("quantite", 0)
        fournisseurs[fournisseur]["count"] += 1
    
    par_fournisseur = [
        {
            "fournisseur": k,
            "montant": v["montant"],
            "quantite": v["quantite"],
            "count": v["count"],
            "pourcentage": round((v["montant"] / montant_total * 100) if montant_total > 0 else 0, 2)
        }
        for k, v in sorted(fournisseurs.items(), key=lambda x: x[1]["montant"], reverse=True)
    ]
    
    # Par mois
    mois_dict = {}
    for p in all_purchases:
        date_creation = p.get("dateCreation")
        if date_creation:
            if isinstance(date_creation, str):
                date_creation = datetime.fromisoformat(date_creation.replace('Z', '+00:00'))
            mois_annee = date_creation.strftime("%Y-%m")
            if mois_annee not in mois_dict:
                mois_dict[mois_annee] = {"montant": 0, "quantite": 0, "count": 0}
            mois_dict[mois_annee]["montant"] += p.get("montantLigneHT", 0)
            mois_dict[mois_annee]["quantite"] += p.get("quantite", 0)
            mois_dict[mois_annee]["count"] += 1
    
    par_mois = [
        {"mois": k, "montant": v["montant"], "quantite": v["quantite"], "count": v["count"]}
        for k, v in sorted(mois_dict.items())
    ]
    
    # Par site
    sites = {}
    for p in all_purchases:
        site = p.get("site", "Non défini")
        if site not in sites:
            sites[site] = {"montant": 0, "quantite": 0, "count": 0}
        sites[site]["montant"] += p.get("montantLigneHT", 0)
        sites[site]["quantite"] += p.get("quantite", 0)
        sites[site]["count"] += 1
    
    par_site = [
        {"site": k, "montant": v["montant"], "quantite": v["quantite"], "count": v["count"]}
        for k, v in sorted(sites.items(), key=lambda x: x[1]["montant"], reverse=True)
    ]
    
    # Par groupe statistique
    groupes = {}
    for p in all_purchases:
        groupe = p.get("groupeStatistique", "Non défini")
        if groupe not in groupes:
            groupes[groupe] = {"montant": 0, "quantite": 0, "count": 0}
        groupes[groupe]["montant"] += p.get("montantLigneHT", 0)
        groupes[groupe]["quantite"] += p.get("quantite", 0)
        groupes[groupe]["count"] += 1
    
    par_groupe = [
        {"groupe": k, "montant": v["montant"], "quantite": v["quantite"], "count": v["count"]}
        for k, v in sorted(groupes.items(), key=lambda x: x[1]["montant"], reverse=True)
    ]
    
    # Articles top
    articles = {}
    for p in all_purchases:
        article = p.get("article", "Inconnu")
        if article not in articles:
            articles[article] = {"montant": 0, "quantite": 0, "count": 0, "description": p.get("description", "")}
        articles[article]["montant"] += p.get("montantLigneHT", 0)
        articles[article]["quantite"] += p.get("quantite", 0)
        articles[article]["count"] += 1
    
    articles_top = [
        {"article": k, **v}
        for k, v in sorted(articles.items(), key=lambda x: x[1]["montant"], reverse=True)[:20]
    ]
    
    return {
        "totalAchats": total_achats,
        "montantTotal": round(montant_total, 2),
        "quantiteTotale": round(quantite_totale, 2),
        "parFournisseur": par_fournisseur,
        "parMois": par_mois,
        "parSite": par_site,
        "parGroupeStatistique": par_groupe,
        "articlesTop": articles_top
    }

@api_router.post("/purchase-history", response_model=PurchaseHistory)
async def create_purchase(purchase: PurchaseHistoryCreate, current_user: dict = Depends(get_current_user)):
    """Créer un nouvel achat"""
    purchase_dict = purchase.model_dump()
    
    # Convertir datetime en ISO string si nécessaire
    if isinstance(purchase_dict.get("dateCreation"), datetime):
        purchase_dict["dateCreation"] = purchase_dict["dateCreation"].isoformat()
    
    purchase_dict["dateEnregistrement"] = datetime.utcnow()
    purchase_dict["_id"] = ObjectId()
    
    # Ajouter l'utilisateur créateur si non fourni
    if not purchase_dict.get("creationUser"):
        purchase_dict["creationUser"] = current_user.get("email")
    
    await db.purchase_history.insert_one(purchase_dict)
    
    return PurchaseHistory(**serialize_doc(purchase_dict))

@api_router.put("/purchase-history/{purchase_id}", response_model=PurchaseHistory)
async def update_purchase(purchase_id: str, purchase_update: PurchaseHistoryUpdate, current_user: dict = Depends(get_current_user)):
    """Modifier un achat"""
    try:
        update_data = {k: v for k, v in purchase_update.model_dump().items() if v is not None}
        
        # Convertir datetime en ISO string si nécessaire
        if "dateCreation" in update_data and isinstance(update_data["dateCreation"], datetime):
            update_data["dateCreation"] = update_data["dateCreation"].isoformat()
        
        await db.purchase_history.update_one(
            {"_id": ObjectId(purchase_id)},
            {"$set": update_data}
        )
        
        purchase = await db.purchase_history.find_one({"_id": ObjectId(purchase_id)})
        return PurchaseHistory(**serialize_doc(purchase))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.delete("/purchase-history/{purchase_id}")
async def delete_purchase(purchase_id: str, current_user: dict = Depends(get_current_user)):
    """Supprimer un achat"""
    try:
        result = await db.purchase_history.delete_one({"_id": ObjectId(purchase_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Achat non trouvé")
        return {"message": "Achat supprimé"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== REPORTS/ANALYTICS ROUTES ====================
@api_router.get("/reports/analytics")
async def get_analytics(current_user: dict = Depends(get_current_user)):
    """Obtenir les données analytiques générales"""
    # Work orders stats
    total_wo = await db.work_orders.count_documents({})
    wo_by_status = {}
    for status in ["OUVERT", "EN_COURS", "EN_ATTENTE", "TERMINE"]:
        count = await db.work_orders.count_documents({"statut": status})
        wo_by_status[status] = count
    
    wo_by_priority = {}
    for priority in ["HAUTE", "MOYENNE", "BASSE", "AUCUNE"]:
        count = await db.work_orders.count_documents({"priorite": priority})
        wo_by_priority[priority] = count
    
    # Equipment stats
    eq_by_status = {}
    for status in ["OPERATIONNEL", "EN_MAINTENANCE", "HORS_SERVICE"]:
        count = await db.equipments.count_documents({"statut": status})
        eq_by_status[status] = count
    
    # Simple mock data for costs and time response
    analytics = {
        "workOrdersParStatut": wo_by_status,
        "workOrdersParPriorite": wo_by_priority,
        "equipementsParStatut": eq_by_status,
        "coutsMaintenance": {
            "janvier": 4500,
            "decembre": 3200,
            "novembre": 2800,
            "octobre": 3500,
            "septembre": 2900,
            "aout": 3100
        },
        "tempsReponse": {
            "moyen": 2.5,
            "median": 2,
            "min": 1,
            "max": 6
        },
        "tauxRealisation": 87,
        "nombreMaintenancesPrev": await db.preventive_maintenance.count_documents({"statut": "ACTIF"}),
        "nombreMaintenancesCorrectives": await db.work_orders.count_documents({"priorite": {"$ne": "AUCUNE"}})
    }
    
    return analytics

# ==================== IMPORT/EXPORT ROUTES ====================
EXPORT_MODULES = {
    "work-orders": "work_orders",
    "equipments": "equipments",
    "users": "users",
    "inventory": "inventory",
    "locations": "locations",
    "vendors": "vendors",
    "purchase-history": "purchase_history"
}

@api_router.get("/export/{module}")
async def export_data(
    module: str,
    format: str = "csv",  # csv ou xlsx
    current_user: dict = Depends(get_current_admin_user)
):
    """Exporter les données d'un module (admin uniquement)"""
    try:
        if module not in EXPORT_MODULES and module != "all":
            raise HTTPException(status_code=400, detail="Module invalide")
        
        # Préparer les données
        data_to_export = {}
        
        if module == "all":
            modules_to_export = EXPORT_MODULES
        else:
            modules_to_export = {module: EXPORT_MODULES[module]}
        
        for mod_name, collection_name in modules_to_export.items():
            items = await db[collection_name].find().to_list(10000)
            
            # Nettoyer les données
            cleaned_items = []
            for item in items:
                cleaned_item = {k: v for k, v in item.items() if k != "_id"}
                cleaned_item["id"] = str(item["_id"])
                
                # Convertir les dates en strings
                for key, value in cleaned_item.items():
                    if isinstance(value, datetime):
                        cleaned_item[key] = value.isoformat()
                    elif isinstance(value, ObjectId):
                        cleaned_item[key] = str(value)
                    elif isinstance(value, dict) or isinstance(value, list):
                        cleaned_item[key] = str(value)
                
                cleaned_items.append(cleaned_item)
            
            data_to_export[mod_name] = cleaned_items
        
        # Générer le fichier
        if format == "csv":
            # Pour CSV, un fichier par module
            if len(data_to_export) == 1:
                mod_name = list(data_to_export.keys())[0]
                df = pd.DataFrame(data_to_export[mod_name])
                
                output = io.StringIO()
                df.to_csv(output, index=False, encoding='utf-8')
                output.seek(0)
                
                return StreamingResponse(
                    io.BytesIO(output.getvalue().encode('utf-8')),
                    media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={mod_name}.csv"}
                )
            else:
                # Pour "all", créer un zip avec plusieurs CSV
                raise HTTPException(status_code=400, detail="Pour exporter tout, utilisez le format xlsx")
        
        elif format == "xlsx":
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                for mod_name, items in data_to_export.items():
                    df = pd.DataFrame(items)
                    sheet_name = mod_name[:31]  # Excel limite à 31 caractères
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            output.seek(0)
            filename = "export_all.xlsx" if module == "all" else f"{module}.xlsx"
            
            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        
        else:
            raise HTTPException(status_code=400, detail="Format invalide (csv ou xlsx)")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@api_router.get("/purchase-history/template")
async def download_purchase_template(format: str = "csv", current_user: dict = Depends(get_current_user)):
    """Télécharger un template vide pour l'import des achats"""
    
    # Structure du template avec les noms de colonnes françaises
    template_data = {
        "Fournisseur": ["Exemple Fournisseur"],
        "N° Commande": ["CMD-001"],
        "N° reception": ["REC-001"],
        "Date de création": ["19/09/2025"],
        "Article": ["Article exemple"],
        "Description 1": ["Description de l'article"],
        "Groupe statistique": ["STK-A"],
        "STK quantité": ["10,00"],
        "Montant ligne HT": ["1500,50"],
        "Quantité retournée": ["0,00"],
        "Site": ["Site Principal"],
        "Creation user": ["admin@example.com"]
    }
    
    df = pd.DataFrame(template_data)
    
    # Générer le fichier CSV avec point-virgule
    output = io.StringIO()
    df.to_csv(output, index=False, sep=';')
    content = output.getvalue()
    
    return Response(
        content=content.encode('utf-8'),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=template_historique_achat.csv"
        }
    )


@api_router.post("/import/{module}")
async def import_data(
    module: str,
    mode: str = "add",  # add ou replace
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_admin_user)
):
    """Importer les données d'un module (admin uniquement)"""
    try:
        if module not in EXPORT_MODULES:
            raise HTTPException(status_code=400, detail="Module invalide")
        
        collection_name = EXPORT_MODULES[module]
        
        # Lire le fichier
        content = await file.read()
        
        # Mapping des colonnes pour purchase-history (basé sur Requêteur.xlsx)
        purchase_column_mapping = {
            # Colonnes avec espaces en trop
            "Fournisseur": "fournisseur",
            "N° Commande ": "numeroCommande",  # Espace à la fin
            "N° Commande": "numeroCommande",
            "N° reception": "numeroReception",
            "Date de création": "dateCreation",
            "Article": "article",
            "Description 1": "description",  # Nom exact du CSV
            "Description": "description",
            "Groupe statistique": "groupeStatistique",
            "Groupe statistique STK": "groupeStatistique",
            "STK quantité": "quantite",  # Nom exact du CSV
            "quantité": "quantite",
            "Quantité": "quantite",
            "Montant ligne HT": "montantLigneHT",
            "Quantité retournée": "quantiteRetournee",
            "Site ": "site",  # Espace à la fin
            "Site": "site",
            "Creation user": "creationUser"
        }
        
        try:
            if file.filename.endswith('.csv'):
                # Détecter automatiquement le séparateur CSV
                content_str = content.decode('utf-8', errors='ignore')
                # Essayer de détecter le séparateur
                first_line = content_str.split('\n')[0] if content_str else ""
                
                # Compter les séparateurs potentiels
                comma_count = first_line.count(',')
                semicolon_count = first_line.count(';')
                tab_count = first_line.count('\t')
                
                # Choisir le séparateur le plus fréquent
                if semicolon_count > comma_count and semicolon_count > tab_count:
                    separator = ';'
                elif tab_count > comma_count:
                    separator = '\t'
                else:
                    separator = ','
                
                logger.info(f"📋 Séparateur détecté: '{separator}' (virgule={comma_count}, point-virgule={semicolon_count}, tab={tab_count})")
                
                df = pd.read_csv(io.BytesIO(content), sep=separator, encoding='utf-8')
                logger.info(f"✅ CSV lu avec succès: {len(df)} lignes, {len(df.columns)} colonnes")
                logger.info(f"📋 Colonnes: {list(df.columns)}")
                
            elif file.filename.endswith(('.xlsx', '.xls', '.xlsb')):
                # Stratégie multi-tentatives pour les fichiers Excel
                df = None
                errors = []
                
                # Tentative 1: openpyxl (moderne, .xlsx)
                if file.filename.endswith('.xlsx'):
                    try:
                        df = pd.read_excel(io.BytesIO(content), engine='openpyxl')
                        logger.info("✅ Fichier lu avec openpyxl")
                    except Exception as e1:
                        errors.append(f"openpyxl: {str(e1)[:100]}")
                
                # Tentative 2: xlrd (ancien format .xls)
                if df is None:
                    try:
                        df = pd.read_excel(io.BytesIO(content), engine='xlrd')
                        logger.info("✅ Fichier lu avec xlrd")
                    except Exception as e2:
                        errors.append(f"xlrd: {str(e2)[:100]}")
                
                # Tentative 3: pyxlsb (format binaire .xlsb)
                if df is None and file.filename.endswith('.xlsb'):
                    try:
                        df = pd.read_excel(io.BytesIO(content), engine='pyxlsb')
                        logger.info("✅ Fichier lu avec pyxlsb")
                    except Exception as e3:
                        errors.append(f"pyxlsb: {str(e3)[:100]}")
                
                # Tentative 4: Méthode par défaut (sans engine spécifique)
                if df is None:
                    try:
                        df = pd.read_excel(io.BytesIO(content))
                        logger.info("✅ Fichier lu avec méthode par défaut")
                    except Exception as e4:
                        errors.append(f"default: {str(e4)[:100]}")
                
                # Si toutes les tentatives ont échoué
                if df is None:
                    error_msg = "Impossible de lire le fichier Excel. Erreurs:\n" + "\n".join(errors)
                    error_msg += "\n\n💡 Solutions:\n"
                    error_msg += "1. Ouvrez le fichier dans Excel et sauvegardez-le à nouveau\n"
                    error_msg += "2. Exportez en CSV depuis Excel: Fichier > Enregistrer sous > CSV\n"
                    error_msg += "3. Utilisez un fichier Excel plus simple sans styles complexes"
                    raise HTTPException(status_code=400, detail=error_msg)
            else:
                raise HTTPException(status_code=400, detail="Format de fichier non supporté (CSV, XLSX, XLS ou XLSB uniquement)")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Erreur de lecture: {str(e)}. Essayez de sauvegarder le fichier en CSV depuis Excel."
            )
        
        # Appliquer le mapping des colonnes pour purchase-history
        if module == "purchase-history":
            df = df.rename(columns=purchase_column_mapping)
            
            # Nettoyer les noms de colonnes (enlever espaces en trop)
            df.columns = df.columns.str.strip()
        
        # Convertir en dictionnaires
        items_to_import = df.to_dict('records')
        
        stats = {
            "total": len(items_to_import),
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "errors": []
        }
        
        for idx, item in enumerate(items_to_import):
            try:
                # Nettoyer les NaN
                cleaned_item = {k: v for k, v in item.items() if pd.notna(v)}
                
                # Traitement spécifique pour purchase-history
                if module == "purchase-history":
                    # S'assurer que les champs numériques sont corrects
                    for num_field in ["quantite", "montantLigneHT", "quantiteRetournee"]:
                        if num_field in cleaned_item:
                            try:
                                # Convertir les virgules en points pour les nombres français
                                value = cleaned_item[num_field]
                                if isinstance(value, str):
                                    # Remplacer virgule par point et enlever espaces
                                    value = value.replace(',', '.').replace(' ', '')
                                cleaned_item[num_field] = float(value)
                            except:
                                if num_field == "quantiteRetournee":
                                    cleaned_item[num_field] = 0.0
                                elif num_field == "quantite":
                                    logger.warning(f"Ligne {idx+1}: quantite invalide '{cleaned_item.get(num_field)}'")
                                    cleaned_item[num_field] = 0.0
                    
                    # Convertir les dates (format français DD/MM/YYYY)
                    if "dateCreation" in cleaned_item:
                        try:
                            date_val = cleaned_item["dateCreation"]
                            if isinstance(date_val, str):
                                # Format français DD/MM/YYYY
                                if '/' in date_val:
                                    parts = date_val.split('/')
                                    if len(parts) == 3:
                                        # Créer date au format ISO
                                        cleaned_item["dateCreation"] = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                                cleaned_item["dateCreation"] = datetime.fromisoformat(cleaned_item["dateCreation"])
                            elif hasattr(date_val, 'to_pydatetime'):
                                cleaned_item["dateCreation"] = date_val.to_pydatetime()
                        except Exception as e:
                            logger.warning(f"Ligne {idx+1}: date invalide '{cleaned_item.get('dateCreation')}': {e}")
                            pass
                    
                    # Ajouter dateEnregistrement et creationUser
                    cleaned_item["dateEnregistrement"] = datetime.utcnow()
                    if "creationUser" not in cleaned_item or not cleaned_item["creationUser"]:
                        cleaned_item["creationUser"] = current_user.get("email", "import")
                
                # Gérer l'ID
                item_id = cleaned_item.get('id')
                if item_id and 'id' in cleaned_item:
                    del cleaned_item['id']
                
                if mode == "replace" and item_id:
                    # Vérifier si l'item existe
                    existing = await db[collection_name].find_one({"_id": ObjectId(item_id)})
                    
                    if existing:
                        # Mettre à jour
                        await db[collection_name].replace_one(
                            {"_id": ObjectId(item_id)},
                            cleaned_item
                        )
                        stats["updated"] += 1
                    else:
                        # Insérer avec l'ID spécifié
                        cleaned_item["_id"] = ObjectId(item_id)
                        await db[collection_name].insert_one(cleaned_item)
                        stats["inserted"] += 1
                else:
                    # Mode add - toujours insérer un nouveau
                    if "_id" in cleaned_item:
                        del cleaned_item["_id"]
                    cleaned_item["_id"] = ObjectId()
                    await db[collection_name].insert_one(cleaned_item)
                    stats["inserted"] += 1
            
            except Exception as e:
                stats["skipped"] += 1
                stats["errors"].append(f"Ligne {stats['inserted'] + stats['updated'] + stats['skipped']}: {str(e)}")
        
        return stats
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
