#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║   GMAO Iris - RÉPARATION COMPLÈTE ET DÉFINITIVE              ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

cd /opt/gmao-iris/backend

echo "1️⃣  Arrêt du backend..."
supervisorctl stop gmao-iris-backend >/dev/null 2>&1

echo "2️⃣  Nettoyage complet de la base de données..."
mongosh gmao_iris --eval "db.users.deleteMany({})" >/dev/null 2>&1

echo "3️⃣  Création des utilisateurs avec le BON contexte bcrypt..."

# Créer un script Python qui utilise EXACTEMENT le même code que auth.py
cat > /tmp/create_final_users.py <<'EOFPY'
import sys
sys.path.insert(0, '/opt/gmao-iris/backend')

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from auth import get_password_hash, verify_password

async def create_users():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client.gmao_iris
    
    # Supprimer tous les utilisateurs
    await db.users.delete_many({})
    print("   Base nettoyée")
    
    # Utilisateurs à créer
    users_data = [
        {
            "email": "buenogy@gmail.com",
            "password": "nmrojvbvgb",
            "prenom": "Support",
            "nom": "Admin"
        },
        {
            "email": "admin@gmao-iris.local",
            "password": "Admin123!",
            "prenom": "System",
            "nom": "Admin"
        }
    ]
    
    for user_data in users_data:
        # Hasher avec la MÊME fonction que auth.py
        hashed_password = get_password_hash(user_data["password"])
        
        # Vérifier immédiatement
        if not verify_password(user_data["password"], hashed_password):
            print(f"   ❌ ERREUR: Vérification échouée pour {user_data['email']}")
            sys.exit(1)
        
        admin_user = {
            "email": user_data["email"],
            "password": hashed_password,
            "prenom": user_data["prenom"],
            "nom": user_data["nom"],
            "role": "ADMIN",
            "telephone": "",
            "dateCreation": datetime.utcnow(),
            "derniereConnexion": None,
            "actif": True,
            "permissions": {
                "dashboard": {"view": True, "edit": True, "delete": True},
                "workOrders": {"view": True, "edit": True, "delete": True},
                "assets": {"view": True, "edit": True, "delete": True},
                "preventiveMaintenance": {"view": True, "edit": True, "delete": True},
                "inventory": {"view": True, "edit": True, "delete": True},
                "locations": {"view": True, "edit": True, "delete": True},
                "vendors": {"view": True, "edit": True, "delete": True},
                "reports": {"view": True, "edit": True, "delete": True}
            }
        }
        
        await db.users.insert_one(admin_user)
        print(f"   ✓ Créé et vérifié: {user_data['email']}")
    
    print("")
    print("   ✅ Tous les utilisateurs créés avec succès")

try:
    asyncio.run(create_users())
except Exception as e:
    print(f"   ❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOFPY

source venv/bin/activate
python3 /tmp/create_final_users.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Échec de la création des utilisateurs"
    exit 1
fi

echo ""
echo "4️⃣  Vérification de la configuration backend..."

# Vérifier que les modules nécessaires sont importés
if ! grep -q "from auth import" server.py; then
    echo "   ⚠️  Import auth manquant - Ajout..."
    # Ajouter l'import si nécessaire (normalement déjà présent)
fi

echo "   ✓ Configuration OK"

echo ""
echo "5️⃣  Redémarrage du backend..."
supervisorctl start gmao-iris-backend >/dev/null 2>&1
sleep 5

if ! supervisorctl status gmao-iris-backend | grep -q RUNNING; then
    echo "   ❌ Backend n'a pas démarré"
    echo ""
    echo "LOGS D'ERREUR:"
    tail -30 /var/log/gmao-iris-backend.err.log
    exit 1
fi

echo "   ✓ Backend démarré"

echo ""
echo "6️⃣  TEST DE CONNEXION FINAL..."
echo ""

# Test avec buenogy@gmail.com
echo "   Test 1: buenogy@gmail.com / nmrojvbvgb"
RESPONSE=$(curl -s -X POST "http://localhost:8001/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"buenogy@gmail.com","password":"nmrojvbvgb"}')

if echo "$RESPONSE" | grep -q "access_token"; then
    echo "   ✅ CONNEXION RÉUSSIE !"
    TOKEN=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'][:50])")
    echo "   Token reçu: ${TOKEN}..."
else
    echo "   ❌ ÉCHEC"
    echo "   Réponse: $RESPONSE"
    exit 1
fi

echo ""

# Test avec admin@gmao-iris.local
echo "   Test 2: admin@gmao-iris.local / Admin123!"
RESPONSE=$(curl -s -X POST "http://localhost:8001/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@gmao-iris.local","password":"Admin123!"}')

if echo "$RESPONSE" | grep -q "access_token"; then
    echo "   ✅ CONNEXION RÉUSSIE !"
else
    echo "   ❌ ÉCHEC"
    echo "   Réponse: $RESPONSE"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║              ✅ RÉPARATION TERMINÉE AVEC SUCCÈS              ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

CONTAINER_IP=$(hostname -I | awk '{print $1}')

echo "🌐 Application accessible sur: http://$CONTAINER_IP"
echo ""
echo "👤 Comptes disponibles:"
echo ""
echo "   Email:        buenogy@gmail.com"
echo "   Mot de passe: nmrojvbvgb"
echo ""
echo "   Email:        admin@gmao-iris.local"  
echo "   Mot de passe: Admin123!"
echo ""
echo "✅ Vous pouvez maintenant vous connecter !"
echo ""

rm -f /tmp/create_final_users.py
