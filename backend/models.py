from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum
import re

# Enums
class UserRole(str, Enum):
    ADMIN = "ADMIN"
    TECHNICIEN = "TECHNICIEN"
    VISUALISEUR = "VISUALISEUR"
    DIRECTEUR = "DIRECTEUR"
    QHSE = "QHSE"
    RSP_PROD = "RSP_PROD"
    PROD = "PROD"
    INDUS = "INDUS"
    LOGISTIQUE = "LOGISTIQUE"
    LABO = "LABO"
    ADV = "ADV"

# Permission Models
class ModulePermission(BaseModel):
    view: bool = False
    edit: bool = False
    delete: bool = False

class UserPermissions(BaseModel):
    dashboard: ModulePermission = ModulePermission(view=True, edit=False, delete=False)
    interventionRequests: ModulePermission = ModulePermission(view=True, edit=False, delete=False)
    workOrders: ModulePermission = ModulePermission(view=True, edit=False, delete=False)
    improvementRequests: ModulePermission = ModulePermission(view=True, edit=False, delete=False)
    improvements: ModulePermission = ModulePermission(view=True, edit=False, delete=False)
    preventiveMaintenance: ModulePermission = ModulePermission(view=True, edit=False, delete=False)
    assets: ModulePermission = ModulePermission(view=True, edit=False, delete=False)
    inventory: ModulePermission = ModulePermission(view=True, edit=False, delete=False)
    locations: ModulePermission = ModulePermission(view=True, edit=False, delete=False)
    meters: ModulePermission = ModulePermission(view=True, edit=False, delete=False)
    vendors: ModulePermission = ModulePermission(view=True, edit=False, delete=False)
    reports: ModulePermission = ModulePermission(view=True, edit=False, delete=False)
    people: ModulePermission = ModulePermission(view=True, edit=False, delete=False)
    planning: ModulePermission = ModulePermission(view=True, edit=False, delete=False)
    purchaseHistory: ModulePermission = ModulePermission(view=True, edit=False, delete=False)
    importExport: ModulePermission = ModulePermission(view=False, edit=False, delete=False)
    journal: ModulePermission = ModulePermission(view=False, edit=False, delete=False)

