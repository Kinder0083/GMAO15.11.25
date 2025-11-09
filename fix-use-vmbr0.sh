#!/usr/bin/env bash

###############################################################################
# Solution : Activer vmbr0 et l'utiliser pour l'installation
###############################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Activation de vmbr0 et Nouvelle Installation          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Activer vmbr0
echo -e "${BLUE}▶${NC} Activation de vmbr0..."
ip link set vmbr0 up
sleep 2

# Vérifier
if ip link show vmbr0 | grep -q "state UP"; then
    echo -e "${GREEN}✓${NC} vmbr0 est maintenant UP"
    ip addr show vmbr0
else
    echo -e "${RED}✗${NC} vmbr0 n'a pas pu être activé"
    echo "Vérifiez /etc/network/interfaces"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PROCHAINES ÉTAPES:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Lancez l'installation avec le script:"
echo "   bash gmao-iris-v1.1.2-install-auto.sh"
echo ""
echo "2. Lors du choix du bridge, sélectionnez vmbr0 (PAS vmbr1)"
echo ""
echo "3. Choisissez IP Statique avec une IP dans 192.168.1.x"
echo "   Exemple: 192.168.1.200"
echo "   Gateway: 192.168.1.254"
echo ""
