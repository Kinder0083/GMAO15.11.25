#!/bin/bash

###############################################################################
# CORRECTION FINALE - Configuration Frontend
# Le problème: Frontend appelle directement le backend sur port 8001
# La solution: Frontend doit passer par Nginx sur port 80
###############################################################################

echo "═══════════════════════════════════════════════════════════════"
echo "  🔧 CORRECTION CONFIGURATION FRONTEND"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Vérifier qu'on est dans le container
if [ ! -d "/opt/gmao-iris" ]; then
    echo "❌ ERREUR: Ce script doit être exécuté DANS le container"
    exit 1
fi

# Obtenir l'IP du container
CONTAINER_IP=$(hostname -I | awk '{print $1}')
echo "IP du container: $CONTAINER_IP"
echo ""

echo "📋 ÉTAPE 1: Correction du .env frontend"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Sauvegarder l'ancien
cp /opt/gmao-iris/frontend/.env /opt/gmao-iris/frontend/.env.backup

# Créer le nouveau .env CORRECT
cat > /opt/gmao-iris/frontend/.env <<EOF
REACT_APP_BACKEND_URL=http://${CONTAINER_IP}
NODE_ENV=production
EOF

echo "Configuration AVANT (incorrecte):"
cat /opt/gmao-iris/frontend/.env.backup
echo ""
echo "Configuration APRÈS (correcte):"
cat /opt/gmao-iris/frontend/.env
echo ""
echo "✅ Configuration corrigée"
echo ""

echo "📋 ÉTAPE 2: Rebuild du frontend"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd /opt/gmao-iris/frontend

echo "Rebuilding... (cela peut prendre 1-2 minutes)"
yarn build > /tmp/yarn_build.log 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Build réussi"
else
    echo "❌ Erreur lors du build"
    echo "Logs:"
    tail -20 /tmp/yarn_build.log
    exit 1
fi
echo ""

echo "📋 ÉTAPE 3: Vérification Nginx"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Vérifier la configuration Nginx
if nginx -t > /dev/null 2>&1; then
    echo "✅ Configuration Nginx valide"
else
    echo "⚠️  Configuration Nginx a des erreurs"
    nginx -t
fi

# Redémarrer Nginx
systemctl restart nginx
sleep 2

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx redémarré"
else
    echo "❌ Problème avec Nginx"
    systemctl status nginx
    exit 1
fi
echo ""

echo "📋 ÉTAPE 4: Test de connexion"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test via Nginx (comme le ferait le navigateur maintenant)
echo "Test du endpoint via Nginx..."
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST http://${CONTAINER_IP}/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"buenogy@gmail.com","password":"Admin2024!"}' 2>&1)

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Test réussi ! Code HTTP: 200"
else
    echo "❌ Test échoué. Code HTTP: $HTTP_CODE"
    echo "$RESPONSE"
fi
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "  ✅ CORRECTION TERMINÉE !"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "🌐 Ouvrez votre navigateur sur:"
echo "   http://${CONTAINER_IP}"
echo ""
echo "🔐 Connectez-vous avec:"
echo "   Email: buenogy@gmail.com"
echo "   Mot de passe: Admin2024!"
echo ""
echo "OU"
echo ""
echo "   Email: admin@gmao-iris.local"
echo "   Mot de passe: Admin2024!"
echo ""
echo "💡 IMPORTANT:"
echo "   - Videz le cache du navigateur (Ctrl+Shift+R ou Cmd+Shift+R)"
echo "   - Si ça ne marche toujours pas, fermez et rouvrez le navigateur"
echo "   - Le problème était que le frontend appelait directement le port 8001"
echo "   - Maintenant il passe correctement par Nginx (port 80)"
echo ""
echo "═══════════════════════════════════════════════════════════════"
