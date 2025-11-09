#!/usr/bin/env bash

###############################################################################
# Configuration correcte de vmbr1 (WiFi) pour GMAO Iris
# Pas besoin de NAT car vmbr1 est déjà sur le réseau local 192.168.1.0/24
###############################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Configuration vmbr1 (WiFi) pour GMAO Iris             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo -e "${BLUE}▶${NC} Correction de la configuration vmbr1..."
echo ""

# Sauvegarder l'ancien fichier
cp /etc/network/interfaces /etc/network/interfaces.backup.$(date +%Y%m%d_%H%M%S)
echo -e "${GREEN}✓${NC} Backup créé"

# Corriger la configuration vmbr1
echo -e "${BLUE}▶${NC} Modification de /etc/network/interfaces..."

# Créer la nouvelle configuration vmbr1 (sans NAT car même réseau)
cat > /tmp/vmbr1_config <<'EOF'

# Bridge WiFi pour containers
auto vmbr1
iface vmbr1 inet static
    address 192.168.1.190/24
    gateway 192.168.1.254
    bridge_ports none
    bridge_stp off
    bridge_fd 0
    # Pas de NAT car déjà sur le réseau local 192.168.1.0/24
EOF

# Supprimer l'ancienne config vmbr1 et ajouter la nouvelle
sed -i '/^auto vmbr1/,/^$/d' /etc/network/interfaces
sed -i '/^iface vmbr1/,/^$/d' /etc/network/interfaces
cat /tmp/vmbr1_config >> /etc/network/interfaces

echo -e "${GREEN}✓${NC} Configuration mise à jour"

# Afficher la nouvelle config
echo ""
echo "Nouvelle configuration vmbr1:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
grep -A 10 "auto vmbr1" /etc/network/interfaces
echo ""

# Recharger la config réseau
echo -e "${BLUE}▶${NC} Rechargement de la configuration réseau..."
ifreload -a
sleep 2

# Vérifier vmbr1
echo ""
echo "État de vmbr1:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ip addr show vmbr1
echo ""

# Test de connectivité
echo -e "${BLUE}▶${NC} Test de connectivité..."
if ping -c 2 -I vmbr1 8.8.8.8 >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Connexion Internet via vmbr1 OK"
else
    echo -e "${YELLOW}⚠${NC} Pas de connexion directe via vmbr1 (mais containers pourront router via gateway)"
fi

if ping -c 2 192.168.1.254 >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Gateway 192.168.1.254 accessible"
else
    echo -e "${RED}✗${NC} Gateway 192.168.1.254 non accessible"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║               ✅ CONFIGURATION TERMINÉE !                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}vmbr1 est maintenant correctement configuré${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CONFIGURATION POUR VOS CONTAINERS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Bridge:   vmbr1"
echo "  IP:       192.168.1.x (choisissez une IP libre, ex: 192.168.1.200)"
echo "  Masque:   /24"
echo "  Gateway:  192.168.1.254"
echo "  DNS:      8.8.8.8, 8.8.4.4"
echo ""
echo "Exemple de commande pour créer un container:"
echo "  pct set CTID -net0 name=eth0,bridge=vmbr1,ip=192.168.1.200/24,gw=192.168.1.254"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Vous pouvez maintenant lancer l'installation:"
echo "  bash gmao-iris-v1.1.2-install-auto.sh"
echo ""
echo "Lors des choix:"
echo "  - Bridge: Choisissez vmbr1"
echo "  - IP Statique: 192.168.1.200 (ou une autre IP libre)"
echo "  - Gateway: 192.168.1.254"
echo ""
