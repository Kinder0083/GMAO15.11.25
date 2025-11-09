#!/usr/bin/env bash

###############################################################################
# Script de diagnostic Proxmox pour GMAO Iris
# À exécuter sur le serveur Proxmox AVANT l'installation
###############################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Diagnostic Proxmox pour GMAO Iris v1.1                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# 1. Version Proxmox
echo -e "${BLUE}[1/6]${NC} Version Proxmox"
pveversion
echo ""

# 2. Templates disponibles
echo -e "${BLUE}[2/6]${NC} Templates CT disponibles"
pveam available --section system | grep debian-12 || echo -e "${RED}✗ Aucun template Debian 12 trouvé${NC}"
echo ""
echo "Templates actuellement téléchargés:"
ls -lh /var/lib/vz/template/cache/*.tar.* 2>/dev/null || echo -e "${YELLOW}⚠ Aucun template téléchargé${NC}"
echo ""

# 3. Storages disponibles
echo -e "${BLUE}[3/6]${NC} Storages disponibles"
pvesm status
echo ""

# 4. Vérifier local-lvm
echo -e "${BLUE}[4/6]${NC} Vérification du storage 'local-lvm'"
if pvesm status | grep -q "local-lvm"; then
    echo -e "${GREEN}✓ local-lvm est disponible${NC}"
    pvesm status | grep local-lvm
else
    echo -e "${YELLOW}⚠ local-lvm n'est PAS disponible${NC}"
    echo "Storages alternatifs disponibles:"
    pvesm status | awk 'NR>1 {print "  - " $1 " (" $2 ")"}'
fi
echo ""

# 5. Vérifier si l'ID 100 est déjà utilisé
echo -e "${BLUE}[5/6]${NC} Vérification de l'ID container 100"
if pct status 100 >/dev/null 2>&1; then
    echo -e "${RED}✗ Container ID 100 existe déjà${NC}"
    pct status 100
    echo "Suggestion: Utilisez un autre ID (ex: 101, 102, etc.)"
else
    echo -e "${GREEN}✓ ID 100 est disponible${NC}"
fi
echo ""

# 6. Espace disque
echo -e "${BLUE}[6/6]${NC} Espace disque disponible"
df -h | grep -E "(Filesystem|/dev/)"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "RECOMMANDATIONS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Recommandations template
if ! ls /var/lib/vz/template/cache/*debian-12*.tar.* >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ TÉLÉCHARGER LE TEMPLATE DEBIAN 12:${NC}"
    echo "   pveam update"
    echo "   pveam download local debian-12-standard_12.7-1_amd64.tar.zst"
    echo ""
fi

# Recommandations storage
if ! pvesm status | grep -q "local-lvm"; then
    echo -e "${YELLOW}⚠ MODIFIER LE SCRIPT D'INSTALLATION:${NC}"
    echo "   Ligne 107 du script gmao-iris-v1.1-install.sh"
    echo "   Remplacer: --rootfs local-lvm:20"
    echo "   Par: --rootfs VOTRE_STORAGE:20"
    echo ""
    echo "   Storages disponibles:"
    pvesm status | awk 'NR>1 {print "     --rootfs " $1 ":20"}'
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
