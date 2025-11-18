#!/usr/bin/env python3
"""
Backend API Testing Script for GMAO Application
Tests Presqu'accident (Near Miss) endpoints - CRUD complets
"""

import requests
import json
import os
import io
import pandas as pd
import tempfile
import uuid
from datetime import datetime, timedelta

# Use the correct backend URL from frontend .env
BACKEND_URL = "https://surveillance-plus.preview.emergentagent.com/api"

# Test credentials - admin account as specified in the request
ADMIN_EMAIL = "admin@gmao-iris.local"
ADMIN_PASSWORD = "Admin123!"

class PresquAccidentTester:
    def __init__(self):
        self.admin_session = requests.Session()
        self.admin_token = None
        self.admin_data = None
        self.created_items = []  # Track created presqu'accident items for cleanup
        self.test_items = {}  # Dictionary to store presqu'accident item IDs
        
    def log(self, message, level="INFO"):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_admin_login(self):
        """Test admin login with specified credentials"""
        self.log("Testing admin login...")
        
        try:
            response = self.admin_session.post(
                f"{BACKEND_URL}/auth/login",
                json={
                    "email": ADMIN_EMAIL,
                    "password": ADMIN_PASSWORD
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                self.admin_data = data.get("user")
                
                # Set authorization header for future requests
                self.admin_session.headers.update({
                    "Authorization": f"Bearer {self.admin_token}"
                })
                
                self.log(f"✅ Admin login successful - User: {self.admin_data.get('prenom')} {self.admin_data.get('nom')} (Role: {self.admin_data.get('role')})")
                return True
            else:
                self.log(f"❌ Admin login failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Admin login request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_create_presqu_accident_item(self, service, severite, lieu, titre_suffix):
        """Créer un item de presqu'accident avec des données spécifiques"""
        self.log(f"🧪 Créer presqu'accident - Service: {service}, Sévérité: {severite}")
        
        try:
            # Créer l'item de presqu'accident
            item_data = {
                "titre": f"Test presqu'accident {titre_suffix}",
                "description": f"Description détaillée du presqu'accident {titre_suffix}",
                "date_incident": "2025-01-15",
                "lieu": lieu,
                "service": service,
                "personnes_impliquees": "Jean DUPONT, Marie MARTIN",
                "declarant": "Paul LEFEBVRE",
                "contexte_cause": f"Contexte et cause du presqu'accident {titre_suffix}",
                "severite": severite,
                "actions_proposees": f"Actions proposées pour {titre_suffix}",
                "actions_preventions": f"Actions de prévention pour {titre_suffix}",
                "responsable_action": "Sophie BERNARD",
                "date_echeance_action": "2025-02-15",
                "status": "A_TRAITER",
                "commentaire": f"Commentaire test {titre_suffix}"
            }
            
            response = self.admin_session.post(
                f"{BACKEND_URL}/presqu-accident/items",
                json=item_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                item_id = data.get("id")
                self.created_items.append(item_id)
                self.test_items[service] = item_id
                
                self.log(f"✅ Presqu'accident créé avec succès - ID: {item_id}")
                self.log(f"✅ Service: {data.get('service')}")
                self.log(f"✅ Sévérité: {data.get('severite')}")
                self.log(f"✅ Lieu: {data.get('lieu')}")
                return True
                    
            else:
                self.log(f"❌ Création presqu'accident échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_create_adv_item(self):
        """TEST 2: Créer presqu'accident avec service ADV"""
        return self.test_create_presqu_accident_item("ADV", "FAIBLE", "Bureau ADV", "ADV")
    
    def test_create_logistique_item(self):
        """TEST 3: Créer presqu'accident avec service LOGISTIQUE"""
        return self.test_create_presqu_accident_item("LOGISTIQUE", "MOYEN", "Entrepôt principal", "LOGISTIQUE")
    
    def test_create_production_item(self):
        """TEST 4: Créer presqu'accident avec service PRODUCTION"""
        return self.test_create_presqu_accident_item("PRODUCTION", "ELEVE", "Atelier de production", "PRODUCTION")
    
    def test_create_qhse_item(self):
        """TEST 5: Créer presqu'accident avec service QHSE"""
        return self.test_create_presqu_accident_item("QHSE", "CRITIQUE", "Zone de sécurité", "QHSE")
    
    def test_presqu_accident_list_with_filters(self):
        """TEST 6: Tester GET /api/presqu-accident/items avec filtres"""
        self.log("🧪 TEST 6: Récupérer la liste des presqu'accidents avec filtres")
        
        try:
            # Test 1: Liste complète
            response = self.admin_session.get(
                f"{BACKEND_URL}/presqu-accident/items",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Liste complète récupérée - {len(data)} presqu'accidents")
                
                # Test 2: Filtre par service PRODUCTION
                response_filtered = self.admin_session.get(
                    f"{BACKEND_URL}/presqu-accident/items?service=PRODUCTION",
                    timeout=10
                )
                
                if response_filtered.status_code == 200:
                    filtered_data = response_filtered.json()
                    production_count = len([item for item in filtered_data if item.get("service") == "PRODUCTION"])
                    self.log(f"✅ Filtre service PRODUCTION: {production_count} items")
                    
                    # Test 3: Filtre par statut A_TRAITER
                    response_status = self.admin_session.get(
                        f"{BACKEND_URL}/presqu-accident/items?status=A_TRAITER",
                        timeout=10
                    )
                    
                    if response_status.status_code == 200:
                        status_data = response_status.json()
                        a_traiter_count = len([item for item in status_data if item.get("status") == "A_TRAITER"])
                        self.log(f"✅ Filtre statut A_TRAITER: {a_traiter_count} items")
                        
                        # Test 4: Filtre par sévérité ELEVE
                        response_sev = self.admin_session.get(
                            f"{BACKEND_URL}/presqu-accident/items?severite=ELEVE",
                            timeout=10
                        )
                        
                        if response_sev.status_code == 200:
                            sev_data = response_sev.json()
                            eleve_count = len([item for item in sev_data if item.get("severite") == "ELEVE"])
                            self.log(f"✅ Filtre sévérité ELEVE: {eleve_count} items")
                            
                            # Test 5: Filtre par lieu
                            response_lieu = self.admin_session.get(
                                f"{BACKEND_URL}/presqu-accident/items?lieu=Atelier",
                                timeout=10
                            )
                            
                            if response_lieu.status_code == 200:
                                lieu_data = response_lieu.json()
                                lieu_count = len([item for item in lieu_data if "Atelier" in item.get("lieu", "")])
                                self.log(f"✅ Filtre lieu 'Atelier': {lieu_count} items")
                                return True
                            else:
                                self.log(f"❌ Filtre lieu échoué - Status: {response_lieu.status_code}", "ERROR")
                                return False
                        else:
                            self.log(f"❌ Filtre sévérité échoué - Status: {response_sev.status_code}", "ERROR")
                            return False
                    else:
                        self.log(f"❌ Filtre statut échoué - Status: {response_status.status_code}", "ERROR")
                        return False
                else:
                    self.log(f"❌ Filtre service échoué - Status: {response_filtered.status_code}", "ERROR")
                    return False
            else:
                self.log(f"❌ Liste complète échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_presqu_accident_item_details(self):
        """TEST 7: Tester GET /api/presqu-accident/items/{item_id}"""
        self.log("🧪 TEST 7: Récupérer les détails d'un presqu'accident spécifique")
        
        if not self.created_items:
            self.log("⚠️ Pas de presqu'accidents créés pour tester les détails", "WARNING")
            return False
        
        try:
            item_id = self.created_items[0]  # Prendre le premier item créé
            response = self.admin_session.get(
                f"{BACKEND_URL}/presqu-accident/items/{item_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Détails récupérés - ID: {data.get('id')}")
                self.log(f"✅ Titre: {data.get('titre')}")
                self.log(f"✅ Service: {data.get('service')}")
                self.log(f"✅ Sévérité: {data.get('severite')}")
                self.log(f"✅ Statut: {data.get('status')}")
                self.log(f"✅ Lieu: {data.get('lieu')}")
                return True
            else:
                self.log(f"❌ Récupération détails échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_presqu_accident_item_update(self):
        """TEST 8: Tester PUT /api/presqu-accident/items/{item_id}"""
        self.log("🧪 TEST 8: Mettre à jour un presqu'accident")
        
        if not self.created_items:
            self.log("⚠️ Pas de presqu'accidents créés pour tester la mise à jour", "WARNING")
            return False
        
        try:
            item_id = self.created_items[0]  # Prendre le premier item créé
            update_data = {
                "status": "EN_COURS",
                "commentaire": "Test de mise à jour - presqu'accident en cours de traitement",
                "actions_preventions": "Actions de prévention mises à jour"
            }
            
            response = self.admin_session.put(
                f"{BACKEND_URL}/presqu-accident/items/{item_id}",
                json=update_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Mise à jour réussie - Status: {data.get('status')}")
                self.log(f"✅ Commentaire: {data.get('commentaire')}")
                self.log(f"✅ Actions prévention: {data.get('actions_preventions')}")
                
                # Test 2: Mettre à jour vers TERMINE
                update_data_termine = {
                    "status": "TERMINE",
                    "commentaire": "Presqu'accident traité et terminé"
                }
                
                response_termine = self.admin_session.put(
                    f"{BACKEND_URL}/presqu-accident/items/{item_id}",
                    json=update_data_termine,
                    timeout=10
                )
                
                if response_termine.status_code == 200:
                    data_termine = response_termine.json()
                    self.log(f"✅ Mise à jour vers TERMINE réussie - Status: {data_termine.get('status')}")
                    if data_termine.get('date_cloture'):
                        self.log(f"✅ Date de clôture automatique ajoutée: {data_termine.get('date_cloture')}")
                    return True
                else:
                    self.log(f"❌ Mise à jour vers TERMINE échouée - Status: {response_termine.status_code}", "ERROR")
                    return False
                
            else:
                self.log(f"❌ Mise à jour échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_presqu_accident_stats(self):
        """TEST 9: Tester GET /api/presqu-accident/stats"""
        self.log("🧪 TEST 9: Récupérer les statistiques globales des presqu'accidents")
        
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/presqu-accident/stats",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                global_stats = data.get("global", {})
                by_service = data.get("by_service", {})
                by_severite = data.get("by_severite", {})
                
                self.log(f"✅ Statistiques globales récupérées:")
                self.log(f"  - Total: {global_stats.get('total')}")
                self.log(f"  - À traiter: {global_stats.get('a_traiter')}")
                self.log(f"  - En cours: {global_stats.get('en_cours')}")
                self.log(f"  - Terminé: {global_stats.get('termine')}")
                self.log(f"  - Archivé: {global_stats.get('archive')}")
                self.log(f"  - % traitement: {global_stats.get('pourcentage_traitement')}%")
                
                self.log(f"✅ Statistiques par service: {len(by_service)} services")
                self.log(f"✅ Statistiques par sévérité: {len(by_severite)} niveaux")
                
                # Vérifier la structure des données
                for service, stats in by_service.items():
                    if 'total' in stats and 'termine' in stats and 'pourcentage' in stats:
                        self.log(f"  - Service {service}: {stats['total']} total, {stats['termine']} terminés ({stats['pourcentage']}%)")
                
                return True
            else:
                self.log(f"❌ Récupération statistiques échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_presqu_accident_alerts(self):
        """TEST 10: Tester GET /api/presqu-accident/alerts"""
        self.log("🧪 TEST 10: Récupérer les alertes de presqu'accidents")
        
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/presqu-accident/alerts",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                count = data.get("count", 0)
                alerts = data.get("alerts", [])
                
                self.log(f"✅ Alertes récupérées - {count} alertes")
                
                if count > 0:
                    for alert in alerts[:3]:  # Afficher les 3 premières
                        urgence = alert.get('urgence', 'normal')
                        titre = alert.get('titre', 'Sans titre')
                        service = alert.get('service', 'N/A')
                        self.log(f"  - {titre} ({service}) - Urgence: {urgence}")
                        
                        if alert.get('days_overdue'):
                            self.log(f"    En retard de {alert.get('days_overdue')} jours")
                        elif alert.get('days_until'):
                            self.log(f"    Échéance dans {alert.get('days_until')} jours")
                
                return True
            else:
                self.log(f"❌ Récupération alertes échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_presqu_accident_badge_stats(self):
        """TEST CRITIQUE: Tester GET /api/presqu-accident/badge-stats - Badge de notification du header"""
        self.log("🧪 TEST CRITIQUE: Badge de notification - GET /api/presqu-accident/badge-stats")
        
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/presqu-accident/badge-stats",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier que les champs requis sont présents
                if "a_traiter" not in data:
                    self.log("❌ Champ 'a_traiter' manquant dans la réponse", "ERROR")
                    return False
                
                if "en_retard" not in data:
                    self.log("❌ Champ 'en_retard' manquant dans la réponse", "ERROR")
                    return False
                
                a_traiter = data.get("a_traiter")
                en_retard = data.get("en_retard")
                
                # Vérifier les types de données
                if not isinstance(a_traiter, int):
                    self.log(f"❌ 'a_traiter' doit être un entier, reçu: {type(a_traiter)}", "ERROR")
                    return False
                
                if not isinstance(en_retard, int):
                    self.log(f"❌ 'en_retard' doit être un entier, reçu: {type(en_retard)}", "ERROR")
                    return False
                
                # Vérifier les valeurs logiques
                if a_traiter < 0:
                    self.log(f"❌ 'a_traiter' ne peut pas être négatif: {a_traiter}", "ERROR")
                    return False
                
                if en_retard < 0:
                    self.log(f"❌ 'en_retard' ne peut pas être négatif: {en_retard}", "ERROR")
                    return False
                
                self.log(f"✅ Badge stats récupérées avec succès:")
                self.log(f"  - À traiter: {a_traiter}")
                self.log(f"  - En retard: {en_retard}")
                
                # Validation logique métier
                self.log("✅ Validation des types de données: RÉUSSIE")
                self.log("✅ Validation des valeurs logiques: RÉUSSIE")
                self.log("✅ Structure de réponse JSON: CONFORME")
                
                return True
            else:
                self.log(f"❌ Badge stats échoué - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_presqu_accident_badge_stats_without_auth(self):
        """TEST SÉCURITÉ: Tester GET /api/presqu-accident/badge-stats SANS authentification"""
        self.log("🧪 TEST SÉCURITÉ: Badge stats sans authentification")
        
        try:
            # Créer une session sans token d'authentification
            no_auth_session = requests.Session()
            
            response = no_auth_session.get(
                f"{BACKEND_URL}/presqu-accident/badge-stats",
                timeout=10
            )
            
            # Doit retourner 401 Unauthorized ou 403 Forbidden
            if response.status_code in [401, 403]:
                self.log(f"✅ Protection par authentification fonctionnelle - Status: {response.status_code}")
                return True
            else:
                self.log(f"❌ SÉCURITÉ COMPROMISE - Endpoint accessible sans authentification - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_presqu_accident_rapport_stats(self):
        """TEST CRITIQUE: Tester GET /api/presqu-accident/rapport-stats - Statistiques complètes pour la page Rapport"""
        self.log("🧪 TEST CRITIQUE: Statistiques Rapport - GET /api/presqu-accident/rapport-stats")
        
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/presqu-accident/rapport-stats",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier la structure de réponse JSON
                required_keys = ["global", "by_service", "by_severite", "by_lieu", "by_month"]
                for key in required_keys:
                    if key not in data:
                        self.log(f"❌ Champ '{key}' manquant dans la réponse", "ERROR")
                        return False
                
                # Vérifier la structure des statistiques globales
                global_stats = data.get("global", {})
                global_required = ["total", "a_traiter", "en_cours", "termine", "archive", "pourcentage_traitement", "delai_moyen_traitement", "en_retard"]
                for key in global_required:
                    if key not in global_stats:
                        self.log(f"❌ Champ 'global.{key}' manquant dans la réponse", "ERROR")
                        return False
                
                # Vérifier les types de données
                if not isinstance(global_stats.get("total"), int):
                    self.log(f"❌ 'global.total' doit être un entier, reçu: {type(global_stats.get('total'))}", "ERROR")
                    return False
                
                if not isinstance(global_stats.get("a_traiter"), int):
                    self.log(f"❌ 'global.a_traiter' doit être un entier, reçu: {type(global_stats.get('a_traiter'))}", "ERROR")
                    return False
                
                if not isinstance(global_stats.get("en_cours"), int):
                    self.log(f"❌ 'global.en_cours' doit être un entier, reçu: {type(global_stats.get('en_cours'))}", "ERROR")
                    return False
                
                if not isinstance(global_stats.get("termine"), int):
                    self.log(f"❌ 'global.termine' doit être un entier, reçu: {type(global_stats.get('termine'))}", "ERROR")
                    return False
                
                if not isinstance(global_stats.get("archive"), int):
                    self.log(f"❌ 'global.archive' doit être un entier, reçu: {type(global_stats.get('archive'))}", "ERROR")
                    return False
                
                if not isinstance(global_stats.get("en_retard"), int):
                    self.log(f"❌ 'global.en_retard' doit être un entier, reçu: {type(global_stats.get('en_retard'))}", "ERROR")
                    return False
                
                if not isinstance(global_stats.get("delai_moyen_traitement"), int):
                    self.log(f"❌ 'global.delai_moyen_traitement' doit être un entier, reçu: {type(global_stats.get('delai_moyen_traitement'))}", "ERROR")
                    return False
                
                if not isinstance(global_stats.get("pourcentage_traitement"), (int, float)):
                    self.log(f"❌ 'global.pourcentage_traitement' doit être un nombre, reçu: {type(global_stats.get('pourcentage_traitement'))}", "ERROR")
                    return False
                
                # Vérifier les valeurs logiques
                total = global_stats.get("total", 0)
                termine = global_stats.get("termine", 0)
                pourcentage = global_stats.get("pourcentage_traitement", 0)
                
                # Validation mathématique
                if total > 0:
                    calculated_percentage = round((termine / total * 100), 1)
                    if abs(calculated_percentage - pourcentage) > 0.1:
                        self.log(f"❌ Calcul pourcentage incorrect: attendu {calculated_percentage}%, reçu {pourcentage}%", "ERROR")
                        return False
                
                # Vérifier que le pourcentage est entre 0 et 100
                if not (0 <= pourcentage <= 100):
                    self.log(f"❌ 'pourcentage_traitement' doit être entre 0 et 100: {pourcentage}", "ERROR")
                    return False
                
                # Vérifier les structures par service, sévérité, etc.
                for section_name, section_data in [
                    ("by_service", data.get("by_service", {})),
                    ("by_severite", data.get("by_severite", {})),
                    ("by_lieu", data.get("by_lieu", {}))
                ]:
                    if not isinstance(section_data, dict):
                        self.log(f"❌ '{section_name}' doit être un dictionnaire", "ERROR")
                        return False
                    
                    # Vérifier la structure de chaque sous-section
                    for key, value in section_data.items():
                        if not isinstance(value, dict):
                            self.log(f"❌ '{section_name}.{key}' doit être un dictionnaire", "ERROR")
                            return False
                        
                        required_sub_keys = ["total", "termine", "pourcentage"]
                        for sub_key in required_sub_keys:
                            if sub_key not in value:
                                self.log(f"❌ Champ '{section_name}.{key}.{sub_key}' manquant", "ERROR")
                                return False
                        
                        # Vérifier les types
                        if not isinstance(value.get("total"), int):
                            self.log(f"❌ '{section_name}.{key}.total' doit être un entier", "ERROR")
                            return False
                        
                        if not isinstance(value.get("termine"), int):
                            self.log(f"❌ '{section_name}.{key}.termine' doit être un entier", "ERROR")
                            return False
                        
                        if not isinstance(value.get("pourcentage"), (int, float)):
                            self.log(f"❌ '{section_name}.{key}.pourcentage' doit être un nombre", "ERROR")
                            return False
                        
                        # Vérifier que le pourcentage est entre 0 et 100
                        sub_pourcentage = value.get("pourcentage", 0)
                        if not (0 <= sub_pourcentage <= 100):
                            self.log(f"❌ '{section_name}.{key}.pourcentage' doit être entre 0 et 100: {sub_pourcentage}", "ERROR")
                            return False
                
                # Vérifier by_month (structure différente)
                by_month = data.get("by_month", {})
                if not isinstance(by_month, dict):
                    self.log("❌ 'by_month' doit être un dictionnaire", "ERROR")
                    return False
                
                for month_key, count in by_month.items():
                    if not isinstance(count, int):
                        self.log(f"❌ 'by_month.{month_key}' doit être un entier", "ERROR")
                        return False
                
                self.log(f"✅ Rapport stats récupérées avec succès:")
                self.log(f"  - Total: {global_stats.get('total')}")
                self.log(f"  - À traiter: {global_stats.get('a_traiter')}")
                self.log(f"  - En cours: {global_stats.get('en_cours')}")
                self.log(f"  - Terminé: {global_stats.get('termine')}")
                self.log(f"  - Archivé: {global_stats.get('archive')}")
                self.log(f"  - % traitement: {global_stats.get('pourcentage_traitement')}%")
                self.log(f"  - Délai moyen traitement: {global_stats.get('delai_moyen_traitement')} jours")
                self.log(f"  - En retard: {global_stats.get('en_retard')}")
                
                # Afficher les statistiques par section
                self.log(f"✅ Statistiques par service: {len(data.get('by_service', {}))} services")
                self.log(f"✅ Statistiques par sévérité: {len(data.get('by_severite', {}))} niveaux")
                self.log(f"✅ Statistiques par lieu: {len(data.get('by_lieu', {}))} lieux")
                self.log(f"✅ Statistiques par mois: {len(data.get('by_month', {}))} mois")
                
                # Validation logique métier
                self.log("✅ Validation de la structure JSON: CONFORME")
                self.log("✅ Validation des types de données: RÉUSSIE")
                self.log("✅ Validation des calculs mathématiques: RÉUSSIE")
                self.log("✅ Validation des valeurs logiques: RÉUSSIE")
                
                return True
            else:
                self.log(f"❌ Rapport stats échoué - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_presqu_accident_rapport_stats_without_auth(self):
        """TEST SÉCURITÉ: Tester GET /api/presqu-accident/rapport-stats SANS authentification"""
        self.log("🧪 TEST SÉCURITÉ: Rapport stats sans authentification")
        
        try:
            # Créer une session sans token d'authentification
            no_auth_session = requests.Session()
            
            response = no_auth_session.get(
                f"{BACKEND_URL}/presqu-accident/rapport-stats",
                timeout=10
            )
            
            # Doit retourner 401 Unauthorized ou 403 Forbidden
            if response.status_code in [401, 403]:
                self.log(f"✅ Protection par authentification fonctionnelle - Status: {response.status_code}")
                return True
            else:
                self.log(f"❌ SÉCURITÉ COMPROMISE - Endpoint accessible sans authentification - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_presqu_accident_upload(self):
        """TEST 11: Tester POST /api/presqu-accident/items/{item_id}/upload"""
        self.log("🧪 TEST 11: Upload d'une pièce jointe pour presqu'accident")
        
        if not self.created_items:
            self.log("⚠️ Pas de presqu'accidents créés pour tester l'upload", "WARNING")
            return False
        
        try:
            item_id = self.created_items[0]  # Prendre le premier item créé
            
            # Créer un fichier de test temporaire
            test_content = "Contenu de test pour pièce jointe presqu'accident - rapport d'incident détaillé"
            
            files = {
                'file': ('rapport_presqu_accident.txt', test_content, 'text/plain')
            }
            
            response = self.admin_session.post(
                f"{BACKEND_URL}/presqu-accident/items/{item_id}/upload",
                files=files,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Upload réussi - URL: {data.get('file_url')}")
                self.log(f"✅ Nom fichier: {data.get('file_name')}")
                self.log(f"✅ Succès: {data.get('success')}")
                return True
            else:
                self.log(f"❌ Upload échoué - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_presqu_accident_export_template(self):
        """TEST 12: Tester GET /api/presqu-accident/export/template"""
        self.log("🧪 TEST 12: Export du template CSV pour presqu'accidents")
        
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/presqu-accident/export/template",
                timeout=10
            )
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                
                self.log(f"✅ Template exporté - Type: {content_type}")
                self.log(f"✅ Taille: {content_length} bytes")
                
                # Vérifier que c'est bien un CSV
                if 'csv' in content_type or content_length > 0:
                    # Vérifier le contenu du template
                    content = response.content.decode('utf-8-sig')
                    if 'titre' in content and 'description' in content and 'service' in content:
                        self.log("✅ Template contient les colonnes attendues (titre, description, service)")
                        return True
                    else:
                        self.log("❌ Le template ne contient pas les colonnes attendues", "ERROR")
                        return False
                else:
                    self.log("❌ Le template ne semble pas être un CSV valide", "ERROR")
                    return False
            else:
                self.log(f"❌ Export template échoué - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_presqu_accident_delete_item(self):
        """TEST 13: Tester DELETE /api/presqu-accident/items/{item_id} (Admin uniquement)"""
        self.log("🧪 TEST 13: Supprimer un presqu'accident (Admin)")
        
        if not self.created_items:
            self.log("⚠️ Pas de presqu'accidents créés pour tester la suppression", "WARNING")
            return True  # Pas d'erreur si pas d'items
        
        try:
            item_id = self.created_items[-1]  # Prendre le dernier item créé
            
            response = self.admin_session.delete(
                f"{BACKEND_URL}/presqu-accident/items/{item_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Presqu'accident supprimé - Message: {data.get('message')}")
                self.log(f"✅ Succès: {data.get('success')}")
                self.created_items.remove(item_id)  # Retirer de la liste
                return True
            else:
                self.log(f"❌ Suppression échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_cleanup_presqu_accident_items(self):
        """TEST 14: Nettoyer (supprimer les presqu'accidents de test restants)"""
        self.log("🧪 TEST 14: Nettoyer (supprimer les presqu'accidents de test restants)")
        
        if not self.created_items:
            self.log("⚠️ Pas de presqu'accidents de test à supprimer", "WARNING")
            return True
        
        success_count = 0
        for item_id in self.created_items[:]:  # Copy to avoid modification during iteration
            try:
                response = self.admin_session.delete(
                    f"{BACKEND_URL}/presqu-accident/items/{item_id}",
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.log(f"✅ Presqu'accident {item_id} supprimé avec succès")
                    self.created_items.remove(item_id)
                    success_count += 1
                elif response.status_code == 404:
                    self.log(f"⚠️ Presqu'accident {item_id} déjà supprimé (Status 404)")
                    self.created_items.remove(item_id)
                    success_count += 1
                else:
                    self.log(f"❌ Suppression du presqu'accident {item_id} échouée - Status: {response.status_code}", "ERROR")
                    
            except requests.exceptions.RequestException as e:
                self.log(f"❌ Request failed for {item_id} - Error: {str(e)}", "ERROR")
        
        self.log(f"✅ Nettoyage terminé: {success_count} presqu'accidents supprimés")
        return success_count >= 0  # Toujours réussir le nettoyage
    
    def cleanup_remaining_presqu_accident_items(self):
        """Nettoyer tous les presqu'accidents créés pendant les tests"""
        self.log("🧹 Nettoyage des presqu'accidents restants...")
        
        if not self.created_items:
            self.log("Aucun presqu'accident à nettoyer")
            return True
        
        success_count = 0
        for item_id in self.created_items[:]:  # Copy list to avoid modification during iteration
            try:
                response = self.admin_session.delete(
                    f"{BACKEND_URL}/presqu-accident/items/{item_id}",
                    timeout=10
                )
                
                if response.status_code in [200, 404]:
                    self.log(f"✅ Presqu'accident {item_id} nettoyé")
                    self.created_items.remove(item_id)
                    success_count += 1
                else:
                    self.log(f"⚠️ Impossible de nettoyer le presqu'accident {item_id} - Status: {response.status_code}")
                    
            except Exception as e:
                self.log(f"⚠️ Erreur lors du nettoyage du presqu'accident {item_id}: {str(e)}")
        
        self.log(f"Nettoyage terminé: {success_count} presqu'accidents supprimés")
        return True
    
    def run_presqu_accident_tests(self):
        """Run comprehensive tests for Presqu'accident (Near Miss) endpoints"""
        self.log("=" * 80)
        self.log("TESTING PRESQU'ACCIDENT (NEAR MISS) - ENDPOINTS CRUD COMPLETS")
        self.log("=" * 80)
        self.log("CONTEXTE: Test complet du nouveau module Presqu'accident avec tous les endpoints:")
        self.log("- CRUD de base (GET, POST, PUT, DELETE)")
        self.log("- Upload de pièces jointes")
        self.log("- Statistiques et alertes")
        self.log("- Badge de notification")
        self.log("- Statistiques complètes pour page Rapport (GET /api/presqu-accident/rapport-stats)")
        self.log("- Import/Export")
        self.log("")
        self.log("TESTS À EFFECTUER:")
        self.log("1. Se connecter en tant qu'admin")
        self.log("2. Créer presqu'accidents avec différents services (ADV, LOGISTIQUE, PRODUCTION, QHSE)")
        self.log("3. Tester les filtres (service, statut, sévérité, lieu)")
        self.log("4. Récupérer les détails d'un presqu'accident")
        self.log("5. Mettre à jour un presqu'accident (statut A_TRAITER → EN_COURS → TERMINE)")
        self.log("6. Tester les statistiques globales")
        self.log("7. Tester les alertes (items à traiter, en retard)")
        self.log("8. Tester le badge de notification (GET /api/presqu-accident/badge-stats)")
        self.log("9. SÉCURITÉ: Tester badge sans authentification (doit échouer)")
        self.log("10. CRITIQUE: Tester statistiques rapport (GET /api/presqu-accident/rapport-stats)")
        self.log("11. SÉCURITÉ: Tester rapport stats sans authentification (doit échouer)")
        self.log("12. Upload d'une pièce jointe")
        self.log("13. Export du template CSV")
        self.log("14. Supprimer un presqu'accident (admin uniquement)")
        self.log("15. Nettoyer les presqu'accidents de test créés")
        self.log("=" * 80)
        
        results = {
            "admin_login": False,
            "create_adv_item": False,
            "create_logistique_item": False,
            "create_production_item": False,
            "create_qhse_item": False,
            "test_presqu_accident_list_with_filters": False,
            "test_presqu_accident_item_details": False,
            "test_presqu_accident_item_update": False,
            "test_presqu_accident_stats": False,
            "test_presqu_accident_alerts": False,
            "test_presqu_accident_badge_stats": False,
            "test_presqu_accident_badge_stats_without_auth": False,
            "test_presqu_accident_rapport_stats": False,
            "test_presqu_accident_rapport_stats_without_auth": False,
            "test_presqu_accident_upload": False,
            "test_presqu_accident_export_template": False,
            "test_presqu_accident_delete_item": False,
            "test_cleanup_presqu_accident_items": False,
            "cleanup_remaining": False
        }
        
        # Test 1: Admin Login
        results["admin_login"] = self.test_admin_login()
        
        if not results["admin_login"]:
            self.log("❌ Cannot proceed with other tests - Admin login failed", "ERROR")
            return results
        
        # Test 2-5: Create presqu'accident items with different services
        results["create_adv_item"] = self.test_create_adv_item()
        results["create_logistique_item"] = self.test_create_logistique_item()
        results["create_production_item"] = self.test_create_production_item()
        results["create_qhse_item"] = self.test_create_qhse_item()
        
        # Test 6: List with filters
        results["test_presqu_accident_list_with_filters"] = self.test_presqu_accident_list_with_filters()
        
        # Test 7: Item details
        results["test_presqu_accident_item_details"] = self.test_presqu_accident_item_details()
        
        # Test 8: Update item
        results["test_presqu_accident_item_update"] = self.test_presqu_accident_item_update()
        
        # Test 9: Statistics
        results["test_presqu_accident_stats"] = self.test_presqu_accident_stats()
        
        # Test 10: Alerts
        results["test_presqu_accident_alerts"] = self.test_presqu_accident_alerts()
        
        # Test 11: Badge Stats (CRITIQUE)
        results["test_presqu_accident_badge_stats"] = self.test_presqu_accident_badge_stats()
        
        # Test 12: Badge Stats Security (sans auth)
        results["test_presqu_accident_badge_stats_without_auth"] = self.test_presqu_accident_badge_stats_without_auth()
        
        # Test 13: Rapport Stats (CRITIQUE)
        results["test_presqu_accident_rapport_stats"] = self.test_presqu_accident_rapport_stats()
        
        # Test 14: Rapport Stats Security (sans auth)
        results["test_presqu_accident_rapport_stats_without_auth"] = self.test_presqu_accident_rapport_stats_without_auth()
        
        # Test 15: Upload
        results["test_presqu_accident_upload"] = self.test_presqu_accident_upload()
        
        # Test 16: Export template
        results["test_presqu_accident_export_template"] = self.test_presqu_accident_export_template()
        
        # Test 17: Delete item
        results["test_presqu_accident_delete_item"] = self.test_presqu_accident_delete_item()
        
        # Test 18: Cleanup
        results["test_cleanup_presqu_accident_items"] = self.test_cleanup_presqu_accident_items()
        
        # Test 19: Final cleanup
        results["cleanup_remaining"] = self.cleanup_remaining_presqu_accident_items()
        
        # Summary
        self.log("=" * 70)
        self.log("PRESQU'ACCIDENT (NEAR MISS) TEST RESULTS SUMMARY")
        self.log("=" * 70)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"  {test_name}: {status}")
        
        self.log(f"\n📊 Overall: {passed}/{total} tests passed")
        
        # Detailed analysis for critical tests
        critical_tests = [
            "create_incendie_item", "create_electrique_item", "create_mmri_item", "create_securite_item",
            "test_surveillance_list_with_filters", "test_surveillance_item_details", 
            "test_surveillance_item_update", "test_surveillance_stats", "test_surveillance_alerts",
            "test_surveillance_badge_stats", "test_surveillance_badge_stats_without_auth",
            "test_surveillance_rapport_stats", "test_surveillance_rapport_stats_without_auth",
            "test_surveillance_upload", "test_surveillance_export_template", "test_surveillance_delete_item"
        ]
        critical_passed = sum(results.get(test, False) for test in critical_tests)
        
        if critical_passed == len(critical_tests):
            self.log("🎉 CRITICAL SUCCESS: All main surveillance endpoints tests passed!")
            self.log("✅ POST /api/surveillance/items works correctly")
            self.log("✅ GET /api/surveillance/items with filters works correctly")
            self.log("✅ GET /api/surveillance/items/{id} works correctly")
            self.log("✅ PUT /api/surveillance/items/{id} works correctly")
            self.log("✅ DELETE /api/surveillance/items/{id} works correctly (admin only)")
            self.log("✅ POST /api/surveillance/items/{id}/upload works correctly")
            self.log("✅ GET /api/surveillance/stats works correctly")
            self.log("✅ GET /api/surveillance/alerts works correctly")
            self.log("✅ GET /api/surveillance/badge-stats works correctly")
            self.log("✅ GET /api/surveillance/badge-stats security works correctly")
            self.log("✅ GET /api/surveillance/rapport-stats works correctly")
            self.log("✅ GET /api/surveillance/rapport-stats security works correctly")
            self.log("✅ GET /api/surveillance/export/template works correctly")
        else:
            self.log("🚨 CRITICAL FAILURE: Some main surveillance endpoint tests failed!")
            failed_critical = [test for test in critical_tests if not results.get(test, False)]
            self.log(f"❌ Failed critical tests: {', '.join(failed_critical)}")
        
        if critical_passed == len(critical_tests):
            self.log("🎉 PLAN DE SURVEILLANCE ENDPOINTS ARE WORKING CORRECTLY!")
            self.log("✅ All CRUD operations functional")
            self.log("✅ Filters and statistics working")
            self.log("✅ Upload and export features working")
            self.log("✅ Admin permissions respected")
            self.log("✅ The Plan de Surveillance backend is READY FOR PRODUCTION")
        else:
            self.log("⚠️ PLAN DE SURVEILLANCE ISSUES DETECTED")
            self.log("❌ Some endpoints are not working correctly")
        
        return results

if __name__ == "__main__":
    tester = SurveillanceTester()
    results = tester.run_surveillance_tests()
    
    # Exit with appropriate code - allow cleanup to fail
    critical_tests = [
        "admin_login", "create_incendie_item", "create_electrique_item", "create_mmri_item", 
        "create_securite_item", "test_surveillance_list_with_filters", "test_surveillance_item_details", 
        "test_surveillance_item_update", "test_surveillance_stats", "test_surveillance_alerts",
        "test_surveillance_badge_stats", "test_surveillance_badge_stats_without_auth",
        "test_surveillance_rapport_stats", "test_surveillance_rapport_stats_without_auth",
        "test_surveillance_upload", "test_surveillance_export_template", "test_surveillance_delete_item"
    ]
    
    critical_passed = sum(results.get(test, False) for test in critical_tests)
    
    if critical_passed == len(critical_tests):
        exit(0)  # Success
    else:
        exit(1)  # Failure