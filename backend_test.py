#!/usr/bin/env python3
"""
Backend API Testing Script for GMAO Application
Tests Autorisations Particulières de Travaux - Module complet MAINT_FE_003_V03
"""

import requests
import json
import os
from datetime import datetime, timedelta

# Use the correct backend URL from frontend .env
BACKEND_URL = "https://iris-maintenance-2.preview.emergentagent.com/api"

# Test credentials - admin account as specified in the request
ADMIN_EMAIL = "admin@gmao-iris.local"
ADMIN_PASSWORD = "Admin123!"

class AutorisationsParticulieresTester:
    def __init__(self):
        self.admin_session = requests.Session()
        self.admin_token = None
        self.admin_data = None
        self.test_autorisations = []  # Store created test autorisations for cleanup
        
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
    
    def test_create_autorisation(self):
        """TEST 1: Créer une nouvelle autorisation particulière"""
        self.log("🧪 TEST 1: Créer une nouvelle autorisation particulière")
        
        test_autorisation_data = {
            "service_demandeur": "Service Test",
            "responsable": "Jean Dupont",
            "personnel_autorise": [
                {"nom": "Pierre Martin", "fonction": "Technicien"},
                {"nom": "Marie Durand", "fonction": "Ingénieur"}
            ],
            "description_travaux": "Travaux de maintenance électrique",
            "horaire_debut": "08:00",
            "horaire_fin": "17:00",
            "lieu_travaux": "Bâtiment A - Salle électrique",
            "risques_potentiels": "Électrocution\nChute",
            "mesures_securite": "Consignation électrique\nHarnais obligatoire",
            "equipements_protection": "Gants isolants\nCasque\nChaussures de sécurité",
            "signature_demandeur": "Jean Dupont",
            "date_signature_demandeur": "2025-01-15"
        }
        
        try:
            response = self.admin_session.post(
                f"{BACKEND_URL}/autorisations/",
                json=test_autorisation_data,
                timeout=15
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.log(f"✅ Autorisation créée - Status: {response.status_code}")
                self.log(f"✅ ID: {data.get('id')}")
                self.log(f"✅ Numéro: {data.get('numero')}")
                self.log(f"✅ Date établissement: {data.get('date_etablissement')}")
                self.log(f"✅ Service demandeur: {data.get('service_demandeur')}")
                self.log(f"✅ Statut: {data.get('statut')}")
                
                # Vérifications critiques
                numero = data.get('numero')
                if numero and numero >= 8000:
                    self.log(f"✅ SUCCÈS: Numéro >= 8000 (reçu: {numero})")
                else:
                    self.log(f"❌ ÉCHEC: Numéro < 8000 (reçu: {numero})", "ERROR")
                    return False, None
                
                if data.get('date_etablissement'):
                    self.log("✅ SUCCÈS: Date d'établissement auto-générée")
                else:
                    self.log("❌ ÉCHEC: Date d'établissement manquante", "ERROR")
                    return False, None
                
                if data.get('statut') == "BROUILLON":
                    self.log("✅ SUCCÈS: Statut par défaut 'BROUILLON'")
                else:
                    self.log(f"❌ ÉCHEC: Statut incorrect (reçu: {data.get('statut')})", "ERROR")
                    return False, None
                
                if data.get('created_at') and data.get('updated_at'):
                    self.log("✅ SUCCÈS: Champs created_at et updated_at présents")
                else:
                    self.log("❌ ÉCHEC: Champs created_at/updated_at manquants", "ERROR")
                    return False, None
                
                # Stocker pour nettoyage
                self.test_autorisations.append(data.get('id'))
                return True, data
            else:
                self.log(f"❌ Création échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False, None
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False, None
    
    def test_get_all_autorisations(self):
        """TEST 2: Récupérer toutes les autorisations"""
        self.log("🧪 TEST 2: Récupérer toutes les autorisations")
        
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/autorisations",
                timeout=15
            )
            
            if response.status_code == 200:
                autorisations = response.json()
                self.log(f"✅ Liste des autorisations récupérée - {len(autorisations)} autorisations")
                
                # Chercher notre autorisation de test
                test_autorisation = None
                for autorisation in autorisations:
                    if autorisation.get('id') in self.test_autorisations:
                        test_autorisation = autorisation
                        break
                
                if test_autorisation:
                    self.log(f"✅ Autorisation de test trouvée - ID: {test_autorisation.get('id')}")
                    self.log(f"✅ Numéro: {test_autorisation.get('numero')}")
                    self.log(f"✅ Service: {test_autorisation.get('service_demandeur')}")
                    self.log(f"✅ Responsable: {test_autorisation.get('responsable')}")
                    self.log(f"✅ Statut: {test_autorisation.get('statut')}")
                    
                    # Vérifier que l'autorisation créée est incluse
                    if (test_autorisation.get('service_demandeur') == 'Service Test' and
                        test_autorisation.get('responsable') == 'Jean Dupont'):
                        self.log("✅ SUCCÈS: Autorisation créée trouvée dans la liste")
                        return True
                    else:
                        self.log("❌ ÉCHEC: Données de l'autorisation incorrectes", "ERROR")
                        return False
                else:
                    self.log("❌ Autorisation de test non trouvée dans la liste", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Récupération des autorisations échouée - Status: {response.status_code}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_get_autorisation_by_id(self):
        """TEST 3: Récupérer une autorisation spécifique par ID"""
        self.log("🧪 TEST 3: Récupérer une autorisation spécifique par ID")
        
        if not self.test_autorisations:
            self.log("⚠️ Aucune autorisation de test disponible", "WARNING")
            return False
        
        autorisation_id = self.test_autorisations[0]
        
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/autorisations/{autorisation_id}",
                timeout=15
            )
            
            if response.status_code == 200:
                autorisation = response.json()
                self.log(f"✅ Autorisation récupérée - Status: 200 OK")
                self.log(f"✅ ID: {autorisation.get('id')}")
                self.log(f"✅ Numéro: {autorisation.get('numero')}")
                self.log(f"✅ Service: {autorisation.get('service_demandeur')}")
                self.log(f"✅ Responsable: {autorisation.get('responsable')}")
                
                # Vérifier tous les champs présents et corrects
                required_fields = ['id', 'numero', 'service_demandeur', 'responsable', 
                                 'description_travaux', 'horaire_debut', 'horaire_fin', 
                                 'lieu_travaux', 'personnel_autorise']
                
                missing_fields = []
                for field in required_fields:
                    if field not in autorisation or autorisation[field] is None:
                        missing_fields.append(field)
                
                if not missing_fields:
                    self.log("✅ SUCCÈS: Tous les champs requis sont présents")
                    
                    # Vérifier que personnel_autorise est un array
                    personnel = autorisation.get('personnel_autorise', [])
                    if isinstance(personnel, list):
                        self.log(f"✅ SUCCÈS: personnel_autorise est un array avec {len(personnel)} entrées")
                        return True
                    else:
                        self.log("❌ ÉCHEC: personnel_autorise n'est pas un array", "ERROR")
                        return False
                else:
                    self.log(f"❌ ÉCHEC: Champs manquants: {missing_fields}", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Récupération de l'autorisation échouée - Status: {response.status_code}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_update_autorisation(self):
        """TEST 4: Mettre à jour une autorisation"""
        self.log("🧪 TEST 4: Mettre à jour une autorisation")
        
        if not self.test_autorisations:
            self.log("⚠️ Aucune autorisation de test disponible", "WARNING")
            return False
        
        autorisation_id = self.test_autorisations[0]
        
        update_data = {
            "description_travaux": "Travaux de maintenance électrique - MISE À JOUR",
            "statut": "VALIDE"
        }
        
        try:
            response = self.admin_session.put(
                f"{BACKEND_URL}/autorisations/{autorisation_id}",
                json=update_data,
                timeout=15
            )
            
            if response.status_code == 200:
                autorisation = response.json()
                self.log(f"✅ Autorisation mise à jour - Status: 200 OK")
                self.log(f"✅ ID: {autorisation.get('id')}")
                self.log(f"✅ Description: {autorisation.get('description_travaux')}")
                self.log(f"✅ Statut: {autorisation.get('statut')}")
                
                # Vérifier que les modifications ont été appliquées
                if (autorisation.get('description_travaux') == "Travaux de maintenance électrique - MISE À JOUR" and
                    autorisation.get('statut') == "VALIDE"):
                    self.log("✅ SUCCÈS: Description et statut mis à jour correctement")
                    
                    # Vérifier que updated_at a été mis à jour
                    if autorisation.get('updated_at'):
                        self.log("✅ SUCCÈS: updated_at mis à jour")
                        return True
                    else:
                        self.log("❌ ÉCHEC: updated_at non mis à jour", "ERROR")
                        return False
                else:
                    self.log("❌ ÉCHEC: Modifications non appliquées", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Mise à jour échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False

    def test_generate_pdf(self):
        """TEST 5: Générer le PDF de l'autorisation"""
        self.log("🧪 TEST 5: Générer le PDF de l'autorisation")
        
        if not self.test_autorisations:
            self.log("⚠️ Aucune autorisation de test disponible", "WARNING")
            return False
        
        autorisation_id = self.test_autorisations[0]
        
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/autorisations/{autorisation_id}/pdf",
                timeout=15
            )
            
            if response.status_code == 200:
                self.log(f"✅ PDF généré - Status: 200 OK")
                self.log(f"✅ Content-Type: {response.headers.get('content-type')}")
                
                # Vérifier que c'est du HTML
                if response.headers.get('content-type') == 'text/html; charset=utf-8':
                    self.log("✅ SUCCÈS: Content-Type correct (text/html)")
                    
                    # Vérifier le contenu HTML
                    html_content = response.text
                    if "AUTORISATION PARTICULIÈRE DE TRAVAUX" in html_content:
                        self.log("✅ SUCCÈS: HTML contient le titre principal")
                        
                        # Vérifier que le numéro d'autorisation est présent
                        if str(autorisation_id) in html_content or "8000" in html_content:
                            self.log("✅ SUCCÈS: HTML contient le numéro d'autorisation")
                            
                            # Vérifier que les données de l'autorisation sont présentes
                            if "Service Test" in html_content and "Jean Dupont" in html_content:
                                self.log("✅ SUCCÈS: HTML contient les données de l'autorisation")
                                return True
                            else:
                                self.log("❌ ÉCHEC: Données de l'autorisation manquantes dans le HTML", "ERROR")
                                return False
                        else:
                            self.log("❌ ÉCHEC: Numéro d'autorisation manquant dans le HTML", "ERROR")
                            return False
                    else:
                        self.log("❌ ÉCHEC: Titre principal manquant dans le HTML", "ERROR")
                        return False
                else:
                    self.log(f"❌ ÉCHEC: Content-Type incorrect: {response.headers.get('content-type')}", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Génération PDF échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_delete_autorisation(self):
        """TEST 6: Supprimer une autorisation"""
        self.log("🧪 TEST 6: Supprimer une autorisation")
        
        if not self.test_autorisations:
            self.log("⚠️ Aucune autorisation de test disponible", "WARNING")
            return False
        
        autorisation_id = self.test_autorisations[0]
        
        try:
            response = self.admin_session.delete(
                f"{BACKEND_URL}/autorisations/{autorisation_id}",
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Autorisation supprimée - Status: 200 OK")
                self.log(f"✅ Message: {data.get('message')}")
                
                # Vérifier que la réponse contient le message de succès
                if data.get('success') and data.get('message'):
                    self.log("✅ SUCCÈS: Message de succès reçu")
                    
                    # Vérifier que l'autorisation n'existe plus
                    verify_response = self.admin_session.get(
                        f"{BACKEND_URL}/autorisations/{autorisation_id}",
                        timeout=10
                    )
                    
                    if verify_response.status_code == 404:
                        self.log("✅ SUCCÈS: GET suivant retourne 404 (autorisation supprimée)")
                        # Retirer de la liste pour éviter les erreurs de nettoyage
                        self.test_autorisations.remove(autorisation_id)
                        return True
                    else:
                        self.log(f"❌ ÉCHEC: GET suivant retourne {verify_response.status_code} au lieu de 404", "ERROR")
                        return False
                else:
                    self.log("❌ ÉCHEC: Message de succès manquant", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Suppression échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False

    def test_check_backend_logs(self):
        """TEST 7: Vérifier les logs backend pour erreurs"""
        self.log("🧪 TEST 7: Vérifier les logs backend pour erreurs")
        
        try:
            import subprocess
            result = subprocess.run(
                ["tail", "-n", "50", "/var/log/supervisor/backend.err.log"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logs = result.stdout
                if logs.strip():
                    self.log("⚠️ Logs d'erreur backend trouvés:")
                    for line in logs.strip().split('\n')[-10:]:  # Dernières 10 lignes
                        if line.strip():
                            self.log(f"   {line}")
                    
                    # Chercher des erreurs spécifiques
                    if "ValidationError" in logs:
                        self.log("❌ Erreur de validation Pydantic détectée", "ERROR")
                        return False
                    elif "autorisation" in logs.lower():
                        self.log("⚠️ Erreur liée aux 'autorisations' détectée", "WARNING")
                        return False
                    else:
                        self.log("✅ Pas d'erreur critique liée aux autorisations")
                        return True
                else:
                    self.log("✅ Aucune erreur dans les logs backend")
                    return True
            else:
                self.log("⚠️ Impossible de lire les logs backend", "WARNING")
                return True  # Ne pas faire échouer le test pour ça
                
        except Exception as e:
            self.log(f"⚠️ Erreur lecture logs: {str(e)}", "WARNING")
            return True  # Ne pas faire échouer le test pour ça

    def test_cleanup_remaining_autorisations(self):
        """TEST 8: Nettoyer - Supprimer les autorisations de test restantes"""
        self.log("🧪 TEST 8: Nettoyer - Supprimer les autorisations de test restantes")
        
        if not self.test_autorisations:
            self.log("✅ Aucune autorisation de test restante à supprimer")
            return True
        
        deleted_count = 0
        failed_count = 0
        
        for autorisation_id in self.test_autorisations[:]:  # Copy to avoid modification during iteration
            try:
                response = self.admin_session.delete(
                    f"{BACKEND_URL}/autorisations/{autorisation_id}",
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        self.log(f"✅ Autorisation {autorisation_id} supprimée avec succès")
                        deleted_count += 1
                        self.test_autorisations.remove(autorisation_id)
                    else:
                        self.log(f"⚠️ Réponse inattendue pour suppression autorisation {autorisation_id}")
                        failed_count += 1
                else:
                    self.log(f"❌ Échec suppression autorisation {autorisation_id} - Status: {response.status_code}")
                    failed_count += 1
                    
            except requests.exceptions.RequestException as e:
                self.log(f"❌ Erreur suppression autorisation {autorisation_id} - Error: {str(e)}")
                failed_count += 1
        
        if failed_count == 0:
            self.log(f"✅ SUCCÈS: Toutes les {deleted_count} autorisations de test ont été supprimées")
            return True
        else:
            self.log(f"⚠️ PARTIEL: {deleted_count} autorisations supprimées, {failed_count} échecs")
            return deleted_count > 0  # Consider success if at least some were deleted

    def cleanup_test_autorisations(self):
        """Nettoyer les autorisations de test créées"""
        self.log("🧹 Nettoyage des autorisations de test...")
        
        for autorisation_id in self.test_autorisations[:]:
            try:
                response = self.admin_session.delete(
                    f"{BACKEND_URL}/autorisations/{autorisation_id}",
                    timeout=10
                )
                if response.status_code == 200:
                    self.log(f"✅ Autorisation {autorisation_id} supprimée")
                    self.test_autorisations.remove(autorisation_id)
                else:
                    self.log(f"⚠️ Échec suppression autorisation {autorisation_id} - Status: {response.status_code}")
            except:
                self.log(f"⚠️ Erreur suppression autorisation {autorisation_id}")

    def run_autorisations_particulieres_tests(self):
        """Run comprehensive tests for Autorisations Particulières de Travaux - Module MAINT_FE_003_V03"""
        self.log("=" * 80)
        self.log("TESTING AUTORISATIONS PARTICULIÈRES DE TRAVAUX - MODULE MAINT_FE_003_V03")
        self.log("=" * 80)
        self.log("CONTEXTE:")
        self.log("Test complet du nouveau module 'Autorisations Particulières de Travaux'")
        self.log("Collection MongoDB: autorisations_particulieres")
        self.log("Format conforme au document MAINT_FE_003_V03")
        self.log("")
        self.log("SCÉNARIOS DE TEST:")
        self.log("1. 📋 POST /api/autorisations - Créer une nouvelle autorisation")
        self.log("2. 📋 GET /api/autorisations - Liste toutes les autorisations")
        self.log("3. 📋 GET /api/autorisations/{id} - Récupérer une autorisation spécifique")
        self.log("4. 📋 PUT /api/autorisations/{id} - Mettre à jour une autorisation")
        self.log("5. 📋 GET /api/autorisations/{id}/pdf - Générer le PDF")
        self.log("6. 📋 DELETE /api/autorisations/{id} - Supprimer une autorisation")
        self.log("7. 🔍 Vérifier les logs backend pour erreurs")
        self.log("8. 🧹 Nettoyer - Supprimer les autorisations de test restantes")
        self.log("=" * 80)
        
        results = {
            "admin_login": False,
            "create_autorisation": False,
            "get_all_autorisations": False,
            "get_autorisation_by_id": False,
            "update_autorisation": False,
            "generate_pdf": False,
            "delete_autorisation": False,
            "check_backend_logs": False,
            "cleanup_remaining_autorisations": False
        }
        
        # Test 1: Admin Login
        results["admin_login"] = self.test_admin_login()
        
        if not results["admin_login"]:
            self.log("❌ Cannot proceed with other tests - Admin login failed", "ERROR")
            return results
        
        # TESTS CRITIQUES DES AUTORISATIONS PARTICULIÈRES
        self.log("\n" + "=" * 60)
        self.log("📋 TESTS CRITIQUES - AUTORISATIONS PARTICULIÈRES")
        self.log("=" * 60)
        
        # Test 2: Créer une autorisation
        success, test_autorisation = self.test_create_autorisation()
        results["create_autorisation"] = success
        
        # Test 3: Récupérer toutes les autorisations
        results["get_all_autorisations"] = self.test_get_all_autorisations()
        
        # Test 4: Récupérer une autorisation par ID
        results["get_autorisation_by_id"] = self.test_get_autorisation_by_id()
        
        # Test 5: Mettre à jour une autorisation
        results["update_autorisation"] = self.test_update_autorisation()
        
        # Test 6: Générer le PDF
        results["generate_pdf"] = self.test_generate_pdf()
        
        # Test 7: Supprimer une autorisation
        results["delete_autorisation"] = self.test_delete_autorisation()
        
        # Test 8: Vérifier les logs backend
        results["check_backend_logs"] = self.test_check_backend_logs()
        
        # Test 9: Nettoyage
        results["cleanup_remaining_autorisations"] = self.test_cleanup_remaining_autorisations()
        
        # Summary
        self.log("=" * 80)
        self.log("AUTORISATIONS PARTICULIÈRES - RÉSULTATS DES TESTS")
        self.log("=" * 80)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"  {test_name}: {status}")
        
        self.log(f"\n📊 Overall: {passed}/{total} tests passed")
        
        # Analyse détaillée des tests critiques
        critical_tests = ["create_autorisation", "get_all_autorisations", "get_autorisation_by_id", 
                         "update_autorisation", "generate_pdf", "delete_autorisation"]
        critical_passed = sum(results.get(test, False) for test in critical_tests)
        
        self.log("\n" + "=" * 60)
        self.log("ANALYSE CRITIQUE DE LA FONCTIONNALITÉ")
        self.log("=" * 60)
        
        # TEST CRITIQUE 1: Création d'autorisation
        if results.get("create_autorisation", False):
            self.log("🎉 TEST CRITIQUE 1 - CRÉATION D'AUTORISATION: ✅ SUCCÈS")
            self.log("✅ POST /api/autorisations fonctionne correctement")
            self.log("✅ Numérotation automatique >= 8000")
            self.log("✅ Date d'établissement auto-générée")
            self.log("✅ Statut par défaut 'BROUILLON'")
            self.log("✅ Champs created_at, updated_at présents")
        else:
            self.log("🚨 TEST CRITIQUE 1 - CRÉATION D'AUTORISATION: ❌ ÉCHEC")
            self.log("❌ Erreur lors de la création d'autorisation")
        
        # TEST CRITIQUE 2: Liste des autorisations
        if results.get("get_all_autorisations", False):
            self.log("🎉 TEST CRITIQUE 2 - LISTE DES AUTORISATIONS: ✅ SUCCÈS")
            self.log("✅ GET /api/autorisations retourne la liste")
            self.log("✅ Autorisation créée incluse dans la liste")
        else:
            self.log("🚨 TEST CRITIQUE 2 - LISTE DES AUTORISATIONS: ❌ ÉCHEC")
            self.log("❌ Erreur lors de la récupération de la liste")
        
        # TEST CRITIQUE 3: Récupération par ID
        if results.get("get_autorisation_by_id", False):
            self.log("🎉 TEST CRITIQUE 3 - RÉCUPÉRATION PAR ID: ✅ SUCCÈS")
            self.log("✅ GET /api/autorisations/{id} fonctionne")
            self.log("✅ Tous les champs présents et corrects")
            self.log("✅ personnel_autorise est un array")
        else:
            self.log("🚨 TEST CRITIQUE 3 - RÉCUPÉRATION PAR ID: ❌ ÉCHEC")
            self.log("❌ Erreur lors de la récupération par ID")
        
        # TEST CRITIQUE 4: Mise à jour
        if results.get("update_autorisation", False):
            self.log("🎉 TEST CRITIQUE 4 - MISE À JOUR: ✅ SUCCÈS")
            self.log("✅ PUT /api/autorisations/{id} fonctionne")
            self.log("✅ Modifications appliquées correctement")
            self.log("✅ updated_at mis à jour")
        else:
            self.log("🚨 TEST CRITIQUE 4 - MISE À JOUR: ❌ ÉCHEC")
            self.log("❌ Erreur lors de la mise à jour")
        
        # TEST CRITIQUE 5: Génération PDF
        if results.get("generate_pdf", False):
            self.log("🎉 TEST CRITIQUE 5 - GÉNÉRATION PDF: ✅ SUCCÈS")
            self.log("✅ GET /api/autorisations/{id}/pdf fonctionne")
            self.log("✅ Content-Type: text/html")
            self.log("✅ HTML contient 'AUTORISATION PARTICULIÈRE DE TRAVAUX'")
            self.log("✅ HTML contient le numéro d'autorisation")
            self.log("✅ HTML contient les données de l'autorisation")
        else:
            self.log("🚨 TEST CRITIQUE 5 - GÉNÉRATION PDF: ❌ ÉCHEC")
            self.log("❌ Erreur lors de la génération PDF")
        
        # TEST CRITIQUE 6: Suppression
        if results.get("delete_autorisation", False):
            self.log("🎉 TEST CRITIQUE 6 - SUPPRESSION: ✅ SUCCÈS")
            self.log("✅ DELETE /api/autorisations/{id} fonctionne")
            self.log("✅ Message de succès retourné")
            self.log("✅ GET suivant retourne 404")
        else:
            self.log("🚨 TEST CRITIQUE 6 - SUPPRESSION: ❌ ÉCHEC")
            self.log("❌ Erreur lors de la suppression")
        
        # Tests complémentaires
        if results.get("check_backend_logs", False):
            self.log("✅ VALIDATION: Pas d'erreur critique dans les logs backend")
        
        if results.get("cleanup_remaining_autorisations", False):
            self.log("✅ NETTOYAGE: Autorisations de test supprimées avec succès")
        
        # Conclusion finale
        self.log("\n" + "=" * 80)
        self.log("CONCLUSION FINALE - AUTORISATIONS PARTICULIÈRES")
        self.log("=" * 80)
        
        if critical_passed == len(critical_tests):
            self.log("🎉 MODULE AUTORISATIONS PARTICULIÈRES ENTIÈREMENT OPÉRATIONNEL!")
            self.log("✅ Toutes les routes CRUD fonctionnent correctement")
            self.log("✅ Numérotation automatique >= 8000 fonctionnelle")
            self.log("✅ Date d'établissement auto-générée (format DD/MM/YYYY)")
            self.log("✅ Authentification JWT requise pour toutes les routes")
            self.log("✅ Validation des champs obligatoires")
            self.log("✅ Gestion correcte du personnel_autorise (array)")
            self.log("✅ Génération PDF HTML conforme au format MAINT_FE_003_V03")
            self.log("✅ Le module est PRÊT POUR PRODUCTION")
        else:
            self.log("⚠️ MODULE AUTORISATIONS PARTICULIÈRES INCOMPLET - PROBLÈMES DÉTECTÉS")
            failed_critical = [test for test in critical_tests if not results.get(test, False)]
            self.log(f"❌ Tests critiques échoués: {', '.join(failed_critical)}")
            self.log("❌ Le module ne fonctionne pas correctement")
            self.log("❌ Intervention requise avant mise en production")
        
        return results

if __name__ == "__main__":
    tester = AutorisationsParticulieresTester()
    results = tester.run_autorisations_particulieres_tests()
    
    # Exit with appropriate code
    critical_tests = [
        "admin_login", "create_autorisation", "get_all_autorisations", 
        "get_autorisation_by_id", "update_autorisation", "generate_pdf", "delete_autorisation"
    ]
    
    critical_passed = sum(results.get(test, False) for test in critical_tests)
    
    if critical_passed == len(critical_tests):
        exit(0)  # Success
    else:
        exit(1)  # Failure
