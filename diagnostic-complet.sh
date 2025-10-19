#!/bin/bash

###############################################################################
# DIAGNOSTIC ULTRA-COMPLET - GMAO IRIS
# Ce script va identifier EXACTEMENT où ça bloque
###############################################################################

echo "═══════════════════════════════════════════════════════════════"
echo "  🔍 DIAGNOSTIC COMPLET - GMAO IRIS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Fonction pour les tests
test_step() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "TEST: $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# TEST 1: Vérifier qu'on est dans le container
test_step "1. Vérification du container"
if [ ! -d "/opt/gmao-iris" ]; then
    echo "❌ ERREUR: Ce script doit être exécuté DANS le container"
    echo "   Utilisez: pct enter <CTID>"
    exit 1
fi
echo "✅ Dans le container"
echo ""

# TEST 2: Vérifier MongoDB
test_step "2. MongoDB"
if systemctl is-active --quiet mongod; then
    echo "✅ MongoDB est actif"
    
    # Tester la connexion
    if mongosh --quiet --eval "db.version()" > /dev/null 2>&1; then
        echo "✅ Connexion MongoDB OK"
        
        # Lister les bases
        echo ""
        echo "Bases de données:"
        mongosh --quiet --eval "db.adminCommand('listDatabases').databases.forEach(function(db){ print('  - ' + db.name + ' (' + db.sizeOnDisk + ' bytes)'); })"
    else
        echo "❌ Impossible de se connecter à MongoDB"
    fi
else
    echo "❌ MongoDB n'est PAS actif"
    echo "   Démarrage..."
    systemctl start mongod
    sleep 3
fi
echo ""

# TEST 3: Configuration backend
test_step "3. Configuration Backend (.env)"
if [ -f "/opt/gmao-iris/backend/.env" ]; then
    echo "✅ Fichier .env existe"
    source /opt/gmao-iris/backend/.env
    echo ""
    echo "Configuration:"
    echo "  MONGO_URL: ${MONGO_URL:-NON DÉFINI}"
    echo "  DB_NAME: ${DB_NAME:-NON DÉFINI}"
    echo "  PORT: ${PORT:-NON DÉFINI}"
    echo "  HOST: ${HOST:-NON DÉFINI}"
    
    if [ -z "$MONGO_URL" ]; then
        echo "⚠️  MONGO_URL non défini!"
    fi
    if [ -z "$DB_NAME" ]; then
        echo "⚠️  DB_NAME non défini!"
    fi
else
    echo "❌ Fichier .env NON TROUVÉ"
fi
echo ""

# TEST 4: Utilisateurs dans la base
test_step "4. Utilisateurs dans la base de données"
DB_NAME=${DB_NAME:-gmao_iris}
USER_COUNT=$(mongosh --quiet "$DB_NAME" --eval "db.users.countDocuments({})" 2>/dev/null || echo "0")
echo "Base de données: $DB_NAME"
echo "Nombre d'utilisateurs: $USER_COUNT"

if [ "$USER_COUNT" -gt 0 ]; then
    echo ""
    echo "Liste des utilisateurs:"
    mongosh --quiet "$DB_NAME" --eval "db.users.find({}, {email: 1, role: 1, statut: 1, _id: 0}).forEach(function(u){ print('  📧 ' + u.email + ' - ' + u.role + ' - ' + (u.statut || 'NO STATUS')); })"
else
    echo "❌ AUCUN utilisateur trouvé dans $DB_NAME"
fi
echo ""

# TEST 5: Backend supervisor
test_step "5. Backend (Supervisor)"
if supervisorctl status gmao-iris-backend | grep -q RUNNING; then
    echo "✅ Backend est RUNNING"
    
    # Vérifier le port
    if netstat -tlnp 2>/dev/null | grep -q ":8001"; then
        echo "✅ Backend écoute sur le port 8001"
    else
        echo "⚠️  Backend ne semble pas écouter sur le port 8001"
    fi
else
    echo "❌ Backend n'est PAS en cours d'exécution"
    echo ""
    echo "Statut:"
    supervisorctl status gmao-iris-backend
fi
echo ""

# TEST 6: Logs backend récents
test_step "6. Logs Backend (20 dernières lignes)"
echo "STDOUT:"
tail -20 /var/log/gmao-iris-backend.out.log 2>/dev/null || echo "Fichier non trouvé"
echo ""
echo "STDERR:"
tail -20 /var/log/gmao-iris-backend.err.log 2>/dev/null || echo "Fichier non trouvé"
echo ""

# TEST 7: Test direct de l'API backend
test_step "7. Test API Backend (direct)"
echo "Test de l'endpoint /api/auth/login avec curl..."
echo ""

# Créer un fichier de test temporaire
cat > /tmp/test_login.json <<'EOF'
{
  "email": "buenogy@gmail.com",
  "password": "Admin2024!"
}
EOF

RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d @/tmp/test_login.json 2>&1)

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | grep -v "HTTP_CODE:")

echo "Code HTTP: $HTTP_CODE"
echo "Réponse:"
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"

if [ "$HTTP_CODE" = "200" ]; then
    echo ""
    echo "✅ Backend répond correctement (200 OK)"
    echo "✅ Le BACKEND FONCTIONNE !"
elif [ "$HTTP_CODE" = "401" ]; then
    echo ""
    echo "❌ Backend retourne 401 (Unauthorized)"
    echo "   PROBLÈME: Email/mot de passe incorrect OU problème de vérification"
else
    echo ""
    echo "❌ Problème avec le backend (Code: $HTTP_CODE)"
fi

rm -f /tmp/test_login.json
echo ""

