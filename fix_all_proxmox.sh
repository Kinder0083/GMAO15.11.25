#!/bin/bash

# Script tout-en-un pour corriger l'installation Proxmox
# - Corrige l'erreur 500 du redémarrage des services
# - Génère le manuel utilisateur complet

echo "🚀 Correction complète de l'installation GMAO Iris (Proxmox)"
echo "================================================================"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Vérifier si le script est exécuté en root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Ce script doit être exécuté en root${NC}"
    echo "Utilisez: sudo bash fix_all_proxmox.sh"
    exit 1
fi

# Chemin de l'installation
INSTALL_DIR="/opt/gmao-iris"

# Vérifier l'installation
if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${RED}❌ Installation non trouvée dans: $INSTALL_DIR${NC}"
    echo "Vérifiez le chemin d'installation"
    exit 1
fi

echo -e "${GREEN}✅ Installation trouvée: $INSTALL_DIR${NC}"
echo ""

# ===========================================
# ÉTAPE 1: Correction du service de mise à jour
# ===========================================
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}📝 ÉTAPE 1/2: Correction service de mise à jour${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

FILE="${INSTALL_DIR}/backend/update_service.py"

if [ ! -f "$FILE" ]; then
    echo -e "${RED}❌ Fichier non trouvé: $FILE${NC}"
    exit 1
fi

# Créer un backup
BACKUP_FILE="${FILE}.backup.$(date +%Y%m%d_%H%M%S)"
echo -e "${YELLOW}📦 Création du backup...${NC}"
cp "$FILE" "$BACKUP_FILE"
echo -e "${GREEN}✅ Backup: $BACKUP_FILE${NC}"

# Vérifier si déjà appliqué
if grep -q "Environnement sans Git, passage à l'étape suivante" "$FILE"; then
    echo -e "${GREEN}✅ Correction déjà appliquée${NC}"
else
    echo -e "${YELLOW}🔨 Application de la correction...${NC}"
    
    # Appliquer la modification avec Python
    python3 << 'PYTHON_EOF'
# Lire le fichier
with open('/opt/gmao-iris/backend/update_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Ancien code
old_text = '''if pull_process.returncode != 0:
                    logger.error(f"❌ Échec du git pull: {pull_stderr.decode()}")
                    return {
                        "success": False,
                        "message": "Échec du téléchargement de la mise à jour",
                        "error": pull_stderr.decode()
                    }'''

# Nouveau code
new_code = '''if pull_process.returncode != 0:
                    error_msg = pull_stderr.decode()
                    logger.warning(f"⚠️ Git pull a échoué: {error_msg}")
                    # Ne pas bloquer si Git n'est pas configuré (environnement sans Git)
                    if "No remote" in error_msg or "no remote" in error_msg or "not a git repository" in error_msg:
                        logger.info("ℹ️ Environnement sans Git, passage à l'étape suivante")
                    else:
                        logger.error(f"❌ Échec du git pull: {error_msg}")
                        return {
                            "success": False,
                            "message": "Échec du téléchargement de la mise à jour",
                            "error": error_msg
                        }'''

# Remplacer
if old_text in content:
    content = content.replace(old_text, new_code)
    with open('/opt/gmao-iris/backend/update_service.py', 'w', encoding='utf-8') as f:
        f.write(content)
    exit(0)
else:
    exit(1)
PYTHON_EOF

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Correction appliquée${NC}"
    else
        echo -e "${RED}❌ Échec de la correction${NC}"
        cp "$BACKUP_FILE" "$FILE"
        exit 1
    fi
fi

# Redémarrer le backend
echo -e "${YELLOW}🔄 Redémarrage du backend...${NC}"
supervisorctl restart backend
sleep 3

if supervisorctl status backend | grep -q RUNNING; then
    echo -e "${GREEN}✅ Backend redémarré${NC}"
else
    echo -e "${RED}❌ Erreur redémarrage backend${NC}"
    exit 1
fi

echo ""

# ===========================================
# ÉTAPE 2: Génération du manuel complet
# ===========================================
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}📚 ÉTAPE 2/2: Génération du manuel complet${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

SCRIPT_FILE="${INSTALL_DIR}/backend/generate_complete_manual.py"

if [ ! -f "$SCRIPT_FILE" ]; then
    echo -e "${RED}❌ Script non trouvé: $SCRIPT_FILE${NC}"
    exit 1
fi

cd "${INSTALL_DIR}/backend" || exit 1

echo -e "${YELLOW}🔨 Génération en cours...${NC}"
python3 generate_complete_manual.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Manuel généré${NC}"
else
    echo -e "${RED}❌ Erreur génération manuel${NC}"
    exit 1
fi

# ===========================================
# RÉSUMÉ FINAL
# ===========================================
echo ""
echo "================================================================"
echo -e "${GREEN}🎉 CORRECTIONS APPLIQUÉES AVEC SUCCÈS !${NC}"
echo "================================================================"
echo ""
echo "📋 Résumé des actions:"
echo "  ✅ Service de mise à jour corrigé"
echo "  ✅ Backend redémarré"
echo "  ✅ Manuel utilisateur généré (12 chapitres, 49 sections)"
echo ""
echo "💡 Prochaines étapes:"
echo "  1. Rafraîchissez votre navigateur (Ctrl + F5)"
echo "  2. Testez le redémarrage des services depuis l'interface"
echo "  3. Ouvrez le manuel utilisateur pour vérifier le contenu"
echo ""
echo "📁 Fichiers modifiés:"
echo "  - ${FILE}"
echo "  - Backup: ${BACKUP_FILE}"
echo ""
echo "================================================================"
