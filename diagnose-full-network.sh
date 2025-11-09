#!/usr/bin/env bash

###############################################################################
# Diagnostic complet Proxmox + Container
# Vérifie la configuration réseau côté Proxmox ET container
###############################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

CTID=102

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Diagnostic Réseau Complet - Proxmox + CT $CTID         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PARTIE 1: Configuration Proxmox (Hôte)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. Bridges disponibles
echo -e "${BLUE}[1] Bridges réseau${NC}"
ip link show | grep -E "vmbr[0-9]" | awk -F': ' '{print $2}' | while read bridge; do
    STATE=$(ip link show $bridge | grep -o "state [A-Z]*" | awk '{print $2}')
    IP=$(ip addr show $bridge 2>/dev/null | grep "inet " | awk '{print $2}')
    echo "  $bridge: État=$STATE IP=$IP"
done
echo ""

# 2. Configuration de vmbr1
echo -e "${BLUE}[2] Configuration vmbr1${NC}"
ip addr show vmbr1 2>/dev/null || echo "  ✗ vmbr1 n'existe pas"
echo ""

# 3. Routes sur Proxmox
echo -e "${BLUE}[3] Table de routage Proxmox${NC}"
ip route | grep vmbr1 || echo "  ✗ Aucune route via vmbr1"
echo ""

# 4. Firewall Proxmox
echo -e "${BLUE}[4] Firewall Proxmox${NC}"
pve-firewall status 2>/dev/null || echo "  N/A"
echo ""

# 5. Fichier de configuration réseau
echo -e "${BLUE}[5] Configuration /etc/network/interfaces${NC}"
grep -A 10 "iface vmbr1" /etc/network/interfaces 2>/dev/null || echo "  ✗ vmbr1 non configuré dans interfaces"
echo ""

# 6. NAT/Masquerading
echo -e "${BLUE}[6] Règles NAT (iptables)${NC}"
iptables -t nat -L POSTROUTING -n -v | grep vmbr1 || echo "  ✗ Pas de NAT pour vmbr1"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "PARTIE 2: Configuration Container $CTID"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 7. Configuration réseau du container dans Proxmox
echo -e "${BLUE}[7] Config CT dans Proxmox${NC}"
pct config $CTID | grep net0
echo ""

# 8. État du container
echo -e "${BLUE}[8] État du container${NC}"
pct status $CTID
echo ""

# 9. Configuration réseau dans le container
echo -e "${BLUE}[9] Interfaces réseau dans CT${NC}"
pct exec $CTID -- ip addr show 2>/dev/null || echo "  ✗ Container arrêté ou inaccessible"
echo ""

echo -e "${BLUE}[10] Routes dans CT${NC}"
pct exec $CTID -- ip route 2>/dev/null || echo "  ✗ Aucune route"
echo ""

echo -e "${BLUE}[11] DNS dans CT${NC}"
pct exec $CTID -- cat /etc/resolv.conf 2>/dev/null || echo "  ✗ Impossible de lire resolv.conf"
echo ""

# 10. Tests de connectivité
echo -e "${BLUE}[12] Test connectivité${NC}"

echo -n "  Ping gateway depuis Proxmox: "
GATEWAY=$(ip route | grep default | awk '{print $3}' | head -1)
if ping -c 1 -W 2 $GATEWAY >/dev/null 2>&1; then
    echo -e "${GREEN}OK${NC} ($GATEWAY)"
else
    echo -e "${RED}ÉCHEC${NC}"
fi

echo -n "  Ping Internet depuis Proxmox: "
if ping -c 1 -W 2 8.8.8.8 >/dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}ÉCHEC${NC}"
fi

