#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     DIAGNOSTIC ULTRA-DÉTAILLÉ - Identification du bug         ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

cd /opt/gmao-iris/backend

cat > /tmp/diagnostic_ultra.py <<'EOFPY'
import sys
sys.path.insert(0, '/opt/gmao-iris/backend')

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from auth import get_password_hash, verify_password
from passlib.context import CryptContext

async def diagnostic():
    print("═══════════════════════════════════════════════════════════════")
    print("ÉTAPE 1 : Connexion à MongoDB")
    print("═══════════════════════════════════════════════════════════════")
    
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client.gmao_iris
    
    print("✓ Connecté à MongoDB")
    print("")
    
    print("═══════════════════════════════════════════════════════════════")
    print("ÉTAPE 2 : Recherche de l'utilisateur buenogy@gmail.com")
    print("═══════════════════════════════════════════════════════════════")
    
    user = await db.users.find_one({"email": "buenogy@gmail.com"})
    
    if not user:
        print("❌ UTILISATEUR NON TROUVÉ DANS LA BASE")
        print("\nListe de tous les emails dans la base :")
        all_users = await db.users.find({}, {"email": 1}).to_list(100)
        for u in all_users:
            print(f"  - {u.get('email')}")
        return
    
    print(f"✓ Utilisateur trouvé")
    print(f"  Email: {user['email']}")
    print(f"  Role: {user['role']}")
    print(f"  Actif: {user['actif']}")
    print("")
    
    print("═══════════════════════════════════════════════════════════════")
    print("ÉTAPE 3 : Analyse du mot de passe hashé")
    print("═══════════════════════════════════════════════════════════════")
    
    if 'password' not in user:
        print("❌ AUCUN CHAMP PASSWORD DANS L'UTILISATEUR")
        return
    
    stored_hash = user['password']
    print(f"✓ Hash trouvé")
    print(f"  Type: {type(stored_hash)}")
    print(f"  Longueur: {len(stored_hash)}")
    print(f"  Début: {stored_hash[:30]}...")
    print(f"  Est un hash bcrypt valide: {stored_hash.startswith('$2b$')}")
    print("")
    
    print("═══════════════════════════════════════════════════════════════")
    print("ÉTAPE 4 : Test avec auth.verify_password (celle utilisée par le backend)")
    print("═══════════════════════════════════════════════════════════════")
    
    test_password = "nmrojvbvgb"
    print(f"Mot de passe testé: '{test_password}'")
    print(f"Longueur: {len(test_password)}")
    
    try:
        result = verify_password(test_password, stored_hash)
        if result:
            print("✅ verify_password() = TRUE - MOT DE PASSE CORRECT")
        else:
            print("❌ verify_password() = FALSE - MOT DE PASSE INCORRECT")
            print("\n🔍 Test avec des variations...")
            
            variations = [
                "nmrojvbvgb ",  # avec espace
                " nmrojvbvgb",  # avec espace avant
                "Nmrojvbvgb",   # première lettre majuscule
                "NMROJVBVGB",   # tout majuscule
            ]
            
            for var in variations:
                if verify_password(var, stored_hash):
                    print(f"✅ TROUVÉ ! Le bon mot de passe est : '{var}'")
                    break
            else:
                print("❌ Aucune variation ne fonctionne")
    except Exception as e:
        print(f"❌ ERREUR lors de verify_password: {e}")
        import traceback
        traceback.print_exc()
    
    print("")
    
    print("═══════════════════════════════════════════════════════════════")
    print("ÉTAPE 5 : Test avec CryptContext directement")
    print("═══════════════════════════════════════════════════════════════")
    
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
    
    try:
        result = pwd_context.verify(test_password, stored_hash)
        if result:
            print("✅ CryptContext.verify() = TRUE")
        else:
            print("❌ CryptContext.verify() = FALSE")
    except Exception as e:
        print(f"❌ ERREUR: {e}")
    
    print("")
    
    print("═══════════════════════════════════════════════════════════════")
    print("ÉTAPE 6 : Recréation avec le mot de passe")
    print("═══════════════════════════════════════════════════════════════")
    
    print("Suppression et recréation de l'utilisateur...")
    await db.users.delete_one({"email": "buenogy@gmail.com"})
    
    # Hasher le mot de passe
    new_hash = get_password_hash("nmrojvbvgb")
    
    # Vérifier IMMÉDIATEMENT avant d'insérer
    immediate_check = verify_password("nmrojvbvgb", new_hash)
    print(f"Vérification immédiate du nouveau hash: {immediate_check}")
    
    if not immediate_check:
        print("❌ ERREUR CRITIQUE: Le hash créé ne peut pas être vérifié !")
        print("Il y a un problème avec les fonctions get_password_hash / verify_password")
        return
    
    # Créer l'utilisateur
    new_user = {
        "email": "buenogy@gmail.com",
        "password": new_hash,
        "prenom": "Support",
        "nom": "Admin",
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
    
    await db.users.insert_one(new_user)
    print("✓ Utilisateur recréé")
    
    # Re-récupérer depuis la base
    user_check = await db.users.find_one({"email": "buenogy@gmail.com"})
    
    # Vérifier à nouveau
    final_check = verify_password("nmrojvbvgb", user_check['password'])
    print(f"Vérification après insertion en base: {final_check}")
    
    if not final_check:
        print("❌ LE HASH A CHANGÉ APRÈS INSERTION DANS MONGODB !")
        print(f"Hash avant: {new_hash[:50]}...")
        print(f"Hash après: {user_check['password'][:50]}...")
    else:
        print("✅ Le hash est identique avant et après insertion")
    
    print("")
    print("═══════════════════════════════════════════════════════════════")
    print("RÉSUMÉ DU DIAGNOSTIC")
    print("═══════════════════════════════════════════════════════════════")

try:
    asyncio.run(diagnostic())
except Exception as e:
    print(f"ERREUR FATALE: {e}")
    import traceback
    traceback.print_exc()
EOFPY

source venv/bin/activate
python3 /tmp/diagnostic_ultra.py

echo ""
echo "Appuyez sur Entrée pour continuer..."
read

rm -f /tmp/diagnostic_ultra.py
