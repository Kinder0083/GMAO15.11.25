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
from datetime import datetime, timedelta, timezone
from bson import ObjectId
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Import our models and dependencies
from models import *
from auth import get_password_hash, verify_password, create_access_token, decode_access_token
import dependencies
from dependencies import get_current_user, get_current_admin_user, check_permission, require_permission
import email_service
from audit_service import AuditService

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'gmao_iris')]

# Initialize dependencies with database
dependencies.set_database(db)

# Initialize audit service
audit_service = AuditService(db)

# Create the main app
app = FastAPI(title="GMAO Atlas API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialiser le scheduler pour les tâches automatiques
scheduler = AsyncIOScheduler()

# Fonction pour vérifier et créer automatiquement les bons de travail pour les maintenances échues
async def auto_check_preventive_maintenance():
    """Fonction exécutée automatiquement chaque jour pour vérifier les maintenances échues"""
    try:
        logger.info("🔄 Vérification automatique des maintenances préventives échues...")
        
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Trouver toutes les maintenances actives dont la date est aujourd'hui ou passée
        pm_list = await db.preventive_maintenances.find({
            "statut": "ACTIF",
            "prochaineMaintenance": {"$lte": today + timedelta(days=1)}
        }).to_list(length=None)
        
        created_count = 0
        updated_count = 0
        errors = []
        
        for pm in pm_list:
            try:
                # Récupérer l'équipement
                equipement = await db.equipments.find_one({"_id": ObjectId(pm["equipement_id"])})
                
                # Créer le bon de travail
                wo_id = str(uuid.uuid4())
                work_order = {
                    "_id": ObjectId(),
                    "id": wo_id,
                    "numero": f"PM-{datetime.utcnow().strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}",
                    "titre": f"Maintenance préventive: {pm['titre']}",
                    "description": f"Maintenance automatique générée depuis la planification préventive '{pm['titre']}'",
                    "type": "PREVENTIF",
                    "priorite": "NORMALE",
                    "statut": "OUVERT",
                    "equipement_id": pm["equipement_id"],
                    "emplacement_id": equipement.get("emplacement_id") if equipement else None,
                    "assigne_a_id": pm.get("assigne_a_id"),
                    "tempsEstime": pm.get("duree"),
                    "dateLimite": datetime.utcnow() + timedelta(days=7),
                    "dateCreation": datetime.utcnow(),
                    "createdBy": "system-auto",
                    "comments": [],
                    "attachments": [],
                    "historique": []
                }
                
                await db.work_orders.insert_one(work_order)
                created_count += 1
                logger.info(f"✅ Bon de travail créé: {work_order['numero']} pour PM '{pm['titre']}'")
                
                # Calculer la prochaine date de maintenance
                next_date = calculate_next_maintenance_date(pm["prochaineMaintenance"], pm["frequence"])
                
                # Mettre à jour la maintenance préventive
                await db.preventive_maintenances.update_one(
                    {"_id": pm["_id"]},
                    {
                        "$set": {
                            "prochaineMaintenance": next_date,
                            "derniereMaintenance": datetime.utcnow()
                        }
                    }
                )
                updated_count += 1
                logger.info(f"✅ Prochaine maintenance mise à jour: {next_date.strftime('%Y-%m-%d')} (fréquence: {pm['frequence']})")
                
            except Exception as e:
                error_msg = f"Erreur pour PM '{pm.get('titre', 'Unknown')}': {str(e)}"
                errors.append(error_msg)
                logger.error(f"❌ {error_msg}")
        
        logger.info(f"✅ Vérification terminée: {created_count} bons créés, {updated_count} maintenances mises à jour, {len(errors)} erreurs")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification automatique des maintenances: {str(e)}")

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
    user_dict["hashed_password"] = hashed_password
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
    password_valid = verify_password(login_request.password, user["hashed_password"])
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
    
    # Log dans l'audit
    await audit_service.log_action(
        user_id=user.get("id", str(user["_id"])),
        user_name=f"{user['prenom']} {user['nom']}",
        user_email=user["email"],
        action=ActionType.LOGIN,
        entity_type=EntityType.USER,
        entity_id=user.get("id", str(user["_id"])),
        entity_name=f"{user['prenom']} {user['nom']}"
    )
    
    # Create access token (valide 1 heure)
    access_token = create_access_token(
        data={"sub": str(user["_id"])},
        expires_delta=timedelta(hours=1)
    )
    
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
        
        # Construire l'URL de réinitialisation
        APP_URL = os.environ.get('APP_URL', 'http://localhost:3000')
        reset_url = f"{APP_URL}/reset-password?token={reset_token}"
        
        # Envoyer l'email de réinitialisation
        try:
            email_sent = email_service.send_password_reset_email(
                to_email=request.email,
                prenom=user.get('prenom', 'Utilisateur'),
                reset_url=reset_url
            )
            
            if email_sent:
                logger.info(f"Email de réinitialisation envoyé à {request.email}")
            else:
                logger.error(f"Échec de l'envoi de l'email de réinitialisation à {request.email}")
        except Exception as email_error:
            logger.error(f"Erreur lors de l'envoi de l'email de réinitialisation : {str(email_error)}")
        
        # Sauvegarder le token dans la base (pour invalider après usage)
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
                "$set": {"hashed_password": hashed_password},
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
    
    # Obtenir les permissions par défaut selon le rôle
    default_permissions = get_default_permissions_by_role(request.role)
    permissions = default_permissions.model_dump()
    
    # Si des permissions personnalisées sont fournies, les utiliser
    if hasattr(request, 'permissions') and request.permissions:
        permissions = request.permissions
    
    # Créer l'utilisateur
    user_dict = {
        "id": str(uuid.uuid4()),
        "nom": request.nom,
        "prenom": request.prenom,
        "email": request.email,
        "telephone": request.telephone or "",
        "role": request.role,
        "service": request.service,
        "hashed_password": hashed_password,
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
        
        # Obtenir les permissions par défaut selon le rôle
        default_permissions = get_default_permissions_by_role(role)
        permissions = default_permissions.model_dump()
        
        # Créer l'utilisateur
        user_dict = {
            "id": str(uuid.uuid4()),
            "nom": request.nom,
            "prenom": request.prenom,
            "email": email,
            "telephone": request.telephone or "",
            "role": role,
            "service": None,
            "hashed_password": hashed_password,
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
    
    if not verify_password(request.old_password, user["hashed_password"]):
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
                "hashed_password": new_hashed_password,
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
    
    if not verify_password(request.old_password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mot de passe actuel incorrect"
        )
    
    # Hasher le nouveau mot de passe
    new_hashed_password = get_password_hash(request.new_password)
    
    # Mettre à jour le mot de passe
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"hashed_password": new_hashed_password}}
    )
    
    logger.info(f"Mot de passe changé pour {user.get('email')}")
    
    return {"message": "Mot de passe changé avec succès"}

