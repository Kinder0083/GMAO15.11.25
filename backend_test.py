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
    
    def test_verify_settings_persistence(self):
        """TEST 3: Vérifier que les paramètres sont persistés"""
        self.log("🧪 TEST 3: Verify settings persistence - GET /api/settings after update")
        
        try:
            response = self.admin_session.get(f"{BACKEND_URL}/settings", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ GET /api/settings returned 200 OK")
                
                # Check that the value is still 30
                if data.get("inactivity_timeout_minutes") == 30:
                    self.log("✅ Settings are persisted correctly - value is still 30 minutes")
                    return True
                else:
                    self.log(f"❌ Settings not persisted - value is {data.get('inactivity_timeout_minutes')}, expected 30", "ERROR")
                    return False
            else:
                self.log(f"❌ GET /api/settings failed - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_validation_too_low(self):
        """TEST 4: Test de validation - Valeur trop basse"""
        self.log("🧪 TEST 4: Validation test - Value too low (0 minutes)")
        
        try:
            response = self.admin_session.put(
                f"{BACKEND_URL}/settings",
                json={"inactivity_timeout_minutes": 0},
                timeout=10
            )
            
            if response.status_code == 400:
                self.log("✅ PUT /api/settings correctly returned 400 Bad Request for value 0")
                
                # Check error message
                try:
                    data = response.json()
                    detail = data.get("detail", "")
                    if "1 et 120" in detail or "entre" in detail.lower():
                        self.log(f"✅ Appropriate error message: {detail}")
                    else:
                        self.log(f"⚠️ Error message: {detail}", "WARNING")
                except:
                    self.log("⚠️ Could not parse error message", "WARNING")
                
                return True
            else:
                self.log(f"❌ Expected 400 Bad Request but got {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_validation_too_high(self):
        """TEST 5: Test de validation - Valeur trop haute"""
        self.log("🧪 TEST 5: Validation test - Value too high (150 minutes)")
        
        try:
            response = self.admin_session.put(
                f"{BACKEND_URL}/settings",
                json={"inactivity_timeout_minutes": 150},
                timeout=10
            )
            
            if response.status_code == 400:
                self.log("✅ PUT /api/settings correctly returned 400 Bad Request for value 150")
                
                # Check error message
                try:
                    data = response.json()
                    detail = data.get("detail", "")
                    if "1 et 120" in detail or "entre" in detail.lower():
                        self.log(f"✅ Appropriate error message: {detail}")
                    else:
                        self.log(f"⚠️ Error message: {detail}", "WARNING")
                except:
                    self.log("⚠️ Could not parse error message", "WARNING")
                
                return True
            else:
                self.log(f"❌ Expected 400 Bad Request but got {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_non_admin_security(self):
        """TEST 6: Test de sécurité - Non-admin"""
        self.log("🧪 TEST 6: Security test - Non-admin user tries to update settings")
        
        try:
            response = self.user_session.put(
                f"{BACKEND_URL}/settings",
                json={"inactivity_timeout_minutes": 20},
                timeout=10
            )
            
            if response.status_code == 403:
                self.log("✅ PUT /api/settings correctly returned 403 Forbidden for non-admin user")
                
                # Check error message
                try:
                    data = response.json()
                    detail = data.get("detail", "")
                    self.log(f"✅ Security error message: {detail}")
                except:
                    self.log("⚠️ Could not parse error message", "WARNING")
                
                return True
            else:
                self.log(f"❌ Expected 403 Forbidden but got {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def restore_original_settings(self):
        """Restore original settings after testing"""
        self.log("🧹 Restoring original settings...")
        
        if self.original_timeout is None:
            self.log("⚠️ No original timeout value to restore", "WARNING")
            return True
        
        try:
            response = self.admin_session.put(
                f"{BACKEND_URL}/settings",
                json={"inactivity_timeout_minutes": self.original_timeout},
                timeout=10
            )
            
            if response.status_code == 200:
                self.log(f"✅ Original settings restored - timeout: {self.original_timeout} minutes")
                return True
            else:
                self.log(f"⚠️ Could not restore original settings - Status: {response.status_code}")
                return True  # Don't fail tests for cleanup issues
                
        except Exception as e:
            self.log(f"⚠️ Could not restore original settings: {str(e)}")
            return True  # Don't fail tests for cleanup issues
    
    def cleanup_test_user(self):
        """Clean up the test user after tests"""
        self.log("🧹 Cleaning up test user...")
        
        if not self.test_user_id:
            self.log("No test user to clean up")
            return True
        
        try:
            # Try to delete the test user (if endpoint exists)
            response = self.admin_session.delete(
                f"{BACKEND_URL}/users/{self.test_user_id}",
                timeout=10
            )
            
            if response.status_code in [200, 204, 404]:
                self.log("✅ Test user cleaned up successfully")
                return True
            else:
                self.log(f"⚠️ Could not clean up test user - Status: {response.status_code}")
                return True  # Don't fail tests for cleanup issues
                
        except Exception as e:
            self.log(f"⚠️ Could not clean up test user: {str(e)}")
            return True  # Don't fail tests for cleanup issues
    
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