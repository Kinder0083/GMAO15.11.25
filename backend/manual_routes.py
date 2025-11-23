"""
Routes pour le manuel utilisateur
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from dependencies import get_current_user, get_current_admin_user
from models import ManualCreate, ManualSearchRequest
from datetime import datetime, timezone
import uuid
import logging

# Logger
logger = logging.getLogger(__name__)

# Créer un routeur séparé pour les endpoints du manuel
router = APIRouter()

# Import de la base de données
from server import db


@router.get("/manual/content")
async def get_manual_content(
    role_filter: Optional[str] = None,
    module_filter: Optional[str] = None,
    level_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Récupérer le contenu du manuel filtré selon le rôle et les préférences"""
    try:
        # Récupérer la version actuelle
        current_version = await db.manual_versions.find_one({"is_current": True})
        if not current_version:
            # Créer le contenu par défaut si aucun manuel n'existe
            return await initialize_default_manual(current_user)
        
        # Récupérer tous les chapitres et sections
        chapters = await db.manual_chapters.find({}).sort("order", 1).to_list(None)
        sections = await db.manual_sections.find({}).sort("order", 1).to_list(None)
        
        # Filtrer selon le rôle de l'utilisateur
        user_role = current_user.get("role", "")
        
        filtered_chapters = []
        for chapter in chapters:
            # Si le chapitre a des rôles cibles et l'utilisateur n'est pas dans la liste, skip
            if chapter.get("target_roles") and user_role not in chapter["target_roles"]:
                continue
            
            # Appliquer les filtres additionnels
            if role_filter and role_filter not in chapter.get("target_roles", []):
                continue
            if module_filter and module_filter not in chapter.get("target_modules", []):
                continue
            
            # Garder l'ID original (ch-001) et non l'ID MongoDB
            if "id" not in chapter or not chapter["id"]:
                chapter["id"] = str(chapter.get("_id"))
            if "_id" in chapter:
                del chapter["_id"]
            filtered_chapters.append(chapter)
        
        filtered_sections = []
        for section in sections:
            # Filtrer selon les rôles
            if section.get("target_roles") and user_role not in section["target_roles"]:
                continue
            
            # Appliquer les filtres
            if role_filter and role_filter not in section.get("target_roles", []):
                continue
            if module_filter and module_filter not in section.get("target_modules", []):
                continue
            if level_filter and section.get("level") != level_filter and section.get("level") != "both":
                continue
            
            # Garder l'ID original (sec-001-01) et non l'ID MongoDB
            if "id" not in section or not section["id"]:
                section["id"] = str(section.get("_id"))
            if "_id" in section:
                del section["_id"]
            filtered_sections.append(section)
        
        return {
            "version": current_version.get("version"),
            "chapters": filtered_chapters,
            "sections": filtered_sections,
            "last_updated": current_version.get("release_date")
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du manuel: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/manual/search")
async def search_manual(
    search_request: ManualSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """Rechercher dans le manuel"""
    try:
        query = search_request.query.lower()
        
        # Recherche dans les sections
        sections = await db.manual_sections.find({}).to_list(None)
        
        results = []
        for section in sections:
            # Calculer le score de pertinence
            score = 0.0
            title_lower = section.get("title", "").lower()
            content_lower = section.get("content", "").lower()
            keywords = [k.lower() for k in section.get("keywords", [])]
            
            # Score basé sur le titre (poids 3)
            if query in title_lower:
                score += 3.0
            
            # Score basé sur les mots-clés (poids 2)
            if any(query in kw for kw in keywords):
                score += 2.0
            
            # Score basé sur le contenu (poids 1)
            if query in content_lower:
                score += 1.0
            
            if score > 0:
                # Extraire un extrait pertinent
                content = section.get("content", "")
                excerpt_start = max(0, content_lower.find(query) - 50)
                excerpt = content[excerpt_start:excerpt_start + 200]
                
                # Trouver le chapitre parent
                chapter_id = None
                chapters = await db.manual_chapters.find({}).to_list(None)
                for chapter in chapters:
                    if section.get("id") in chapter.get("sections", []):
                        chapter_id = str(chapter.get("_id", chapter.get("id")))
                        break
                
                results.append({
                    "section_id": str(section.get("_id", section.get("id"))),
                    "chapter_id": chapter_id,
                    "title": section.get("title"),
                    "excerpt": excerpt,
                    "relevance_score": score
                })
        
        # Trier par score
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return {"results": results[:10]}  # Top 10 résultats
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/manual/content")
async def create_or_update_manual(
    manual_data: ManualCreate,
    current_user: dict = Depends(get_current_admin_user)
):
    """Créer ou mettre à jour le contenu du manuel (Super Admin uniquement)"""
    try:
        # Marquer les anciennes versions comme non-actuelles
        await db.manual_versions.update_many(
            {"is_current": True},
            {"$set": {"is_current": False}}
        )
        
        # Créer une nouvelle version
        from models import ManualVersion
        version = ManualVersion(
            version=manual_data.version,
            changes=manual_data.changes,
            author_id=current_user["id"],
            author_name=f"{current_user.get('prenom', '')} {current_user.get('nom', '')}",
            is_current=True
        )
        await db.manual_versions.insert_one(version.model_dump())
        
        # Supprimer les chapitres et sections existants
        await db.manual_chapters.delete_many({})
        await db.manual_sections.delete_many({})
        
        # Insérer les nouveaux chapitres
        for chapter in manual_data.chapters:
            await db.manual_chapters.insert_one(chapter.model_dump())
        
        # Insérer les nouvelles sections
        for section in manual_data.sections:
            await db.manual_sections.insert_one(section.model_dump())
        
        logger.info(f"📚 Manuel mis à jour vers version {manual_data.version} par {current_user['email']}")
        
        return {"success": True, "message": f"Manuel mis à jour vers version {manual_data.version}"}
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du manuel: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/manual/export/pdf")
async def export_manual_pdf(
    role_filter: Optional[str] = None,
    module_filter: Optional[str] = None,
    include_images: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """Exporter le manuel en PDF"""
    try:
        # Pour l'instant, retourner un message
        return {
            "message": "Export PDF en cours de développement",
            "download_url": None
        }
    except Exception as e:
        logger.error(f"Erreur lors de l'export PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def initialize_default_manual(current_user: dict):
    """Initialiser le manuel avec le contenu par défaut"""
    try:
        logger.info("📚 Initialisation du manuel avec contenu par défaut...")
        
        now = datetime.now(timezone.utc)
        
        # Créer la version initiale
        version = {
            "id": str(uuid.uuid4()),
            "version": "1.0",
            "release_date": now.isoformat(),
            "changes": ["Création initiale du manuel"],
            "author_id": current_user.get("id", "system"),
            "author_name": current_user.get("nom", "Système") + " " + current_user.get("prenom", ""),
            "is_current": True
        }
        await db.manual_versions.insert_one(version)
        
        # Créer le premier chapitre
        chapter1 = {
            "id": "ch-001",
            "title": "🚀 Guide de Démarrage",
            "description": "Premiers pas avec GMAO Iris",
            "icon": "Rocket",
            "order": 1,
            "sections": ["sec-001-01", "sec-001-02"],
            "target_roles": [],
            "target_modules": [],
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        await db.manual_chapters.insert_one(chapter1)
        
        # Créer les sections du chapitre 1
        section1 = {
            "id": "sec-001-01",
            "title": "Bienvenue dans GMAO Iris",
            "content": """GMAO Iris est votre solution complète de gestion de maintenance assistée par ordinateur.

📌 **Qu'est-ce qu'une GMAO ?**

Une GMAO (Gestion de Maintenance Assistée par Ordinateur) est un logiciel qui permet de gérer l'ensemble des activités de maintenance d'une entreprise :

• Planification des interventions
• Suivi des équipements
• Gestion des stocks de pièces
• Traçabilité des actions
• Analyse des performances

🎯 **Objectifs de GMAO Iris :**

1. **Optimiser** la maintenance préventive et curative
2. **Réduire** les temps d'arrêt des équipements
3. **Suivre** l'historique complet de vos installations
4. **Analyser** les performances avec des rapports détaillés
5. **Collaborer** efficacement entre les équipes

✅ **Premiers pas recommandés :**

1. Consultez la section "Connexion et Navigation"
2. Familiarisez-vous avec votre rôle et vos permissions
3. Explorez les différents modules selon vos besoins
4. N'hésitez pas à utiliser la fonction de recherche dans ce manuel

💡 **Astuce :** Utilisez le bouton "Aide" en haut à droite pour signaler un problème ou demander de l'assistance à tout moment.""",
            "order": 1,
            "parent_id": None,
            "target_roles": [],
            "target_modules": [],
            "level": "beginner",
            "images": [],
            "video_url": None,
            "keywords": ["bienvenue", "introduction", "gmao"],
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        await db.manual_sections.insert_one(section1)
        
        section2 = {
            "id": "sec-001-02",
            "title": "Connexion et Navigation",
            "content": """📱 **Se Connecter à GMAO Iris**

1. **Accéder à l'application**
   • Ouvrez votre navigateur web (Chrome, Firefox, Edge, Safari)
   • Saisissez l'URL de GMAO Iris
   • Bookmark la page pour un accès rapide

2. **Première Connexion**
   • Email : Votre adresse email professionnelle
   • Mot de passe : Mot de passe fourni par l'administrateur
   • ⚠️ Changez votre mot de passe lors de la première connexion

3. **Changer votre mot de passe**
   • Minimum 8 caractères
   • Au moins une majuscule, une minuscule et un chiffre

🗺️ **Navigation dans l'Interface**

**Sidebar (Barre latérale)**
• Contient tous les modules principaux
• Cliquez sur un élément pour accéder au module
• Utilisez l'icône ☰ pour réduire/agrandir la sidebar

**Header (En-tête)**
• Logo et nom de l'application à gauche
• Boutons "Manuel" et "Aide" au centre
• Badges de notifications
• Votre profil à droite

🔔 **Notifications**

• Badge ROUGE : Maintenances préventives dues
• Badge BLEU : Maintenances bientôt dues
• Badge ORANGE : Ordres de travail en retard
• Badge VERT : Alertes stock faible

Cliquez sur un badge pour voir les détails.""",
            "order": 2,
            "parent_id": None,
            "target_roles": [],
            "target_modules": [],
            "level": "beginner",
            "images": [],
            "video_url": None,
            "keywords": ["connexion", "navigation", "interface"],
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        await db.manual_sections.insert_one(section2)
        
        logger.info("✅ Manuel initialisé avec succès")
        
        # Retourner le contenu
        return {
            "version": "1.0",
            "chapters": [chapter1],
            "sections": [section1, section2],
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation du manuel: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
