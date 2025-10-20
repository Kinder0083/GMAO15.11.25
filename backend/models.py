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

# Permission Models
class ModulePermission(BaseModel):
    view: bool = False
    edit: bool = False
    delete: bool = False

class UserPermissions(BaseModel):
    dashboard: ModulePermission = ModulePermission(view=True, edit=False, delete=False)
    workOrders: ModulePermission = ModulePermission(view=True, edit=False, delete=False)
    assets: ModulePermission = ModulePermission(view=True, edit=False, delete=False)
    preventiveMaintenance: ModulePermission = ModulePermission(view=True, edit=False, delete=False)
    inventory: ModulePermission = ModulePermission(view=True, edit=False, delete=False)
    locations: ModulePermission = ModulePermission(view=True, edit=False, delete=False)
    vendors: ModulePermission = ModulePermission(view=True, edit=False, delete=False)
    reports: ModulePermission = ModulePermission(view=True, edit=False, delete=False)

class WorkOrderStatus(str, Enum):
    OUVERT = "OUVERT"
    EN_COURS = "EN_COURS"
    EN_ATTENTE = "EN_ATTENTE"
    TERMINE = "TERMINE"

class Priority(str, Enum):
    HAUTE = "HAUTE"
    MOYENNE = "MOYENNE"
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
    assigne_a_id: str
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
