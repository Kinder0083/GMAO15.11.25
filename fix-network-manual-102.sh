#!/usr/bin/env bash

###############################################################################
# Correction réseau pour container 102
# Configure une IP statique si DHCP ne fonctionne pas
###############################################################################

CTID=102

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

msg() { echo -e "${BLUE}▶${NC} $1"; }
ok() { echo -e "${GREEN}✓${NC} $1"; }
err() { echo -e "${RED}✗${NC} $1"; exit 1; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Correction Réseau Container $CTID                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Détecter la configuration du bridge vmbr1 sur Proxmox
msg "Détection de la configuration réseau de vmbr1..."
PROXMOX_IP=$(ip addr show vmbr1 | grep "inet " | awk '{print $2}' | cut -d'/' -f1)
PROXMOX_CIDR=$(ip addr show vmbr1 | grep "inet " | awk '{print $2}')
GATEWAY=$(ip route | grep "default.*vmbr1" | awk '{print $3}')

if [[ -z "$GATEWAY" ]]; then
    # Si pas de gateway par défaut, prendre l'IP du bridge comme gateway
    GATEWAY=$PROXMOX_IP
fi

echo "  IP Proxmox (vmbr1): $PROXMOX_CIDR"
echo "  Gateway détectée: $GATEWAY"
echo ""

# Proposer une configuration
warn "Le DHCP ne semble pas fonctionner sur vmbr1"
echo ""
echo "Choisissez le mode de configuration:"
echo "  1) IP Statique (recommandé)"
echo "  2) Réessayer avec DHCP"
echo ""
read -p "Votre choix [1]: " CHOICE
CHOICE=${CHOICE:-1}

if [[ "$CHOICE" == "2" ]]; then
    msg "Configuration DHCP..."
    
    # Arrêter le container
    pct stop $CTID
    sleep 2
    
    # Modifier la config pour forcer DHCP
    pct set $CTID -net0 name=eth0,bridge=vmbr1,firewall=0,ip=dhcp
    
    # Redémarrer
    pct start $CTID
    sleep 5
    
    # Installer dhclient dans le container
    pct exec $CTID -- bash -c "apt-get update -qq && apt-get install -y -qq isc-dhcp-client"
    
    # Demander une IP DHCP
    pct exec $CTID -- dhclient eth0
    sleep 3
    
    # Vérifier
    CONTAINER_IP=$(pct exec $CTID -- hostname -I | awk '{print $1}')
    
    if [[ -n "$CONTAINER_IP" && "$CONTAINER_IP" != "127.0.0.1" ]]; then
        ok "DHCP configuré avec succès: $CONTAINER_IP"
    else
        err "DHCP n'a pas fonctionné. Relancez le script et choisissez l'option 1 (IP Statique)"
    fi
    
else
    # Configuration IP Statique
    msg "Configuration IP Statique..."
    echo ""
    
    # Extraire le réseau et le masque
    NETWORK_PREFIX=$(echo $PROXMOX_CIDR | cut -d'.' -f1-3)
    CIDR_MASK=$(echo $PROXMOX_CIDR | cut -d'/' -f2)
    
    # Proposer une IP par défaut
    SUGGESTED_IP="${NETWORK_PREFIX}.150"
    
    echo "Configuration réseau détectée:"
    echo "  Réseau: ${NETWORK_PREFIX}.0/${CIDR_MASK}"
    echo "  Gateway: $GATEWAY"
    echo ""
    
    read -p "Adresse IP pour le container [$SUGGESTED_IP]: " CONTAINER_IP
    CONTAINER_IP=${CONTAINER_IP:-$SUGGESTED_IP}
    
    read -p "Masque CIDR [/$CIDR_MASK]: " CONTAINER_CIDR
    CONTAINER_CIDR=${CONTAINER_CIDR:-$CIDR_MASK}
    
    read -p "Gateway [$GATEWAY]: " CONTAINER_GW
    CONTAINER_GW=${CONTAINER_GW:-$GATEWAY}
    
    echo ""
    echo "Configuration qui sera appliquée:"
    echo "  IP: ${CONTAINER_IP}/${CONTAINER_CIDR}"
    echo "  Gateway: $CONTAINER_GW"
    echo ""
    read -p "Confirmer ? (y/n): " CONFIRM
    [[ ! $CONFIRM =~ ^[Yy]$ ]] && err "Configuration annulée"
    
    # Arrêter le container
    msg "Arrêt du container..."
    pct stop $CTID
    sleep 2
    
    # Modifier la configuration réseau de Proxmox
    msg "Configuration de l'IP statique..."
    pct set $CTID -net0 name=eth0,bridge=vmbr1,firewall=0,ip=${CONTAINER_IP}/${CONTAINER_CIDR},gw=${CONTAINER_GW}
    
    # Redémarrer le container
    msg "Démarrage du container..."
    pct start $CTID
    sleep 5
    
    # Configurer le DNS
    msg "Configuration du DNS..."
    pct exec $CTID -- bash -c 'cat > /etc/resolv.conf <<EOF
nameserver 8.8.8.8
nameserver 8.8.4.4
nameserver 1.1.1.1
EOF'
    
    # Vérifier la configuration
    msg "Vérification..."
    
    echo ""
    echo "Configuration réseau du container:"
    pct exec $CTID -- ip addr show eth0
    echo ""
    echo "Route par défaut:"
    pct exec $CTID -- ip route
    echo ""
    
    # Test de connectivité
    if pct exec $CTID -- ping -c 2 8.8.8.8 >/dev/null 2>&1; then
        ok "Connexion Internet OK"
        
        if pct exec $CTID -- ping -c 2 google.com >/dev/null 2>&1; then
            ok "Résolution DNS OK"
        else
            warn "DNS ne fonctionne pas"
        fi
    else
        err "Pas de connexion Internet. Vérifiez:
        1. L'IP ${CONTAINER_IP} est dans le bon réseau
        2. La gateway ${CONTAINER_GW} est correcte
        3. Le firewall n'est pas bloquant"
    fi
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║               ✅ RÉSEAU CONFIGURÉ !                            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "IP du container: $CONTAINER_IP"
echo ""
echo "Pour continuer l'installation, relancez le script d'installation"
echo "ou exécutez manuellement les étapes d'installation dans le container."
echo ""
