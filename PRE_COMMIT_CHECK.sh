#!/bin/bash

# Script de vérification avant commit
# Vérifie que toutes les corrections critiques sont en place

echo "🔍 Vérification pré-commit..."
echo ""

ERRORS=0

# Vérification 1: Pas de EntityType.SYSTEM
echo "1️⃣ Vérification EntityType.SYSTEM..."
if grep -r "EntityType\.SYSTEM" backend/server.py backend/models.py 2>/dev/null; then
    echo "❌ ERREUR: EntityType.SYSTEM trouvé (doit être EntityType.SETTINGS)"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ OK: Pas de EntityType.SYSTEM"
fi
echo ""

# Vérification 2: Pas de ActionType.OTHER
echo "2️⃣ Vérification ActionType.OTHER..."
if grep -r "ActionType\.OTHER" backend/server.py backend/models.py 2>/dev/null; then
    echo "❌ ERREUR: ActionType.OTHER trouvé (doit être ActionType.UPDATE ou autre)"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ OK: Pas de ActionType.OTHER"
fi
echo ""

# Vérification 3: Pas de doublon route updates/apply
echo "3️⃣ Vérification doublon route updates/apply..."
COUNT=$(grep -c '@api_router.post("/updates/apply")' backend/server.py 2>/dev/null || echo "0")
if [ "$COUNT" -gt 1 ]; then
    echo "❌ ERREUR: $COUNT définitions de /updates/apply trouvées (doit être 1)"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ OK: Une seule route /updates/apply"
fi
echo ""

# Vérification 4: Fichier config.js existe
echo "4️⃣ Vérification fichier config.js..."
if [ ! -f "frontend/src/utils/config.js" ]; then
    echo "❌ ERREUR: frontend/src/utils/config.js manquant"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ OK: config.js présent"
fi
echo ""

# Vérification 5: GitConflictDialog existe
echo "5️⃣ Vérification GitConflictDialog.jsx..."
if [ ! -f "frontend/src/components/Common/GitConflictDialog.jsx" ]; then
    echo "❌ ERREUR: GitConflictDialog.jsx manquant"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ OK: GitConflictDialog.jsx présent"
fi
echo ""

# Vérification 6: Modèles SMTP
echo "6️⃣ Vérification modèles SMTP..."
if ! grep -q "class SMTPConfig" backend/models.py 2>/dev/null; then
    echo "❌ ERREUR: Modèles SMTP manquants dans models.py"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ OK: Modèles SMTP présents"
fi
echo ""

# Vérification 7: Endpoints SMTP
echo "7️⃣ Vérification endpoints SMTP..."
if ! grep -q '/smtp/config' backend/server.py 2>/dev/null; then
    echo "❌ ERREUR: Endpoints SMTP manquants dans server.py"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ OK: Endpoints SMTP présents"
fi
echo ""

# Vérification 8: Section SMTP dans SpecialSettings
echo "8️⃣ Vérification section SMTP dans SpecialSettings..."
if ! grep -q "Configuration SMTP" frontend/src/pages/SpecialSettings.jsx 2>/dev/null; then
    echo "❌ ERREUR: Section SMTP manquante dans SpecialSettings.jsx"
    ERRORS=$((ERRORS + 1))
else
    echo "✅ OK: Section SMTP présente"
fi
echo ""

# Résultat final
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $ERRORS -eq 0 ]; then
    echo "✅ TOUTES LES VÉRIFICATIONS PASSÉES !"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📦 Prêt pour le commit !"
    echo ""
    echo "Commandes suggérées :"
    echo "  git add ."
    echo "  git commit -F COMMIT_MESSAGE.txt"
    echo "  git push origin main"
    echo ""
    exit 0
else
    echo "❌ $ERRORS ERREUR(S) DÉTECTÉE(S) !"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "⚠️  Corrigez les erreurs avant de commit !"
    echo ""
    exit 1
fi
