#!/bin/bash

# Script de vérification de santé GMAO Iris
# Version: 1.0

echo "╔══════════════════════════════════════════════════════════╗"
echo "║        Vérification de santé GMAO Iris                  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_ok() {
    echo -e "${GREEN}[✓]${NC} $1"
}

check_error() {
    echo -e "${RED}[✗]${NC} $1"
    ERRORS=$((ERRORS+1))
}

check_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

ERRORS=0

echo "=== Services ==="

# MongoDB
if systemctl is-active --quiet mongod; then
    check_ok "MongoDB est actif"
else
    check_error "MongoDB est arrêté"
fi

# Nginx
if systemctl is-active --quiet nginx; then
    check_ok "Nginx est actif"
else
    check_error "Nginx est arrêté"
fi

# Backend
if supervisorctl status gmao-iris-backend 2>/dev/null | grep -q RUNNING; then
    check_ok "Backend est actif"
else
    check_error "Backend est arrêté"
fi

echo ""
echo "=== Ports ==="

# Port 80 (Nginx)
if netstat -tuln 2>/dev/null | grep -q ":80 " || ss -tuln 2>/dev/null | grep -q ":80 "; then
    check_ok "Port 80 (Frontend) est ouvert"
else
    check_error "Port 80 n'est pas en écoute"
fi

# Port 8001 (Backend)
if netstat -tuln 2>/dev/null | grep -q ":8001 " || ss -tuln 2>/dev/null | grep -q ":8001 "; then
    check_ok "Port 8001 (Backend) est ouvert"
else
    check_error "Port 8001 n'est pas en écoute"
fi

# Port 27017 (MongoDB)
if netstat -tuln 2>/dev/null | grep -q ":27017 " || ss -tuln 2>/dev/null | grep -q ":27017 "; then
    check_ok "Port 27017 (MongoDB) est ouvert"
else
    check_error "Port 27017 n'est pas en écoute"
fi

echo ""
echo "=== Configuration ==="

# Fichier .env
if [ -f "/opt/gmao-iris/frontend/.env" ]; then
    check_ok "Fichier .env existe"
    BACKEND_URL=$(grep REACT_APP_BACKEND_URL /opt/gmao-iris/frontend/.env 2>/dev/null | cut -d'=' -f2)
    if [ -n "$BACKEND_URL" ]; then
        echo "   URL Backend: $BACKEND_URL"
    fi
else
    check_error "Fichier .env manquant"
fi

# Frontend build
if [ -d "/opt/gmao-iris/frontend/build" ]; then
    check_ok "Frontend compilé"
else
    check_warning "Frontend build manquant"
fi

echo ""
echo "=== Tests de connexion ==="

# Test backend
if curl -s http://localhost:8001/api/updates/version > /dev/null 2>&1; then
    check_ok "Backend répond"
else
    check_warning "Backend ne répond pas"
fi

# Test MongoDB
if mongosh --quiet --eval "db.serverStatus().ok" > /dev/null 2>&1; then
    check_ok "MongoDB accessible"
else
    check_error "MongoDB inaccessible"
fi

# Test frontend
if curl -s http://localhost > /dev/null 2>&1; then
    check_ok "Frontend accessible"
else
    check_error "Frontend inaccessible"
fi

echo ""
echo "=== Espace disque ==="
df -h / | tail -1 | awk '{print "Utilisation: "$5" ("$3" utilisés sur "$2")"}'

echo ""
echo "════════════════════════════════════════════════════════════"

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ Tous les services sont opérationnels${NC}"
    exit 0
else
    echo -e "${RED}❌ $ERRORS erreur(s) détectée(s)${NC}"
    echo ""
    echo "Commandes utiles pour corriger:"
    echo "  - MongoDB: chown -R mongodb:mongodb /var/lib/mongodb /var/log/mongodb"
    echo "             rm -f /var/lib/mongodb/mongod.lock"
    echo "             systemctl restart mongod"
    echo "  - Nginx:   systemctl restart nginx"
    echo "  - Backend: supervisorctl restart gmao-iris-backend"
    exit 1
fi
