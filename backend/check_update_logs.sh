#!/bin/bash

# Script pour consulter les logs de mise à jour

echo "═══════════════════════════════════════════════"
echo "  LOGS DE MISE À JOUR - Dernières 50 lignes"
echo "═══════════════════════════════════════════════"
echo ""

if [ -f "/tmp/update_process.log" ]; then
    echo "📋 Fichier de log trouvé: /tmp/update_process.log"
    echo ""
    tail -n 50 /tmp/update_process.log
else
    echo "⚠️  Aucun fichier de log trouvé à /tmp/update_process.log"
    echo ""
    echo "Recherche dans les logs supervisor..."
    echo ""
    tail -n 100 /var/log/supervisor/backend.out.log | grep -i "mise à jour\|update\|erreur"
fi

echo ""
echo "═══════════════════════════════════════════════"
echo "  LOGS BACKEND (recherche 'update' et 'erreur')"
echo "═══════════════════════════════════════════════"
echo ""
tail -n 100 /var/log/supervisor/backend.err.log | grep -E "update|Update|erreur|Erreur|ERROR|Exception"
