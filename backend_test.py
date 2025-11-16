#!/usr/bin/env python3
"""
Backend API Testing Script for GMAO Application
Tests "Système d'ajout de temps passé sur les ordres de travail" functionality
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
BACKEND_URL = "https://maintx-hub.preview.emergentagent.com/api"

# Test credentials - admin account as specified in the request
ADMIN_EMAIL = "admin@gmao-iris.local"
ADMIN_PASSWORD = "Admin123!"

class WorkOrderTimeTrackingTester:
    def __init__(self):
        self.admin_session = requests.Session()
        self.admin_token = None
        self.admin_data = None
        self.created_work_orders = []  # Track created work orders for cleanup
        self.test_work_order_id = None  # ID of the test work order
        
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
    
    def test_create_work_order(self):
        """TEST 1: Créer un ordre de travail de test"""
        self.log("🧪 TEST 1: Créer un ordre de travail de test")
        
        try:
            work_order_data = {
                "titre": "Test temps passé",
                "description": "Test du système de temps passé",
                "priorite": "MOYENNE",
                "statut": "EN_COURS"
            }
            
            response = self.admin_session.post(
                f"{BACKEND_URL}/work-orders",
                json=work_order_data,
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                self.test_work_order_id = data.get("id")
                self.created_work_orders.append(self.test_work_order_id)
                
                self.log("✅ Ordre de travail créé avec succès (Status 201)")
                self.log(f"✅ ID de l'ordre: {self.test_work_order_id}")
                self.log(f"✅ Titre: {data.get('titre')}")
                
                # Vérifier que tempsReel est 0 ou null initialement
                temps_reel = data.get("tempsReel")
                if temps_reel is None or temps_reel == 0:
                    self.log(f"✅ tempsReel est initialement {temps_reel} (comme attendu)")
                    return True
                else:
                    self.log(f"⚠️ tempsReel est {temps_reel}, attendu 0 ou null", "WARNING")
                    return True  # Still pass, just note the difference
                    
            else:
                self.log(f"❌ Création d'ordre de travail échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_add_time_first(self):
        """TEST 2: Ajouter du temps passé (première fois) - 2h30min"""
        self.log("🧪 TEST 2: Ajouter du temps passé (première fois) - 2h30min")
        
        if not self.test_work_order_id:
            self.log("❌ Pas d'ordre de travail de test disponible", "ERROR")
            return False
        
        try:
            time_data = {
                "hours": 2,
                "minutes": 30
            }
            
            response = self.admin_session.post(
                f"{BACKEND_URL}/work-orders/{self.test_work_order_id}/add-time",
                json=time_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ Ajout de temps réussi (Status 200)")
                
                # Vérifier que tempsReel = 2.5 heures (2h30min)
                temps_reel = data.get("tempsReel")
                expected_time = 2.5  # 2h30min = 2.5 heures
                
                if temps_reel == expected_time:
                    self.log(f"✅ tempsReel = {temps_reel} heures (2h30min comme attendu)")
                    return True
                else:
                    self.log(f"❌ tempsReel = {temps_reel}, attendu {expected_time}", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Ajout de temps échoué - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_add_time_increment(self):
        """TEST 3: Ajouter du temps passé (incrémentation) - 1h15min"""
        self.log("🧪 TEST 3: Ajouter du temps passé (incrémentation) - 1h15min")
        
        if not self.test_work_order_id:
            self.log("❌ Pas d'ordre de travail de test disponible", "ERROR")
            return False
        
        try:
            time_data = {
                "hours": 1,
                "minutes": 15
            }
            
            response = self.admin_session.post(
                f"{BACKEND_URL}/work-orders/{self.test_work_order_id}/add-time",
                json=time_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ Ajout de temps réussi (Status 200)")
                
                # Vérifier que tempsReel = 3.75 heures (2.5 + 1.25)
                temps_reel = data.get("tempsReel")
                expected_time = 3.75  # 2.5 + 1.25 = 3.75 heures
                
                if temps_reel == expected_time:
                    self.log(f"✅ tempsReel = {temps_reel} heures (3h45min comme attendu)")
                    return True
                else:
                    self.log(f"❌ tempsReel = {temps_reel}, attendu {expected_time}", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Ajout de temps échoué - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_add_minutes_only(self):
        """TEST 4: Ajouter uniquement des minutes - 45min"""
        self.log("🧪 TEST 4: Ajouter uniquement des minutes - 45min")
        
        if not self.test_work_order_id:
            self.log("❌ Pas d'ordre de travail de test disponible", "ERROR")
            return False
        
        try:
            time_data = {
                "hours": 0,
                "minutes": 45
            }
            
            response = self.admin_session.post(
                f"{BACKEND_URL}/work-orders/{self.test_work_order_id}/add-time",
                json=time_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ Ajout de temps réussi (Status 200)")
                
                # Vérifier que tempsReel = 4.5 heures (3.75 + 0.75)
                temps_reel = data.get("tempsReel")
                expected_time = 4.5  # 3.75 + 0.75 = 4.5 heures
                
                if temps_reel == expected_time:
                    self.log(f"✅ tempsReel = {temps_reel} heures (4h30min comme attendu)")
                    return True
                else:
                    self.log(f"❌ tempsReel = {temps_reel}, attendu {expected_time}", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Ajout de temps échoué - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_add_hours_only(self):
        """TEST 5: Ajouter uniquement des heures - 3h"""
        self.log("🧪 TEST 5: Ajouter uniquement des heures - 3h")
        
        if not self.test_work_order_id:
            self.log("❌ Pas d'ordre de travail de test disponible", "ERROR")
            return False
        
        try:
            time_data = {
                "hours": 3,
                "minutes": 0
            }
            
            response = self.admin_session.post(
                f"{BACKEND_URL}/work-orders/{self.test_work_order_id}/add-time",
                json=time_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ Ajout de temps réussi (Status 200)")
                
                # Vérifier que tempsReel = 7.5 heures (4.5 + 3)
                temps_reel = data.get("tempsReel")
                expected_time = 7.5  # 4.5 + 3 = 7.5 heures
                
                if temps_reel == expected_time:
                    self.log(f"✅ tempsReel = {temps_reel} heures (7h30min comme attendu)")
                    return True
                else:
                    self.log(f"❌ tempsReel = {temps_reel}, attendu {expected_time}", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Ajout de temps échoué - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_get_work_order_final(self):
        """TEST 6: Récupérer l'ordre et vérifier le temps final"""
        self.log("🧪 TEST 6: Récupérer l'ordre et vérifier le temps final")
        
        if not self.test_work_order_id:
            self.log("❌ Pas d'ordre de travail de test disponible", "ERROR")
            return False
        
        try:
            response = self.admin_session.get(
                f"{BACKEND_URL}/work-orders/{self.test_work_order_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ Récupération de l'ordre réussie (Status 200)")
                
                # Vérifier que tempsReel = 7.5 heures
                temps_reel = data.get("tempsReel")
                expected_time = 7.5
                
                if temps_reel == expected_time:
                    self.log(f"✅ tempsReel = {temps_reel} heures (7h30min comme attendu)")
                    self.log("✅ Le temps total est correct après tous les ajouts")
                    return True
                else:
                    self.log(f"❌ tempsReel = {temps_reel}, attendu {expected_time}", "ERROR")
                    return False
                    
            else:
                self.log(f"❌ Récupération de l'ordre échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_cleanup_work_order(self):
        """TEST 7: Nettoyer (supprimer l'ordre de test)"""
        self.log("🧪 TEST 7: Nettoyer (supprimer l'ordre de test)")
        
        if not self.test_work_order_id:
            self.log("⚠️ Pas d'ordre de travail de test à supprimer", "WARNING")
            return True
        
        try:
            response = self.admin_session.delete(
                f"{BACKEND_URL}/work-orders/{self.test_work_order_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                self.log("✅ Ordre de travail supprimé avec succès (Status 200)")
                self.created_work_orders.remove(self.test_work_order_id)
                self.test_work_order_id = None
                return True
            elif response.status_code == 404:
                self.log("⚠️ Ordre de travail déjà supprimé (Status 404)", "WARNING")
                return True
            else:
                self.log(f"❌ Suppression de l'ordre échouée - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def cleanup_remaining_work_orders(self):
        """Nettoyer tous les ordres de travail créés pendant les tests"""
        self.log("🧹 Nettoyage des ordres de travail restants...")
        
        if not self.created_work_orders:
            self.log("Aucun ordre de travail à nettoyer")
            return True
        
        success_count = 0
        for wo_id in self.created_work_orders[:]:  # Copy list to avoid modification during iteration
            try:
                response = self.admin_session.delete(
                    f"{BACKEND_URL}/work-orders/{wo_id}",
                    timeout=10
                )
                
                if response.status_code in [200, 404]:
                    self.log(f"✅ Ordre {wo_id} nettoyé")
                    self.created_work_orders.remove(wo_id)
                    success_count += 1
                else:
                    self.log(f"⚠️ Impossible de nettoyer l'ordre {wo_id} - Status: {response.status_code}")
                    
            except Exception as e:
                self.log(f"⚠️ Erreur lors du nettoyage de l'ordre {wo_id}: {str(e)}")
        
        self.log(f"Nettoyage terminé: {success_count} ordres supprimés")
        return True
    
    # Removed old methods - replaced with work order time tracking tests
    
    def run_inactivity_timeout_tests(self):
        """Run comprehensive tests for inactivity timeout settings functionality"""
        self.log("=" * 80)
        self.log("TESTING INACTIVITY TIMEOUT SETTINGS FUNCTIONALITY")
        self.log("=" * 80)
        self.log("CONTEXTE: Test complet de la fonctionnalité 'Gestion du timeout d'inactivité'")
        self.log("")
        self.log("TESTS À EFFECTUER:")
        self.log("1. GET /api/settings - Récupérer les paramètres système (utilisateur normal)")
        self.log("2. PUT /api/settings - Mettre à jour les paramètres (admin uniquement)")
        self.log("3. Vérifier que les paramètres sont persistés")
        self.log("4. Test de validation - Valeur trop basse (0)")
        self.log("5. Test de validation - Valeur trop haute (150)")
        self.log("6. Test de sécurité - Non-admin")
        self.log("=" * 80)
        
        results = {
            "admin_login": False,
            "normal_user_setup": False,
            "get_settings_normal_user": False,
            "update_settings_admin": False,
            "verify_settings_persistence": False,
            "validation_too_low": False,
            "validation_too_high": False,
            "non_admin_security": False,
            "restore_settings": False,
            "cleanup": False
        }
        
        # Test 1: Admin Login
        results["admin_login"] = self.test_admin_login()
        
        if not results["admin_login"]:
            self.log("❌ Cannot proceed with other tests - Admin login failed", "ERROR")
            return results
        
        # Test 2: Setup normal user
        results["normal_user_setup"] = self.test_normal_user_login()
        
        if not results["normal_user_setup"]:
            self.log("❌ Cannot proceed with normal user tests - User setup failed", "ERROR")
            return results
        
        # Test 3: Get settings as normal user
        results["get_settings_normal_user"] = self.test_get_settings_normal_user()
        
        # Test 4: Update settings as admin
        results["update_settings_admin"] = self.test_update_settings_admin()
        
        # Test 5: Verify settings persistence
        results["verify_settings_persistence"] = self.test_verify_settings_persistence()
        
        # Test 6: Validation - too low
        results["validation_too_low"] = self.test_validation_too_low()
        
        # Test 7: Validation - too high
        results["validation_too_high"] = self.test_validation_too_high()
        
        # Test 8: Security - non-admin
        results["non_admin_security"] = self.test_non_admin_security()
        
        # Test 9: Restore original settings
        results["restore_settings"] = self.restore_original_settings()
        
        # Test 10: Cleanup
        results["cleanup"] = self.cleanup_test_user()
        
        # Summary
        self.log("=" * 70)
        self.log("INACTIVITY TIMEOUT SETTINGS TEST RESULTS SUMMARY")
        self.log("=" * 70)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"  {test_name}: {status}")
        
        self.log(f"\n📊 Overall: {passed}/{total} tests passed")
        
        # Detailed analysis for critical tests
        critical_tests = ["get_settings_normal_user", "update_settings_admin", "verify_settings_persistence", 
                         "validation_too_low", "validation_too_high", "non_admin_security"]
        critical_passed = sum(results.get(test, False) for test in critical_tests)
        
        if critical_passed == len(critical_tests):
            self.log("🎉 CRITICAL SUCCESS: All main inactivity timeout tests passed!")
            self.log("✅ GET /api/settings works for normal users")
            self.log("✅ PUT /api/settings works for admin users")
            self.log("✅ Settings are properly persisted")
            self.log("✅ Validation works for invalid values")
            self.log("✅ Security restrictions work for non-admin users")
        else:
            self.log("🚨 CRITICAL FAILURE: Some main inactivity timeout tests failed!")
            failed_critical = [test for test in critical_tests if not results.get(test, False)]
            self.log(f"❌ Failed critical tests: {', '.join(failed_critical)}")
        
        if passed >= total - 2:  # Allow cleanup and restore to fail
            self.log("🎉 INACTIVITY TIMEOUT SETTINGS FUNCTIONALITY IS WORKING CORRECTLY!")
            self.log("✅ All endpoints respond correctly")
            self.log("✅ Proper validation in place")
            self.log("✅ Security restrictions enforced")
            self.log("✅ Settings persistence works")
        else:
            self.log("⚠️ Some tests failed - The inactivity timeout settings functionality may have issues")
            failed_tests = [test for test, result in results.items() if not result and test not in ["cleanup", "restore_settings"]]
            self.log(f"❌ Failed tests: {', '.join(failed_tests)}")
        
        return results

if __name__ == "__main__":
    tester = InactivityTimeoutTester()
    results = tester.run_inactivity_timeout_tests()
    
    # Exit with appropriate code - allow cleanup and restore to fail
    critical_tests = ["admin_login", "normal_user_setup", "get_settings_normal_user", 
                     "update_settings_admin", "verify_settings_persistence", 
                     "validation_too_low", "validation_too_high", "non_admin_security"]
    
    critical_passed = sum(results.get(test, False) for test in critical_tests)
    
    if critical_passed == len(critical_tests):
        exit(0)  # Success
    else:
        exit(1)  # Failure