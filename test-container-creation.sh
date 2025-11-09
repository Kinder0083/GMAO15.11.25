#!/usr/bin/env bash

###############################################################################
# Test de création de container avec vmbr1
# Teste la commande pct create avant l'installation complète
###############################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Test de création de container avec vmbr1              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Trouver un ID libre
CTID=200
while pct status $CTID >/dev/null 2>&1; do
    ((CTID++))
done

echo "Test avec container ID: $CTID"
echo ""

# Détecter le template
TEMPLATE=$(ls /var/lib/vz/template/cache/*debian-12*.tar.* 2>/dev/null | head -1 | xargs basename)

if [[ -z "$TEMPLATE" ]]; then
    echo -e "${RED}✗${NC} Pas de template Debian 12 trouvé"
    exit 1
fi

echo -e "${GREEN}✓${NC} Template: $TEMPLATE"
echo ""

# Configuration de test
TEST_IP="192.168.1.200"
TEST_GW="192.168.1.254"
BRIDGE="vmbr1"

echo "Configuration de test:"
echo "  IP: $TEST_IP/24"
echo "  Gateway: $TEST_GW"
echo "  Bridge: $BRIDGE"
echo ""

read -p "Mot de passe root pour le test: " ROOT_PASS

echo ""
echo -e "${BLUE}▶${NC} Création du container de test..."
echo ""

# Commande de création
CMD="pct create $CTID local:vztmpl/$TEMPLATE \
  --arch amd64 \
  --cores 1 \
  --hostname test-gmao \
  --memory 512 \
  --net0 name=eth0,bridge=$BRIDGE,ip=${TEST_IP}/24,gw=${TEST_GW} \
  --onboot 0 \
  --ostype debian \
  --rootfs local-lvm:4 \
  --unprivileged 1 \
  --features nesting=1 \
  --password '$ROOT_PASS'"

echo "Commande:"
echo "$CMD"
echo ""

if eval "$CMD"; then
    echo ""
    echo -e "${GREEN}✓${NC} Container créé avec succès !"
    echo ""
    
    # Démarrer
    echo -e "${BLUE}▶${NC} Démarrage..."
    pct start $CTID
    sleep 5
    
    # Configurer DNS
    pct exec $CTID -- bash -c 'cat > /etc/resolv.conf <<EOF
nameserver 8.8.8.8
nameserver 8.8.4.4
EOF'
    
    # Tester réseau
    echo ""
    echo -e "${BLUE}▶${NC} Test réseau..."
    echo ""
    pct exec $CTID -- ip addr show eth0
    echo ""
    pct exec $CTID -- ip route
    echo ""
    
    if pct exec $CTID -- ping -c 2 8.8.8.8 2>/dev/null; then
        echo ""
        echo -e "${GREEN}✓✓✓ SUCCÈS ! Le réseau fonctionne ! ✓✓✓${NC}"
        echo ""
        echo "Vous pouvez maintenant lancer l'installation complète:"
        echo "  bash gmao-iris-v1.1.2-install-auto.sh"
    else
        echo ""
        echo -e "${RED}✗${NC} Le container n'a pas de connexion Internet"
        echo ""
        echo "Diagnostic:"
        pct enter $CTID
    fi
    
    echo ""
    read -p "Supprimer le container de test ? (y/n): " DELETE
    if [[ $DELETE =~ ^[Yy]$ ]]; then
        pct stop $CTID
        pct destroy $CTID
        echo -e "${GREEN}✓${NC} Container de test supprimé"
    fi
else
    echo ""
    echo -e "${RED}✗${NC} Échec de la création"
    echo ""
    echo "Erreur détectée. Vérifiez:"
    echo "  1. Le template existe"
    echo "  2. Le storage local-lvm est disponible"
    echo "  3. L'IP $TEST_IP/24 et la gateway $TEST_GW sont corrects"
fi
