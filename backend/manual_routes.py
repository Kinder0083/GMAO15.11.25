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
        
        # Filtrer les chapitres qui n'ont plus de sections après filtrage
        section_ids = {s["id"] for s in filtered_sections}
        final_chapters = []
        for chapter in filtered_chapters:
            # Vérifier si le chapitre a au moins une section visible
            chapter_has_sections = any(
                sec_id in section_ids 
                for sec_id in chapter.get("sections", [])
            )
            if chapter_has_sections:
                final_chapters.append(chapter)
        
        return {
            "version": current_version.get("version"),
            "chapters": final_chapters,
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



@router.get("/manual/export-pdf")
async def export_manual_pdf(
    level_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Exporter le manuel en PDF"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
        from reportlab.lib import colors
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from io import BytesIO
        from fastapi.responses import StreamingResponse
        
        # Récupérer le contenu du manuel
        manual_content = await get_manual_content(
            role_filter=None,
            module_filter=None,
            level_filter=level_filter,
            current_user=current_user
        )
        
        # Créer le buffer PDF en mémoire
        buffer = BytesIO()
        
        # Créer le document PDF
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
            title="Manuel Utilisateur GMAO Iris",
            author="GMAO Iris"
        )
        
        # Styles
        styles = getSampleStyleSheet()
        
        # Style pour le titre principal
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Style pour les chapitres
        chapter_style = ParagraphStyle(
            'ChapterTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        # Style pour les sections
        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=8,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        )
        
        # Style pour le contenu
        content_style = ParagraphStyle(
            'ContentText',
            parent=styles['BodyText'],
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
            fontName='Helvetica'
        )
        
        # Construire le contenu du PDF
        story = []
        
        # Page de garde
        story.append(Spacer(1, 3*cm))
        story.append(Paragraph("Manuel Utilisateur", title_style))
        story.append(Paragraph("GMAO Iris", title_style))
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph(f"Version {manual_content['version']}", styles['Normal']))
        story.append(Paragraph(f"Généré le {datetime.now(timezone.utc).strftime('%d/%m/%Y à %H:%M')}", styles['Normal']))
        story.append(PageBreak())
        
        # Table des matières
        story.append(Paragraph("Table des Matières", chapter_style))
        story.append(Spacer(1, 0.5*cm))
        
        for chapter in manual_content['chapters']:
            chapter_sections = [s for s in manual_content['sections'] if s['id'] in chapter.get('sections', [])]
            if chapter_sections:
                story.append(Paragraph(f"<b>{chapter['title']}</b>", styles['Normal']))
                for section in chapter_sections:
                    level_badge = ""
                    if section.get('level') == 'beginner':
                        level_badge = " 🎓"
                    elif section.get('level') == 'advanced':
                        level_badge = " ⚡"
                    story.append(Paragraph(f"  • {section['title']}{level_badge}", styles['Normal']))
                story.append(Spacer(1, 0.3*cm))
        
        story.append(PageBreak())
        
        # Contenu de chaque chapitre et section
        for chapter in manual_content['chapters']:
            # Titre du chapitre
            story.append(Paragraph(chapter['title'], chapter_style))
            story.append(Paragraph(chapter.get('description', ''), styles['Italic']))
            story.append(Spacer(1, 0.5*cm))
            
            # Sections du chapitre
            chapter_sections = [s for s in manual_content['sections'] if s['id'] in chapter.get('sections', [])]
            
            for section in chapter_sections:
                # Titre de section avec badge niveau
                section_title = section['title']
                if section.get('level') == 'beginner':
                    section_title += " 🎓 Débutant"
                elif section.get('level') == 'advanced':
                    section_title += " ⚡ Avancé"
                
                story.append(Paragraph(section_title, section_style))
                
                # Contenu de la section (formatage simple)
                content = section.get('content', '')
                
                # Fonction pour nettoyer et formater le texte pour PDF
                def clean_text_for_pdf(text):
                    # Échapper les caractères spéciaux XML/HTML
                    text = text.replace('&', '&amp;')
                    text = text.replace('<', '&lt;')
                    text = text.replace('>', '&gt;')
                    
                    # Supprimer les emojis et caractères Unicode problématiques
                    import re
                    text = re.sub(r'[^\x00-\x7F]+', '', text)  # Supprimer Unicode non-ASCII
                    
                    # Convertir markdown gras (** texte **)
                    # Utiliser regex pour remplacer par paires
                    parts = text.split('**')
                    result = []
                    for i, part in enumerate(parts):
                        if i % 2 == 0:
                            result.append(part)  # Texte normal
                        else:
                            result.append(f'<b>{part}</b>')  # Texte en gras
                    
                    return ''.join(result)
                
                # Diviser en paragraphes
                paragraphs = content.split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        # Traiter les listes à puces
                        if para.strip().startswith('•') or para.strip().startswith('-'):
                            lines = para.split('\n')
                            for line in lines:
                                if line.strip():
                                    cleaned_line = clean_text_for_pdf(line.strip())
                                    try:
                                        story.append(Paragraph(cleaned_line, content_style))
                                    except Exception as e:
                                        # En cas d'erreur, ajouter le texte brut
                                        logger.warning(f"Erreur formatage ligne: {str(e)}")
                                        story.append(Paragraph(line.strip().replace('&', '&amp;'), content_style))
                        else:
                            # Paragraphe normal
                            cleaned_para = clean_text_for_pdf(para.strip())
                            try:
                                story.append(Paragraph(cleaned_para, content_style))
                            except Exception as e:
                                # En cas d'erreur, ajouter le texte brut
                                logger.warning(f"Erreur formatage paragraphe: {str(e)}")
                                story.append(Paragraph(para.strip().replace('&', '&amp;'), content_style))
                        
                        story.append(Spacer(1, 0.2*cm))
                
                story.append(Spacer(1, 0.5*cm))
            
            # Saut de page entre chapitres
            story.append(PageBreak())
        
        # Générer le PDF
        doc.build(story)
        
        # Préparer la réponse
        buffer.seek(0)
        
        filename = f"manuel_gmao_iris_{datetime.now(timezone.utc).strftime('%Y%m%d')}.pdf"
        
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        logger.error(f"Erreur lors de l'export PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération du PDF: {str(e)}")


