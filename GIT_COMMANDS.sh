#!/bin/bash

# ========================================
# Commandes Git pour sauvegarder sur GitHub
# ========================================

echo "🚀 Préparation du commit pour GitHub"
echo ""

# 1. Vérification pré-commit
echo "1️⃣ Vérification pré-commit..."
./PRE_COMMIT_CHECK.sh
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Vérifications échouées. Arrêt."
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 2. Voir les fichiers modifiés
echo "2️⃣ Fichiers modifiés :"
git status --short
echo ""

# 3. Afficher les statistiques
echo "3️⃣ Statistiques :"
git diff --stat
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Demander confirmation
read -p "📦 Voulez-vous procéder au commit ? (o/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[OoYy]$ ]]; then
    echo "❌ Commit annulé."
    exit 0
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 4. Ajouter tous les fichiers
echo "4️⃣ Ajout des fichiers..."
git add .
echo "✅ Fichiers ajoutés"
echo ""

# 5. Commit avec le message préparé
echo "5️⃣ Création du commit..."
git commit -F COMMIT_MESSAGE.txt
if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du commit"
    exit 1
fi
echo "✅ Commit créé"
echo ""

# 6. Afficher le commit
echo "6️⃣ Détails du commit :"
git log -1 --stat
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Demander confirmation pour le push
read -p "🚀 Voulez-vous pousser vers GitHub ? (o/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[OoYy]$ ]]; then
    echo "⏸️  Push reporté. Vous pouvez le faire plus tard avec :"
    echo "   git push origin main"
    exit 0
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 7. Push vers GitHub
echo "7️⃣ Push vers GitHub..."
git push origin main
if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du push"
    echo ""
    echo "Possible causes :"
    echo "  - Authentification GitHub requise"
    echo "  - Pas de connexion internet"
    echo "  - Branche non à jour"
    echo ""
    echo "Essayez :"
    echo "  git pull --rebase origin main"
    echo "  git push origin main"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ SUCCÈS !"
echo ""
echo "📦 Modifications sauvegardées sur GitHub !"
echo ""
echo "🌐 Voir sur GitHub :"
echo "   https://github.com/Kinder0083/GMAO"
echo ""
echo "📋 Prochaines étapes :"
echo "   1. Aller sur votre serveur Proxmox"
echo "   2. cd /opt/gmao-iris"
echo "   3. git pull origin main"
echo "   4. cd frontend && yarn build"
echo "   5. sudo systemctl reload nginx"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