echo -n "  Ping depuis Container: "
if pct exec $CTID -- ping -c 1 -W 2 8.8.8.8 >/dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}ÉCHEC - PAS DE RÉSEAU${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ANALYSE ET RECOMMANDATIONS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Analyse
VMBR1_EXISTS=$(ip link show vmbr1 >/dev/null 2>&1 && echo "yes" || echo "no")
VMBR1_HAS_IP=$(ip addr show vmbr1 2>/dev/null | grep "inet " >/dev/null && echo "yes" || echo "no")
VMBR1_UP=$(ip link show vmbr1 2>/dev/null | grep "state UP" >/dev/null && echo "yes" || echo "no")
NAT_CONFIGURED=$(iptables -t nat -L POSTROUTING -n | grep vmbr1 >/dev/null && echo "yes" || echo "no")

if [[ "$VMBR1_EXISTS" == "no" ]]; then
    echo -e "${RED}✗ PROBLÈME: vmbr1 n'existe pas !${NC}"
    echo ""
    echo "  Solution: Créer vmbr1 dans /etc/network/interfaces"
    echo ""
    
elif [[ "$VMBR1_UP" == "no" ]]; then
    echo -e "${RED}✗ PROBLÈME: vmbr1 existe mais n'est pas UP${NC}"
    echo ""
    echo "  Solution: "
    echo "    ifup vmbr1"
    echo ""
    
elif [[ "$VMBR1_HAS_IP" == "no" ]]; then
    echo -e "${YELLOW}⚠ ATTENTION: vmbr1 n'a pas d'adresse IP${NC}"
    echo ""
    echo "  Si c'est un bridge NAT, il doit avoir une IP"
    echo "  Exemple de configuration dans /etc/network/interfaces:"
    echo ""
    echo "    auto vmbr1"
    echo "    iface vmbr1 inet static"
    echo "        address 10.10.10.1/24"
    echo "        bridge-ports none"
    echo "        bridge-stp off"
    echo "        bridge-fd 0"
    echo ""
    echo "        post-up   echo 1 > /proc/sys/net/ipv4/ip_forward"
    echo "        post-up   iptables -t nat -A POSTROUTING -s 10.10.10.0/24 -o vmbr0 -j MASQUERADE"
    echo "        post-down iptables -t nat -D POSTROUTING -s 10.10.10.0/24 -o vmbr0 -j MASQUERADE"
    echo ""
    
elif [[ "$NAT_CONFIGURED" == "no" ]]; then
    echo -e "${YELLOW}⚠ ATTENTION: Pas de NAT configuré pour vmbr1${NC}"
    echo ""
    echo "  Si vmbr1 est un réseau privé, il faut configurer le NAT"
    echo ""
    echo "  Commandes à exécuter:"
    VMBR1_NET=$(ip addr show vmbr1 | grep "inet " | awk '{print $2}' | cut -d'/' -f1 | sed 's/\.[0-9]*$/.0/')
    VMBR1_CIDR=$(ip addr show vmbr1 | grep "inet " | awk '{print $2}' | cut -d'/' -f2)
    MAIN_BRIDGE=$(ip route | grep default | grep -o "dev [a-z0-9]*" | awk '{print $2}')
    
    echo "    # Activer le forwarding IP"
    echo "    echo 1 > /proc/sys/net/ipv4/ip_forward"
    echo ""
    echo "    # Configurer le NAT (adaptez vmbr0 si nécessaire)"
    echo "    iptables -t nat -A POSTROUTING -s ${VMBR1_NET}/${VMBR1_CIDR} -o ${MAIN_BRIDGE:-vmbr0} -j MASQUERADE"
    echo ""
    echo "  Pour rendre permanent, ajoutez dans /etc/network/interfaces:"
    echo "    post-up   echo 1 > /proc/sys/net/ipv4/ip_forward"
    echo "    post-up   iptables -t nat -A POSTROUTING -s ${VMBR1_NET}/${VMBR1_CIDR} -o ${MAIN_BRIDGE:-vmbr0} -j MASQUERADE"
    echo ""
else
    echo -e "${GREEN}✓ Configuration de base correcte${NC}"
    echo ""
    echo "  Le problème peut venir de:"
    echo "  1. Firewall bloquant"
    echo "  2. Configuration du container incorrecte"
    echo "  3. Problème de routage"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
