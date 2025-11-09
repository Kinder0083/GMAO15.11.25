#!/usr/bin/env bash

###############################################################################
# Correction rapide du réseau pour container 102
# À exécuter depuis le serveur Proxmox
###############################################################################

CTID=102

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Correction Réseau Container $CTID                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Configurer le DNS dans le container
echo "▶ Configuration du DNS..."
pct exec $CTID -- bash -c 'cat > /etc/resolv.conf <<EOF
nameserver 8.8.8.8
nameserver 8.8.4.4
nameserver 1.1.1.1
EOF'

# Vérifier et configurer la passerelle si nécessaire
echo "▶ Vérification de la passerelle..."

# Obtenir la configuration réseau du container
GATEWAY=$(pct exec $CTID -- ip route | grep default | awk '{print $3}')

if [[ -z "$GATEWAY" ]]; then
    echo "⚠ Aucune passerelle détectée"
    echo "Veuillez entrer l'adresse IP de votre passerelle (routeur):"
    echo "Exemple: 192.168.1.1 ou 10.0.0.1"
    read -p "Gateway IP: " GW_IP
    
    if [[ -n "$GW_IP" ]]; then
        pct exec $CTID -- ip route add default via $GW_IP
        echo "✓ Passerelle configurée: $GW_IP"
    fi
else
    echo "✓ Passerelle détectée: $GATEWAY"
fi

echo ""
echo "▶ Test de connectivité..."

# Tester le DNS
if pct exec $CTID -- ping -c 2 8.8.8.8 >/dev/null 2>&1; then
    echo "✓ Connexion Internet OK"
else
    echo "✗ Pas de connexion Internet"
    echo ""
    echo "Solutions possibles:"
    echo "1. Vérifier la configuration réseau de Proxmox"
    echo "2. Vérifier le firewall (pve-firewall status)"
    echo "3. Redémarrer le container: pct restart $CTID"
    exit 1
fi

# Tester la résolution DNS
if pct exec $CTID -- ping -c 2 google.com >/dev/null 2>&1; then
    echo "✓ Résolution DNS OK"
else
    echo "✗ DNS ne fonctionne pas"
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║               ✅ RÉSEAU CORRIGÉ !                              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Vous pouvez maintenant relancer l'installation depuis l'étape du clonage:"
echo ""
echo "pct exec $CTID -- bash <<'APPEOF'
cd /opt
rm -rf gmao-iris 2>/dev/null || true

# Remplacez par votre token et repo
GITHUB_TOKEN='VOTRE_TOKEN'
GITHUB_USER='VOTRE_USER'
REPO_NAME='VOTRE_REPO'
BRANCH='main'

GIT_URL=\"https://\${GITHUB_TOKEN}@github.com/\${GITHUB_USER}/\${REPO_NAME}.git\"

git clone -b \$BRANCH \$GIT_URL gmao-iris || {
    echo 'Erreur: Impossible de cloner le dépôt'
    exit 1
}

echo '✓ Dépôt cloné avec succès'
APPEOF"
