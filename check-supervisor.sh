#!/bin/bash

# Script de diagnostic Supervisor
# À exécuter : bash check-supervisor.sh

echo "======================================"
echo "DIAGNOSTIC SUPERVISOR - GMAO IRIS"
echo "======================================"
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 1. Vérifier si supervisor est installé
echo -e "${BLUE}1. Vérification installation Supervisor...${NC}"
if command -v supervisorctl &> /dev/null; then
    echo -e "${GREEN}✅ Supervisor installé${NC}"
    supervisorctl version
else
    echo -e "${RED}❌ Supervisor NON installé${NC}"
    echo "   Installer avec : sudo apt-get install supervisor"
fi
echo ""

# 2. Vérifier le service supervisor
echo -e "${BLUE}2. Vérification service Supervisor...${NC}"
if systemctl is-active --quiet supervisor; then
    echo -e "${GREEN}✅ Service supervisor ACTIF${NC}"
else
    echo -e "${RED}❌ Service supervisor ARRÊTÉ${NC}"
    echo "   Démarrer avec : sudo systemctl start supervisor"
fi
echo ""

# 3. Lister tous les processus supervisés
echo -e "${BLUE}3. Liste des processus supervisés...${NC}"
supervisorctl status
echo ""

# 4. Vérifier les fichiers de configuration
echo -e "${BLUE}4. Vérification fichiers de configuration...${NC}"

# Vérifier supervisor.conf principal
if [ -f /etc/supervisor/supervisord.conf ]; then
    echo -e "${GREEN}✅ /etc/supervisor/supervisord.conf trouvé${NC}"
else
    echo -e "${RED}❌ /etc/supervisor/supervisord.conf MANQUANT${NC}"
fi

# Vérifier répertoire conf.d
if [ -d /etc/supervisor/conf.d ]; then
    echo -e "${GREEN}✅ Répertoire /etc/supervisor/conf.d trouvé${NC}"
    echo "   Fichiers de configuration :"
    ls -l /etc/supervisor/conf.d/*.conf 2>/dev/null | awk '{print "   ", $9}' || echo "   Aucun fichier .conf trouvé"
else
    echo -e "${RED}❌ Répertoire /etc/supervisor/conf.d MANQUANT${NC}"
fi
echo ""

# 5. Vérifier la configuration backend
echo -e "${BLUE}5. Vérification configuration backend...${NC}"
BACKEND_CONF="/etc/supervisor/conf.d/backend.conf"
if [ -f "$BACKEND_CONF" ]; then
    echo -e "${GREEN}✅ Configuration backend trouvée : $BACKEND_CONF${NC}"
    echo "   Contenu :"
    cat "$BACKEND_CONF" | sed 's/^/   /'
else
    echo -e "${RED}❌ Configuration backend MANQUANTE : $BACKEND_CONF${NC}"
    echo "   Le fichier de configuration backend n'existe pas !"
fi
echo ""

# 6. Vérifier le répertoire backend
echo -e "${BLUE}6. Vérification répertoire backend...${NC}"
BACKEND_DIR="/opt/gmao-iris/backend"
if [ -d "$BACKEND_DIR" ]; then
    echo -e "${GREEN}✅ Répertoire backend trouvé : $BACKEND_DIR${NC}"
    echo "   Fichiers principaux :"
    ls -la "$BACKEND_DIR" | grep -E "(server.py|\.env|requirements.txt|venv)" | sed 's/^/   /'
else
    echo -e "${RED}❌ Répertoire backend MANQUANT : $BACKEND_DIR${NC}"
fi
echo ""

# 7. Vérifier l'environnement virtuel Python
echo -e "${BLUE}7. Vérification environnement virtuel Python...${NC}"
VENV_DIR="/opt/gmao-iris/backend/venv"
if [ -d "$VENV_DIR" ]; then
    echo -e "${GREEN}✅ Environnement virtuel trouvé : $VENV_DIR${NC}"
    if [ -f "$VENV_DIR/bin/python3" ]; then
        echo -e "${GREEN}✅ Python3 trouvé dans venv${NC}"
        "$VENV_DIR/bin/python3" --version
    else
        echo -e "${RED}❌ Python3 manquant dans venv${NC}"
    fi
else
    echo -e "${RED}❌ Environnement virtuel MANQUANT : $VENV_DIR${NC}"
    echo "   Créer avec : cd $BACKEND_DIR && python3 -m venv venv"
fi
echo ""

# 8. Vérifier les logs supervisor
echo -e "${BLUE}8. Logs supervisor (dernières lignes)...${NC}"
if [ -f /var/log/supervisor/supervisord.log ]; then
    echo "   Dernières lignes de supervisord.log :"
    tail -n 10 /var/log/supervisor/supervisord.log | sed 's/^/   /'
else
    echo -e "${YELLOW}⚠️  Fichier log supervisord non trouvé${NC}"
fi
echo ""

# 9. Vérifier les logs backend
echo -e "${BLUE}9. Logs backend (si disponibles)...${NC}"
if [ -f /var/log/supervisor/backend.err.log ]; then
    echo "   Dernières erreurs backend :"
    tail -n 10 /var/log/supervisor/backend.err.log | sed 's/^/   /'
else
    echo -e "${YELLOW}⚠️  Pas de logs backend (normal si jamais démarré)${NC}"
fi
echo ""

# 10. Commandes de correction suggérées
echo "======================================"
echo -e "${BLUE}COMMANDES DE CORRECTION${NC}"
echo "======================================"
echo ""

if ! systemctl is-active --quiet supervisor; then
    echo "1. Démarrer supervisor :"
    echo "   sudo systemctl start supervisor"
    echo "   sudo systemctl enable supervisor"
    echo ""
fi

if [ ! -f "$BACKEND_CONF" ]; then
    echo "2. Le fichier de configuration backend est MANQUANT !"
    echo "   Il faut créer : $BACKEND_CONF"
    echo "   Voulez-vous que je le crée maintenant ? (voir script fix-supervisor.sh)"
    echo ""
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "3. Créer l'environnement virtuel Python :"
    echo "   cd $BACKEND_DIR"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    echo ""
fi

echo "4. Recharger la configuration supervisor :"
echo "   sudo supervisorctl reread"
echo "   sudo supervisorctl update"
echo "   sudo supervisorctl start backend"
echo ""

echo "5. Installer python-dotenv pour le script de test :"
echo "   cd $BACKEND_DIR"
echo "   source venv/bin/activate"
echo "   pip install python-dotenv"
echo ""

echo "======================================"
echo "FIN DU DIAGNOSTIC"
echo "======================================"