# Fonction helper pour obtenir les permissions par défaut selon le rôle
def get_default_permissions_by_role(role: str) -> UserPermissions:
    """Retourne les permissions par défaut selon le rôle de l'utilisateur"""
    
    # Permissions complètes pour ADMIN
    if role == "ADMIN":
        return UserPermissions(
            dashboard=ModulePermission(view=True, edit=True, delete=True),
            interventionRequests=ModulePermission(view=True, edit=True, delete=True),
            workOrders=ModulePermission(view=True, edit=True, delete=True),
            improvementRequests=ModulePermission(view=True, edit=True, delete=True),
            improvements=ModulePermission(view=True, edit=True, delete=True),
            preventiveMaintenance=ModulePermission(view=True, edit=True, delete=True),
            assets=ModulePermission(view=True, edit=True, delete=True),
            inventory=ModulePermission(view=True, edit=True, delete=True),
            locations=ModulePermission(view=True, edit=True, delete=True),
            meters=ModulePermission(view=True, edit=True, delete=True),
            vendors=ModulePermission(view=True, edit=True, delete=True),
            reports=ModulePermission(view=True, edit=True, delete=True),
            people=ModulePermission(view=True, edit=True, delete=True),
            planning=ModulePermission(view=True, edit=True, delete=True),
            purchaseHistory=ModulePermission(view=True, edit=True, delete=True),
            importExport=ModulePermission(view=True, edit=True, delete=True),
            journal=ModulePermission(view=True, edit=False, delete=False)
        )
    
    # DIRECTEUR : Demande d'inter./Demandes d'amél. en visualisation et modification
    # Ordres de travail/Améliorations/Maintenance prev./Compteurs/Historique Achat en visualisation seulement
    elif role == "DIRECTEUR":
        return UserPermissions(
            dashboard=ModulePermission(view=True, edit=False, delete=False),
            interventionRequests=ModulePermission(view=True, edit=True, delete=False),
            workOrders=ModulePermission(view=True, edit=False, delete=False),
            improvementRequests=ModulePermission(view=True, edit=True, delete=False),
            improvements=ModulePermission(view=True, edit=False, delete=False),
            preventiveMaintenance=ModulePermission(view=True, edit=False, delete=False),
            assets=ModulePermission(view=True, edit=False, delete=False),
            inventory=ModulePermission(view=True, edit=False, delete=False),
            locations=ModulePermission(view=True, edit=False, delete=False),
            meters=ModulePermission(view=True, edit=False, delete=False),
            vendors=ModulePermission(view=True, edit=False, delete=False),
            reports=ModulePermission(view=True, edit=False, delete=False),
            people=ModulePermission(view=True, edit=False, delete=False),
            planning=ModulePermission(view=True, edit=False, delete=False),
            purchaseHistory=ModulePermission(view=True, edit=False, delete=False),
            importExport=ModulePermission(view=False, edit=False, delete=False),
            journal=ModulePermission(view=False, edit=False, delete=False)
        )
    
    # QHSE : Demande d'inter./Demandes d'amél. en visualisation et modification
    # Ordres de travail/Améliorations/Compteurs en visualisation seulement
    elif role == "QHSE":
        return UserPermissions(
            dashboard=ModulePermission(view=True, edit=False, delete=False),
            interventionRequests=ModulePermission(view=True, edit=True, delete=False),
            workOrders=ModulePermission(view=True, edit=False, delete=False),
            improvementRequests=ModulePermission(view=True, edit=True, delete=False),
            improvements=ModulePermission(view=True, edit=False, delete=False),
            preventiveMaintenance=ModulePermission(view=True, edit=False, delete=False),
            assets=ModulePermission(view=True, edit=False, delete=False),
            inventory=ModulePermission(view=True, edit=False, delete=False),
            locations=ModulePermission(view=True, edit=False, delete=False),
            meters=ModulePermission(view=True, edit=False, delete=False),
            vendors=ModulePermission(view=False, edit=False, delete=False),
            reports=ModulePermission(view=True, edit=False, delete=False),
            people=ModulePermission(view=False, edit=False, delete=False),
            planning=ModulePermission(view=False, edit=False, delete=False),
            purchaseHistory=ModulePermission(view=False, edit=False, delete=False),
            importExport=ModulePermission(view=False, edit=False, delete=False),
            journal=ModulePermission(view=False, edit=False, delete=False)
        )
    
    # LABO et ADV : Demande d'inter. en visualisation et modification
    # Fournisseurs/Compteurs/Historique Achat en visualisation seulement
    elif role in ["LABO", "ADV"]:
        return UserPermissions(
            dashboard=ModulePermission(view=True, edit=False, delete=False),
            interventionRequests=ModulePermission(view=True, edit=True, delete=False),
            workOrders=ModulePermission(view=False, edit=False, delete=False),
            improvementRequests=ModulePermission(view=False, edit=False, delete=False),
            improvements=ModulePermission(view=False, edit=False, delete=False),
            preventiveMaintenance=ModulePermission(view=False, edit=False, delete=False),
            assets=ModulePermission(view=False, edit=False, delete=False),
            inventory=ModulePermission(view=False, edit=False, delete=False),
            locations=ModulePermission(view=False, edit=False, delete=False),
            meters=ModulePermission(view=True, edit=False, delete=False),
            vendors=ModulePermission(view=True, edit=False, delete=False),
            reports=ModulePermission(view=True, edit=False, delete=False),
            people=ModulePermission(view=False, edit=False, delete=False),
            planning=ModulePermission(view=False, edit=False, delete=False),
            purchaseHistory=ModulePermission(view=True, edit=False, delete=False),
            importExport=ModulePermission(view=False, edit=False, delete=False),
            journal=ModulePermission(view=False, edit=False, delete=False)
        )
    
    # PROD (RSP_PROD et PROD) : Demande d'inter./Demandes d'amél./Ordres de travail/Améliorations/Equipement en visualisation et modification
    # Inventaire/Maintenance prev. en visualisation seulement
    elif role in ["RSP_PROD", "PROD"]:
        return UserPermissions(
            dashboard=ModulePermission(view=True, edit=False, delete=False),
            interventionRequests=ModulePermission(view=True, edit=True, delete=False),
            workOrders=ModulePermission(view=True, edit=True, delete=False),
            improvementRequests=ModulePermission(view=True, edit=True, delete=False),
            improvements=ModulePermission(view=True, edit=True, delete=False),
            preventiveMaintenance=ModulePermission(view=True, edit=False, delete=False),
            assets=ModulePermission(view=True, edit=True, delete=False),
            inventory=ModulePermission(view=True, edit=False, delete=False),
            locations=ModulePermission(view=True, edit=False, delete=False),
            meters=ModulePermission(view=False, edit=False, delete=False),
            vendors=ModulePermission(view=False, edit=False, delete=False),
            reports=ModulePermission(view=True, edit=False, delete=False),
            people=ModulePermission(view=False, edit=False, delete=False),
            planning=ModulePermission(view=False, edit=False, delete=False),
            purchaseHistory=ModulePermission(view=False, edit=False, delete=False),
            importExport=ModulePermission(view=False, edit=False, delete=False),
            journal=ModulePermission(view=False, edit=False, delete=False)
        )
    
    # INDUS : Demande d'inter./Demandes d'amél./Ordres de travail/Améliorations/Equipement en visualisation et modification
    # Inventaire/Maintenance prev./Compteurs en visualisation seulement
    elif role == "INDUS":
        return UserPermissions(
            dashboard=ModulePermission(view=True, edit=False, delete=False),
            interventionRequests=ModulePermission(view=True, edit=True, delete=False),
            workOrders=ModulePermission(view=True, edit=True, delete=False),
            improvementRequests=ModulePermission(view=True, edit=True, delete=False),
            improvements=ModulePermission(view=True, edit=True, delete=False),
            preventiveMaintenance=ModulePermission(view=True, edit=False, delete=False),
            assets=ModulePermission(view=True, edit=True, delete=False),
            inventory=ModulePermission(view=True, edit=False, delete=False),
            locations=ModulePermission(view=True, edit=False, delete=False),
            meters=ModulePermission(view=True, edit=False, delete=False),
            vendors=ModulePermission(view=False, edit=False, delete=False),
            reports=ModulePermission(view=True, edit=False, delete=False),
            people=ModulePermission(view=False, edit=False, delete=False),
            planning=ModulePermission(view=False, edit=False, delete=False),
            purchaseHistory=ModulePermission(view=False, edit=False, delete=False),
            importExport=ModulePermission(view=False, edit=False, delete=False),
            journal=ModulePermission(view=False, edit=False, delete=False)
        )
    
    # LOGISTIQUE : Même que PROD mais peut-être avec accès Fournisseurs
    elif role == "LOGISTIQUE":
        return UserPermissions(
            dashboard=ModulePermission(view=True, edit=False, delete=False),
            interventionRequests=ModulePermission(view=True, edit=True, delete=False),
            workOrders=ModulePermission(view=True, edit=True, delete=False),
            improvementRequests=ModulePermission(view=True, edit=True, delete=False),
            improvements=ModulePermission(view=True, edit=True, delete=False),
            preventiveMaintenance=ModulePermission(view=True, edit=False, delete=False),
            assets=ModulePermission(view=True, edit=True, delete=False),
            inventory=ModulePermission(view=True, edit=True, delete=False),
            locations=ModulePermission(view=True, edit=False, delete=False),
            meters=ModulePermission(view=False, edit=False, delete=False),
            vendors=ModulePermission(view=True, edit=False, delete=False),
            reports=ModulePermission(view=True, edit=False, delete=False),
            people=ModulePermission(view=False, edit=False, delete=False),
            planning=ModulePermission(view=False, edit=False, delete=False),
            purchaseHistory=ModulePermission(view=True, edit=False, delete=False),
            importExport=ModulePermission(view=False, edit=False, delete=False),
            journal=ModulePermission(view=False, edit=False, delete=False)
        )
    
    # TECHNICIEN : Permissions complètes sur les modules opérationnels
    elif role == "TECHNICIEN":
        return UserPermissions(
            dashboard=ModulePermission(view=True, edit=False, delete=False),
            interventionRequests=ModulePermission(view=True, edit=True, delete=True),
            workOrders=ModulePermission(view=True, edit=True, delete=True),
            improvementRequests=ModulePermission(view=True, edit=True, delete=True),
            improvements=ModulePermission(view=True, edit=True, delete=True),
            preventiveMaintenance=ModulePermission(view=True, edit=True, delete=True),
            assets=ModulePermission(view=True, edit=True, delete=True),
            inventory=ModulePermission(view=True, edit=True, delete=True),
            locations=ModulePermission(view=True, edit=True, delete=True),
            meters=ModulePermission(view=True, edit=True, delete=True),
            vendors=ModulePermission(view=True, edit=True, delete=True),
            reports=ModulePermission(view=True, edit=False, delete=False),
            people=ModulePermission(view=True, edit=False, delete=False),
            planning=ModulePermission(view=True, edit=True, delete=False),
            purchaseHistory=ModulePermission(view=True, edit=True, delete=True),
            importExport=ModulePermission(view=False, edit=False, delete=False),
            journal=ModulePermission(view=False, edit=False, delete=False)
        )
    
    # VISUALISEUR : Visualisation uniquement sur tout
    elif role == "VISUALISEUR":
        return UserPermissions(
            dashboard=ModulePermission(view=True, edit=False, delete=False),
            interventionRequests=ModulePermission(view=True, edit=False, delete=False),
            workOrders=ModulePermission(view=True, edit=False, delete=False),
            improvementRequests=ModulePermission(view=True, edit=False, delete=False),
            improvements=ModulePermission(view=True, edit=False, delete=False),
            preventiveMaintenance=ModulePermission(view=True, edit=False, delete=False),
            assets=ModulePermission(view=True, edit=False, delete=False),
            inventory=ModulePermission(view=True, edit=False, delete=False),
            locations=ModulePermission(view=True, edit=False, delete=False),
            meters=ModulePermission(view=True, edit=False, delete=False),
            vendors=ModulePermission(view=True, edit=False, delete=False),
            reports=ModulePermission(view=True, edit=False, delete=False),
            people=ModulePermission(view=True, edit=False, delete=False),
            planning=ModulePermission(view=True, edit=False, delete=False),
            purchaseHistory=ModulePermission(view=True, edit=False, delete=False),
            importExport=ModulePermission(view=False, edit=False, delete=False),
            journal=ModulePermission(view=False, edit=False, delete=False)
        )
    
    # Par défaut : permissions minimales
    else:
        return UserPermissions()


