#!/usr/bin/env bash

###############################################################################
# Diagnostic et correction réseau container 102
###############################################################################

CTID=102

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Diagnostic Réseau Container $CTID                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Vérifier config dans Proxmox
echo -e "${BLUE}[1] Configuration réseau Proxmox${NC}"
pct config $CTID | grep net0
echo ""

# Vérifier dans le container
echo -e "${BLUE}[2] Configuration dans le container${NC}"
echo "IP:"
pct exec $CTID -- ip addr show eth0
echo ""
echo "Routes:"
pct exec $CTID -- ip route
echo ""
echo "DNS:"
pct exec $CTID -- cat /etc/resolv.conf
echo ""

# Tests de connectivité
echo -e "${BLUE}[3] Tests de connectivité${NC}"

echo -n "  Depuis Proxmox vers gateway (192.168.1.254): "
if ping -c 1 -W 2 192.168.1.254 >/dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}ÉCHEC${NC}"
fi

echo -n "  Depuis Proxmox vers 8.8.8.8: "
if ping -c 1 -W 2 8.8.8.8 >/dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}ÉCHEC${NC}"
fi

echo -n "  Depuis Container vers gateway (192.168.1.254): "
if pct exec $CTID -- ping -c 1 -W 2 192.168.1.254 >/dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}ÉCHEC - Le container ne peut pas joindre la gateway${NC}"
fi

echo -n "  Depuis Container vers 8.8.8.8: "
if pct exec $CTID -- ping -c 1 -W 2 8.8.8.8 >/dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}ÉCHEC${NC}"
fi

echo ""
echo -e "${BLUE}[4] Configuration vmbr1 sur Proxmox${NC}"
ip addr show vmbr1
echo ""
echo "Forwarding IP:"
cat /proc/sys/net/ipv4/ip_forward
echo ""

echo -e "${BLUE}[5] Règles firewall/iptables${NC}"
iptables -L FORWARD -n -v | head -10
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CORRECTION AUTOMATIQUE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

read -p "Voulez-vous appliquer les corrections ? (y/n): " APPLY

if [[ ! $APPLY =~ ^[Yy]$ ]]; then
    exit 0
fi

echo ""
echo -e "${BLUE}▶${NC} Application des corrections..."

# 1. Activer le forwarding IP
echo "1. Activation du forwarding IP..."
echo 1 > /proc/sys/net/ipv4/ip_forward
sysctl -w net.ipv4.ip_forward=1 >/dev/null
echo -e "${GREEN}✓${NC} Forwarding IP activé"

# 2. Autoriser le forwarding dans iptables
echo "2. Configuration iptables..."
iptables -P FORWARD ACCEPT 2>/dev/null
iptables -A FORWARD -i vmbr1 -j ACCEPT 2>/dev/null
iptables -A FORWARD -o vmbr1 -j ACCEPT 2>/dev/null
echo -e "${GREEN}✓${NC} Règles iptables configurées"

# 3. S'assurer que vmbr1 peut router
echo "3. Configuration du bridge vmbr1..."
echo 0 > /sys/class/net/vmbr1/bridge/forward_delay 2>/dev/null || true
echo -e "${GREEN}✓${NC} Bridge configuré"

# 4. Vérifier que le container a bien le DNS
echo "4. Configuration DNS dans le container..."
pct exec $CTID -- bash -c 'cat > /etc/resolv.conf <<EOF
nameserver 8.8.8.8
nameserver 8.8.4.4
nameserver 192.168.1.254
EOF'
echo -e "${GREEN}✓${NC} DNS configuré"

# 5. Redémarrer l'interface réseau du container
echo "5. Redémarrage réseau container..."
pct exec $CTID -- ip link set eth0 down 2>/dev/null || true
pct exec $CTID -- ip link set eth0 up 2>/dev/null || true
sleep 2
echo -e "${GREEN}✓${NC} Interface redémarrée"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TESTS FINAUX"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

sleep 2

echo -n "Test ping gateway depuis container: "
if pct exec $CTID -- ping -c 2 192.168.1.254 >/dev/null 2>&1; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ ÉCHEC${NC}"
fi

echo -n "Test ping Internet depuis container: "
if pct exec $CTID -- ping -c 2 8.8.8.8 >/dev/null 2>&1; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ ÉCHEC${NC}"
fi

echo -n "Test résolution DNS depuis container: "
if pct exec $CTID -- ping -c 2 google.com >/dev/null 2>&1; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ ÉCHEC${NC}"
fi

echo ""

# Vérifier le résultat final
if pct exec $CTID -- ping -c 2 8.8.8.8 >/dev/null 2>&1; then
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║              ✅ RÉSEAU FONCTIONNEL !                           ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Le container a maintenant accès à Internet !"
    echo ""
    echo "Pour rendre les changements permanents, ajoutez dans /etc/sysctl.conf:"
    echo "  net.ipv4.ip_forward=1"
    echo ""
    echo "Puis: sysctl -p"
    echo ""
    echo "Vous pouvez maintenant continuer l'installation manuellement:"
    echo "  pct enter $CTID"
    echo "  cd /opt"
    echo "  # Puis suivre les étapes d'installation"
else
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║              ⚠ PROBLÈME PERSISTANT                            ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Le problème réseau persiste. Causes possibles:"
    echo "  1. Firewall sur le routeur WiFi qui bloque"
    echo "  2. Configuration WiFi qui ne permet pas le bridge"
    echo "  3. Isolation WiFi activée (AP isolation)"
    echo ""
    echo "Solutions à essayer:"
    echo "  1. Vérifier les paramètres du point d'accès WiFi"
    echo "  2. Désactiver l'isolation AP/client isolation"
    echo "  3. Utiliser vmbr0 (réseau filaire) à la place"
fi