# ==================== WORK ORDERS ROUTES ====================
@api_router.get("/work-orders", response_model=List[WorkOrder])
async def get_work_orders(
    date_debut: str = None,
    date_fin: str = None,
    date_type: str = "creation",  # "creation" ou "echeance"
    current_user: dict = Depends(require_permission("workOrders", "view"))
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
            cleaned_attachments = []
            for att in wo["attachments"]:
                # Ignorer si att n'est pas un dict
                if not isinstance(att, dict):
                    continue
                if "_id" in att and isinstance(att["_id"], ObjectId):
                    att["_id"] = str(att["_id"])
                for key, value in att.items():
                    if isinstance(value, ObjectId):
                        att[key] = str(value)
                cleaned_attachments.append(att)
            wo["attachments"] = cleaned_attachments
        
        if wo.get("assigne_a_id"):
            wo["assigneA"] = await get_user_by_id(wo["assigne_a_id"])
        if wo.get("emplacement_id"):
            wo["emplacement"] = await get_location_by_id(wo["emplacement_id"])
        if wo.get("equipement_id"):
            wo["equipement"] = await get_equipment_by_id(wo["equipement_id"])
        
        # Ajouter le nom du créateur
        if wo.get("createdBy"):
            try:
                # Essayer de chercher par ObjectId
                creator = await db.users.find_one({"_id": ObjectId(wo["createdBy"])})
                if creator:
                    wo["createdByName"] = f"{creator.get('prenom', '')} {creator.get('nom', '')}".strip()
                else:
                    # Sinon essayer par le champ id (UUID)
                    creator = await db.users.find_one({"id": wo["createdBy"]})
                    if creator:
                        wo["createdByName"] = f"{creator.get('prenom', '')} {creator.get('nom', '')}".strip()
            except Exception as e:
                # Si ça échoue, laisser vide
                logger.error(f"Erreur lors de la recherche du créateur {wo.get('createdBy')}: {e}")
                pass
    
    # Ajouter un numero par défaut si manquant (pour compatibilité avec anciens ordres)
    for wo in work_orders:
        if "numero" not in wo or not wo["numero"]:
            wo["numero"] = "N/A"
    
    return [WorkOrder(**wo) for wo in work_orders]

@api_router.get("/work-orders/{wo_id}", response_model=WorkOrder)
async def get_work_order(wo_id: str, current_user: dict = Depends(get_current_user)):
    """Détails d'un ordre de travail"""
    try:
        # Chercher par le champ id (UUID) au lieu de _id
        wo = await db.work_orders.find_one({"id": wo_id})
        if not wo:
            raise HTTPException(status_code=404, detail="Ordre de travail non trouvé")
        
        wo = serialize_doc(wo)
        if wo.get("assigne_a_id"):
            wo["assigneA"] = await get_user_by_id(wo["assigne_a_id"])
        if wo.get("emplacement_id"):
            wo["emplacement"] = await get_location_by_id(wo["emplacement_id"])
        if wo.get("equipement_id"):
            wo["equipement"] = await get_equipment_by_id(wo["equipement_id"])
        
        # Ajouter le nom du créateur
        if wo.get("createdBy"):
            try:
                # Essayer de chercher par ObjectId
                creator = await db.users.find_one({"_id": ObjectId(wo["createdBy"])})
                if creator:
                    wo["createdByName"] = f"{creator.get('prenom', '')} {creator.get('nom', '')}".strip()
                else:
                    # Sinon essayer par le champ id (UUID)
                    creator = await db.users.find_one({"id": wo["createdBy"]})
                    if creator:
                        wo["createdByName"] = f"{creator.get('prenom', '')} {creator.get('nom', '')}".strip()
            except Exception as e:
                # Si ça échoue, laisser vide
                logger.error(f"Erreur lors de la recherche du créateur {wo.get('createdBy')}: {e}")
                pass
        
        # Ajouter un numero par défaut si manquant
        if "numero" not in wo or not wo["numero"]:
            wo["numero"] = "N/A"
        
        return WorkOrder(**wo)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/work-orders", response_model=WorkOrder)
async def create_work_order(wo_create: WorkOrderCreate, current_user: dict = Depends(require_permission("workOrders", "edit"))):
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
    wo_dict["comments"] = []  # Initialiser les commentaires
    wo_dict["createdBy"] = current_user.get("id")  # Ajouter le créateur
    wo_dict["_id"] = ObjectId()
    
    await db.work_orders.insert_one(wo_dict)
    
    # Log dans l'audit
    await audit_service.log_action(
        user_id=current_user["id"],
        user_name=f"{current_user['prenom']} {current_user['nom']}",
        user_email=current_user["email"],
        action=ActionType.CREATE,
        entity_type=EntityType.WORK_ORDER,
        entity_id=wo_dict.get("id"),
        entity_name=wo_dict["titre"],
        details=f"Ordre de travail #{numero} créé"
    )
    
    wo = serialize_doc(wo_dict)
    if wo.get("assigne_a_id"):
        wo["assigneA"] = await get_user_by_id(wo["assigne_a_id"])
    if wo.get("emplacement_id"):
        wo["emplacement"] = await get_location_by_id(wo["emplacement_id"])
    if wo.get("equipement_id"):
        wo["equipement"] = await get_equipment_by_id(wo["equipement_id"])
    
    return WorkOrder(**wo)

@api_router.put("/work-orders/{wo_id}", response_model=WorkOrder)
async def update_work_order(wo_id: str, wo_update: WorkOrderUpdate, current_user: dict = Depends(require_permission("workOrders", "edit"))):
    """Modifier un ordre de travail"""
    from dependencies import can_edit_work_order_status
    
    try:
        # Récupérer l'ordre de travail existant
        existing_wo = await db.work_orders.find_one({"_id": ObjectId(wo_id)})
        if not existing_wo:
            raise HTTPException(status_code=404, detail="Ordre de travail non trouvé")
        
        existing_wo["id"] = str(existing_wo["_id"])
        
        # Vérifier les permissions
        user_role = current_user.get("role")
        user_id = current_user.get("id")
        created_by = existing_wo.get("createdBy")
        assigne_a_id = existing_wo.get("assigne_a_id")
        
        # Admin : peut tout modifier
        if user_role == "ADMIN":
            can_full_edit = True
        # Technicien : peut modifier ce qu'il a créé
        elif user_role == "TECHNICIEN":
            can_full_edit = (created_by == user_id)
        # Visualiseur assigné : peut seulement modifier le statut
        elif user_role == "VISUALISEUR":
            can_full_edit = False
            # Vérifier si le visualiseur est assigné
            if assigne_a_id != user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Vous ne pouvez pas modifier cet ordre de travail"
                )
            # Le visualiseur ne peut modifier que le statut
            if wo_update.model_dump(exclude_unset=True).keys() != {'statut'}:
                raise HTTPException(
                    status_code=403,
                    detail="Les visualiseurs ne peuvent modifier que le statut"
                )
        else:
            raise HTTPException(status_code=403, detail="Permission refusée")
        
        # Si pas de permission complète et qu'on essaie de modifier autre chose que le statut
        if not can_full_edit:
            update_dict = wo_update.model_dump(exclude_unset=True)
            if len(update_dict) > 1 or (len(update_dict) == 1 and 'statut' not in update_dict):
                raise HTTPException(
                    status_code=403,
                    detail="Vous ne pouvez modifier que le statut de cet ordre de travail"
                )
        
        # Appliquer les modifications
        update_data = {k: v for k, v in wo_update.model_dump().items() if v is not None}
        
        if wo_update.statut == WorkOrderStatus.TERMINE and "dateTermine" not in update_data:
            update_data["dateTermine"] = datetime.utcnow()
        
        await db.work_orders.update_one(
            {"_id": ObjectId(wo_id)},
            {"$set": update_data}
        )
        
        # Log dans l'audit
        changes_desc = ", ".join([f"{k}: {v}" for k, v in update_data.items()])
        await audit_service.log_action(
            user_id=current_user["id"],
            user_name=f"{current_user['prenom']} {current_user['nom']}",
            user_email=current_user["email"],
            action=ActionType.UPDATE,
            entity_type=EntityType.WORK_ORDER,
            entity_id=existing_wo.get("id"),
            entity_name=existing_wo["titre"],
            details=f"Modifications: {changes_desc}",
            changes=update_data
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.delete("/work-orders/{wo_id}")
async def delete_work_order(wo_id: str, current_user: dict = Depends(require_permission("workOrders", "delete"))):
    """Supprimer un ordre de travail"""
    try:
        # Récupérer l'ordre de travail avant suppression pour le log
        wo = await db.work_orders.find_one({"_id": ObjectId(wo_id)})
        if not wo:
            raise HTTPException(status_code=404, detail="Ordre de travail non trouvé")
        
        result = await db.work_orders.delete_one({"_id": ObjectId(wo_id)})
        
        # Log dans l'audit
        await audit_service.log_action(
            user_id=current_user["id"],
            user_name=f"{current_user['prenom']} {current_user['nom']}",
            user_email=current_user["email"],
            action=ActionType.DELETE,
            entity_type=EntityType.WORK_ORDER,
            entity_id=wo.get("id"),
            entity_name=wo.get("titre", ""),
            details=f"Ordre de travail #{wo.get('numero')} supprimé"
        )
        
        return {"message": "Ordre de travail supprimé"}
    except HTTPException:
        raise
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
async def get_equipments(current_user: dict = Depends(require_permission("assets", "view"))):
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
async def create_equipment(eq_create: EquipmentCreate, current_user: dict = Depends(require_permission("assets", "edit"))):
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
    eq_dict["createdBy"] = current_user.get("id")  # Ajouter le créateur
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
async def update_equipment(eq_id: str, eq_update: EquipmentUpdate, current_user: dict = Depends(require_permission("assets", "edit"))):
    """Modifier un équipement"""
    from dependencies import can_edit_resource
    
    try:
        # Récupérer l'équipement existant
        existing_eq = await db.equipments.find_one({"_id": ObjectId(eq_id)})
        if not existing_eq:
            raise HTTPException(status_code=404, detail="Équipement non trouvé")
        
        existing_eq["id"] = str(existing_eq["_id"])
        
        # Vérifier les permissions (sauf admin, seulement le créateur peut modifier)
        if not can_edit_resource(current_user, existing_eq):
            raise HTTPException(
                status_code=403,
                detail="Vous ne pouvez modifier que les équipements que vous avez créés"
            )
        
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
    except HTTPException:
        raise
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
async def delete_equipment(eq_id: str, current_user: dict = Depends(require_permission("assets", "delete"))):
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
async def get_locations(current_user: dict = Depends(require_permission("locations", "view"))):
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
async def create_location(loc_create: LocationCreate, current_user: dict = Depends(require_permission("locations", "edit"))):
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
async def update_location(loc_id: str, loc_update: LocationUpdate, current_user: dict = Depends(require_permission("locations", "edit"))):
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
async def delete_location(loc_id: str, current_user: dict = Depends(require_permission("locations", "delete"))):
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
async def get_inventory(current_user: dict = Depends(require_permission("inventory", "view"))):
    """Liste tous les articles de l'inventaire"""
    inventory = await db.inventory.find().to_list(1000)
    return [Inventory(**serialize_doc(item)) for item in inventory]

@api_router.post("/inventory", response_model=Inventory)
async def create_inventory_item(inv_create: InventoryCreate, current_user: dict = Depends(require_permission("inventory", "edit"))):
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
async def get_preventive_maintenance(current_user: dict = Depends(require_permission("preventiveMaintenance", "view"))):
    """Liste toutes les maintenances préventives"""
    pm_list = await db.preventive_maintenances.find().to_list(1000)
    
    for pm in pm_list:
        pm["id"] = str(pm["_id"])
        del pm["_id"]
        
        if pm.get("equipement_id"):
            pm["equipement"] = await get_equipment_by_id(pm["equipement_id"])
        if pm.get("assigne_a_id"):
            pm["assigneA"] = await get_user_by_id(pm["assigne_a_id"])
    
    return [PreventiveMaintenance(**pm) for pm in pm_list]

@api_router.post("/preventive-maintenance", response_model=PreventiveMaintenance)
async def create_preventive_maintenance(pm_create: PreventiveMaintenanceCreate, current_user: dict = Depends(require_permission("preventiveMaintenance", "edit"))):
    """Créer une nouvelle maintenance préventive"""
    pm_dict = pm_create.model_dump()
    pm_dict["dateCreation"] = datetime.utcnow()
    pm_dict["derniereMaintenance"] = None
    pm_dict["_id"] = ObjectId()
    
    await db.preventive_maintenances.insert_one(pm_dict)
    
    pm = serialize_doc(pm_dict)
    if pm.get("equipement_id"):
        pm["equipement"] = await get_equipment_by_id(pm["equipement_id"])
    if pm.get("assigne_a_id"):
        pm["assigneA"] = await get_user_by_id(pm["assigne_a_id"])
    
    return PreventiveMaintenance(**pm)

@api_router.put("/preventive-maintenance/{pm_id}", response_model=PreventiveMaintenance)
async def update_preventive_maintenance(pm_id: str, pm_update: PreventiveMaintenanceUpdate, current_user: dict = Depends(require_permission("preventiveMaintenance", "edit"))):
    """Modifier une maintenance préventive"""
    try:
        update_data = {k: v for k, v in pm_update.model_dump().items() if v is not None}
        
        await db.preventive_maintenances.update_one(
            {"_id": ObjectId(pm_id)},
            {"$set": update_data}
        )
        
        pm = await db.preventive_maintenances.find_one({"_id": ObjectId(pm_id)})
        pm = serialize_doc(pm)
        
        if pm.get("equipement_id"):
            pm["equipement"] = await get_equipment_by_id(pm["equipement_id"])
        if pm.get("assigne_a_id"):
            pm["assigneA"] = await get_user_by_id(pm["assigne_a_id"])
        
        return PreventiveMaintenance(**pm)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.delete("/preventive-maintenance/{pm_id}")
async def delete_preventive_maintenance(pm_id: str, current_user: dict = Depends(require_permission("preventiveMaintenance", "delete"))):
    """Supprimer une maintenance préventive"""
    try:
        result = await db.preventive_maintenances.delete_one({"_id": ObjectId(pm_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Maintenance préventive non trouvée")
        return {"message": "Maintenance préventive supprimée"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def calculate_next_maintenance_date(current_date: datetime, frequency: str) -> datetime:
    """Calcule la prochaine date de maintenance selon la fréquence"""
    if frequency == "QUOTIDIENNE":
        return current_date + timedelta(days=1)
    elif frequency == "HEBDOMADAIRE":
        return current_date + timedelta(weeks=1)
    elif frequency == "MENSUELLE":
        # Ajouter un mois
        month = current_date.month
        year = current_date.year
        if month == 12:
            month = 1
            year += 1
        else:
            month += 1
        return current_date.replace(year=year, month=month)
    elif frequency == "ANNUELLE":
        return current_date.replace(year=current_date.year + 1)
    else:
        # Par défaut, mensuelle
        return current_date + timedelta(days=30)

@api_router.post("/preventive-maintenance/check-and-execute")
async def check_and_execute_due_maintenances(current_user: dict = Depends(get_current_admin_user)):
    """Vérifie et exécute MANUELLEMENT les maintenances échues (admin uniquement)"""
    try:
        logger.info(f"🔄 Vérification MANUELLE déclenchée par {current_user.get('email', 'Unknown')}")
        await auto_check_preventive_maintenance()
        return {"success": True, "message": "Vérification manuelle effectuée - Consultez les logs pour les détails"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/preventive-maintenance/check-and-execute-OLD")
async def check_and_execute_due_maintenances_old(current_user: dict = Depends(get_current_admin_user)):
    """Version détaillée pour debug (admin uniquement)"""
    try:
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Trouver toutes les maintenances actives dont la date est aujourd'hui ou passée
        pm_list = await db.preventive_maintenances.find({
            "statut": "ACTIF",
            "prochaineMaintenance": {"$lte": today + timedelta(days=1)}
        }).to_list(length=None)
        
        created_count = 0
        updated_count = 0
        errors = []
        
        for pm in pm_list:
            try:
                # Récupérer l'équipement
                equipement = await db.equipments.find_one({"_id": ObjectId(pm["equipement_id"])})
                
                # Créer le bon de travail
                wo_id = str(uuid.uuid4())
                work_order = {
                    "_id": ObjectId(),
                    "id": wo_id,
                    "numero": f"PM-{datetime.utcnow().strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}",
                    "titre": f"Maintenance préventive: {pm['titre']}",
                    "description": f"Maintenance automatique générée depuis la planification préventive",
                    "type": "PREVENTIF",
                    "priorite": "NORMALE",
                    "statut": "OUVERT",
                    "equipement_id": pm["equipement_id"],
                    "emplacement_id": equipement.get("emplacement_id") if equipement else None,
                    "assigne_a_id": pm.get("assigne_a_id"),
                    "tempsEstime": pm.get("duree"),
                    "dateLimite": datetime.utcnow() + timedelta(days=7),
                    "dateCreation": datetime.utcnow(),
                    "createdBy": "system",
                    "comments": [],
                    "attachments": [],
                    "historique": []
                }
                
                await db.work_orders.insert_one(work_order)
                created_count += 1
                
                # Calculer la prochaine date de maintenance
                next_date = calculate_next_maintenance_date(pm["prochaineMaintenance"], pm["frequence"])
                
                # Mettre à jour la maintenance préventive
                await db.preventive_maintenances.update_one(
                    {"_id": pm["_id"]},
                    {
                        "$set": {
                            "prochaineMaintenance": next_date,
                            "derniereMaintenance": datetime.utcnow()
                        }
                    }
                )
                updated_count += 1
                
            except Exception as e:
                errors.append(f"Erreur pour PM {pm.get('titre', 'Unknown')}: {str(e)}")
        
        return {
            "success": True,
            "workOrdersCreated": created_count,
            "maintenancesUpdated": updated_count,
            "errors": errors
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        "hashed_password": hashed_password,
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


@api_router.get("/users/default-permissions/{role}")
async def get_default_permissions_for_role(
    role: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """Obtenir les permissions par défaut pour un rôle spécifique (admin uniquement)"""
    try:
        default_permissions = get_default_permissions_by_role(role)
        return {"role": role, "permissions": default_permissions.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de la récupération des permissions: {str(e)}")

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

@api_router.post("/users/{user_id}/set-password-permanent")
async def set_password_permanent(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Marquer le mot de passe temporaire comme permanent (désactiver le changement obligatoire au premier login)
    L'utilisateur peut uniquement modifier son propre statut, sauf si c'est un admin
    """
    try:
        # Vérifier que l'utilisateur existe
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        # Vérifier que l'utilisateur modifie son propre compte OU qu'il est admin
        current_user_id = current_user.get("id")
        is_admin = current_user.get("role") == "ADMIN"
        
        if str(user_id) != str(current_user_id) and not is_admin:
            raise HTTPException(
                status_code=403, 
                detail="Vous ne pouvez modifier que votre propre statut"
            )
        
        # Mettre à jour le champ firstLogin à False
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"firstLogin": False}}
        )
        
        # Enregistrer l'action dans le journal d'audit
        await audit_service.log_action(
            user_id=current_user_id,
            user_name=f"{current_user['prenom']} {current_user['nom']}",
            user_email=current_user["email"],
            action=ActionType.UPDATE,
            entity_type=EntityType.USER,
            entity_id=user_id,
            entity_name=f"{user.get('prenom', '')} {user.get('nom', '')}".strip(),
            details=f"Mot de passe temporaire conservé comme permanent",
            changes={"firstLogin": False}
        )
        
        return {
            "success": True,
            "message": "Mot de passe conservé avec succès"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")



@api_router.post("/users/{user_id}/reset-password-admin")
async def reset_password_admin(
    user_id: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Réinitialiser le mot de passe d'un utilisateur (Admin uniquement)
    Génère un nouveau mot de passe temporaire et force le changement au prochain login
    """
    try:
        # Vérifier que l'utilisateur existe
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        # Générer un nouveau mot de passe temporaire
        temp_password = generate_temp_password()
        
        # Hasher le mot de passe
        hashed_password = get_password_hash(temp_password)
        
        # Mettre à jour le mot de passe et forcer le changement au prochain login
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "hashed_password": hashed_password,
                    "firstLogin": True
                }
            }
        )
        
        # Enregistrer l'action dans le journal d'audit
        await audit_service.log_action(
            user_id=current_user.get("id"),
            user_name=f"{current_user['prenom']} {current_user['nom']}",
            user_email=current_user["email"],
            action=ActionType.UPDATE,
            entity_type=EntityType.USER,
            entity_id=user_id,
            entity_name=f"{user.get('prenom', '')} {user.get('nom', '')}".strip(),
            details=f"Réinitialisation du mot de passe par l'administrateur",
            changes={"firstLogin": True, "password_reset": "admin_action"}
        )
        
        # Envoyer un email à l'utilisateur avec le nouveau mot de passe
        try:
            email_sent = email_service.send_account_created_email(
                to_email=user['email'],
                prenom=user.get('prenom', ''),
                temp_password=temp_password
            )
            
            if email_sent:
                logger.info(f"Email de réinitialisation envoyé à {user['email']}")
        except Exception as email_error:
            logger.error(f"Erreur lors de l'envoi de l'email de réinitialisation : {str(email_error)}")
        
        return {
            "success": True,
            "message": "Mot de passe réinitialisé avec succès",
            "tempPassword": temp_password,
            "emailSent": email_sent if 'email_sent' in locals() else False
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la réinitialisation du mot de passe : {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


# ==================== SETTINGS ROUTES ====================
@api_router.get("/settings")
async def get_system_settings(current_user: dict = Depends(get_current_user)):
    """Récupérer les paramètres système"""
    try:
        settings = await db.system_settings.find_one({"_id": "default"})
        if not settings:
            # Paramètres par défaut
            default_settings = {
                "_id": "default",
                "inactivity_timeout_minutes": 15
            }
            await db.system_settings.insert_one(default_settings)
            return SystemSettings(**default_settings)
        
        return SystemSettings(**settings)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des paramètres : {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@api_router.put("/settings")
async def update_system_settings(
    settings_update: SystemSettingsUpdate,
    current_user: dict = Depends(get_current_admin_user)
):
    """Mettre à jour les paramètres système (Admin uniquement)"""
    try:
        # Vérifier que la valeur est dans une plage acceptable (entre 1 et 120 minutes)
        if settings_update.inactivity_timeout_minutes is not None:
            if settings_update.inactivity_timeout_minutes < 1 or settings_update.inactivity_timeout_minutes > 120:
                raise HTTPException(
                    status_code=400, 
                    detail="Le temps d'inactivité doit être entre 1 et 120 minutes"
                )
        
        # Mettre à jour ou créer les paramètres
        update_data = {k: v for k, v in settings_update.model_dump().items() if v is not None}
        
        settings = await db.system_settings.find_one({"_id": "default"})
        if not settings:
            # Créer les paramètres par défaut
            default_settings = {
                "_id": "default",
                "inactivity_timeout_minutes": settings_update.inactivity_timeout_minutes or 15
            }
            await db.system_settings.insert_one(default_settings)
            settings = default_settings
        else:
            # Mettre à jour
            await db.system_settings.update_one(
                {"_id": "default"},
                {"$set": update_data}
            )
            settings.update(update_data)
        
        # Journaliser l'action
        await audit_service.log_action(
            user_id=current_user["id"],
            user_name=f"{current_user['prenom']} {current_user['nom']}",
            user_email=current_user["email"],
            action=ActionType.UPDATE,
            entity_type=EntityType.SETTINGS,
            entity_id="default",
            entity_name="System Settings",
            details="Modification des paramètres système",
            changes=update_data
        )
        
        return SystemSettings(**settings)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des paramètres : {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

# ==================== VENDORS ROUTES ====================
@api_router.get("/vendors", response_model=List[Vendor])
async def get_vendors(current_user: dict = Depends(require_permission("vendors", "view"))):
    """Liste tous les fournisseurs"""
    vendors = await db.vendors.find().to_list(1000)
    return [Vendor(**serialize_doc(vendor)) for vendor in vendors]

@api_router.post("/vendors", response_model=Vendor)
async def create_vendor(vendor_create: VendorCreate, current_user: dict = Depends(require_permission("vendors", "edit"))):
    """Créer un nouveau fournisseur"""
    vendor_dict = vendor_create.model_dump()
    vendor_dict["dateCreation"] = datetime.utcnow()
    vendor_dict["_id"] = ObjectId()
    
    await db.vendors.insert_one(vendor_dict)
    
    return Vendor(**serialize_doc(vendor_dict))

@api_router.put("/vendors/{vendor_id}", response_model=Vendor)
async def update_vendor(vendor_id: str, vendor_update: VendorUpdate, current_user: dict = Depends(require_permission("vendors", "edit"))):
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
async def delete_vendor(vendor_id: str, current_user: dict = Depends(require_permission("vendors", "delete"))):
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
                'numeroReception': p.get('numeroReception'),  # Premier N° reception de la commande
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
async def get_purchase_history(current_user: dict = Depends(require_permission("purchaseHistory", "view"))):
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
async def get_purchase_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Statistiques complètes des achats"""
    
    # Filtres de date
    match_filter = {}
    if start_date:
        match_filter["dateCreation"] = {"$gte": datetime.fromisoformat(start_date)}
    if end_date:
        if "dateCreation" in match_filter:
            match_filter["dateCreation"]["$lte"] = datetime.fromisoformat(end_date)
        else:
            match_filter["dateCreation"] = {"$lte": datetime.fromisoformat(end_date)}
    
    # Total des achats
    all_purchases = await db.purchase_history.find(match_filter).to_list(10000)
    
    if not all_purchases:
        return {
            "totalAchats": 0,
            "montantTotal": 0,
            "commandesTotales": 0,
            "parFournisseur": [],
            "parMois": [],
            "parSite": [],
            "parGroupeStatistique": [],
            "articlesTop": [],
            "par_utilisateur": [],
            "par_mois": []
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
    
    # NOUVELLES STATS - Par utilisateur (créateur colonne L)
    user_stats = {}
    for purchase in all_purchases:
        user = purchase.get('creationUser', 'Inconnu')
        num_commande = purchase.get('numeroCommande')
        montant = purchase.get('montantLigneHT', 0)
        
        if user not in user_stats:
            user_stats[user] = {
                'utilisateur': user,
                'commandes': set(),
                'montant_total': 0,
                'nb_lignes': 0
            }
        
        if num_commande:
            user_stats[user]['commandes'].add(num_commande)
        user_stats[user]['montant_total'] += montant
        user_stats[user]['nb_lignes'] += 1
    
    # Convertir en liste
    users_list = []
    for user, data in user_stats.items():
        nb_commandes = len(data['commandes'])
        montant = data['montant_total']
        pourcentage = (montant / montant_total * 100) if montant_total > 0 else 0
        
        users_list.append({
            'utilisateur': user,
            'nb_commandes': nb_commandes,
            'nb_lignes': data['nb_lignes'],
            'montant_total': round(montant, 2),
            'pourcentage': round(pourcentage, 2)
        })
    
    users_list.sort(key=lambda x: x['montant_total'], reverse=True)
    
    # NOUVELLES STATS - Par mois (format liste)
    monthly_stats = {}
    for purchase in all_purchases:
        date = purchase.get('dateCreation')
        if date:
            if isinstance(date, str):
                date = datetime.fromisoformat(date.replace('Z', '+00:00'))
            month_key = date.strftime('%Y-%m')
            num_commande = purchase.get('numeroCommande')
            montant = purchase.get('montantLigneHT', 0)
            
            if month_key not in monthly_stats:
                monthly_stats[month_key] = {
                    'mois': month_key,
                    'commandes': set(),
                    'montant': 0,
                    'nb_lignes': 0
                }
            
            if num_commande:
                monthly_stats[month_key]['commandes'].add(num_commande)
            monthly_stats[month_key]['montant'] += montant
            monthly_stats[month_key]['nb_lignes'] += 1
    
    monthly_list = []
    for month, data in monthly_stats.items():
        monthly_list.append({
            'mois': month,
            'nb_commandes': len(data['commandes']),
            'nb_lignes': data['nb_lignes'],
            'montant_total': round(data['montant'], 2)
        })
    monthly_list.sort(key=lambda x: x['mois'])
    
    # Par fournisseur (ancienne stat - gardée)
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
    
    # Par mois (ancien format - gardé pour compatibilité)
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
        "commandesTotales": commandes_totales,
        "parFournisseur": par_fournisseur,
        "parMois": par_mois,
        "parSite": par_site,
        "parGroupeStatistique": par_groupe,
        "articlesTop": articles_top,
        "par_utilisateur": users_list,  # NOUVELLES STATS
        "par_mois": monthly_list  # NOUVELLES STATS (format différent)
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
async def delete_purchase(purchase_id: str, current_user: dict = Depends(require_permission("purchaseHistory", "delete"))):
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
async def get_analytics(current_user: dict = Depends(require_permission("reports", "view"))):
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
        "nombreMaintenancesPrev": await db.preventive_maintenances.count_documents({"statut": "ACTIF"}),
        "nombreMaintenancesCorrectives": await db.work_orders.count_documents({"priorite": {"$ne": "AUCUNE"}})
    }
    
    return analytics

# ==================== IMPORT/EXPORT ROUTES ====================
EXPORT_MODULES = {
    "intervention-requests": "intervention_requests",
    "work-orders": "work_orders",
    "improvement-requests": "improvement_requests",
    "improvements": "improvements",
    "equipments": "equipments",
    "meters": "meters",
    "meter-readings": "meter_readings",
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
        if module not in EXPORT_MODULES and module != "all":
            raise HTTPException(status_code=400, detail="Module invalide")
        
        # Déterminer les modules à traiter
        if module == "all":
            modules_to_import = EXPORT_MODULES
        else:
            modules_to_import = {module: EXPORT_MODULES[module]}
        
        # Lire le fichier
        content = await file.read()
        
        # Mappings de colonnes pour chaque module
        column_mappings = {
            "purchase-history": {
                "Fournisseur": "fournisseur",
                "N° Commande ": "numeroCommande",
                "N° Commande": "numeroCommande",
                "N° reception": "numeroReception",
                "Date de création": "dateCreation",
                "Article": "article",
                "Description 1": "description",
                "Description": "description",
                "Groupe statistique": "groupeStatistique",
                "Groupe statistique STK": "groupeStatistique",
                "STK quantité": "quantite",
                "quantité": "quantite",
                "Quantité": "quantite",
                "Montant ligne HT": "montantLigneHT",
                "Quantité retournée": "quantiteRetournee",
                "Site ": "site",
                "Site": "site",
                "Creation user": "creationUser"
            },
            "work-orders": {
                "ID": "id",
                "Titre": "title",
                "Title": "title",
                "Description": "description",
                "Priorité": "priority",
                "Priority": "priority",
                "Statut": "status",
                "Status": "status",
                "Date création": "dateCreation",
                "Date début": "dateDebut",
                "Date fin": "dateFin",
                "Équipement": "equipment",
                "Equipment": "equipment",
                "Assigné à": "assignedTo",
                "Assigned To": "assignedTo",
                "Type": "type"
            },
            "equipments": {
                "ID": "id",
                "Nom": "name",
                "Name": "name",
                "Code": "code",
                "Type": "type",
                "Marque": "brand",
                "Brand": "brand",
                "Modèle": "model",
                "Model": "model",
                "Numéro de série": "serialNumber",
                "Serial Number": "serialNumber",
                "Zone": "location",
                "Location": "location",
                "Statut": "status",
                "Status": "status",
                "Date installation": "installDate"
            },
            "intervention-requests": {
                "ID": "id",
                "Titre": "title",
                "Title": "title",
                "Description": "description",
                "Priorité": "priority",
                "Priority": "priority",
                "Statut": "status",
                "Status": "status",
                "Date création": "dateCreation",
                "Équipement": "equipment",
                "Equipment": "equipment",
                "Demandeur": "requestedBy",
                "Requested By": "requestedBy"
            },
            "improvement-requests": {
                "ID": "id",
                "Titre": "title",
                "Title": "title",
                "Description": "description",
                "Priorité": "priority",
                "Priority": "priority",
                "Statut": "status",
                "Status": "status",
                "Date création": "dateCreation",
                "Demandeur": "requestedBy"
            },
            "improvements": {
                "ID": "id",
                "Titre": "title",
                "Title": "title",
                "Description": "description",
                "Priorité": "priority",
                "Priority": "priority",
                "Statut": "status",
                "Status": "status",
                "Date création": "dateCreation",
                "Date début": "dateDebut",
                "Date fin": "dateFin",
                "Assigné à": "assignedTo"
            },
            "locations": {
                "ID": "id",
                "Nom": "name",
                "Name": "name",
                "Code": "code",
                "Type": "type",
                "Parent": "parent",
                "Description": "description"
            },
            "meters": {
                "ID": "id",
                "Nom": "name",
                "Name": "name",
                "Type": "type",
                "Équipement": "equipment",
                "Equipment": "equipment",
                "Unité": "unit",
                "Unit": "unit",
                "Valeur actuelle": "currentValue",
                "Current Value": "currentValue"
            },
            "users": {
                "ID": "id",
                "Email": "email",
                "Prénom": "prenom",
                "First Name": "prenom",
                "Nom": "nom",
                "Last Name": "nom",
                "Rôle": "role",
                "Role": "role",
                "Téléphone": "telephone",
                "Phone": "telephone",
                "Service": "service"
            },
            "inventory": {
                "ID": "id",
                "Nom": "name",
                "Name": "name",
                "Code": "code",
                "Type": "type",
                "Catégorie": "category",
                "Category": "category",
                "Quantité": "quantity",
                "Quantity": "quantity",
                "Zone": "location",
                "Location": "location"
            },
            "vendors": {
                "ID": "id",
                "Nom": "name",
                "Name": "name",
                "Email": "email",
                "Téléphone": "phone",
                "Phone": "phone",
                "Adresse": "address",
                "Address": "address",
                "Type": "type",
                "Statut": "status",
                "Status": "status"
            }
        }
        
        # Lire le fichier selon le type et le module
        data_sheets = {}
        
        try:
            if file.filename.endswith('.csv'):
                if module == "all":
                    raise HTTPException(status_code=400, detail="Pour importer toutes les données, utilisez un fichier Excel multi-feuilles")
                
                # Détecter automatiquement le séparateur CSV
                content_str = content.decode('utf-8', errors='ignore')
                first_line = content_str.split('\n')[0] if content_str else ""
                
                comma_count = first_line.count(',')
                semicolon_count = first_line.count(';')
                tab_count = first_line.count('\t')
                
                if semicolon_count > comma_count and semicolon_count > tab_count:
                    separator = ';'
                elif tab_count > comma_count:
                    separator = '\t'
                else:
                    separator = ','
                
                logger.info(f"📋 Séparateur détecté: '{separator}'")
                df = pd.read_csv(io.BytesIO(content), sep=separator, encoding='utf-8')
                logger.info(f"✅ CSV lu: {len(df)} lignes, {len(df.columns)} colonnes")
                data_sheets[module] = df
                
            elif file.filename.endswith(('.xlsx', '.xls', '.xlsb')):
                if module == "all":
                    # Lire toutes les feuilles pour l'import complet
                    try:
                        all_sheets = pd.read_excel(io.BytesIO(content), sheet_name=None, engine='openpyxl')
                        logger.info(f"✅ Fichier Excel multi-feuilles lu: {len(all_sheets)} feuilles")
                        
                        # Mapper les noms de feuilles aux modules
                        sheet_to_module = {
                            "intervention-requests": "intervention-requests",
                            "intervention_requests": "intervention-requests", 
                            "work-orders": "work-orders",
                            "work_orders": "work-orders",
                            "improvement-requests": "improvement-requests",
                            "improvement_requests": "improvement-requests",
                            "improvements": "improvements",
                            "equipments": "equipments",
                            "locations": "locations",
                            "inventory": "inventory",
                            "purchase-history": "purchase-history",
                            "purchase_history": "purchase-history",
                            "meters": "meters",
                            "users": "users",
                            "people": "users",  # Support both names
                            "vendors": "vendors",
                            "fournisseurs": "vendors"
                        }
                        
                        for sheet_name, df in all_sheets.items():
                            # Essayer de mapper le nom de la feuille à un module
                            module_name = sheet_to_module.get(sheet_name.lower())
                            if module_name and module_name in modules_to_import:
                                data_sheets[module_name] = df
                                logger.info(f"📋 Feuille '{sheet_name}' mappée au module '{module_name}': {len(df)} lignes")
                        
                        if not data_sheets:
                            available_sheets = list(all_sheets.keys())
                            expected_sheets = list(modules_to_import.keys())
                            raise HTTPException(
                                status_code=400, 
                                detail=f"Aucune feuille reconnue. Feuilles disponibles: {available_sheets}. Feuilles attendues: {expected_sheets}"
                            )
                            
                    except Exception as e:
                        if "Aucune feuille reconnue" in str(e):
                            raise
                        raise HTTPException(status_code=400, detail=f"Erreur lecture multi-feuilles: {str(e)}")
                else:
                    # Lire une seule feuille pour un module spécifique
                    df = None
                    errors = []
                    
                    # Tentatives multiples de lecture
                    if file.filename.endswith('.xlsx'):
                        try:
                            df = pd.read_excel(io.BytesIO(content), engine='openpyxl')
                            logger.info("✅ Fichier lu avec openpyxl")
                        except Exception as e1:
                            errors.append(f"openpyxl: {str(e1)[:100]}")
                    
                    if df is None:
                        try:
                            df = pd.read_excel(io.BytesIO(content), engine='xlrd')
                            logger.info("✅ Fichier lu avec xlrd")
                        except Exception as e2:
                            errors.append(f"xlrd: {str(e2)[:100]}")
                    
                    if df is None and file.filename.endswith('.xlsb'):
                        try:
                            df = pd.read_excel(io.BytesIO(content), engine='pyxlsb')
                            logger.info("✅ Fichier lu avec pyxlsb")
                        except Exception as e3:
                            errors.append(f"pyxlsb: {str(e3)[:100]}")
                    
                    if df is None:
                        try:
                            df = pd.read_excel(io.BytesIO(content))
                            logger.info("✅ Fichier lu avec méthode par défaut")
                        except Exception as e4:
                            errors.append(f"default: {str(e4)[:100]}")
                    
                    if df is None:
                        error_msg = "Impossible de lire le fichier Excel. Erreurs:\n" + "\n".join(errors)
                        error_msg += "\n\n💡 Solutions:\n"
                        error_msg += "1. Ouvrez le fichier dans Excel et sauvegardez-le à nouveau\n"
                        error_msg += "2. Exportez en CSV depuis Excel\n"
                        error_msg += "3. Utilisez un fichier Excel plus simple"
                        raise HTTPException(status_code=400, detail=error_msg)
                    
                    data_sheets[module] = df
            else:
                raise HTTPException(status_code=400, detail="Format non supporté (CSV, XLSX, XLS ou XLSB)")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Erreur de lecture: {str(e)}. Essayez CSV."
            )
        
        # Traiter chaque feuille/module
        overall_stats = {
            "total": 0,
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "errors": [],
            "modules": {}
        }
        
        for current_module, df in data_sheets.items():
            collection_name = modules_to_import[current_module]
            
            # Appliquer le mapping des colonnes si disponible
            if current_module in column_mappings:
                df = df.rename(columns=column_mappings[current_module])
            
            # Nettoyer les noms de colonnes - convertir en string d'abord
            df.columns = [str(col).strip() if col is not None else f'col_{i}' for i, col in enumerate(df.columns)]
            
            # Convertir en dictionnaires
            items_to_import = df.to_dict('records')
            
            module_stats = {
                "total": len(items_to_import),
                "inserted": 0,
                "updated": 0,
                "skipped": 0,
                "errors": []
            }
            
            logger.info(f"🔄 Traitement du module '{current_module}': {len(items_to_import)} éléments")
            
            for idx, item in enumerate(items_to_import):
                try:
                    # Nettoyer les NaN
                    cleaned_item = {k: v for k, v in item.items() if pd.notna(v)}
                    
                    # Convertir et initialiser les champs qui doivent être des listes
                    list_fields = ["comments", "attachments", "historique", "permissions"]
                    for list_field in list_fields:
                        if list_field in cleaned_item:
                            if isinstance(cleaned_item[list_field], str):
                                # Convertir string JSON en liste
                                import json
                                try:
                                    parsed = json.loads(cleaned_item[list_field])
                                    cleaned_item[list_field] = parsed if isinstance(parsed, list) else []
                                except:
                                    # Si c'est '[]' ou un string vide, mettre liste vide
                                    cleaned_item[list_field] = []
                            elif not isinstance(cleaned_item[list_field], list):
                                cleaned_item[list_field] = []
                        else:
                            # Initialiser le champ s'il n'existe pas
                            cleaned_item[list_field] = []
                    
                    # Traitement spécifique purchase-history
                    if current_module == "purchase-history":
                        for num_field in ["quantite", "montantLigneHT", "quantiteRetournee"]:
                            if num_field in cleaned_item:
                                try:
                                    value = cleaned_item[num_field]
                                    if isinstance(value, str):
                                        value = value.replace(',', '.').replace(' ', '')
                                    cleaned_item[num_field] = float(value)
                                except:
                                    if num_field == "quantiteRetournee":
                                        cleaned_item[num_field] = 0.0
                                    elif num_field == "quantite":
                                        cleaned_item[num_field] = 0.0
                        
                        # Convertir dates françaises
                        if "dateCreation" in cleaned_item:
                            try:
                                date_val = cleaned_item["dateCreation"]
                                if isinstance(date_val, str):
                                    if '/' in date_val:
                                        parts = date_val.split('/')
                                        if len(parts) == 3:
                                            cleaned_item["dateCreation"] = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                                    cleaned_item["dateCreation"] = datetime.fromisoformat(cleaned_item["dateCreation"])
                                elif hasattr(date_val, 'to_pydatetime'):
                                    cleaned_item["dateCreation"] = date_val.to_pydatetime()
                            except Exception as e:
                                logger.warning(f"Module {current_module}, ligne {idx+1}: date invalide")
                                pass
                        
                        cleaned_item["dateEnregistrement"] = datetime.utcnow()
                        if "creationUser" not in cleaned_item or not cleaned_item["creationUser"]:
                            cleaned_item["creationUser"] = current_user.get("email", "import")
                    
                    # Traitement générique pour les autres modules
                    else:
                        # Convertir les dates
                        date_fields = ["dateCreation", "dateDebut", "dateFin", "installDate", "dateEnregistrement"]
                        for date_field in date_fields:
                            if date_field in cleaned_item:
                                try:
                                    date_val = cleaned_item[date_field]
                                    if isinstance(date_val, str):
                                        if '/' in date_val:
                                            parts = date_val.split('/')
                                            if len(parts) == 3:
                                                cleaned_item[date_field] = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                                        cleaned_item[date_field] = datetime.fromisoformat(cleaned_item[date_field])
                                    elif hasattr(date_val, 'to_pydatetime'):
                                        cleaned_item[date_field] = date_val.to_pydatetime()
                                except:
                                    pass
                        
                        # Ajouter métadonnées obligatoires
                        if "dateCreation" not in cleaned_item:
                            cleaned_item["dateCreation"] = datetime.utcnow()
                        
                        # Initialiser champs spécifiques par module
                        if current_module in ["work-orders", "improvements"]:
                            # Champs obligatoires pour work-orders et improvements
                            if "numero" not in cleaned_item:
                                cleaned_item["numero"] = "N/A"
                            if "statut" not in cleaned_item:
                                cleaned_item["statut"] = "OUVERT"
                            if "priorite" not in cleaned_item:
                                cleaned_item["priorite"] = "MOYENNE"
                        
                        elif current_module in ["intervention-requests", "improvement-requests"]:
                            # Champs obligatoires pour les demandes
                            if "statut" not in cleaned_item:
                                cleaned_item["statut"] = "EN_ATTENTE"
                            if "priorite" not in cleaned_item:
                                cleaned_item["priorite"] = "MOYENNE"
                        
                        elif current_module == "equipments":
                            # Champs obligatoires pour équipements
                            if "statut" not in cleaned_item:
                                cleaned_item["statut"] = "OPERATIONNEL"
                            if "actif" not in cleaned_item:
                                cleaned_item["actif"] = True
                        
                        elif current_module == "meters":
                            # Champs obligatoires pour compteurs
                            if "actif" not in cleaned_item:
                                cleaned_item["actif"] = True
                        
                        elif current_module == "users":
                            # Champs obligatoires pour utilisateurs
                            if "actif" not in cleaned_item:
                                cleaned_item["actif"] = True
                            if "role" not in cleaned_item:
                                cleaned_item["role"] = "VISUALISEUR"
                    
                    # Gérer l'ID
                    item_id = cleaned_item.get('id')
                    if item_id and 'id' in cleaned_item:
                        del cleaned_item['id']
                    
                    if mode == "replace" and item_id:
                        try:
                            existing = await db[collection_name].find_one({"_id": ObjectId(item_id)})
                            
                            if existing:
                                # Garder l'id lors du replace
                                cleaned_item["id"] = item_id
                                await db[collection_name].replace_one(
                                    {"_id": ObjectId(item_id)},
                                    cleaned_item
                                )
                                module_stats["updated"] += 1
                            else:
                                cleaned_item["_id"] = ObjectId(item_id)
                                # Ajouter le champ id
                                cleaned_item["id"] = item_id
                                await db[collection_name].insert_one(cleaned_item)
                                module_stats["inserted"] += 1
                        except:
                            # Si l'ID n'est pas valide, insérer comme nouveau
                            if "_id" in cleaned_item:
                                del cleaned_item["_id"]
                            
                            # Générer nouvel ObjectId
                            new_id = ObjectId()
                            cleaned_item["_id"] = new_id
                            
                            # IMPORTANT: Ajouter le champ 'id' (string) pour Pydantic
                            cleaned_item["id"] = str(new_id)
                            
                            await db[collection_name].insert_one(cleaned_item)
                            module_stats["inserted"] += 1
                    else:
                        # Mode add
                        if "_id" in cleaned_item:
                            del cleaned_item["_id"]
                        
                        # Générer nouvel ObjectId
                        new_id = ObjectId()
                        cleaned_item["_id"] = new_id
                        
                        # IMPORTANT: Ajouter le champ 'id' (string) pour Pydantic
                        cleaned_item["id"] = str(new_id)
                        
                        await db[collection_name].insert_one(cleaned_item)
                        module_stats["inserted"] += 1
                
                except Exception as e:
                    module_stats["skipped"] += 1
                    error_msg = f"Module {current_module}, ligne {module_stats['inserted'] + module_stats['updated'] + module_stats['skipped']}: {str(e)[:100]}"
                    module_stats["errors"].append(error_msg)
                    logger.warning(error_msg)
            
            # Ajouter les stats du module aux stats globales
            overall_stats["total"] += module_stats["total"]
            overall_stats["inserted"] += module_stats["inserted"]
            overall_stats["updated"] += module_stats["updated"]
            overall_stats["skipped"] += module_stats["skipped"]
            overall_stats["errors"].extend(module_stats["errors"])
            overall_stats["modules"][current_module] = module_stats
            
            logger.info(f"✅ Module '{current_module}' traité: {module_stats['inserted']} ajoutés, {module_stats['updated']} mis à jour, {module_stats['skipped']} ignorés")
        
        return overall_stats
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur import: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== UPDATE ROUTES ====================
from update_manager import UpdateManager

update_manager = UpdateManager(db)

@api_router.get("/updates/current")
async def get_current_version(current_user: dict = Depends(get_current_admin_user)):
    """Récupère la version actuelle (admin uniquement)"""
    version = await update_manager.get_current_version()
    return {
        "version": version,
        "date": datetime.now().isoformat()
    }

@api_router.get("/updates/check")
async def check_updates(current_user: dict = Depends(get_current_admin_user)):
    """Vérifie si une mise à jour est disponible (admin uniquement)"""
    current = await update_manager.get_current_version()
    latest = await update_manager.check_github_version()
    
    return {
        "current_version": current,
        "latest_version": latest,
        "update_available": latest is not None and latest.get("available", False)
    }

@api_router.get("/updates/changelog")
async def get_changelog(
    from_version: Optional[str] = None,
    current_user: dict = Depends(get_current_admin_user)
):
    """Récupère le changelog (admin uniquement)"""
    changelog = await update_manager.get_changelog(from_version)
    return {"changelog": changelog}

@api_router.get("/updates/history")
async def get_update_history(current_user: dict = Depends(get_current_admin_user)):
    """Récupère l'historique des mises à jour (admin uniquement)"""
    history = await update_manager.get_update_history()
    return {"history": history}

@api_router.post("/updates/apply")
async def apply_update(
    github_token: Optional[str] = None,
    current_user: dict = Depends(get_current_admin_user)
):
    """Applique la mise à jour (admin uniquement)"""
    result = await update_manager.apply_update(github_token)
    
    if not result["success"]:
        raise HTTPException(
            status_code=500,
            detail=result.get("message", "Erreur lors de la mise à jour")
        )
    
    return result

@api_router.post("/updates/backup")
async def create_backup(current_user: dict = Depends(get_current_admin_user)):
    """Crée un backup de la base de données (admin uniquement)"""
    result = await update_manager.create_backup()
    
    if not result["success"]:
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Erreur lors de la création du backup")
        )
    
    return result

@api_router.post("/updates/rollback")
async def rollback_update(
    backup_path: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """Restaure une version précédente (admin uniquement)"""
    result = await update_manager.rollback_to_version(backup_path)
    
    if not result["success"]:
        raise HTTPException(
            status_code=500,
            detail=result.get("message", "Erreur lors du rollback")
        )
    
    return result

# ==================== AUDIT LOG ROUTES (JOURNAL) ====================
@api_router.get("/audit-logs")
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Récupère les logs d'audit (admin uniquement)
    Supporte les filtres: user_id, action, entity_type, start_date, end_date
    """
    try:
        # Convertir les strings en enums si fournis
        action_enum = ActionType(action) if action else None
        entity_type_enum = EntityType(entity_type) if entity_type else None
        
        # Convertir les dates si fournies
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        logs, total = await audit_service.get_logs(
            skip=skip,
            limit=limit,
            user_id=user_id,
            action=action_enum,
            entity_type=entity_type_enum,
            start_date=start_dt,
            end_date=end_dt
        )
        
        return {
            "logs": logs,
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des logs d'audit: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la récupération des logs d'audit"
        )

@api_router.get("/audit-logs/entity/{entity_type}/{entity_id}")
async def get_entity_audit_history(
    entity_type: str,
    entity_id: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Récupère l'historique complet d'une entité spécifique (admin uniquement)
    """
    try:
        entity_type_enum = EntityType(entity_type)
        logs = await audit_service.get_entity_history(entity_type_enum, entity_id)
        
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "history": logs
        }
        
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Type d'entité invalide: {entity_type}"
        )
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'historique: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la récupération de l'historique"
        )

@api_router.get("/audit-logs/export")
async def export_audit_logs(
    format: str = "csv",
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Exporte les logs d'audit en CSV ou Excel (admin uniquement)
    """
    try:
        # Récupérer tous les logs avec filtres
        action_enum = ActionType(action) if action else None
        entity_type_enum = EntityType(entity_type) if entity_type else None
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        logs, _ = await audit_service.get_logs(
            skip=0,
            limit=10000,  # Limite haute pour export
            user_id=user_id,
            action=action_enum,
            entity_type=entity_type_enum,
            start_date=start_dt,
            end_date=end_dt
        )
        
        # Préparer les données pour l'export
        paris_tz = pytz.timezone('Europe/Paris')
        export_data = []
        for log in logs:
            # Convertir UTC vers Europe/Paris
            timestamp_utc = log["timestamp"]
            if timestamp_utc.tzinfo is None:
                timestamp_utc = pytz.utc.localize(timestamp_utc)
            timestamp_paris = timestamp_utc.astimezone(paris_tz)
            
            export_data.append({
                "Date/Heure": timestamp_paris.strftime("%d/%m/%Y %H:%M:%S"),
                "Utilisateur": log["user_name"],
                "Email": log["user_email"],
                "Action": log["action"],
                "Type": log["entity_type"],
                "Entité": log.get("entity_name", ""),
                "Détails": log.get("details", "")
            })
        
        df = pd.DataFrame(export_data)
        
        # Créer le fichier selon le format demandé
        if format.lower() == "csv":
            output = io.StringIO()
            df.to_csv(output, index=False, encoding='utf-8-sig')
            output.seek(0)
            
            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                }
            )
        else:  # Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Audit Logs')
            output.seek(0)
            
            return Response(
                content=output.getvalue(),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                }
            )
        
    except Exception as e:
        logger.error(f"Erreur lors de l'export des logs: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de l'export des logs"
        )

# ==================== WORK ORDER COMMENTS ROUTES ====================
@api_router.post("/work-orders/{work_order_id}/comments")
async def add_work_order_comment(
    work_order_id: str,
    comment: CommentCreate,
    current_user: dict = Depends(get_current_user)
):
    """Ajoute un commentaire à un ordre de travail"""
    try:
        # Vérifier que l'ordre de travail existe (chercher par _id ObjectId)
        work_order = await db.work_orders.find_one({"_id": ObjectId(work_order_id)})
        if not work_order:
            raise HTTPException(status_code=404, detail="Ordre de travail non trouvé")
        
        # Créer le commentaire
        new_comment = {
            "id": str(uuid.uuid4()),
            "user_id": current_user.get("id", str(work_order["_id"])),
            "user_name": f"{current_user['prenom']} {current_user['nom']}",
            "text": comment.text,
            "timestamp": datetime.now(timezone.utc)
        }
        
        # Ajouter le commentaire à l'ordre de travail
        await db.work_orders.update_one(
            {"_id": ObjectId(work_order_id)},
            {"$push": {"comments": new_comment}}
        )
        
        # Log dans l'audit
        await audit_service.log_action(
            user_id=current_user["id"],
            user_name=f"{current_user['prenom']} {current_user['nom']}",
            user_email=current_user["email"],
            action=ActionType.UPDATE,
            entity_type=EntityType.WORK_ORDER,
            entity_id=work_order_id,
            entity_name=work_order.get("titre", ""),
            details=f"Commentaire ajouté: {comment.text[:50]}..."
        )
        
        return new_comment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout du commentaire: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de l'ajout du commentaire"
        )

@api_router.get("/work-orders/{work_order_id}/comments")
async def get_work_order_comments(
    work_order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupère tous les commentaires d'un ordre de travail"""
    try:
        work_order = await db.work_orders.find_one({"_id": ObjectId(work_order_id)})
        if not work_order:
            raise HTTPException(status_code=404, detail="Ordre de travail non trouvé")
        
        comments = work_order.get("comments", [])
        return {"comments": comments}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des commentaires: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la récupération des commentaires"
        )



# ==================== METERS (COMPTEURS) ENDPOINTS ====================

@api_router.post("/meters", response_model=Meter, status_code=201)
async def create_meter(meter: MeterCreate, current_user: dict = Depends(require_permission("meters", "edit"))):
    """Créer un nouveau compteur"""
    try:
        meter_id = str(uuid.uuid4())
        meter_data = meter.model_dump()
        meter_data["id"] = meter_id
        meter_data["date_creation"] = datetime.utcnow()
        meter_data["actif"] = True
        
        # Récupérer les informations de l'emplacement si fourni
        if meter_data.get("emplacement_id"):
            location = await db.locations.find_one({"id": meter_data["emplacement_id"]})
            if location:
                meter_data["emplacement"] = {"id": location["id"], "nom": location["nom"]}
        
        await db.meters.insert_one(meter_data)
        
        # Audit log
        await audit_service.log_action(
            user_id=current_user["id"],
            user_name=current_user.get("nom", "") + " " + current_user.get("prenom", ""),
            user_email=current_user["email"],
            action=ActionType.CREATE,
            entity_type=EntityType.WORK_ORDER,  # Utilisons WORK_ORDER comme proxy
            entity_id=meter_id,
            entity_name=meter.nom
        )
        
        return Meter(**meter_data)
    except Exception as e:
        logger.error(f"Erreur création compteur: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/meters", response_model=List[Meter])
async def get_all_meters(current_user: dict = Depends(get_current_user)):
    """Récupérer tous les compteurs"""
    try:
        meters = []
        async for meter in db.meters.find({"actif": True}).sort("date_creation", -1):
            meters.append(Meter(**meter))
        return meters
    except Exception as e:
        logger.error(f"Erreur récupération compteurs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/meters/{meter_id}", response_model=Meter)
async def get_meter(meter_id: str, current_user: dict = Depends(get_current_user)):
    """Récupérer un compteur spécifique"""
    meter = await db.meters.find_one({"id": meter_id})
    if not meter:
        raise HTTPException(status_code=404, detail="Compteur non trouvé")
    return Meter(**meter)

@api_router.put("/meters/{meter_id}", response_model=Meter)
async def update_meter(
    meter_id: str,
    meter_update: MeterUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour un compteur"""
    meter = await db.meters.find_one({"id": meter_id})
    if not meter:
        raise HTTPException(status_code=404, detail="Compteur non trouvé")
    
    update_data = {k: v for k, v in meter_update.model_dump().items() if v is not None}
    
    # Mettre à jour l'emplacement si nécessaire
    if "emplacement_id" in update_data:
        if update_data["emplacement_id"]:
            location = await db.locations.find_one({"id": update_data["emplacement_id"]})
            if location:
                update_data["emplacement"] = {"id": location["id"], "nom": location["nom"]}
        else:
            update_data["emplacement"] = None
    
    await db.meters.update_one({"id": meter_id}, {"$set": update_data})
    
    # Récupérer le compteur mis à jour
    updated_meter = await db.meters.find_one({"id": meter_id})
    
    # Audit log
    await audit_service.log_action(
        user_id=current_user["id"],
        user_name=current_user.get("nom", "") + " " + current_user.get("prenom", ""),
        user_email=current_user["email"],
        action=ActionType.UPDATE,
        entity_type=EntityType.WORK_ORDER,
        entity_id=meter_id,
        entity_name=updated_meter["nom"]
    )
    
    return Meter(**updated_meter)

@api_router.delete("/meters/{meter_id}")
async def delete_meter(meter_id: str, current_user: dict = Depends(require_permission("meters", "delete"))):
    """Supprimer un compteur (soft delete)"""
    meter = await db.meters.find_one({"id": meter_id})
    if not meter:
        raise HTTPException(status_code=404, detail="Compteur non trouvé")
    
    # Soft delete
    await db.meters.update_one({"id": meter_id}, {"$set": {"actif": False}})
    
    # Audit log
    await audit_service.log_action(
        user_id=current_user["id"],
        user_name=current_user.get("nom", "") + " " + current_user.get("prenom", ""),
        user_email=current_user["email"],
        action=ActionType.DELETE,
        entity_type=EntityType.WORK_ORDER,
        entity_id=meter_id,
        entity_name=meter["nom"]
    )
    
    return {"message": "Compteur supprimé"}

# ==================== METER READINGS (RELEVÉS) ENDPOINTS ====================

@api_router.post("/meters/{meter_id}/readings", response_model=MeterReading, status_code=201)
async def create_reading(
    meter_id: str,
    reading: MeterReadingCreate,
    current_user: dict = Depends(get_current_user)
):
    """Créer un nouveau relevé pour un compteur"""
    try:
        # Vérifier que le compteur existe
        meter = await db.meters.find_one({"id": meter_id})
        if not meter:
            raise HTTPException(status_code=404, detail="Compteur non trouvé")
        
        # Récupérer le dernier relevé pour calculer la consommation
        last_reading = await db.meter_readings.find_one(
            {"meter_id": meter_id},
            sort=[("date_releve", -1)]
        )
        
        reading_id = str(uuid.uuid4())
        reading_data = reading.model_dump()
        reading_data["id"] = reading_id
        reading_data["meter_id"] = meter_id
        reading_data["created_by"] = current_user["id"]
        reading_data["created_by_name"] = f"{current_user.get('prenom', '')} {current_user.get('nom', '')}"
        reading_data["meter_nom"] = meter["nom"]
        reading_data["date_creation"] = datetime.utcnow()
        
        # Calculer la consommation
        if last_reading:
            consommation = reading_data["valeur"] - last_reading["valeur"]
            reading_data["consommation"] = max(0, consommation)  # Éviter les valeurs négatives
            
            # Calculer le coût si prix unitaire disponible
            prix = reading_data.get("prix_unitaire") or meter.get("prix_unitaire")
            if prix and reading_data["consommation"]:
                reading_data["cout"] = reading_data["consommation"] * prix
        else:
            reading_data["consommation"] = 0
            reading_data["cout"] = 0
        
        # Si pas de prix spécifié, utiliser celui du compteur
        if not reading_data.get("prix_unitaire"):
            reading_data["prix_unitaire"] = meter.get("prix_unitaire")
        if not reading_data.get("abonnement_mensuel"):
            reading_data["abonnement_mensuel"] = meter.get("abonnement_mensuel")
        
        await db.meter_readings.insert_one(reading_data)
        
        return MeterReading(**reading_data)
    except Exception as e:
        logger.error(f"Erreur création relevé: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/meters/{meter_id}/readings", response_model=List[MeterReading])
async def get_meter_readings(
    meter_id: str,
    current_user: dict = Depends(get_current_user),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Récupérer tous les relevés d'un compteur"""
    try:
        query = {"meter_id": meter_id}
        
        # Filtrer par date si fourni
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if end_date:
                date_filter["$lte"] = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query["date_releve"] = date_filter
        
        readings = []
        async for reading in db.meter_readings.find(query).sort("date_releve", -1):
            readings.append(MeterReading(**reading))
        return readings
    except Exception as e:
        logger.error(f"Erreur récupération relevés: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/meters/{meter_id}/statistics")
async def get_meter_statistics(
    meter_id: str,
    current_user: dict = Depends(get_current_user),
    period: str = "month"  # week, month, quarter, year
):
    """Obtenir les statistiques d'un compteur"""
    try:
        meter = await db.meters.find_one({"id": meter_id})
        if not meter:
            raise HTTPException(status_code=404, detail="Compteur non trouvé")
        
        # Calculer la période
        now = datetime.utcnow()
        if period == "week":
            start_date = now - timedelta(days=7)
        elif period == "month":
            start_date = now - timedelta(days=30)
        elif period == "quarter":
            start_date = now - timedelta(days=90)
        elif period == "year":
            start_date = now - timedelta(days=365)
        else:
            start_date = now - timedelta(days=30)
        
        # Récupérer les relevés de la période
        readings = []
        async for reading in db.meter_readings.find({
            "meter_id": meter_id,
            "date_releve": {"$gte": start_date}
        }).sort("date_releve", 1):
            readings.append(reading)
        
        if not readings:
            return {
                "meter_id": meter_id,
                "meter_nom": meter["nom"],
                "period": period,
                "total_consommation": 0,
                "total_cout": 0,
                "moyenne_journaliere": 0,
                "dernier_releve": None,
                "evolution": []
            }
        
        # Calculer les statistiques
        total_consommation = sum(r.get("consommation", 0) for r in readings if r.get("consommation"))
        total_cout = sum(r.get("cout", 0) for r in readings if r.get("cout"))
        
        # Calculer la moyenne journalière
        if len(readings) > 1:
            first_date = readings[0]["date_releve"]
            last_date = readings[-1]["date_releve"]
            days = (last_date - first_date).days or 1
            moyenne_journaliere = total_consommation / days
        else:
            moyenne_journaliere = 0
        
        # Préparer l'évolution
        evolution = [
            {
                "date": r["date_releve"].isoformat(),
                "valeur": r["valeur"],
                "consommation": r.get("consommation", 0),
                "cout": r.get("cout", 0)
            }
            for r in readings
        ]
        
        # Serialize the last reading to avoid ObjectId issues
        dernier_releve = None
        if readings:
            last_reading = readings[-1].copy()
            # Remove any ObjectId fields that might cause serialization issues
            if "_id" in last_reading:
                del last_reading["_id"]
            dernier_releve = last_reading
        
        return {
            "meter_id": meter_id,
            "meter_nom": meter["nom"],
            "period": period,
            "total_consommation": round(total_consommation, 2),
            "total_cout": round(total_cout, 2),
            "moyenne_journaliere": round(moyenne_journaliere, 2),
            "dernier_releve": dernier_releve,
            "evolution": evolution,
            "nombre_releves": len(readings)
        }
    except Exception as e:
        logger.error(f"Erreur calcul statistiques: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/readings/{reading_id}")
async def delete_reading(reading_id: str, current_user: dict = Depends(get_current_user)):
    """Supprimer un relevé"""
    reading = await db.meter_readings.find_one({"id": reading_id})
    if not reading:
        raise HTTPException(status_code=404, detail="Relevé non trouvé")
    
    await db.meter_readings.delete_one({"id": reading_id})
    return {"message": "Relevé supprimé"}



# ==================== INTERVENTION REQUESTS (DEMANDES D'INTERVENTION) ENDPOINTS ====================

@api_router.post("/intervention-requests", response_model=InterventionRequest, status_code=201)
async def create_intervention_request(
    request: InterventionRequestCreate,
    current_user: dict = Depends(require_permission("interventionRequests", "edit"))
):
    """Créer une nouvelle demande d'intervention"""
    try:
        request_id = str(uuid.uuid4())
        request_data = request.model_dump()
        request_data["id"] = request_id
        request_data["date_creation"] = datetime.utcnow()
        request_data["created_by"] = current_user["id"]
        request_data["created_by_name"] = f"{current_user.get('prenom', '')} {current_user.get('nom', '')}"
        request_data["work_order_id"] = None
        request_data["work_order_date_limite"] = None
        request_data["converted_at"] = None
        request_data["converted_by"] = None
        
        # Récupérer les informations de l'équipement si fourni
        if request_data.get("equipement_id"):
            equipment = await db.equipments.find_one({"id": request_data["equipement_id"]})
            if equipment:
                request_data["equipement"] = {"id": equipment["id"], "nom": equipment["nom"]}
        
        # Récupérer les informations de l'emplacement si fourni
        if request_data.get("emplacement_id"):
            location = await db.locations.find_one({"id": request_data["emplacement_id"]})
            if location:
                request_data["emplacement"] = {"id": location["id"], "nom": location["nom"]}
        
        await db.intervention_requests.insert_one(request_data)
        
        # Audit log
        await audit_service.log_action(
            user_id=current_user["id"],
            user_name=current_user.get("nom", "") + " " + current_user.get("prenom", ""),
            user_email=current_user["email"],
            action=ActionType.CREATE,
            entity_type=EntityType.WORK_ORDER,
            entity_id=request_id,
            entity_name=request.titre,
            details=f"Création demande d'intervention"
        )
        
        return InterventionRequest(**request_data)
    except Exception as e:
        logger.error(f"Erreur création demande d'intervention: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/intervention-requests", response_model=List[InterventionRequest])
async def get_all_intervention_requests(current_user: dict = Depends(require_permission("interventionRequests", "view"))):
    """Récupérer toutes les demandes d'intervention"""
    try:
        requests = []
        async for req in db.intervention_requests.find().sort("date_creation", -1):
            requests.append(InterventionRequest(**req))
        return requests
    except Exception as e:
        logger.error(f"Erreur récupération demandes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/intervention-requests/{request_id}", response_model=InterventionRequest)
async def get_intervention_request(request_id: str, current_user: dict = Depends(require_permission("interventionRequests", "view"))):
    """Récupérer une demande d'intervention spécifique"""
    req = await db.intervention_requests.find_one({"id": request_id})
    if not req:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    return InterventionRequest(**req)

@api_router.put("/intervention-requests/{request_id}", response_model=InterventionRequest)
async def update_intervention_request(
    request_id: str,
    request_update: InterventionRequestUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour une demande d'intervention"""
    req = await db.intervention_requests.find_one({"id": request_id})
    if not req:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    
    update_data = {k: v for k, v in request_update.model_dump().items() if v is not None}
    
    # Mettre à jour l'équipement si nécessaire
    if "equipement_id" in update_data:
        if update_data["equipement_id"]:
            equipment = await db.equipments.find_one({"id": update_data["equipement_id"]})
            if equipment:
                update_data["equipement"] = {"id": equipment["id"], "nom": equipment["nom"]}
        else:
            update_data["equipement"] = None
    
    # Mettre à jour l'emplacement si nécessaire
    if "emplacement_id" in update_data:
        if update_data["emplacement_id"]:
            location = await db.locations.find_one({"id": update_data["emplacement_id"]})
            if location:
                update_data["emplacement"] = {"id": location["id"], "nom": location["nom"]}
        else:
            update_data["emplacement"] = None
    
    await db.intervention_requests.update_one({"id": request_id}, {"$set": update_data})
    
    # Récupérer la demande mise à jour
    updated_req = await db.intervention_requests.find_one({"id": request_id})
    
    # Audit log
    await audit_service.log_action(
        user_id=current_user["id"],
        user_name=current_user.get("nom", "") + " " + current_user.get("prenom", ""),
        user_email=current_user["email"],
        action=ActionType.UPDATE,
        entity_type=EntityType.WORK_ORDER,
        entity_id=request_id,
        entity_name=updated_req['titre'],
        details=f"Modification demande d'intervention"
    )
    
    return InterventionRequest(**updated_req)

@api_router.delete("/intervention-requests/{request_id}")
async def delete_intervention_request(request_id: str, current_user: dict = Depends(require_permission("interventionRequests", "delete"))):
    """Supprimer une demande d'intervention"""
    req = await db.intervention_requests.find_one({"id": request_id})
    if not req:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    
    await db.intervention_requests.delete_one({"id": request_id})
    
    # Audit log
    await audit_service.log_action(
        user_id=current_user["id"],
        user_name=current_user.get("nom", "") + " " + current_user.get("prenom", ""),
        user_email=current_user["email"],
        action=ActionType.DELETE,
        entity_type=EntityType.WORK_ORDER,
        entity_id=request_id,
        entity_name=req['titre'],
        details=f"Suppression demande d'intervention"
    )
    
    return {"message": "Demande supprimée"}

@api_router.post("/intervention-requests/{request_id}/convert-to-work-order", response_model=dict)
async def convert_to_work_order(
    request_id: str,
    assignee_id: Optional[str] = None,
    date_limite: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Convertir une demande d'intervention en ordre de travail (Admin/Technicien uniquement)"""
    # Vérifier que l'utilisateur est admin ou technicien
    if current_user.get("role") not in ["ADMIN", "TECHNICIEN"]:
        raise HTTPException(status_code=403, detail="Accès refusé : Seuls les administrateurs et techniciens peuvent convertir des demandes")
    
    try:
        # Récupérer la demande
        req = await db.intervention_requests.find_one({"id": request_id})
        if not req:
            raise HTTPException(status_code=404, detail="Demande non trouvée")
        
        # Vérifier si déjà convertie
        if req.get("work_order_id"):
            raise HTTPException(status_code=400, detail="Cette demande a déjà été convertie en ordre de travail")
        
        # Créer l'ordre de travail
        work_order_id = str(uuid.uuid4())
        
        # Générer le numéro d'ordre (comme pour les créations normales)
        count = await db.work_orders.count_documents({})
        numero = str(5800 + count + 1)
        
        # Utiliser la date limite fournie ou celle de la demande
        date_limite_ordre = None
        if date_limite:
            date_limite_ordre = datetime.fromisoformat(date_limite.replace('Z', '+00:00'))
        elif req.get("date_limite_desiree"):
            date_limite_ordre = req.get("date_limite_desiree")
        
        work_order_data = {
            "id": work_order_id,
            "numero": numero,
            "titre": req["titre"],
            "description": req["description"],
            "statut": "OUVERT",
            "priorite": req["priorite"],
            "equipement_id": req.get("equipement_id"),
            "equipement": req.get("equipement"),
            "emplacement_id": req.get("emplacement_id"),
            "emplacement": req.get("emplacement"),
            "assigne_a_id": assignee_id,
            "assigneA": None,
            "dateLimite": date_limite_ordre,
            "tempsEstime": None,
            "dateCreation": datetime.utcnow(),
            "createdBy": req["created_by"],
            "createdByName": req.get("created_by_name"),
            "tempsReel": None,
            "dateTermine": None,
            "attachments": [],
            "comments": []
        }
        
        # Récupérer les informations de l'assigné si fourni
        if assignee_id:
            assignee = await db.users.find_one({"id": assignee_id})
            if assignee:
                work_order_data["assigneA"] = {
                    "id": assignee["id"],
                    "nom": assignee["nom"],
                    "prenom": assignee["prenom"]
                }
        
        await db.work_orders.insert_one(work_order_data)
        
        # Mettre à jour la demande avec les informations de l'ordre créé
        await db.intervention_requests.update_one(
            {"id": request_id},
            {"$set": {
                "work_order_id": work_order_id,
                "work_order_numero": numero,
                "work_order_date_limite": date_limite_ordre,
                "converted_at": datetime.utcnow(),
                "converted_by": current_user["id"]
            }}
        )
        
        # Émettre un événement pour rafraîchir les notifications
        # Note: Dans une vraie application, on utiliserait des WebSockets
        
        return {
            "message": "Demande convertie en ordre de travail avec succès",
            "work_order_id": work_order_id,
            "request_id": request_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur conversion demande: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)



# ==================== IMPROVEMENT REQUESTS (DEMANDES D'AMÉLIORATION) ENDPOINTS ====================

@api_router.post("/improvement-requests", response_model=ImprovementRequest, status_code=201)
async def create_improvement_request(
    request: ImprovementRequestCreate,
    current_user: dict = Depends(get_current_user)
):
    """Créer une nouvelle demande d'amélioration"""
    try:
        request_id = str(uuid.uuid4())
        request_data = request.model_dump()
        request_data["id"] = request_id
        request_data["date_creation"] = datetime.utcnow()
        request_data["created_by"] = current_user["id"]
        request_data["created_by_name"] = f"{current_user.get('prenom', '')} {current_user.get('nom', '')}"
        request_data["improvement_id"] = None
        request_data["improvement_numero"] = None
        request_data["improvement_date_limite"] = None
        request_data["converted_at"] = None
        request_data["converted_by"] = None
        
        if request_data.get("equipement_id"):
            equipment = await db.equipments.find_one({"id": request_data["equipement_id"]})
            if equipment:
                request_data["equipement"] = {"id": equipment["id"], "nom": equipment["nom"]}
        
        if request_data.get("emplacement_id"):
            location = await db.locations.find_one({"id": request_data["emplacement_id"]})
            if location:
                request_data["emplacement"] = {"id": location["id"], "nom": location["nom"]}
        
        await db.improvement_requests.insert_one(request_data)
        
        await audit_service.log_action(
            user_id=current_user["id"],
            user_name=current_user.get("nom", "") + " " + current_user.get("prenom", ""),
            user_email=current_user["email"],
            action=ActionType.CREATE,
            entity_type=EntityType.IMPROVEMENT_REQUEST,
            entity_id=request_id,
            entity_name=request.titre,
            details=f"Création demande d'amélioration"
        )
        
        return ImprovementRequest(**request_data)
    except Exception as e:
        logger.error(f"Erreur création demande d'amélioration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/improvement-requests", response_model=List[ImprovementRequest])
async def get_all_improvement_requests(current_user: dict = Depends(require_permission("improvementRequests", "view"))):
    """Récupérer toutes les demandes d'amélioration"""
    try:
        requests = []
        async for req in db.improvement_requests.find().sort("date_creation", -1):
            requests.append(ImprovementRequest(**req))
        return requests
    except Exception as e:
        logger.error(f"Erreur récupération demandes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/improvement-requests/{request_id}", response_model=ImprovementRequest)
async def get_improvement_request(request_id: str, current_user: dict = Depends(require_permission("improvementRequests", "view"))):
    """Récupérer une demande d'amélioration spécifique"""
    req = await db.improvement_requests.find_one({"id": request_id})
    if not req:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    return ImprovementRequest(**req)

@api_router.put("/improvement-requests/{request_id}", response_model=ImprovementRequest)
async def update_improvement_request(
    request_id: str,
    request_update: ImprovementRequestUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour une demande d'amélioration"""
    req = await db.improvement_requests.find_one({"id": request_id})
    if not req:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    
    update_data = {k: v for k, v in request_update.model_dump().items() if v is not None}
    
    if "equipement_id" in update_data:
        if update_data["equipement_id"]:
            equipment = await db.equipments.find_one({"id": update_data["equipement_id"]})
            if equipment:
                update_data["equipement"] = {"id": equipment["id"], "nom": equipment["nom"]}
        else:
            update_data["equipement"] = None
    
    if "emplacement_id" in update_data:
        if update_data["emplacement_id"]:
            location = await db.locations.find_one({"id": update_data["emplacement_id"]})
            if location:
                update_data["emplacement"] = {"id": location["id"], "nom": location["nom"]}
        else:
            update_data["emplacement"] = None
    
    await db.improvement_requests.update_one({"id": request_id}, {"$set": update_data})
    updated_req = await db.improvement_requests.find_one({"id": request_id})
    
    await audit_service.log_action(
        user_id=current_user["id"],
        user_name=current_user.get("nom", "") + " " + current_user.get("prenom", ""),
        user_email=current_user["email"],
        action=ActionType.UPDATE,
        entity_type=EntityType.IMPROVEMENT_REQUEST,
        entity_id=request_id,
        entity_name=updated_req['titre'],
        details=f"Modification demande d'amélioration"
    )
    
    return ImprovementRequest(**updated_req)

@api_router.delete("/improvement-requests/{request_id}")
async def delete_improvement_request(request_id: str, current_user: dict = Depends(require_permission("improvementRequests", "delete"))):
    """Supprimer une demande d'amélioration"""
    req = await db.improvement_requests.find_one({"id": request_id})
    if not req:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    
    await db.improvement_requests.delete_one({"id": request_id})
    
    await audit_service.log_action(
        user_id=current_user["id"],
        user_name=current_user.get("nom", "") + " " + current_user.get("prenom", ""),
        user_email=current_user["email"],
        action=ActionType.DELETE,
        entity_type=EntityType.IMPROVEMENT_REQUEST,
        entity_id=request_id,
        entity_name=req['titre'],
        details=f"Suppression demande d'amélioration"
    )
    
    return {"message": "Demande supprimée"}

@api_router.post("/improvement-requests/{request_id}/convert-to-improvement", response_model=dict)
async def convert_to_improvement(
    request_id: str,
    assignee_id: Optional[str] = None,
    date_limite: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Convertir une demande d'amélioration en amélioration (Admin/Technicien uniquement)"""
    if current_user.get("role") not in ["ADMIN", "TECHNICIEN"]:
        raise HTTPException(status_code=403, detail="Accès refusé")
    
    try:
        req = await db.improvement_requests.find_one({"id": request_id})
        if not req:
            raise HTTPException(status_code=404, detail="Demande non trouvée")
        
        if req.get("improvement_id"):
            raise HTTPException(status_code=400, detail="Cette demande a déjà été convertie")
        
        improvement_id = str(uuid.uuid4())
        count = await db.improvements.count_documents({})
        numero = str(7000 + count + 1)
        
        date_limite_imp = None
        if date_limite:
            date_limite_imp = datetime.fromisoformat(date_limite.replace('Z', '+00:00'))
        elif req.get("date_limite_desiree"):
            date_limite_imp = req.get("date_limite_desiree")
        
        improvement_data = {
            "id": improvement_id,
            "numero": numero,
            "titre": req["titre"],
            "description": req["description"],
            "statut": "OUVERT",
            "priorite": req["priorite"],
            "equipement_id": req.get("equipement_id"),
            "equipement": req.get("equipement"),
            "emplacement_id": req.get("emplacement_id"),
            "emplacement": req.get("emplacement"),
            "assigne_a_id": assignee_id,
            "assigneA": None,
            "dateLimite": date_limite_imp,
            "tempsEstime": None,
            "dateCreation": datetime.utcnow(),
            "createdBy": req["created_by"],
            "createdByName": req.get("created_by_name"),
            "tempsReel": None,
            "dateTermine": None,
            "attachments": [],
            "comments": []
        }
        
        if assignee_id:
            assignee = await db.users.find_one({"id": assignee_id})
            if assignee:
                improvement_data["assigneA"] = {
                    "id": assignee["id"],
                    "nom": assignee["nom"],
                    "prenom": assignee["prenom"]
                }
        
        await db.improvements.insert_one(improvement_data)
        
        await db.improvement_requests.update_one(
            {"id": request_id},
            {"$set": {
                "improvement_id": improvement_id,
                "improvement_numero": numero,
                "improvement_date_limite": date_limite_imp,
                "converted_at": datetime.utcnow(),
                "converted_by": current_user["id"]
            }}
        )
        
        await audit_service.log_action(
            user_id=current_user["id"],
            user_name=f"{current_user.get('prenom', '')} {current_user.get('nom', '')}",
            user_email=current_user.get("email", ""),
            action=ActionType.CREATE,
            entity_type=EntityType.IMPROVEMENT,
            entity_id=improvement_id,
            entity_name=f"Amélioration #{numero}",
            details=f"Converti depuis demande: {req['titre']}"
        )
        
        return {
            "message": "Demande convertie en amélioration avec succès",
            "improvement_id": improvement_id,
            "improvement_numero": numero,
            "request_id": request_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur conversion demande: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Attachments et Comments pour Improvement Requests
@api_router.post("/improvement-requests/{request_id}/attachments")
async def upload_improvement_request_attachment(
    request_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload fichier pour une demande d'amélioration"""
    req = await db.improvement_requests.find_one({"id": request_id})
    if not req:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    
    return await upload_attachment_generic(request_id, file, "improvement_requests", current_user)

@api_router.get("/improvement-requests/{request_id}/attachments/{filename}")
async def download_improvement_request_attachment(request_id: str, filename: str, current_user: dict = Depends(get_current_user)):
    """Télécharger un fichier d'une demande d'amélioration"""
    return await download_attachment_generic(request_id, filename, "improvement_requests")

@api_router.post("/improvement-requests/{request_id}/comments")
async def add_improvement_request_comment(
    request_id: str,
    comment_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Ajouter un commentaire à une demande d'amélioration"""
    req = await db.improvement_requests.find_one({"id": request_id})
    if not req:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    
    comment = {
        "id": str(uuid.uuid4()),
        "text": comment_data.get("text", ""),
        "user_id": current_user["id"],
        "user_name": f"{current_user.get('prenom', '')} {current_user.get('nom', '')}",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await db.improvement_requests.update_one(
        {"id": request_id},
        {"$push": {"comments": comment}}
    )
    
    return comment

@api_router.get("/improvement-requests/{request_id}/comments")
async def get_improvement_request_comments(request_id: str, current_user: dict = Depends(get_current_user)):
    """Récupérer les commentaires d'une demande d'amélioration"""
    req = await db.improvement_requests.find_one({"id": request_id})
    if not req:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    
    return req.get("comments", [])

# Attachments pour Improvements
@api_router.post("/improvements/{imp_id}/attachments")
async def upload_improvement_attachment(
    imp_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload fichier pour une amélioration"""
    imp = await db.improvements.find_one({"id": imp_id})
    if not imp:
        raise HTTPException(status_code=404, detail="Amélioration non trouvée")
    
    return await upload_attachment_generic(imp_id, file, "improvements", current_user)

@api_router.get("/improvements/{imp_id}/attachments/{filename}")
async def download_improvement_attachment(imp_id: str, filename: str, current_user: dict = Depends(get_current_user)):
    """Télécharger un fichier d'une amélioration"""
    return await download_attachment_generic(imp_id, filename, "improvements")

# Comments pour Improvements
@api_router.post("/improvements/{imp_id}/comments")
async def add_improvement_comment(
    imp_id: str,
    comment_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Ajouter un commentaire à une amélioration"""
    imp = await db.improvements.find_one({"id": imp_id})
    if not imp:
        raise HTTPException(status_code=404, detail="Amélioration non trouvée")
    
    comment = {
        "id": str(uuid.uuid4()),
        "text": comment_data.get("text", ""),
        "user_id": current_user["id"],
        "user_name": f"{current_user.get('prenom', '')} {current_user.get('nom', '')}",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await db.improvements.update_one(
        {"id": imp_id},
        {"$push": {"comments": comment}}
    )
    
    return comment

@api_router.get("/improvements/{imp_id}/comments")
async def get_improvement_comments(imp_id: str, current_user: dict = Depends(get_current_user)):
    """Récupérer les commentaires d'une amélioration"""
    imp = await db.improvements.find_one({"id": imp_id})
    if not imp:
        raise HTTPException(status_code=404, detail="Amélioration non trouvée")
    
    return imp.get("comments", [])

# ==================== IMPROVEMENTS (AMÉLIORATIONS) ENDPOINTS ====================

@api_router.get("/improvements", response_model=List[Improvement])
async def get_improvements(
    current_user: dict = Depends(get_current_user),
    statut: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    date_type: str = "creation"
):
    """Récupérer toutes les améliorations avec filtres"""
    try:
        query = {}
        
        if statut:
            query["statut"] = statut
        
        if start_date or end_date:
            date_field = "dateCreation" if date_type == "creation" else "dateLimite"
            date_filter = {}
            if start_date:
                date_filter["$gte"] = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if end_date:
                date_filter["$lte"] = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query[date_field] = date_filter
        
        improvements = []
        async for imp in db.improvements.find(query).sort("dateCreation", -1):
            if imp.get("assigne_a_id"):
                imp["assigneA"] = await get_user_by_id(imp["assigne_a_id"])
            if imp.get("emplacement_id"):
                imp["emplacement"] = await get_location_by_id(imp["emplacement_id"])
            if imp.get("equipement_id"):
                imp["equipement"] = await get_equipment_by_id(imp["equipement_id"])
            
            if imp.get("createdBy"):
                try:
                    creator = await db.users.find_one({"id": imp["createdBy"]})
                    if creator:
                        imp["createdByName"] = f"{creator.get('prenom', '')} {creator.get('nom', '')}".strip()
                except Exception as e:
                    logger.error(f"Erreur recherche créateur: {e}")
            
            if "numero" not in imp or not imp["numero"]:
                imp["numero"] = "N/A"
            
            improvements.append(Improvement(**imp))
        
        return improvements
    except Exception as e:
        logger.error(f"Erreur récupération améliorations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/improvements/{imp_id}", response_model=Improvement)
async def get_improvement(imp_id: str, current_user: dict = Depends(require_permission("improvements", "view"))):
    """Détails d'une amélioration"""
    try:
        imp = await db.improvements.find_one({"id": imp_id})
        if not imp:
            raise HTTPException(status_code=404, detail="Amélioration non trouvée")
        
        imp = serialize_doc(imp)
        if imp.get("assigne_a_id"):
            imp["assigneA"] = await get_user_by_id(imp["assigne_a_id"])
        if imp.get("emplacement_id"):
            imp["emplacement"] = await get_location_by_id(imp["emplacement_id"])
        if imp.get("equipement_id"):
            imp["equipement"] = await get_equipment_by_id(imp["equipement_id"])
        
        if imp.get("createdBy"):
            try:
                creator = await db.users.find_one({"id": imp["createdBy"]})
                if creator:
                    imp["createdByName"] = f"{creator.get('prenom', '')} {creator.get('nom', '')}".strip()
            except Exception as e:
                logger.error(f"Erreur recherche créateur: {e}")
        
        if "numero" not in imp or not imp["numero"]:
            imp["numero"] = "N/A"
        
        return Improvement(**imp)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/improvements", response_model=Improvement)
async def create_improvement(imp_create: ImprovementCreate, current_user: dict = Depends(require_permission("improvements", "edit"))):
    """Créer une nouvelle amélioration"""
    count = await db.improvements.count_documents({})
    numero = str(7000 + count + 1)
    
    improvement_id = str(uuid.uuid4())
    improvement_data = imp_create.model_dump()
    improvement_data["id"] = improvement_id
    improvement_data["numero"] = numero
    improvement_data["statut"] = "OUVERT"
    improvement_data["dateCreation"] = datetime.utcnow()
    improvement_data["createdBy"] = current_user["id"]
    improvement_data["createdByName"] = f"{current_user.get('prenom', '')} {current_user.get('nom', '')}"
    improvement_data["tempsReel"] = None
    improvement_data["dateTermine"] = None
    improvement_data["attachments"] = []
    improvement_data["comments"] = []
    
    if improvement_data.get("assigne_a_id"):
        assignee = await db.users.find_one({"id": improvement_data["assigne_a_id"]})
        if assignee:
            improvement_data["assigneA"] = {
                "id": assignee["id"],
                "nom": assignee["nom"],
                "prenom": assignee["prenom"]
            }
    
    if improvement_data.get("equipement_id"):
        equipment = await db.equipments.find_one({"id": improvement_data["equipement_id"]})
        if equipment:
            improvement_data["equipement"] = {"id": equipment["id"], "nom": equipment["nom"]}
    
    if improvement_data.get("emplacement_id"):
        location = await db.locations.find_one({"id": improvement_data["emplacement_id"]})
        if location:
            improvement_data["emplacement"] = {"id": location["id"], "nom": location["nom"]}
    
    await db.improvements.insert_one(improvement_data)
    
    await audit_service.log_action(
        user_id=current_user["id"],
        user_name=f"{current_user.get('nom', '')} {current_user.get('prenom', '')}",
        user_email=current_user["email"],
        action=ActionType.CREATE,
        entity_type=EntityType.IMPROVEMENT,
        entity_id=improvement_id,
        entity_name=imp_create.titre,
        details="Création amélioration"
    )
    
    return Improvement(**improvement_data)

@api_router.put("/improvements/{imp_id}", response_model=Improvement)
async def update_improvement(
    imp_id: str,
    imp_update: ImprovementUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour une amélioration"""
    imp = await db.improvements.find_one({"id": imp_id})
    if not imp:
        raise HTTPException(status_code=404, detail="Amélioration non trouvée")
    
    update_data = {k: v for k, v in imp_update.model_dump().items() if v is not None}
    
    if update_data.get("statut") == "TERMINE" and "dateTermine" not in update_data:
        update_data["dateTermine"] = datetime.utcnow()
    
    if "assigne_a_id" in update_data:
        if update_data["assigne_a_id"]:
            assignee = await db.users.find_one({"id": update_data["assigne_a_id"]})
            if assignee:
                update_data["assigneA"] = {
                    "id": assignee["id"],
                    "nom": assignee["nom"],
                    "prenom": assignee["prenom"]
                }
        else:
            update_data["assigneA"] = None
    
    if "equipement_id" in update_data:
        if update_data["equipement_id"]:
            equipment = await db.equipments.find_one({"id": update_data["equipement_id"]})
            if equipment:
                update_data["equipement"] = {"id": equipment["id"], "nom": equipment["nom"]}
        else:
            update_data["equipement"] = None
    
    if "emplacement_id" in update_data:
        if update_data["emplacement_id"]:
            location = await db.locations.find_one({"id": update_data["emplacement_id"]})
            if location:
                update_data["emplacement"] = {"id": location["id"], "nom": location["nom"]}
        else:
            update_data["emplacement"] = None
    
    await db.improvements.update_one({"id": imp_id}, {"$set": update_data})
    updated_imp = await db.improvements.find_one({"id": imp_id})
    
    updated_imp = serialize_doc(updated_imp)
    if updated_imp.get("assigne_a_id"):
        updated_imp["assigneA"] = await get_user_by_id(updated_imp["assigne_a_id"])
    if updated_imp.get("emplacement_id"):
        updated_imp["emplacement"] = await get_location_by_id(updated_imp["emplacement_id"])
    if updated_imp.get("equipement_id"):
        updated_imp["equipement"] = await get_equipment_by_id(updated_imp["equipement_id"])
    
    await audit_service.log_action(
        user_id=current_user["id"],
        user_name=f"{current_user.get('nom', '')} {current_user.get('prenom', '')}",
        user_email=current_user["email"],
        action=ActionType.UPDATE,
        entity_type=EntityType.IMPROVEMENT,
        entity_id=imp_id,
        entity_name=updated_imp["titre"],
        details="Modification amélioration"
    )
    
    return Improvement(**updated_imp)

@api_router.delete("/improvements/{imp_id}")
async def delete_improvement(imp_id: str, current_user: dict = Depends(require_permission("improvements", "delete"))):
    """Supprimer une amélioration"""
    imp = await db.improvements.find_one({"id": imp_id})
    if not imp:
        raise HTTPException(status_code=404, detail="Amélioration non trouvée")
    
    await db.improvements.delete_one({"id": imp_id})
    
    await audit_service.log_action(
        user_id=current_user["id"],
        user_name=f"{current_user.get('nom', '')} {current_user.get('prenom', '')}",
        user_email=current_user["email"],
        action=ActionType.DELETE,
        entity_type=EntityType.IMPROVEMENT,
        entity_id=imp_id,
        entity_name=imp["titre"],
        details="Suppression amélioration"
    )
    
    return {"message": "Amélioration supprimée"}


# ==================== UPDATE MANAGEMENT ENDPOINTS ====================
from update_service import UpdateService

# Initialiser le service de mise à jour
update_service = UpdateService(db)

@api_router.get("/updates/check")
async def check_updates(current_user: dict = Depends(get_current_admin_user)):
    """
    Vérifie si une mise à jour est disponible (Admin uniquement)
    """
    try:
        update_info = await update_service.check_for_updates()
        return update_info if update_info else {"available": False, "current_version": update_service.current_version}
    except Exception as e:
        logger.error(f"❌ Erreur vérification mises à jour: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/updates/status")
async def get_update_status(current_user: dict = Depends(get_current_admin_user)):
    """
    Récupère le statut actuel des mises à jour (Admin uniquement)
    """
    try:
        status = await update_service.get_update_status()
        return status
    except Exception as e:
        logger.error(f"❌ Erreur récupération statut: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/updates/dismiss/{version}")
async def dismiss_update(version: str, current_user: dict = Depends(get_current_admin_user)):
    """
    Marque une notification de mise à jour comme dismissée (Admin uniquement)
    """
    try:
        await update_service.dismiss_update_notification(version)
        return {"message": "Notification dismissée"}
    except Exception as e:
        logger.error(f"❌ Erreur dismiss notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/updates/apply")
async def apply_update(
    version: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Applique une mise à jour (Admin uniquement)
    Crée une sauvegarde complète, puis applique la MAJ et redémarre les services
    """
    try:
        logger.info(f"🚀 Demande d'application de la mise à jour vers {version} par {current_user.get('email')}")
        
        # Enregistrer dans l'audit
        await audit_service.log_action(
            user_id=current_user.get("id"),
            user_name=f"{current_user.get('prenom')} {current_user.get('nom')}",
            user_email=current_user.get("email"),
            action=ActionType.UPDATE,
            entity_type=EntityType.SYSTEM,
            entity_id="system",
            entity_name=f"Mise à jour vers {version}"
        )
        
        result = await update_service.apply_update(version)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("message"))
            
    except Exception as e:
        logger.error(f"❌ Erreur application mise à jour: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/updates/recent-info")
async def get_recent_update_info(current_user: dict = Depends(get_current_user)):
    """
    Récupère les informations des mises à jour récentes (pour le popup utilisateur)
    Disponible pour tous les utilisateurs connectés
    """
    try:
        info = await update_service.get_recent_updates_info(days=3)
        return info
    except Exception as e:
        logger.error(f"❌ Erreur récupération info MAJ récente: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/updates/version")
async def get_current_version():
    """
    Retourne la version actuelle de l'application (public)
    """
    return {
        "version": update_service.current_version,
        "app_name": "GMAO Iris"
    }


# Include the router in the main app (MUST be after all endpoint definitions)
app.include_router(api_router)

@app.on_event("startup")
async def startup_scheduler():
    """Démarre le scheduler au démarrage de l'application"""
    try:
        # Configurer le scheduler pour s'exécuter chaque jour à minuit (heure locale)
        scheduler.add_job(
            auto_check_preventive_maintenance,
            CronTrigger(hour=0, minute=0),  # Tous les jours à minuit
            id='check_preventive_maintenance',
            name='Vérification automatique maintenances préventives',
            replace_existing=True
        )
        
        # Configurer la vérification automatique des mises à jour à 1h00 du matin
        scheduler.add_job(
            update_service.check_for_updates,
            CronTrigger(hour=1, minute=0),  # Tous les jours à 1h00
            id='check_updates',
            name='Vérification automatique des mises à jour',
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("✅ Scheduler démarré:")
        logger.info("   - Vérification maintenances préventives: tous les jours à 00h00")
        logger.info("   - Vérification mises à jour: tous les jours à 01h00")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du démarrage du scheduler: {str(e)}")

@app.on_event("shutdown")
async def shutdown_services():
    """Arrête les services lors de l'arrêt de l'application"""
    try:
        scheduler.shutdown()
        logger.info("✅ Scheduler arrêté")
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'arrêt du scheduler: {str(e)}")
    
    client.close()
    logger.info("✅ Connexion MongoDB fermée")
