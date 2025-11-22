"""
Routes API pour les Demandes d'Arrêt pour Maintenance
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import logging
import uuid
from bson import ObjectId

from dependencies import get_current_user
from models import (
    DemandeArretMaintenance, DemandeArretMaintenanceCreate, DemandeArretMaintenanceUpdate,
    DemandeArretStatus, PlanningEquipementEntry, EquipmentStatus, UserRole
)
import email_service
import os
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection - utilise les mêmes variables d'environnement que server.py
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'gmao_iris')]

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demandes-arret", tags=["demandes-arret"])

def serialize_doc(doc):
    """Convert MongoDB document to JSON serializable format"""
    if doc is None:
        return None
    
    # Convertir le _id principal seulement si pas d'id existant
    if "_id" in doc:
        if "id" not in doc:
            doc["id"] = str(doc["_id"])
        del doc["_id"]
    
    # Convertir récursivement tous les ObjectId
    for key, value in list(doc.items()):
        if isinstance(value, ObjectId):
            doc[key] = str(value)
        elif isinstance(value, list):
            doc[key] = [
                str(item) if isinstance(item, ObjectId) 
                else serialize_doc(item) if isinstance(item, dict) 
                else item 
                for item in value
            ]
        elif isinstance(value, dict):
            doc[key] = serialize_doc(value)
    
    return doc

# ==================== CRUD DEMANDES ====================

@router.post("/")
async def create_demande_arret(
    demande: DemandeArretMaintenanceCreate,
    current_user: dict = Depends(get_current_user)
):
    """Créer une nouvelle demande d'arrêt pour maintenance"""
    try:
        # Récupérer le destinataire
        logger.info(f"🔍 Recherche destinataire avec ID: {demande.destinataire_id}")
        destinataire = await db.users.find_one({"_id": ObjectId(demande.destinataire_id)})
        logger.info(f"🔍 Destinataire trouvé: {destinataire is not None}")
        if not destinataire:
            raise HTTPException(status_code=404, detail="Destinataire non trouvé")
        
        # Récupérer les informations des équipements
        equipement_noms = []
        for eq_id in demande.equipement_ids:
            logger.info(f"🔍 Recherche équipement avec ID: {eq_id}")
            equipement = await db.equipments.find_one({"_id": ObjectId(eq_id)})
            logger.info(f"🔍 Équipement trouvé: {equipement is not None}")
            if equipement:
                equipement_noms.append(equipement.get("nom", ""))
                logger.info(f"🔍 Nom équipement: {equipement.get('nom', '')}")
        
        # Calculer la date d'expiration (7 jours)
        date_creation = datetime.now(timezone.utc)
        date_expiration = date_creation + timedelta(days=7)
        
        # Créer la demande
        data = demande.model_dump()
        data["id"] = str(uuid.uuid4())
        data["demandeur_id"] = current_user.get("id")
        data["demandeur_nom"] = f"{current_user.get('prenom', '')} {current_user.get('nom', '')}"
        data["destinataire_nom"] = f"{destinataire.get('prenom', '')} {destinataire.get('nom', '')}"
        data["destinataire_email"] = destinataire.get("email")
        data["equipement_noms"] = equipement_noms
        data["statut"] = DemandeArretStatus.EN_ATTENTE
        data["date_creation"] = date_creation.isoformat()
        data["date_expiration"] = date_expiration.isoformat()
        data["validation_token"] = str(uuid.uuid4())
        data["created_at"] = date_creation.isoformat()
        data["updated_at"] = date_creation.isoformat()
        
        # Ajouter _id pour MongoDB
        data["_id"] = ObjectId()
        
        await db.demandes_arret.insert_one(data)
        
        # Envoyer l'email de demande
        await send_demande_email(data)
        
        logger.info(f"Demande d'arrêt créée: {data['id']}")
        return serialize_doc(data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur création demande: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def get_demandes_arret(
    statut: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Récupérer toutes les demandes d'arrêt (avec filtre optionnel)"""
    try:
        filter_query = {}
        if statut:
            filter_query["statut"] = statut
        
        demandes = await db.demandes_arret.find(filter_query).sort("date_creation", -1).to_list(length=None)
        
        # Sérialiser les documents
        serialized_demandes = [serialize_doc(demande) for demande in demandes]
        
        return serialized_demandes
    except Exception as e:
        logger.error(f"Erreur récupération demandes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{demande_id}")
async def get_demande_by_id(
    demande_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupérer une demande par ID"""
    try:
        demande = await db.demandes_arret.find_one({"id": demande_id})
        if not demande:
            raise HTTPException(status_code=404, detail="Demande non trouvée")
        
        return serialize_doc(demande)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération demande: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== VALIDATION / REFUS ====================

@router.post("/validate/{token}")
async def validate_demande_by_token(
    token: str,
    commentaire: Optional[str] = None
):
    """Valider une demande via le token d'email (pas besoin d'auth)"""
    try:
        demande = await db.demandes_arret.find_one({"validation_token": token})
        if not demande:
            raise HTTPException(status_code=404, detail="Demande non trouvée ou token invalide")
        
        # Vérifier que la demande n'est pas déjà traitée
        if demande["statut"] != DemandeArretStatus.EN_ATTENTE:
            raise HTTPException(status_code=400, detail="Cette demande a déjà été traitée")
        
        # Vérifier que la demande n'a pas expiré
        date_expiration = datetime.fromisoformat(demande["date_expiration"])
        if datetime.now(timezone.utc) > date_expiration:
            # Auto-refuser
            await db.demandes_arret.update_one(
                {"id": demande["id"]},
                {"$set": {
                    "statut": DemandeArretStatus.EXPIREE,
                    "date_reponse": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            raise HTTPException(status_code=400, detail="Cette demande a expiré (délai de 7 jours dépassé)")
        
        # Approuver la demande
        await db.demandes_arret.update_one(
            {"id": demande["id"]},
            {"$set": {
                "statut": DemandeArretStatus.APPROUVEE,
                "date_reponse": datetime.now(timezone.utc).isoformat(),
                "commentaire_reponse": commentaire or "",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Créer les entrées dans le planning équipement
        for equipement_id in demande["equipement_ids"]:
            entry = {
                "id": str(uuid.uuid4()),
                "equipement_id": equipement_id,
                "date_debut": demande["date_debut"],
                "date_fin": demande["date_fin"],
                "periode_debut": demande["periode_debut"],
                "periode_fin": demande["periode_fin"],
                "statut": EquipmentStatus.EN_MAINTENANCE,
                "demande_arret_id": demande["id"],
                "work_order_id": demande.get("work_order_id"),
                "maintenance_preventive_id": demande.get("maintenance_preventive_id"),
                "commentaire": demande.get("commentaire", ""),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.planning_equipement.insert_one(entry)
        
        logger.info(f"Demande approuvée: {demande['id']}")
        
        # Envoyer email de confirmation au demandeur
        await send_confirmation_email(demande, approved=True, commentaire=commentaire)
        
        return {"message": "Demande approuvée avec succès", "demande_id": demande["id"]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur validation demande: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/refuse/{token}")
async def refuse_demande_by_token(
    token: str,
    commentaire: Optional[str] = None,
    date_proposee: Optional[str] = None
):
    """Refuser une demande via le token d'email"""
    try:
        demande = await db.demandes_arret.find_one({"validation_token": token})
        if not demande:
            raise HTTPException(status_code=404, detail="Demande non trouvée ou token invalide")
        
        if demande["statut"] != DemandeArretStatus.EN_ATTENTE:
            raise HTTPException(status_code=400, detail="Cette demande a déjà été traitée")
        
        # Refuser la demande
        update_data = {
            "statut": DemandeArretStatus.REFUSEE,
            "date_reponse": datetime.now(timezone.utc).isoformat(),
            "commentaire_reponse": commentaire or "",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if date_proposee:
            update_data["date_proposee"] = date_proposee
        
        await db.demandes_arret.update_one(
            {"id": demande["id"]},
            {"$set": update_data}
        )
        
        logger.info(f"Demande refusée: {demande['id']}")
        
        # Envoyer email de refus au demandeur
        await send_confirmation_email(demande, approved=False, commentaire=commentaire, date_proposee=date_proposee)
        
        return {"message": "Demande refusée", "demande_id": demande["id"]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur refus demande: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== PLANNING EQUIPEMENT ====================

@router.get("/planning/equipements")
async def get_planning_equipements(
    date_debut: Optional[str] = None,
    date_fin: Optional[str] = None,
    equipement_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Récupérer le planning des équipements"""
    try:
        filter_query = {}
        
        if equipement_id:
            filter_query["equipement_id"] = equipement_id
        
        if date_debut and date_fin:
            filter_query["$or"] = [
                {"date_debut": {"$lte": date_fin}, "date_fin": {"$gte": date_debut}},
            ]
        
        entries = await db.planning_equipement.find(filter_query).to_list(length=None)
        
        for entry in entries:
            if "_id" in entry:
                del entry["_id"]
        
        return entries
    except Exception as e:
        logger.error(f"Erreur récupération planning: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== VÉRIFICATION EXPIRATION ====================

@router.post("/check-expired")
async def check_expired_demandes():
    """Vérifier et marquer comme expirées les demandes > 7 jours (appelé par cron)"""
    try:
        now = datetime.now(timezone.utc)
        
        # Trouver les demandes expirées
        demandes_expirees = await db.demandes_arret.find({
            "statut": DemandeArretStatus.EN_ATTENTE,
            "date_expiration": {"$lt": now.isoformat()}
        }).to_list(length=None)
        
        count = 0
        for demande in demandes_expirees:
            await db.demandes_arret.update_one(
                {"id": demande["id"]},
                {"$set": {
                    "statut": DemandeArretStatus.EXPIREE,
                    "date_reponse": now.isoformat(),
                    "commentaire_reponse": "Demande expirée automatiquement après 7 jours sans réponse",
                    "updated_at": now.isoformat()
                }}
            )
            
            # Envoyer email d'expiration
            await send_expiration_email(demande)
            count += 1
        
        logger.info(f"{count} demandes expirées marquées")
        return {"expired_count": count}
    except Exception as e:
        logger.error(f"Erreur vérification expiration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== FONCTIONS EMAIL ====================

async def send_demande_email(demande: dict):
    """Envoyer l'email de demande d'arrêt au destinataire"""
    try:
        import os
        FRONTEND_URL = os.environ.get('FRONTEND_URL', os.environ.get('APP_URL', 'http://localhost:3000'))
        
        approve_link = f"{FRONTEND_URL}/validate-demande-arret?token={demande['validation_token']}&action=approve"
        refuse_link = f"{FRONTEND_URL}/validate-demande-arret?token={demande['validation_token']}&action=refuse"
        
        equipements_str = ", ".join(demande["equipement_noms"])
        
        subject = f"Demande d'Arrêt pour Maintenance - {equipements_str}"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2563eb; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
        .info-box {{ background: white; padding: 15px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #2563eb; }}
        .button {{ display: inline-block; padding: 12px 30px; margin: 10px 5px; text-decoration: none; border-radius: 6px; font-weight: bold; text-align: center; }}
        .btn-approve {{ background-color: #10b981; color: white; }}
        .btn-refuse {{ background-color: #ef4444; color: white; }}
        .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 Demande d'Arrêt pour Maintenance</h1>
        </div>
        <div class="content">
            <p>Bonjour <strong>{demande['destinataire_nom']}</strong>,</p>
            <p>Vous avez reçu une nouvelle demande d'arrêt d'équipement pour maintenance.</p>
            
            <div class="info-box">
                <h3>📋 Détails de la demande</h3>
                <p><strong>Demandeur:</strong> {demande['demandeur_nom']}</p>
                <p><strong>Équipements:</strong> {equipements_str}</p>
                <p><strong>Période:</strong> Du {demande['date_debut']} ({demande['periode_debut']}) au {demande['date_fin']} ({demande['periode_fin']})</p>
                {f"<p><strong>Commentaire:</strong> {demande['commentaire']}</p>" if demande.get('commentaire') else ""}
                <p><strong>Date limite de réponse:</strong> {demande['date_expiration'][:10]} (7 jours)</p>
            </div>
            
            <p style="text-align: center; margin: 30px 0;">
                <a href="{approve_link}" class="button btn-approve">✓ Approuver</a>
                <a href="{refuse_link}" class="button btn-refuse">✗ Refuser</a>
            </p>
            
            <p style="color: #dc2626; font-weight: bold;">⚠️ Cette demande sera automatiquement refusée si aucune réponse n'est donnée dans les 7 jours.</p>
        </div>
        <div class="footer">
            <p>GMAO Iris - Système de Gestion de Maintenance</p>
        </div>
    </div>
</body>
</html>
        """
        
        text_content = f"""
Demande d'Arrêt pour Maintenance

Demandeur: {demande['demandeur_nom']}
Équipements: {equipements_str}
Période: Du {demande['date_debut']} au {demande['date_fin']}

Approuver: {approve_link}
Refuser: {refuse_link}

Cette demande expire le {demande['date_expiration'][:10]}
        """
        
        success = email_service.send_email(
            to_email=demande['destinataire_email'],
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
        
        if not success:
            logger.warning(f"Échec envoi email demande: {demande['id']}")
        
        return success
    except Exception as e:
        logger.error(f"Erreur envoi email demande: {str(e)}")
        return False

async def send_confirmation_email(demande: dict, approved: bool, commentaire: Optional[str] = None, date_proposee: Optional[str] = None):
    """Envoyer email de confirmation au demandeur"""
    # À implémenter
    pass

async def send_expiration_email(demande: dict):
    """Envoyer email d'expiration"""
    # À implémenter
    pass

# ==================== FONCTION CRON ====================

async def check_expired_demandes_cron():
    """Fonction appelée par le cron pour vérifier les demandes expirées"""
    try:
        logger.info("🕐 Début vérification demandes expirées...")
        result = await check_expired_demandes()
        logger.info(f"✅ Vérification terminée: {result['expired_count']} demande(s) expirée(s)")
    except Exception as e:
        logger.error(f"❌ Erreur vérification cron: {str(e)}")
