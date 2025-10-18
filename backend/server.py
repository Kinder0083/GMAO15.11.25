from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from datetime import datetime
from bson import ObjectId

# Import our models and dependencies
from models import *
from auth import get_password_hash, verify_password, create_access_token
import dependencies
from dependencies import get_current_user, get_current_admin_user

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'gmao_atlas')]

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
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    if "password" in doc:
        del doc["password"]
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
    # Find user
    user = await db.users.find_one({"email": login_request.email})
    if not user or not verify_password(login_request.password, user["password"]):
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

# ==================== WORK ORDERS ROUTES ====================
@api_router.get("/work-orders", response_model=List[WorkOrder])
async def get_work_orders(current_user: dict = Depends(get_current_user)):
    """Liste tous les ordres de travail"""
    work_orders = await db.work_orders.find().to_list(1000)
    
    # Populate references
    for wo in work_orders:
        wo["id"] = str(wo["_id"])
        del wo["_id"]
        
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
    
    return [Equipment(**eq) for eq in equipments]

@api_router.post("/equipments", response_model=Equipment)
async def create_equipment(eq_create: EquipmentCreate, current_user: dict = Depends(get_current_user)):
    """Créer un nouvel équipement"""
    eq_dict = eq_create.model_dump()
    eq_dict["dateCreation"] = datetime.utcnow()
    eq_dict["derniereMaintenance"] = None
    eq_dict["_id"] = ObjectId()
    
    await db.equipments.insert_one(eq_dict)
    
    eq = serialize_doc(eq_dict)
    if eq.get("emplacement_id"):
        eq["emplacement"] = await get_location_by_id(eq["emplacement_id"])
    
    return Equipment(**eq)

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
        
        return Equipment(**eq)
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

# ==================== LOCATIONS ROUTES ====================
@api_router.get("/locations", response_model=List[Location])
async def get_locations(current_user: dict = Depends(get_current_user)):
    """Liste tous les emplacements"""
    locations = await db.locations.find().to_list(1000)
    return [Location(**serialize_doc(loc)) for loc in locations]

@api_router.post("/locations", response_model=Location)
async def create_location(loc_create: LocationCreate, current_user: dict = Depends(get_current_user)):
    """Créer un nouvel emplacement"""
    loc_dict = loc_create.model_dump()
    loc_dict["dateCreation"] = datetime.utcnow()
    loc_dict["_id"] = ObjectId()
    
    await db.locations.insert_one(loc_dict)
    
    return Location(**serialize_doc(loc_dict))

@api_router.put("/locations/{loc_id}", response_model=Location)
async def update_location(loc_id: str, loc_update: LocationUpdate, current_user: dict = Depends(get_current_user)):
    """Modifier un emplacement"""
    try:
        update_data = {k: v for k, v in loc_update.model_dump().items() if v is not None}
        
        await db.locations.update_one(
            {"_id": ObjectId(loc_id)},
            {"$set": update_data}
        )
        
        loc = await db.locations.find_one({"_id": ObjectId(loc_id)})
        return Location(**serialize_doc(loc))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.delete("/locations/{loc_id}")
async def delete_location(loc_id: str, current_user: dict = Depends(get_current_user)):
    """Supprimer un emplacement"""
    try:
        result = await db.locations.delete_one({"_id": ObjectId(loc_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Emplacement non trouvé")
        return {"message": "Emplacement supprimé"}
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