class WorkOrderStatus(str, Enum):
    OUVERT = "OUVERT"
    EN_COURS = "EN_COURS"
    EN_ATTENTE = "EN_ATTENTE"
    TERMINE = "TERMINE"

class Priority(str, Enum):
    HAUTE = "HAUTE"
    MOYENNE = "MOYENNE"
    NORMALE = "NORMALE"
    BASSE = "BASSE"
    AUCUNE = "AUCUNE"

class EquipmentStatus(str, Enum):
    OPERATIONNEL = "OPERATIONNEL"
    EN_MAINTENANCE = "EN_MAINTENANCE"
    HORS_SERVICE = "HORS_SERVICE"
    ALERTE_S_EQUIP = "ALERTE_S_EQUIP"

class Frequency(str, Enum):
    HEBDOMADAIRE = "HEBDOMADAIRE"
    MENSUEL = "MENSUEL"
    TRIMESTRIEL = "TRIMESTRIEL"
    ANNUEL = "ANNUEL"

class PMStatus(str, Enum):
    ACTIF = "ACTIF"
    INACTIF = "INACTIF"

class ActionType(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"

class EntityType(str, Enum):
    USER = "USER"
    WORK_ORDER = "WORK_ORDER"
    EQUIPMENT = "EQUIPMENT"
    LOCATION = "LOCATION"
    VENDOR = "VENDOR"
    INVENTORY = "INVENTORY"
    PREVENTIVE_MAINTENANCE = "PREVENTIVE_MAINTENANCE"
    PURCHASE_HISTORY = "PURCHASE_HISTORY"
    IMPROVEMENT_REQUEST = "IMPROVEMENT_REQUEST"
    IMPROVEMENT = "IMPROVEMENT"

# Audit Log Models
class AuditLog(BaseModel):
    id: str
    timestamp: datetime
    user_id: str
    user_name: str
    user_email: str
    action: ActionType
    entity_type: EntityType
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    details: Optional[str] = None
    changes: Optional[Dict] = None

class AuditLogCreate(BaseModel):
    user_id: str
    user_name: str
    user_email: str
    action: ActionType
    entity_type: EntityType
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    details: Optional[str] = None
    changes: Optional[Dict] = None

# Comment Models
class Comment(BaseModel):
    id: str
    user_id: str
    user_name: str
    text: str
    timestamp: datetime

class CommentCreate(BaseModel):
    text: str

# User Models
class UserBase(BaseModel):
    nom: str
    prenom: str
    email: str  # Changé de EmailStr à str pour accepter .local
    telephone: Optional[str] = None
    role: UserRole = UserRole.VISUALISEUR
    service: Optional[str] = None
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        # Validation basique d'email qui accepte les domaines locaux
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$|^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.local$'
        if not re.match(email_pattern, v):
            raise ValueError('Format d\'email invalide')
        return v.lower()

class UserCreate(UserBase):
    password: str

class UserInvite(BaseModel):
    nom: str
    prenom: str
    email: str
    telephone: Optional[str] = None
    role: UserRole = UserRole.VISUALISEUR
    service: Optional[str] = None
    permissions: Optional[UserPermissions] = None
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        # Validation basique d'email qui accepte les domaines locaux
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$|^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.local$'
        if not re.match(email_pattern, v):
            raise ValueError('Format d\'email invalide')
        return v.lower()

class UserUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    role: Optional[UserRole] = None
    service: Optional[str] = None
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Validation basique d'email qui accepte les domaines locaux
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$|^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.local$'
        if not re.match(email_pattern, v):
            raise ValueError('Format d\'email invalide')
        return v.lower()

class UserProfileUpdate(BaseModel):
    """Modèle pour mise à jour du profil utilisateur depuis Settings"""
    nom: Optional[str] = None
    prenom: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    service: Optional[str] = None
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Validation basique d'email qui accepte les domaines locaux
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$|^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.local$'
        if not re.match(email_pattern, v):
            raise ValueError('Format d\'email invalide')
        return v.lower()

class UserPermissionsUpdate(BaseModel):
    permissions: UserPermissions

class User(UserBase):
    id: str
    statut: str = "actif"
    dateCreation: datetime
    derniereConnexion: Optional[datetime] = None
    permissions: UserPermissions = Field(default_factory=UserPermissions)
    firstLogin: Optional[bool] = False  # True si premier login, nécessite changement de mot de passe

    class Config:
        from_attributes = True

# Auth Models
class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class LoginRequest(BaseModel):
    email: str
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        # Validation basique d'email qui accepte les domaines locaux
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$|^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.local$'
        if not re.match(email_pattern, v):
            raise ValueError('Format d\'email invalide')
        return v.lower()


class ForgotPasswordRequest(BaseModel):
    email: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        # Validation basique d'email qui accepte les domaines locaux
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$|^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.local$'
        if not re.match(email_pattern, v):
            raise ValueError('Format d\'email invalide')
        return v.lower()

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class CompleteRegistrationRequest(BaseModel):
    token: str
    password: str
    prenom: str
    nom: str
    telephone: Optional[str] = None

class InviteMemberRequest(BaseModel):
    email: str
    role: UserRole
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        # Validation basique d'email qui accepte les domaines locaux
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$|^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.local$'
        if not re.match(email_pattern, v):
            raise ValueError('Format d\'email invalide')
        return v.lower()

class CreateMemberRequest(BaseModel):
    email: str
    prenom: str
    nom: str
    role: UserRole
    telephone: Optional[str] = None
    service: Optional[str] = None
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        # Validation basique d'email qui accepte les domaines locaux
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$|^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.local$'
        if not re.match(email_pattern, v):
            raise ValueError('Format d\'email invalide')
        return v.lower()

# Work Order Models
class WorkOrderBase(BaseModel):
    titre: str
    description: str
    statut: WorkOrderStatus = WorkOrderStatus.OUVERT
    priorite: Priority = Priority.AUCUNE
    equipement_id: Optional[str] = None
    assigne_a_id: Optional[str] = None
    emplacement_id: Optional[str] = None
    dateLimite: Optional[datetime] = None
    tempsEstime: Optional[float] = None
    createdBy: Optional[str] = None  # ID de l'utilisateur créateur

class WorkOrderCreate(WorkOrderBase):
    pass

class WorkOrderUpdate(BaseModel):
    titre: Optional[str] = None
    description: Optional[str] = None
    statut: Optional[WorkOrderStatus] = None
    priorite: Optional[Priority] = None
    equipement_id: Optional[str] = None
    assigne_a_id: Optional[str] = None
    emplacement_id: Optional[str] = None
    dateLimite: Optional[datetime] = None
    tempsEstime: Optional[float] = None
    tempsReel: Optional[float] = None

class WorkOrder(WorkOrderBase):
    id: str
    numero: str
    tempsReel: Optional[float] = None
    dateCreation: datetime
    dateTermine: Optional[datetime] = None
    equipement: Optional[dict] = None
    assigneA: Optional[dict] = None
    emplacement: Optional[dict] = None
    attachments: List[dict] = []
    comments: List[Comment] = []
    createdByName: Optional[str] = None

    class Config:
        from_attributes = True

# Attachment Model
class AttachmentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    size: int
    mime_type: str
    uploaded_at: datetime
    url: str

# Equipment Models
class EquipmentBase(BaseModel):
    nom: str
    categorie: Optional[str] = None
    emplacement_id: str
    statut: EquipmentStatus = EquipmentStatus.OPERATIONNEL
    dateAchat: Optional[datetime] = None
    coutAchat: Optional[float] = None
    numeroSerie: Optional[str] = None
    anneeFabrication: Optional[int] = None
    garantie: Optional[str] = None
    parent_id: Optional[str] = None

class EquipmentCreate(BaseModel):
    nom: str
    categorie: Optional[str] = None
    emplacement_id: Optional[str] = None  # Optional to allow inheritance from parent
    statut: EquipmentStatus = EquipmentStatus.OPERATIONNEL
    dateAchat: Optional[datetime] = None
    coutAchat: Optional[float] = None
    numeroSerie: Optional[str] = None
    anneeFabrication: Optional[int] = None
    garantie: Optional[str] = None
    parent_id: Optional[str] = None

class EquipmentUpdate(BaseModel):
    nom: Optional[str] = None
    categorie: Optional[str] = None
    emplacement_id: Optional[str] = None
    statut: Optional[EquipmentStatus] = None
    dateAchat: Optional[datetime] = None
    coutAchat: Optional[float] = None
    numeroSerie: Optional[str] = None
    anneeFabrication: Optional[int] = None
    garantie: Optional[str] = None
    derniereMaintenance: Optional[datetime] = None
    parent_id: Optional[str] = None

class Equipment(EquipmentBase):
    id: str
    derniereMaintenance: Optional[datetime] = None
    dateCreation: datetime
    emplacement: Optional[dict] = None
    parent: Optional[dict] = None
    hasChildren: bool = False
    createdBy: Optional[str] = None  # ID de l'utilisateur créateur

    class Config:
        from_attributes = True

# Location Models (renommées en Zone)
class LocationBase(BaseModel):
    nom: str
    adresse: Optional[str] = None
    ville: Optional[str] = None
    codePostal: Optional[str] = None
    type: Optional[str] = None
    parent_id: Optional[str] = None  # Pour hiérarchie (sous-zones)

class LocationCreate(LocationBase):
    pass

class LocationUpdate(BaseModel):
    nom: Optional[str] = None
    adresse: Optional[str] = None
    ville: Optional[str] = None
    codePostal: Optional[str] = None
    type: Optional[str] = None
    parent_id: Optional[str] = None

class Location(LocationBase):
    id: str
    dateCreation: datetime
    parent: Optional[dict] = None  # Informations de la zone parente
    hasChildren: bool = False  # Indique si cette zone a des sous-zones
    level: int = 0  # Niveau dans la hiérarchie (0 = racine, 1 = sous-zone, 2 = sous-sous-zone)

    class Config:
        from_attributes = True

# Inventory Models
class InventoryBase(BaseModel):
    nom: str
    reference: str
    categorie: str
    quantite: int
    quantiteMin: int
    prixUnitaire: float
    fournisseur: str
    emplacement: str

class InventoryCreate(InventoryBase):
    pass

class InventoryUpdate(BaseModel):
    nom: Optional[str] = None
    reference: Optional[str] = None
    categorie: Optional[str] = None
    quantite: Optional[int] = None
    quantiteMin: Optional[int] = None
    prixUnitaire: Optional[float] = None
    fournisseur: Optional[str] = None
    emplacement: Optional[str] = None

class Inventory(InventoryBase):
    id: str
    dateCreation: datetime
    derniereModification: datetime

    class Config:
        from_attributes = True

# Preventive Maintenance Models
class PreventiveMaintenanceBase(BaseModel):
    titre: str
    equipement_id: str
    frequence: Frequency
    prochaineMaintenance: datetime
    assigne_a_id: Optional[str] = None
    duree: float
    statut: PMStatus = PMStatus.ACTIF

class PreventiveMaintenanceCreate(PreventiveMaintenanceBase):
    pass

class PreventiveMaintenanceUpdate(BaseModel):
    titre: Optional[str] = None
    equipement_id: Optional[str] = None
    frequence: Optional[Frequency] = None
    prochaineMaintenance: Optional[datetime] = None
    assigne_a_id: Optional[str] = None
    duree: Optional[float] = None
    statut: Optional[PMStatus] = None
    derniereMaintenance: Optional[datetime] = None

class PreventiveMaintenance(PreventiveMaintenanceBase):
    id: str
    derniereMaintenance: Optional[datetime] = None
    dateCreation: datetime
    equipement: Optional[dict] = None
    assigneA: Optional[dict] = None

    class Config:
        from_attributes = True

# Availability Models
class UserAvailability(BaseModel):
    user_id: str
    date: datetime
    disponible: bool = True
    motif: Optional[str] = None  # Raison de l'indisponibilité (congé, maladie, etc.)

class UserAvailabilityCreate(BaseModel):
    user_id: str
    date: datetime
    disponible: bool = True
    motif: Optional[str] = None

class UserAvailabilityUpdate(BaseModel):
    disponible: Optional[bool] = None
    motif: Optional[str] = None

class UserAvailabilityResponse(UserAvailability):
    id: str
    user: Optional[dict] = None

    class Config:
        from_attributes = True

# Vendor Models
class VendorBase(BaseModel):
    nom: str
    contact: str
    email: str
    telephone: str
    adresse: str
    specialite: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        # Validation basique d'email qui accepte les domaines locaux
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$|^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.local$'
        if not re.match(email_pattern, v):
            raise ValueError('Format d\'email invalide')
        return v.lower()

class VendorCreate(VendorBase):
    pass

class VendorUpdate(BaseModel):
    nom: Optional[str] = None
    contact: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    adresse: Optional[str] = None
    specialite: Optional[str] = None
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Validation basique d'email qui accepte les domaines locaux
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$|^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.local$'
        if not re.match(email_pattern, v):
            raise ValueError('Format d\'email invalide')
        return v.lower()

class Vendor(VendorBase):
    id: str
    dateCreation: datetime

    class Config:
        from_attributes = True


# Purchase History Models (Historique Achat)
class PurchaseHistoryBase(BaseModel):
    fournisseur: str
    numeroCommande: str
    numeroReception: Optional[str] = None
    dateCreation: datetime
    article: str
    description: Optional[str] = None
    groupeStatistique: Optional[str] = None
    quantite: float
    montantLigneHT: float
    quantiteRetournee: Optional[float] = 0.0
    site: Optional[str] = None
    creationUser: Optional[str] = None

class PurchaseHistoryCreate(PurchaseHistoryBase):
    pass

class PurchaseHistoryUpdate(BaseModel):
    fournisseur: Optional[str] = None
    numeroCommande: Optional[str] = None
    numeroReception: Optional[str] = None
    dateCreation: Optional[datetime] = None
    article: Optional[str] = None
    description: Optional[str] = None
    groupeStatistique: Optional[str] = None
    quantite: Optional[float] = None
    montantLigneHT: Optional[float] = None
    quantiteRetournee: Optional[float] = None
    site: Optional[str] = None
    creationUser: Optional[str] = None

class PurchaseHistory(PurchaseHistoryBase):
    id: str
    dateEnregistrement: datetime  # Date d'enregistrement dans la BD

    class Config:
        from_attributes = True


# Meter (Compteur) Models
class MeterType(str, Enum):
    EAU = "EAU"  # Eau
    GAZ = "GAZ"  # Gaz
    ELECTRICITE = "ELECTRICITE"  # Électricité
    AIR_COMPRIME = "AIR_COMPRIME"  # Air comprimé
    VAPEUR = "VAPEUR"  # Vapeur
    FUEL = "FUEL"  # Fuel/Mazout
    SOLAIRE = "SOLAIRE"  # Énergie solaire
    AUTRE = "AUTRE"  # Autre

class Meter(BaseModel):
    id: str
    nom: str
    type: MeterType
    numero_serie: Optional[str] = None
    emplacement_id: Optional[str] = None
    emplacement: Optional[Dict] = None
    unite: str  # m³, kWh, L, etc.
    prix_unitaire: Optional[float] = None  # Prix par unité
    abonnement_mensuel: Optional[float] = None  # Abonnement fixe mensuel
    date_creation: datetime
    notes: Optional[str] = None
    actif: bool = True

class MeterCreate(BaseModel):
    nom: str
    type: MeterType
    numero_serie: Optional[str] = None
    emplacement_id: Optional[str] = None
    unite: str = "kWh"
    prix_unitaire: Optional[float] = None
    abonnement_mensuel: Optional[float] = None
    notes: Optional[str] = None

class MeterUpdate(BaseModel):
    nom: Optional[str] = None
    numero_serie: Optional[str] = None
    emplacement_id: Optional[str] = None
    unite: Optional[str] = None
    prix_unitaire: Optional[float] = None
    abonnement_mensuel: Optional[float] = None
    notes: Optional[str] = None
    actif: Optional[bool] = None

# Reading (Relevé) Models
class MeterReading(BaseModel):
    id: str
    meter_id: str
    meter_nom: Optional[str] = None
    date_releve: datetime
    valeur: float  # Index du compteur
    notes: Optional[str] = None
    created_by: str
    created_by_name: Optional[str] = None
    consommation: Optional[float] = None  # Calculée automatiquement
    cout: Optional[float] = None  # Calculé automatiquement
    prix_unitaire: Optional[float] = None  # Prix au moment du relevé
    abonnement_mensuel: Optional[float] = None  # Abonnement au moment du relevé
    date_creation: datetime

class MeterReadingCreate(BaseModel):
    date_releve: datetime
    valeur: float
    notes: Optional[str] = None
    prix_unitaire: Optional[float] = None
    abonnement_mensuel: Optional[float] = None

class MeterReadingUpdate(BaseModel):
    date_releve: Optional[datetime] = None
    valeur: Optional[float] = None
    notes: Optional[str] = None
    prix_unitaire: Optional[float] = None
    abonnement_mensuel: Optional[float] = None



# Intervention Request (Demande d'intervention) Models
class InterventionRequest(BaseModel):
    id: str
    titre: str
    description: str
    priorite: Priority
    equipement_id: Optional[str] = None
    equipement: Optional[Dict] = None
    emplacement_id: Optional[str] = None
    emplacement: Optional[Dict] = None
    date_limite_desiree: Optional[datetime] = None
    date_creation: datetime
    created_by: str
    created_by_name: Optional[str] = None
    work_order_id: Optional[str] = None  # ID de l'ordre de travail créé
    work_order_numero: Optional[str] = None  # Numéro de l'ordre de travail créé (ex: 5801)
    work_order_date_limite: Optional[datetime] = None  # Date limite de l'ordre créé
    converted_at: Optional[datetime] = None  # Date de conversion
    converted_by: Optional[str] = None  # ID de qui a converti

class InterventionRequestCreate(BaseModel):
    titre: str
    description: str
    priorite: Priority = Priority.AUCUNE
    equipement_id: Optional[str] = None
    emplacement_id: Optional[str] = None
    date_limite_desiree: Optional[datetime] = None

class InterventionRequestUpdate(BaseModel):
    titre: Optional[str] = None
    description: Optional[str] = None
    priorite: Optional[Priority] = None
    equipement_id: Optional[str] = None
    emplacement_id: Optional[str] = None
    date_limite_desiree: Optional[datetime] = None



# Improvement Request (Demande d'amélioration) Models
class ImprovementRequest(BaseModel):
    id: str
    titre: str
    description: str
    priorite: Priority
    equipement_id: Optional[str] = None
    equipement: Optional[Dict] = None
    emplacement_id: Optional[str] = None
    emplacement: Optional[Dict] = None
    date_limite_desiree: Optional[datetime] = None
    date_creation: datetime
    created_by: str
    created_by_name: Optional[str] = None
    improvement_id: Optional[str] = None  # ID de l'amélioration créée
    improvement_numero: Optional[str] = None  # Numéro de l'amélioration créée
    improvement_date_limite: Optional[datetime] = None  # Date limite de l'amélioration créée
    converted_at: Optional[datetime] = None  # Date de conversion
    converted_by: Optional[str] = None  # ID de qui a converti

class ImprovementRequestCreate(BaseModel):
    titre: str
    description: str
    priorite: Priority = Priority.AUCUNE
    equipement_id: Optional[str] = None
    emplacement_id: Optional[str] = None
    date_limite_desiree: Optional[datetime] = None

class ImprovementRequestUpdate(BaseModel):
    titre: Optional[str] = None
    description: Optional[str] = None
    priorite: Optional[Priority] = None
    equipement_id: Optional[str] = None
    emplacement_id: Optional[str] = None
    date_limite_desiree: Optional[datetime] = None

# Improvement (Amélioration) Models - Copie de WorkOrder
class Improvement(BaseModel):
    id: str
    numero: str
    titre: str
    description: str
    statut: WorkOrderStatus
    priorite: Priority
    equipement_id: Optional[str] = None
    equipement: Optional[Dict] = None
    emplacement_id: Optional[str] = None
    emplacement: Optional[Dict] = None
    assigne_a_id: Optional[str] = None
    assigneA: Optional[Dict] = None
    dateLimite: Optional[datetime] = None
    tempsEstime: Optional[int] = None
    tempsReel: Optional[int] = None
    dateCreation: datetime
    dateTermine: Optional[datetime] = None
    createdBy: str
    createdByName: Optional[str] = None
    attachments: Optional[List[Dict]] = []
    comments: Optional[List[Dict]] = []

class ImprovementCreate(BaseModel):
    titre: str
    description: str
    priorite: Priority = Priority.AUCUNE
    equipement_id: Optional[str] = None
    emplacement_id: Optional[str] = None
    assigne_a_id: Optional[str] = None
    dateLimite: Optional[datetime] = None
    tempsEstime: Optional[int] = None

class ImprovementUpdate(BaseModel):
    titre: Optional[str] = None
    description: Optional[str] = None
    statut: Optional[WorkOrderStatus] = None
    priorite: Optional[Priority] = None
    equipement_id: Optional[str] = None
    emplacement_id: Optional[str] = None
    assigne_a_id: Optional[str] = None
    dateLimite: Optional[datetime] = None
    tempsEstime: Optional[int] = None
    tempsReel: Optional[int] = None

