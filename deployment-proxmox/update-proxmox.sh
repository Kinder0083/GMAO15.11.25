#!/bin/bash

echo "=========================================="
echo "Mise à jour GMAO Iris sur Proxmox"
echo "=========================================="
echo ""

# Vérifier qu'on est dans le bon dossier
if [ ! -f "docker-compose.yml" ] && [ ! -f "package.json" ]; then
    echo "❌ Erreur: Ce script doit être exécuté depuis le dossier racine de l'application"
    echo "   Exemple: cd /opt/gmao-iris && ./deployment-proxmox/update-proxmox.sh"
    exit 1
fi

echo "📦 Dossier actuel: $(pwd)"
echo ""

# Sauvegarder la configuration actuelle
echo "💾 Sauvegarde de la configuration actuelle..."
if [ -f "frontend/.env" ]; then
    cp frontend/.env frontend/.env.backup.$(date +%Y%m%d_%H%M%S)
    echo "   ✅ Sauvegarde de frontend/.env créée"
fi

# Mettre à jour le code
echo ""
echo "🔄 Mise à jour du code depuis GitHub..."
read -p "Continuer avec 'git pull' ? (oui/non) : " CONFIRM_PULL

if [ "$CONFIRM_PULL" = "oui" ]; then
    git pull origin main
    if [ $? -eq 0 ]; then
        echo "   ✅ Code mis à jour"
    else
        echo "   ❌ Erreur lors du git pull"
        exit 1
    fi
else
    echo "   ⚠️  Mise à jour du code ignorée"
fi

# Restaurer le fichier .env
echo ""
echo "🔧 Restauration de la configuration..."
LATEST_BACKUP=$(ls -t frontend/.env.backup.* 2>/dev/null | head -1)
if [ -n "$LATEST_BACKUP" ]; then
    cp "$LATEST_BACKUP" frontend/.env
    echo "   ✅ Configuration restaurée depuis: $LATEST_BACKUP"
else
    echo "   ⚠️  Aucune sauvegarde trouvée, vérifiez frontend/.env manuellement"
fi

# Redémarrer les services
echo ""
echo "🔄 Redémarrage des services..."
echo "   Quelle méthode utilisez-vous ?"
echo "   1) Docker Compose"
echo "   2) Supervisor"
echo "   3) Systemd"
echo "   4) PM2"
echo "   5) Aucune (je le ferai manuellement)"
read -p "Choix (1-5) : " RESTART_METHOD

case $RESTART_METHOD in
    1)
        echo "   🐳 Redémarrage Docker Compose..."
        docker-compose down
        docker-compose up -d --build
        echo "   ✅ Services Docker redémarrés"
        ;;
    2)
        echo "   📦 Redémarrage Supervisor..."
        sudo supervisorctl restart all
        echo "   ✅ Services Supervisor redémarrés"
        ;;
    3)
        echo "   🔧 Redémarrage Systemd..."
        sudo systemctl restart gmao-frontend
        sudo systemctl restart gmao-backend
        echo "   ✅ Services Systemd redémarrés"
        ;;
    4)
        echo "   ⚡ Redémarrage PM2..."
        pm2 restart all
        echo "   ✅ Services PM2 redémarrés"
        ;;
    5)
        echo "   ⚠️  N'oubliez pas de redémarrer vos services manuellement !"
        ;;
    *)
        echo "   ❌ Choix invalide"
        ;;
esac

echo ""
echo "=========================================="
echo "✅ MISE À JOUR TERMINÉE"
echo "=========================================="
echo ""
echo "🔍 Vérifications recommandées:"
echo "   1. Testez l'accès à l'application"
echo "   2. Vérifiez les logs pour d'éventuelles erreurs"
echo "   3. Testez les fonctionnalités principales"
echo ""
echo "📝 Commandes utiles:"
echo "   - Voir les logs backend: tail -f /var/log/supervisor/backend.err.log"
echo "   - Voir les logs frontend: tail -f /var/log/supervisor/frontend.err.log"
echo "   - Voir les logs Docker: docker-compose logs -f"
echo ""
