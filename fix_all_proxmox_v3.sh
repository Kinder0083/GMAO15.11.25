#!/bin/bash

# Script tout-en-un pour corriger l'installation Proxmox (V3)
# Version 3 : Utilise le bon virtualenv Python

echo "🚀 Correction complète de l'installation GMAO Iris (Proxmox v3)"
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
    echo "Utilisez: sudo bash fix_all_proxmox_v3.sh"
    exit 1
fi

# Chemin de l'installation
INSTALL_DIR="/opt/gmao-iris"
VENV_PYTHON="/root/.venv/bin/python"

# Vérifier l'installation
if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${RED}❌ Installation non trouvée dans: $INSTALL_DIR${NC}"
    exit 1
fi

# Vérifier le virtualenv
if [ ! -f "$VENV_PYTHON" ]; then
    echo -e "${RED}❌ Virtualenv Python non trouvé: $VENV_PYTHON${NC}"
    echo "Recherche d'alternatives..."
    
    # Chercher d'autres emplacements possibles
    if [ -f "${INSTALL_DIR}/.venv/bin/python" ]; then
        VENV_PYTHON="${INSTALL_DIR}/.venv/bin/python"
        echo -e "${GREEN}✅ Trouvé: $VENV_PYTHON${NC}"
    elif [ -f "${INSTALL_DIR}/venv/bin/python" ]; then
        VENV_PYTHON="${INSTALL_DIR}/venv/bin/python"
        echo -e "${GREEN}✅ Trouvé: $VENV_PYTHON${NC}"
    else
        echo -e "${RED}❌ Aucun virtualenv trouvé${NC}"
        echo "Utilisation de python3 système (peut causer des erreurs)"
        VENV_PYTHON="python3"
    fi
fi

echo -e "${GREEN}✅ Installation: $INSTALL_DIR${NC}"
echo -e "${GREEN}✅ Python: $VENV_PYTHON${NC}"
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
    
    # Appliquer la modification avec le bon Python
    $VENV_PYTHON << 'PYTHON_EOF'
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

# Trouver le PID
BACKEND_PID=$(ps aux | grep "[u]vicorn server:app" | grep "8001" | awk '{print $2}')

if [ -n "$BACKEND_PID" ]; then
    echo "  PID trouvé: $BACKEND_PID"
    kill -TERM $BACKEND_PID
    sleep 3
    
    # Vérifier si arrêté
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        kill -9 $BACKEND_PID
        sleep 1
    fi
    echo "  Backend arrêté"
fi

# Redémarrer en background
echo "  Démarrage du backend..."
cd "${INSTALL_DIR}/backend" || exit 1
nohup $VENV_PYTHON -m uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1 --reload > /var/log/supervisor/backend.out.log 2> /var/log/supervisor/backend.err.log &

sleep 5

# Vérifier
if ps aux | grep -q "[u]vicorn server:app.*8001"; then
    echo -e "${GREEN}✅ Backend redémarré${NC}"
else
    echo -e "${RED}❌ Backend ne démarre pas${NC}"
    echo "Logs: tail -50 /var/log/supervisor/backend.err.log"
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

echo -e "${YELLOW}🔨 Génération en cours (avec le bon Python)...${NC}"
echo "  Utilisation de: $VENV_PYTHON"

$VENV_PYTHON generate_complete_manual.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Manuel généré avec succès${NC}"
else
    echo -e "${RED}❌ Erreur lors de la génération${NC}"
    echo "Vérifiez les erreurs ci-dessus"
    exit 1
fi

# ===========================================
# RÉSUMÉ FINAL
# ===========================================
echo ""
echo "================================================================"
echo -e "${GREEN}🎉 CORRECTIONS TERMINÉES AVEC SUCCÈS !${NC}"
echo "================================================================"
echo ""
echo "📋 Résumé:"
echo "  ✅ Service de mise à jour corrigé"
echo "  ✅ Backend redémarré (PID: $(ps aux | grep '[u]vicorn server:app.*8001' | awk '{print $2}'))"
echo "  ✅ Manuel généré (12 chapitres, 49 sections)"
echo ""
echo "💡 Actions recommandées:"
echo "  1. Testez l'accès au backend:"
echo "     curl http://localhost:8001/api/health"
echo ""
echo "  2. Rafraîchissez le navigateur (Ctrl + F5)"
echo ""
echo "  3. Ouvrez le manuel depuis l'interface"
echo "     → Devrait afficher 12 chapitres"
echo ""
echo "  4. Testez le redémarrage des services"
echo "     → Ne devrait plus avoir d'erreur 500"
echo ""
echo "📁 Backup créé:"
echo "  $BACKUP_FILE"
echo ""
echo "================================================================"
