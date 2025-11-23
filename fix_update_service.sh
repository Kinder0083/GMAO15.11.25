#!/bin/bash

# Script de correction du service de mise à jour
# Corrige l'erreur 500 lors du redémarrage des services

echo "🔧 Correction du service de mise à jour..."
echo "=========================================="

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Vérifier si le script est exécuté en root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Ce script doit être exécuté en root${NC}"
    echo "Utilisez: sudo bash fix_update_service.sh"
    exit 1
fi

# Chemin du fichier
FILE="/app/backend/update_service.py"

# Vérifier que le fichier existe
if [ ! -f "$FILE" ]; then
    echo -e "${RED}❌ Fichier non trouvé: $FILE${NC}"
    exit 1
fi

# Créer un backup
BACKUP_FILE="${FILE}.backup.$(date +%Y%m%d_%H%M%S)"
echo -e "${YELLOW}📦 Création du backup...${NC}"
cp "$FILE" "$BACKUP_FILE"
echo -e "${GREEN}✅ Backup créé: $BACKUP_FILE${NC}"

# Vérifier si la modification est déjà appliquée
if grep -q "Environnement sans Git, passage à l'étape suivante" "$FILE"; then
    echo -e "${GREEN}✅ La modification est déjà appliquée !${NC}"
    echo "Aucune action nécessaire."
    exit 0
fi

# Appliquer la modification
echo -e "${YELLOW}🔨 Application de la correction...${NC}"

# Créer un fichier temporaire avec la correction
cat > /tmp/update_service_patch.py << 'PATCH_EOF'
                if pull_process.returncode != 0:
                    error_msg = pull_stderr.decode()
                    logger.warning(f"⚠️ Git pull a échoué: {error_msg}")
                    # Ne pas bloquer si Git n'est pas configuré (environnement sans Git)
                    if "No remote" in error_msg or "no remote" in error_msg or "not a git repository" in error_msg:
                        logger.info("ℹ️ Environnement sans Git, passage à l'étape suivante")
                    else:
                        logger.error(f"❌ Échec du git pull: {error_msg}")
                        return {
                            "success": False,
                            "message": "Échec du téléchargement de la mise à jour",
                            "error": error_msg
                        }
PATCH_EOF

# Utiliser Python pour faire le remplacement
python3 << 'PYTHON_EOF'
import re

# Lire le fichier
with open('/app/backend/update_service.py', 'r') as f:
    content = f.read()

# Pattern à rechercher (ancien code)
old_pattern = r'''                if pull_process\.returncode != 0:
                    logger\.error\(f"❌ Échec du git pull: \{pull_stderr\.decode\(\)\}"\)
                    return \{
                        "success": False,
                        "message": "Échec du téléchargement de la mise à jour",
                        "error": pull_stderr\.decode\(\)
                    \}'''

# Nouveau code
new_code = '''                if pull_process.returncode != 0:
                    error_msg = pull_stderr.decode()
                    logger.warning(f"⚠️ Git pull a échoué: {error_msg}")
                    # Ne pas bloquer si Git n'est pas configuré (environnement sans Git)
                    if "No remote" in error_msg or "no remote" in error_msg or "not a git repository" in error_msg:
                        logger.info("ℹ️ Environnement sans Git, passage à l'étape suivante")
                    else:
                        logger.error(f"❌ Échec du git pull: {error_msg}")
                        return {
                            "success": False,
                            "message": "Échec du téléchargement de la mise à jour",
                            "error": error_msg
                        }'''

# Remplacer
content_modified = re.sub(old_pattern, new_code, content)

# Vérifier si le remplacement a été fait
if content != content_modified:
    # Sauvegarder
    with open('/app/backend/update_service.py', 'w') as f:
        f.write(content_modified)
    print("SUCCESS")
else:
    print("FAIL")
PYTHON_EOF

# Vérifier le résultat
if [ $? -eq 0 ] && grep -q "Environnement sans Git, passage à l'étape suivante" "$FILE"; then
    echo -e "${GREEN}✅ Modification appliquée avec succès${NC}"
else
    echo -e "${RED}❌ Échec de l'application de la modification${NC}"
    echo "Restauration du backup..."
    cp "$BACKUP_FILE" "$FILE"
    echo -e "${YELLOW}⚠️ Fichier restauré à partir du backup${NC}"
    exit 1
fi

# Redémarrer le backend
echo -e "${YELLOW}🔄 Redémarrage du backend...${NC}"
supervisorctl restart backend
sleep 3

# Vérifier le statut
if supervisorctl status backend | grep -q RUNNING; then
    echo -e "${GREEN}✅ Backend redémarré avec succès${NC}"
else
    echo -e "${RED}❌ Erreur lors du redémarrage du backend${NC}"
    echo "Vérifiez les logs: tail -50 /var/log/supervisor/backend.err.log"
    exit 1
fi

# Résumé
echo ""
echo "=========================================="
echo -e "${GREEN}🎉 Correction appliquée avec succès !${NC}"
echo ""
echo "📋 Résumé:"
echo "  - Backup: $BACKUP_FILE"
echo "  - Fichier modifié: $FILE"
echo "  - Backend redémarré: ✅"
echo ""
echo "💡 Vous pouvez maintenant redémarrer les services depuis l'interface"
echo "   sans rencontrer l'erreur 500."
echo ""
echo "🔙 Pour restaurer le backup en cas de problème:"
echo "   cp $BACKUP_FILE $FILE"
echo "   supervisorctl restart backend"
echo "=========================================="
