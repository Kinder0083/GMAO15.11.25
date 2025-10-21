#!/bin/bash
###############################################################################
# Diagnostic Connexion Externe - GMAO Iris
###############################################################################

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     DIAGNOSTIC CONNEXION EXTERNE - GMAO IRIS                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# 1. Vérifier les variables .env
echo "1️⃣ Vérification configuration backend (.env):"
echo "─────────────────────────────────────────────"
cd /app/backend
if [ -f .env ]; then
    echo "✅ Fichier .env trouvé"
    echo ""
    echo "SECRET_KEY présent: $(grep -q '^SECRET_KEY=' .env && echo '✅ OUI' || echo '❌ NON')"
    echo "ALGORITHM présent: $(grep -q '^ALGORITHM=' .env && echo '✅ OUI' || echo '❌ NON')"
    echo "ACCESS_TOKEN_EXPIRE_MINUTES présent: $(grep -q '^ACCESS_TOKEN_EXPIRE_MINUTES=' .env && echo '✅ OUI' || echo '❌ NON')"
    
    # Afficher les valeurs (masquer le SECRET_KEY)
    echo ""
    echo "Valeurs configurées:"
    grep '^SECRET_KEY=' .env | sed 's/SECRET_KEY="\(.\{10\}\).*/SECRET_KEY="\1..." (masqué)/'
    grep '^ALGORITHM=' .env
    grep '^ACCESS_TOKEN_EXPIRE_MINUTES=' .env
else
    echo "❌ Fichier .env NON TROUVÉ !"
fi

echo ""
echo "2️⃣ Vérification auth.py (variable JWT):"
echo "─────────────────────────────────────────────"
if grep -q 'SECRET_KEY = os.environ.get("SECRET_KEY"' /app/backend/auth.py; then
    echo "✅ auth.py utilise bien SECRET_KEY (correct)"
elif grep -q 'SECRET_KEY = os.environ.get("JWT_SECRET_KEY"' /app/backend/auth.py; then
    echo "❌ auth.py utilise JWT_SECRET_KEY (INCORRECT - à corriger)"
else
    echo "⚠️ Variable SECRET_KEY non trouvée dans auth.py"
fi

echo ""
echo "3️⃣ Test création token JWT:"
echo "─────────────────────────────────────────────"
python3 << 'PYEOF'
import sys
sys.path.insert(0, '/app/backend')

try:
    from auth import create_access_token
    token = create_access_token({"sub": "test@example.com"})
    print(f"✅ Token créé avec succès")
    print(f"Token (20 premiers caractères): {token[:20]}...")
except Exception as e:
    print(f"❌ Erreur création token: {e}")
PYEOF

echo ""
echo "4️⃣ Test login avec l'API:"
echo "─────────────────────────────────────────────"
curl -s -X POST "http://localhost:8001/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@gmao.com","password":"Admin123!"}' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'access_token' in data:
        print('✅ Login local réussi')
        print(f'Token reçu: {data[\"access_token\"][:20]}...')
    else:
        print(f'❌ Login échoué: {data}')
except:
    print('❌ Erreur parsing réponse')
"

echo ""
echo "5️⃣ Vérification CORS:"
echo "─────────────────────────────────────────────"
grep -n 'CORS_ORIGINS' /app/backend/.env || echo "⚠️ CORS_ORIGINS non défini"
grep -n 'allow_origins' /app/backend/server.py | head -2

echo ""
echo "6️⃣ Logs backend (30 dernières lignes):"
echo "─────────────────────────────────────────────"
tail -n 30 /var/log/supervisor/backend.err.log | tail -15

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                     DIAGNOSTIC TERMINÉ                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📝 Pour tester depuis l'extérieur:"
echo "   1. Utilisez votre IP publique ou DNS"
echo "   2. Assurez-vous que le port est bien redirigé"
echo "   3. Testez avec: curl -v https://votre-domaine/api/auth/login"
echo ""
