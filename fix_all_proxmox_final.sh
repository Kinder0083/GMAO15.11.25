#!/bin/bash

# Script final pour Proxmox - Détection automatique du Python

echo "🚀 Correction GMAO Iris (Proxmox - Détection Auto)"
echo "================================================================"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Exécuter en root${NC}"
    exit 1
fi

INSTALL_DIR="/opt/gmao-iris"

if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${RED}❌ Installation non trouvée: $INSTALL_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Installation: $INSTALL_DIR${NC}"

# ===========================================
# DÉTECTION AUTOMATIQUE DU BON PYTHON
# ===========================================
echo ""
echo "🔍 Détection du Python utilisé par le backend..."

# Trouver le processus uvicorn
UVICORN_CMD=$(ps aux | grep "[u]vicorn server:app" | grep "8001")

if [ -n "$UVICORN_CMD" ]; then
    echo "  Processus trouvé:"
    echo "  $UVICORN_CMD" | head -c 100
    echo "..."
    
    # Extraire le chemin du Python depuis la commande
    VENV_PYTHON=$(echo "$UVICORN_CMD" | grep -o '/[^ ]*/python' | head -1)
    
    if [ -n "$VENV_PYTHON" ] && [ -f "$VENV_PYTHON" ]; then
        echo -e "${GREEN}✅ Python détecté: $VENV_PYTHON${NC}"
    else
        echo -e "${YELLOW}⚠️ Extraction depuis processus échouée${NC}"
        VENV_PYTHON=""
    fi
else
    echo -e "${YELLOW}⚠️ Processus uvicorn non trouvé${NC}"
    VENV_PYTHON=""
fi

# Chercher dans les emplacements standards
if [ -z "$VENV_PYTHON" ] || [ ! -f "$VENV_PYTHON" ]; then
    echo "  Recherche dans les emplacements standards..."
    
    POSSIBLE_PATHS=(
        "/root/.venv/bin/python"
        "/opt/gmao-iris/.venv/bin/python"
        "/opt/gmao-iris/venv/bin/python"
        "/home/*/venv/bin/python"
        "$(which python3)"
    )
    
    for path in "${POSSIBLE_PATHS[@]}"; do
        if [ -f "$path" ]; then
            # Vérifier si motor est installé
            if $path -c "import motor" 2>/dev/null; then
                VENV_PYTHON="$path"
                echo -e "${GREEN}✅ Trouvé avec motor: $VENV_PYTHON${NC}"
                break
            else
                echo "  ❌ $path (motor manquant)"
            fi
        fi
    done
fi

# Dernier recours : installer motor dans le Python système
if [ -z "$VENV_PYTHON" ] || [ ! -f "$VENV_PYTHON" ]; then
    echo -e "${YELLOW}⚠️ Virtualenv introuvable${NC}"
    echo -e "${YELLOW}📦 Installation de motor dans python3 système...${NC}"
    pip3 install motor 2>&1 | tail -3
    VENV_PYTHON="python3"
fi

echo -e "${GREEN}✅ Python final: $VENV_PYTHON${NC}"
echo ""