# TEST 8: Nginx
test_step "8. Nginx"
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx est actif"
    
    # Tester la configuration
    if nginx -t > /dev/null 2>&1; then
        echo "✅ Configuration Nginx valide"
    else
        echo "⚠️  Configuration Nginx a des erreurs:"
        nginx -t
    fi
    
    # Vérifier le port 80
    if netstat -tlnp 2>/dev/null | grep -q ":80"; then
        echo "✅ Nginx écoute sur le port 80"
    else
        echo "⚠️  Nginx ne semble pas écouter sur le port 80"
    fi
else
    echo "❌ Nginx n'est PAS actif"
fi
echo ""

# TEST 9: Configuration Nginx
test_step "9. Configuration Nginx GMAO"
if [ -f "/etc/nginx/sites-enabled/gmao-iris" ]; then
    echo "✅ Configuration gmao-iris existe"
    echo ""
    echo "Contenu (partie API):"
    grep -A 10 "location /api" /etc/nginx/sites-enabled/gmao-iris
else
    echo "❌ Configuration gmao-iris NON TROUVÉE"
fi
echo ""

# TEST 10: Frontend
test_step "10. Frontend Build"
if [ -d "/opt/gmao-iris/frontend/build" ]; then
    echo "✅ Répertoire build existe"
    
    # Vérifier index.html
    if [ -f "/opt/gmao-iris/frontend/build/index.html" ]; then
        echo "✅ index.html existe"
    else
        echo "❌ index.html NON TROUVÉ"
    fi
else
    echo "❌ Répertoire build NON TROUVÉ"
fi
echo ""

# TEST 11: Variables d'environnement frontend
test_step "11. Configuration Frontend"
if [ -f "/opt/gmao-iris/frontend/.env" ]; then
    echo "✅ Fichier .env frontend existe"
    echo ""
    cat /opt/gmao-iris/frontend/.env
else
    echo "❌ Fichier .env frontend NON TROUVÉ"
fi
echo ""

# TEST 12: Test complet via Nginx
test_step "12. Test via Nginx (comme le navigateur)"
CONTAINER_IP=$(hostname -I | awk '{print $1}')
echo "IP du container: $CONTAINER_IP"
echo "Test de l'endpoint via Nginx..."
echo ""

RESPONSE_NGINX=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST http://$CONTAINER_IP/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"buenogy@gmail.com","password":"Admin2024!"}' 2>&1)

HTTP_CODE_NGINX=$(echo "$RESPONSE_NGINX" | grep "HTTP_CODE:" | cut -d: -f2)
BODY_NGINX=$(echo "$RESPONSE_NGINX" | grep -v "HTTP_CODE:")

echo "Code HTTP: $HTTP_CODE_NGINX"
echo "Réponse:"
echo "$BODY_NGINX" | python3 -m json.tool 2>/dev/null || echo "$BODY_NGINX"

if [ "$HTTP_CODE_NGINX" = "200" ]; then
    echo ""
    echo "✅✅✅ Nginx fonctionne correctement !"
    echo "✅ L'APPLICATION FONCTIONNE !"
    echo ""
    echo "⚠️  Si vous ne pouvez toujours pas vous connecter depuis votre navigateur,"
    echo "    le problème vient de votre réseau/firewall/configuration DNS"
elif [ "$HTTP_CODE_NGINX" = "502" ]; then
    echo ""
    echo "❌ Erreur 502 Bad Gateway"
    echo "   Nginx ne peut pas joindre le backend"
else
    echo ""
    echo "❌ Problème avec Nginx (Code: $HTTP_CODE_NGINX)"
fi
echo ""

# RÉSUMÉ FINAL
echo "═══════════════════════════════════════════════════════════════"
echo "  📊 RÉSUMÉ DU DIAGNOSTIC"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Vérifier les problèmes critiques
CRITICAL_ISSUES=0

if ! systemctl is-active --quiet mongod; then
    echo "❌ MongoDB n'est pas actif"
    CRITICAL_ISSUES=$((CRITICAL_ISSUES + 1))
fi

if [ "$USER_COUNT" -eq 0 ]; then
    echo "❌ Aucun utilisateur dans la base $DB_NAME"
    CRITICAL_ISSUES=$((CRITICAL_ISSUES + 1))
fi

if ! supervisorctl status gmao-iris-backend | grep -q RUNNING; then
    echo "❌ Backend ne tourne pas"
    CRITICAL_ISSUES=$((CRITICAL_ISSUES + 1))
fi

if ! systemctl is-active --quiet nginx; then
    echo "❌ Nginx n'est pas actif"
    CRITICAL_ISSUES=$((CRITICAL_ISSUES + 1))
fi

if [ "$HTTP_CODE" != "200" ]; then
    echo "❌ Backend retourne $HTTP_CODE au lieu de 200"
    CRITICAL_ISSUES=$((CRITICAL_ISSUES + 1))
fi

echo ""
if [ $CRITICAL_ISSUES -eq 0 ]; then
    echo "✅✅✅ TOUT FONCTIONNE CORRECTEMENT !"
    echo ""
    echo "Si vous ne pouvez toujours pas vous connecter:"
    echo "1. Vérifiez l'URL dans votre navigateur"
    echo "2. Videz le cache du navigateur (Ctrl+Shift+R)"
    echo "3. Vérifiez que vous utilisez: http://$CONTAINER_IP"
    echo "4. Essayez depuis un autre appareil sur le même réseau"
else
    echo "⚠️  $CRITICAL_ISSUES problème(s) critique(s) détecté(s)"
    echo ""
    echo "PARTAGEZ CE DIAGNOSTIC COMPLET POUR OBTENIR DE L'AIDE"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
