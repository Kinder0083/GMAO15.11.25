#!/bin/bash

echo "═══════════════════════════════════════════════════════════════"
echo "  DIAGNOSTIC APPROFONDI - Test de connexion"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Script Python pour tester directement
cat > /tmp/test_connection.py <<'EOFPY'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

async def test_auth():
    print("1️⃣  Connexion à MongoDB...")
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client.gmao_iris
    
    print("2️⃣  Recherche de l'utilisateur 'buenogy@gmail.com'...")
    user = await db.users.find_one({"email": "buenogy@gmail.com"})
    
    if not user:
        print("   ❌ UTILISATEUR NON TROUVÉ")
        return
    
    print(f"   ✓ Utilisateur trouvé")
    print(f"   - Email: {user.get('email')}")
    print(f"   - Role: {user.get('role')}")
    print(f"   - Actif: {user.get('actif')}")
    print(f"   - Password hash présent: {'Oui' if user.get('password') else 'Non'}")
    
    if user.get('password'):
        password_hash = user['password']
        print(f"   - Hash commence par: {password_hash[:20]}...")
        print(f"   - Longueur du hash: {len(password_hash)}")
    
    print("")
    print("3️⃣  Test de vérification du mot de passe...")
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    
    test_password = "nmrojvbvgb"
    print(f"   - Mot de passe testé: {test_password}")
    
    try:
        is_valid = pwd_context.verify(test_password, user['password'])
        if is_valid:
            print("   ✅ MOT DE PASSE VALIDE")
        else:
            print("   ❌ MOT DE PASSE INVALIDE")
            
            # Test avec d'autres mots de passe courants
            print("")
            print("   Test avec d'autres mots de passe...")
            for pwd in ["Admin123!", "admin123", "password", "nmrojvbvgb "]:
                if pwd_context.verify(pwd, user['password']):
                    print(f"   ⚠️  Le mot de passe correct est : {pwd}")
                    break
    except Exception as e:
        print(f"   ❌ ERREUR lors de la vérification: {str(e)}")
    
    print("")
    print("4️⃣  Vérification de la structure de l'endpoint login...")
    print("   Recherche dans le code backend...")
    
    # Lire le code du endpoint login
    try:
        with open('/opt/gmao-iris/backend/server.py', 'r') as f:
            content = f.read()
            
            # Chercher la fonction de login
            if 'def login' in content:
                print("   ✓ Fonction login trouvée")
                
                # Vérifier les méthodes utilisées
                if 'verify_password' in content:
                    print("   ✓ Utilise verify_password")
                if 'pwd_context.verify' in content:
                    print("   ✓ Utilise pwd_context.verify")
                    
    except Exception as e:
        print(f"   ⚠️  Impossible de lire server.py: {e}")

asyncio.run(test_auth())
EOFPY

cd /opt/gmao-iris/backend
source venv/bin/activate
python3 /tmp/test_connection.py

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Test manuel avec le endpoint backend"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Test direct du endpoint
echo "Test 1 : Connexion avec buenogy@gmail.com"
curl -s -X POST "http://localhost:8001/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"buenogy@gmail.com","password":"nmrojvbvgb"}' | python3 -m json.tool

echo ""
echo "Test 2 : Connexion avec admin@gmao-iris.local"
curl -s -X POST "http://localhost:8001/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@gmao-iris.local","password":"Admin123!"}' | python3 -m json.tool

echo ""
echo "═══════════════════════════════════════════════════════════════"
