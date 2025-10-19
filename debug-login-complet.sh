#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     DIAGNOSTIC COMPLET DU FLUX DE CONNEXION                   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

cd /opt/gmao-iris/backend

echo "ÉTAPE 1 : Vérification de la base de données utilisée"
echo "═══════════════════════════════════════════════════════════════"
grep "db = client" server.py
echo ""

echo "ÉTAPE 2 : Liste de toutes les bases MongoDB"
echo "═══════════════════════════════════════════════════════════════"
mongosh --quiet --eval "db.adminCommand('listDatabases').databases.forEach(function(d) { print(d.name); })"
echo ""

echo "ÉTAPE 3 : Comptage des utilisateurs dans chaque base"
echo "═══════════════════════════════════════════════════════════════"
for dbname in $(mongosh --quiet --eval "db.adminCommand('listDatabases').databases.forEach(function(d) { print(d.name); })"); do
    if [[ "$dbname" != "admin" && "$dbname" != "config" && "$dbname" != "local" ]]; then
        count=$(mongosh --quiet $dbname --eval "db.users.countDocuments({})")
        echo "  $dbname : $count utilisateur(s)"
    fi
done
echo ""

echo "ÉTAPE 4 : Ajout de logs de débogage dans le endpoint login"
echo "═══════════════════════════════════════════════════════════════"

# Créer une version modifiée avec des logs
cat > /tmp/test_login_debug.py <<'EOFPY'
import sys
sys.path.insert(0, '/opt/gmao-iris/backend')

from fastapi import FastAPI, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from models import LoginRequest, Token, User
from auth import verify_password, create_access_token, serialize_doc
from datetime import datetime
import os

app = FastAPI()

# Connexion MongoDB
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db_name = os.environ.get('DB_NAME', 'gmao_iris')
db = client[db_name]

print(f"🔍 Configuration:")
print(f"  MongoDB URL: {mongo_url}")
print(f"  DB Name: {db_name}")
print("")

@app.post("/auth/login")
async def login_debug(login_request: LoginRequest):
    """Version debug du endpoint login"""
    print("═══════════════════════════════════════════════════════════════")
    print("NOUVELLE TENTATIVE DE CONNEXION")
    print("═══════════════════════════════════════════════════════════════")
    print(f"Email reçu: '{login_request.email}'")
    print(f"Password reçu: '{login_request.password}'")
    print(f"Longueur password: {len(login_request.password)}")
    print("")
    
    # Recherche de l'utilisateur
    print("1️⃣  Recherche de l'utilisateur dans la base...")
    user = await db.users.find_one({"email": login_request.email})
    
    if not user:
        print("❌ UTILISATEUR NON TROUVÉ")
        print(f"   Recherche effectuée dans: {db_name}.users")
        print(f"   Email cherché: {login_request.email}")
        
        # Liste tous les emails
        all_users = await db.users.find({}, {"email": 1}).to_list(100)
        print(f"   Emails dans la base:")
        for u in all_users:
            print(f"     - {u.get('email')}")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ERREUR: Utilisateur non trouvé"
        )
    
    print(f"✓ Utilisateur trouvé: {user['email']}")
    print(f"  Role: {user['role']}")
    print(f"  Actif: {user.get('actif', 'N/A')}")
    print("")
    
    # Vérification du mot de passe
    print("2️⃣  Vérification du mot de passe...")
    print(f"  Password hash dans DB: {user['password'][:30]}...")
    
    try:
        is_valid = verify_password(login_request.password, user["password"])
        print(f"  Résultat verify_password(): {is_valid}")
        
        if not is_valid:
            print("❌ MOT DE PASSE INVALIDE")
            print(f"   Password fourni: '{login_request.password}'")
            print(f"   Hash en base: {user['password'][:50]}...")
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="ERREUR: Mot de passe incorrect"
            )
        
        print("✓ Mot de passe correct")
        print("")
        
    except Exception as e:
        print(f"❌ EXCEPTION lors de verify_password: {e}")
        raise
    
    # Mise à jour dernière connexion
    print("3️⃣  Mise à jour dernière connexion...")
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"derniereConnexion": datetime.utcnow()}}
    )
    print("✓ Dernière connexion mise à jour")
    print("")
    
    # Création du token
    print("4️⃣  Création du token JWT...")
    access_token = create_access_token(data={"sub": str(user["_id"])})
    print(f"✓ Token créé: {access_token[:50]}...")
    print("")
    
    # Sérialisation de l'utilisateur
    print("5️⃣  Sérialisation de l'utilisateur...")
    try:
        serialized = serialize_doc(user.copy())
        user_obj = User(**serialized)
        print(f"✓ Utilisateur sérialisé")
        print("")
    except Exception as e:
        print(f"❌ ERREUR lors de la sérialisation: {e}")
        raise
    
    print("✅✅✅ CONNEXION RÉUSSIE ✅✅✅")
    print("═══════════════════════════════════════════════════════════════")
    print("")
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user_obj
    )

# Test direct
if __name__ == "__main__":
    import asyncio
    
    async def test():
        req = LoginRequest(email="buenogy@gmail.com", password="nmrojvbvgb")
        try:
            result = await login_debug(req)
            print("\n🎉 RÉSULTAT FINAL:")
            print(f"  Token: {result.access_token[:50]}...")
            print(f"  User: {result.user.email}")
        except Exception as e:
            print(f"\n❌ ERREUR FINALE: {e}")
    
    asyncio.run(test())
EOFPY

echo "Exécution du test de connexion avec débogage complet..."
echo ""
source venv/bin/activate
python3 /tmp/test_login_debug.py

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "ÉTAPE 5 : Test avec curl sur le vrai endpoint"
echo "═══════════════════════════════════════════════════════════════"
echo ""

RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "http://localhost:8001/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"buenogy@gmail.com","password":"nmrojvbvgb"}')

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | grep -v "HTTP_CODE")

echo "Code HTTP: $HTTP_CODE"
echo "Réponse:"
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"

echo ""
echo "═══════════════════════════════════════════════════════════════"

rm -f /tmp/test_login_debug.py