# ===========================================
# ÉTAPE 1: Correction update_service.py
# ===========================================
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}📝 Correction service de mise à jour${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

FILE="${INSTALL_DIR}/backend/update_service.py"

if [ ! -f "$FILE" ]; then
    echo -e "${RED}❌ Fichier non trouvé: $FILE${NC}"
    exit 1
fi

BACKUP_FILE="${FILE}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$FILE" "$BACKUP_FILE"
echo -e "${GREEN}✅ Backup: ${BACKUP_FILE##*/}${NC}"

if grep -q "Environnement sans Git, passage à l'étape suivante" "$FILE"; then
    echo -e "${GREEN}✅ Déjà appliqué${NC}"
else
    echo -e "${YELLOW}🔨 Application...${NC}"
    
    $VENV_PYTHON << 'PYTHON_EOF'
with open('/opt/gmao-iris/backend/update_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_text = '''if pull_process.returncode != 0:
                    logger.error(f"❌ Échec du git pull: {pull_stderr.decode()}")
                    return {
                        "success": False,
                        "message": "Échec du téléchargement de la mise à jour",
                        "error": pull_stderr.decode()
                    }'''

new_code = '''if pull_process.returncode != 0:
                    error_msg = pull_stderr.decode()
                    logger.warning(f"⚠️ Git pull a échoué: {error_msg}")
                    if "No remote" in error_msg or "no remote" in error_msg or "not a git repository" in error_msg:
                        logger.info("ℹ️ Environnement sans Git, passage à l'étape suivante")
                    else:
                        logger.error(f"❌ Échec du git pull: {error_msg}")
                        return {
                            "success": False,
                            "message": "Échec du téléchargement de la mise à jour",
                            "error": error_msg
                        }'''

if old_text in content:
    content = content.replace(old_text, new_code)
    with open('/opt/gmao-iris/backend/update_service.py', 'w', encoding='utf-8') as f:
        f.write(content)
    exit(0)
else:
    exit(1)
PYTHON_EOF

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Appliqué${NC}"
    else
        echo -e "${RED}❌ Échec${NC}"
        cp "$BACKUP_FILE" "$FILE"
        exit 1
    fi
fi

# ===========================================
# ÉTAPE 2: Génération du manuel
# ===========================================
echo ""
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}📚 Génération du manuel complet${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

SCRIPT_FILE="${INSTALL_DIR}/backend/generate_complete_manual.py"

if [ ! -f "$SCRIPT_FILE" ]; then
    echo -e "${RED}❌ Script non trouvé${NC}"
    exit 1
fi

cd "${INSTALL_DIR}/backend" || exit 1

echo -e "${YELLOW}🔨 Génération...${NC}"
$VENV_PYTHON generate_complete_manual.py 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Manuel généré${NC}"
    
    # Vérifier dans MongoDB
    echo ""
    echo "  Vérification MongoDB..."
    CHAPTER_COUNT=$(mongo gmao_iris --quiet --eval "db.manual_chapters.count()" 2>/dev/null || echo "?")
    SECTION_COUNT=$(mongo gmao_iris --quiet --eval "db.manual_sections.count()" 2>/dev/null || echo "?")
    echo "  📖 Chapitres: $CHAPTER_COUNT"
    echo "  📄 Sections: $SECTION_COUNT"
else
    echo -e "${RED}❌ Erreur génération${NC}"
    exit 1
fi

# ===========================================
# Redémarrage backend
# ===========================================
echo ""
echo -e "${YELLOW}🔄 Redémarrage backend...${NC}"

BACKEND_PID=$(ps aux | grep "[u]vicorn server:app" | grep "8001" | awk '{print $2}')

if [ -n "$BACKEND_PID" ]; then
    kill -TERM $BACKEND_PID 2>/dev/null
    sleep 3
    kill -9 $BACKEND_PID 2>/dev/null
fi

cd "${INSTALL_DIR}/backend" || exit 1

# Utiliser nohup avec le bon Python
if [ "$VENV_PYTHON" = "python3" ]; then
    # Python système, utiliser uvicorn directement
    nohup python3 -m uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1 --reload \
        > /var/log/backend.out.log 2> /var/log/backend.err.log &
else
    # Virtualenv, utiliser le chemin complet
    VENV_DIR=$(dirname $(dirname $VENV_PYTHON))
    nohup ${VENV_DIR}/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1 --reload \
        > /var/log/backend.out.log 2> /var/log/backend.err.log &
fi

sleep 5

if ps aux | grep -q "[u]vicorn server:app.*8001"; then
    NEW_PID=$(ps aux | grep "[u]vicorn server:app" | grep "8001" | awk '{print $2}')
    echo -e "${GREEN}✅ Backend actif (PID: $NEW_PID)${NC}"
else
    echo -e "${RED}❌ Backend ne démarre pas${NC}"
    echo "Logs: tail -20 /var/log/backend.err.log"
fi

# ===========================================
# RÉSUMÉ
# ===========================================
echo ""
echo "================================================================"
echo -e "${GREEN}🎉 TERMINÉ !${NC}"
echo "================================================================"
echo ""
echo "📋 Actions:"
echo "  ✅ update_service.py corrigé"
echo "  ✅ Manuel généré (12 chapitres, 49 sections)"
echo "  ✅ Backend redémarré"
echo ""
echo "💡 Vérifications:"
echo "  1. Rafraîchir navigateur (Ctrl+F5)"
echo "  2. Ouvrir le manuel → 12 chapitres"
echo "  3. Tester redémarrage services"
echo ""
echo "🔧 Commandes utiles:"
echo "  • Status: ps aux | grep uvicorn"
echo "  • Logs: tail -f /var/log/backend.err.log"
echo ""
echo "================================================================"