# ========================================
# ENDPOINTS ADMIN - ÉDITION DU MANUEL
# ========================================

@router.put("/manual/sections/{section_id}")
async def update_manual_section(
    section_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    level: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    current_user: dict = Depends(require_permission("admin", "edit"))
):
    """Mettre à jour une section du manuel (ADMIN uniquement)"""
    try:
        # Construire l'update
        update_data = {
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if title is not None:
            update_data["title"] = title
        if content is not None:
            update_data["content"] = content
        if level is not None:
            if level not in ["beginner", "advanced", "both"]:
                raise HTTPException(status_code=400, detail="Niveau invalide")
            update_data["level"] = level
        if keywords is not None:
            update_data["keywords"] = keywords
        
        # Mettre à jour dans MongoDB
        result = await db.manual_sections.update_one(
            {"id": section_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Section non trouvée")
        
        # Log audit
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": current_user.get("id"),
            "user_email": current_user.get("email"),
            "user_name": f"{current_user.get('firstName', '')} {current_user.get('lastName', '')}".strip(),
            "action": "UPDATE",
            "entity_type": "manual_section",
            "entity_id": section_id,
            "details": update_data
        })
        
        logger.info(f"Section {section_id} mise à jour par {current_user.get('email')}")
        
        return {"message": "Section mise à jour avec succès", "section_id": section_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de la section: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/manual/sections")
async def create_manual_section(
    chapter_id: str,
    title: str,
    content: str,
    level: str = "beginner",
    keywords: List[str] = [],
    current_user: dict = Depends(require_permission("admin", "edit"))
):
    """Créer une nouvelle section du manuel (ADMIN uniquement)"""
    try:
        # Vérifier que le chapitre existe
        chapter = await db.manual_chapters.find_one({"id": chapter_id})
        if not chapter:
            raise HTTPException(status_code=404, detail="Chapitre non trouvé")
        
        # Générer ID pour la nouvelle section
        # Format: sec-XXX-YY où XXX est le numéro du chapitre
        chapter_num = chapter_id.split('-')[1]
        
        # Compter les sections existantes du chapitre
        existing_sections = chapter.get("sections", [])
        new_section_num = len(existing_sections) + 1
        section_id = f"sec-{chapter_num}-{new_section_num:02d}"
        
        # Créer la section
        now = datetime.now(timezone.utc)
        section = {
            "id": section_id,
            "title": title,
            "content": content,
            "order": new_section_num,
            "parent_id": None,
            "target_roles": [],
            "target_modules": [],
            "level": level,
            "images": [],
            "video_url": None,
            "keywords": keywords,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        await db.manual_sections.insert_one(section)
        
        # Ajouter la section au chapitre
        await db.manual_chapters.update_one(
            {"id": chapter_id},
            {"$push": {"sections": section_id}}
        )
        
        # Log audit
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "timestamp": now.isoformat(),
            "user_id": current_user.get("id"),
            "user_email": current_user.get("email"),
            "user_name": f"{current_user.get('firstName', '')} {current_user.get('lastName', '')}".strip(),
            "action": "CREATE",
            "entity_type": "manual_section",
            "entity_id": section_id,
            "details": {"chapter_id": chapter_id, "title": title}
        })
        
        logger.info(f"Section {section_id} créée par {current_user.get('email')}")
        
        return {"message": "Section créée avec succès", "section_id": section_id, "section": section}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la création de la section: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/manual/sections/{section_id}")
async def delete_manual_section(
    section_id: str,
    current_user: dict = Depends(require_permission("admin", "delete"))
):
    """Supprimer une section du manuel (ADMIN uniquement)"""
    try:
        # Vérifier que la section existe
        section = await db.manual_sections.find_one({"id": section_id})
        if not section:
            raise HTTPException(status_code=404, detail="Section non trouvée")
        
        # Trouver le chapitre parent
        chapter = await db.manual_chapters.find_one({"sections": section_id})
        
        # Supprimer la section
        await db.manual_sections.delete_one({"id": section_id})
        
        # Retirer de la liste des sections du chapitre
        if chapter:
            await db.manual_chapters.update_one(
                {"id": chapter["id"]},
                {"$pull": {"sections": section_id}}
            )
        
        # Log audit
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": current_user.get("id"),
            "user_email": current_user.get("email"),
            "user_name": f"{current_user.get('firstName', '')} {current_user.get('lastName', '')}".strip(),
            "action": "DELETE",
            "entity_type": "manual_section",
            "entity_id": section_id,
            "details": {"title": section.get("title")}
        })
        
        logger.info(f"Section {section_id} supprimée par {current_user.get('email')}")
        
        return {"message": "Section supprimée avec succès"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de la section: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

