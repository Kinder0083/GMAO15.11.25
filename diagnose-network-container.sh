#!/usr/bin/env bash

###############################################################################
# Diagnostic réseau pour container Proxmox
# À exécuter DANS le container pour vérifier la connectivité
###############################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           Diagnostic Réseau Container Proxmox                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# 1. Configuration IP
echo -e "${BLUE}[1/6]${NC} Configuration IP"
ip addr show eth0
echo ""

# 2. Passerelle par défaut
echo -e "${BLUE}[2/6]${NC} Passerelle (Gateway)"
ip route | grep default || echo -e "${RED}✗ Aucune passerelle configurée${NC}"
echo ""

# 3. Configuration DNS
echo -e "${BLUE}[3/6]${NC} Serveurs DNS"
cat /etc/resolv.conf
echo ""

# 4. Test de ping vers la passerelle
echo -e "${BLUE}[4/6]${NC} Test ping vers la passerelle"
GATEWAY=$(ip route | grep default | awk '{print $3}')
if [[ -n "$GATEWAY" ]]; then
    if ping -c 2 $GATEWAY >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Passerelle $GATEWAY accessible${NC}"
    else
        echo -e "${RED}✗ Passerelle $GATEWAY non accessible${NC}"
    fi
else
    echo -e "${RED}✗ Aucune passerelle configurée${NC}"
fi
echo ""

# 5. Test de résolution DNS
echo -e "${BLUE}[5/6]${NC} Test résolution DNS"
if host google.com >/dev/null 2>&1; then
    echo -e "${GREEN}✓ DNS fonctionne${NC}"
else
    echo -e "${RED}✗ DNS ne fonctionne pas${NC}"
fi
echo ""

# 6. Test connexion Internet
echo -e "${BLUE}[6/6]${NC} Test connexion Internet"
if ping -c 2 8.8.8.8 >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Connexion Internet OK (via IP)${NC}"
else
    echo -e "${RED}✗ Pas de connexion Internet${NC}"
fi

if curl -s --connect-timeout 5 http://google.com >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Accès HTTP OK${NC}"
else
    echo -e "${RED}✗ Pas d'accès HTTP${NC}"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SOLUTIONS POSSIBLES:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Recommandations DNS
if ! grep -q "nameserver" /etc/resolv.conf || ! host google.com >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ CORRIGER LE DNS:${NC}"
    echo "   echo 'nameserver 8.8.8.8' > /etc/resolv.conf"
    echo "   echo 'nameserver 8.8.4.4' >> /etc/resolv.conf"
    echo ""
fi

# Recommandations Gateway
if [[ -z "$GATEWAY" ]]; then
    echo -e "${YELLOW}⚠ AJOUTER UNE PASSERELLE:${NC}"
    echo "   ip route add default via VOTRE_GATEWAY_IP"
    echo "   Exemple: ip route add default via 192.168.1.1"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
