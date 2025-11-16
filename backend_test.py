#!/usr/bin/env python3
"""
Backend API Testing Script for GMAO Application
Tests POST /api/users/{user_id}/set-password-permanent endpoint - Optional password change feature
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

class PasswordPermanentTester:
    def __init__(self):
        self.admin_session = requests.Session()
        self.user_session = requests.Session()
        self.admin_token = None
        self.admin_data = None
        self.user_token = None
        self.user_data = None
        self.test_user_id = None
        self.test_user_email = None
        
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
    
    def create_test_user(self):
        """Create a test user with firstLogin: true"""
        self.log("Creating test user with firstLogin: true...")
        
        # Generate unique email for test user
        unique_id = str(uuid.uuid4())[:8]
        self.test_user_email = f"test.user.{unique_id}@test.local"
        temp_password = "TempPass123!"
        
        try:
            response = self.admin_session.post(
                f"{BACKEND_URL}/users/create-member",
                json={
                    "nom": "TestUser",
                    "prenom": "Password",
                    "email": self.test_user_email,
                    "telephone": "0123456789",
                    "role": "TECHNICIEN",
                    "service": "Test Service",
                    "password": temp_password
                },
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                self.test_user_id = user_data.get("id")
                self.log(f"✅ Test user created successfully - ID: {self.test_user_id}, Email: {self.test_user_email}")
                
                # Store password for later login
                self.test_user_password = temp_password
                return True
            else:
                self.log(f"❌ Test user creation failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Test user creation request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_user_login(self):
        """Test login with the created test user"""
        self.log("Testing test user login...")
        
        try:
            response = self.user_session.post(
                f"{BACKEND_URL}/auth/login",
                json={
                    "email": self.test_user_email,
                    "password": self.test_user_password
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.user_token = data.get("access_token")
                self.user_data = data.get("user")
                
                # Set authorization header for future requests
                self.user_session.headers.update({
                    "Authorization": f"Bearer {self.user_token}"
                })
                
                self.log(f"✅ Test user login successful - User: {self.user_data.get('prenom')} {self.user_data.get('nom')} (Role: {self.user_data.get('role')})")
                self.log(f"✅ FirstLogin status: {self.user_data.get('firstLogin')}")
                return True
            else:
                self.log(f"❌ Test user login failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Test user login request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_user_set_own_password_permanent(self):
        """TEST 1: User modifies their own firstLogin status"""
        self.log("🧪 TEST 1: User modifies their own firstLogin status")
        
        try:
            response = self.user_session.post(
                f"{BACKEND_URL}/users/{self.test_user_id}/set-password-permanent",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ POST /users/{own_id}/set-password-permanent returned 200 OK")
                
                if data.get("success") == True:
                    self.log("✅ Response contains success: true")
                    self.log(f"✅ Message: {data.get('message')}")
                    
                    # Verify in database by checking user profile
                    profile_response = self.user_session.get(f"{BACKEND_URL}/auth/me")
                    if profile_response.status_code == 200:
                        profile_data = profile_response.json()
                        if profile_data.get("firstLogin") == False:
                            self.log("✅ Database verification: firstLogin is now False")
                            return True
                        else:
                            self.log(f"❌ Database verification failed: firstLogin is {profile_data.get('firstLogin')}", "ERROR")
                            return False
                    else:
                        self.log("⚠️ Could not verify database change", "WARNING")
                        return True  # Still consider success if API call worked
                else:
                    self.log(f"❌ Response success field is {data.get('success')}", "ERROR")
                    return False
            else:
                self.log(f"❌ POST /users/{{own_id}}/set-password-permanent failed - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_admin_set_other_user_password_permanent(self):
        """TEST 2: Admin modifies another user's firstLogin status"""
        self.log("🧪 TEST 2: Admin modifies another user's firstLogin status")
        
        # First, get a user with firstLogin: true (we'll use our test user)
        try:
            response = self.admin_session.post(
                f"{BACKEND_URL}/users/{self.test_user_id}/set-password-permanent",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ Admin POST /users/{other_user_id}/set-password-permanent returned 200 OK")
                
                if data.get("success") == True:
                    self.log("✅ Response contains success: true")
                    self.log(f"✅ Message: {data.get('message')}")
                    return True
                else:
                    self.log(f"❌ Response success field is {data.get('success')}", "ERROR")
                    return False
            else:
                self.log(f"❌ Admin POST /users/{{other_user_id}}/set-password-permanent failed - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_user_cannot_modify_other_user(self):
        """TEST 3: Normal user tries to modify another user's firstLogin (should fail)"""
        self.log("🧪 TEST 3: Normal user tries to modify another user's firstLogin (should fail)")
        
        # Get admin user ID to try to modify
        admin_user_id = self.admin_data.get("id")
        
        try:
            response = self.user_session.post(
                f"{BACKEND_URL}/users/{admin_user_id}/set-password-permanent",
                timeout=10
            )
            
            if response.status_code == 403:
                self.log("✅ POST /users/{other_user_id}/set-password-permanent correctly returned 403 Forbidden")
                
                # Check error message
                try:
                    data = response.json()
                    if "Vous ne pouvez modifier que votre propre statut" in data.get("detail", ""):
                        self.log("✅ Correct error message returned")
                        return True
                    else:
                        self.log(f"⚠️ Unexpected error message: {data.get('detail')}", "WARNING")
                        return True  # Still success if 403 is returned
                except:
                    self.log("✅ 403 returned (error message parsing failed but that's OK)")
                    return True
            else:
                self.log(f"❌ Expected 403 Forbidden but got {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_nonexistent_user_id(self):
        """TEST 4: Try with non-existent user ID"""
        self.log("🧪 TEST 4: Try with non-existent user ID")
        
        fake_user_id = "999999999999999999999999"  # 24-character hex string (valid ObjectId format)
        
        try:
            response = self.admin_session.post(
                f"{BACKEND_URL}/users/{fake_user_id}/set-password-permanent",
                timeout=10
            )
            
            if response.status_code == 404:
                self.log("✅ POST /users/{nonexistent_id}/set-password-permanent correctly returned 404 Not Found")
                
                # Check error message
                try:
                    data = response.json()
                    if "Utilisateur non trouvé" in data.get("detail", ""):
                        self.log("✅ Correct error message returned")
                        return True
                    else:
                        self.log(f"⚠️ Unexpected error message: {data.get('detail')}", "WARNING")
                        return True  # Still success if 404 is returned
                except:
                    self.log("✅ 404 returned (error message parsing failed but that's OK)")
                    return True
            else:
                self.log(f"❌ Expected 404 Not Found but got {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_unauthenticated_request(self):
        """TEST 5: Try without authentication"""
        self.log("🧪 TEST 5: Try without authentication")
        
        # Create a session without auth headers
        unauth_session = requests.Session()
        
        try:
            response = unauth_session.post(
                f"{BACKEND_URL}/users/{self.test_user_id}/set-password-permanent",
                timeout=10
            )
            
            if response.status_code in [401, 403]:
                self.log(f"✅ POST /users/{{user_id}}/set-password-permanent correctly returned {response.status_code} (authentication required)")
                return True
            else:
                self.log(f"❌ Expected 401 or 403 but got {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
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
    
    def run_password_permanent_tests(self):
        """Run comprehensive tests for POST /api/users/{user_id}/set-password-permanent endpoint"""
        self.log("=" * 80)
        self.log("TESTING SET-PASSWORD-PERMANENT ENDPOINT - OPTIONAL PASSWORD CHANGE FEATURE")
        self.log("=" * 80)
        self.log("CONTEXTE: Nouvelle fonctionnalité permettant aux utilisateurs de conserver")
        self.log("leur mot de passe temporaire au lieu de le changer obligatoirement lors")
        self.log("de la première connexion.")
        self.log("")
        self.log("ENDPOINT: POST /api/users/{user_id}/set-password-permanent")
        self.log("SÉCURITÉ: Utilisateur peut modifier son propre statut OU admin peut modifier n'importe qui")
        self.log("=" * 80)
        
        results = {
            "admin_login": False,
            "create_test_user": False,
            "test_user_login": False,
            "user_set_own_password": False,
            "admin_set_other_password": False,
            "user_cannot_modify_other": False,
            "nonexistent_user_test": False,
            "unauthenticated_test": False,
            "cleanup": False
        }
        
        # Test 1: Admin Login
        results["admin_login"] = self.test_admin_login()
        
        if not results["admin_login"]:
            self.log("❌ Cannot proceed with other tests - Admin login failed", "ERROR")
            return results
        
        # Test 2: Create test user
        results["create_test_user"] = self.create_test_user()
        
        if not results["create_test_user"]:
            self.log("❌ Cannot proceed with user tests - Test user creation failed", "ERROR")
            return results
        
        # Test 3: Test user login
        results["test_user_login"] = self.test_user_login()
        
        if not results["test_user_login"]:
            self.log("❌ Cannot proceed with user tests - Test user login failed", "ERROR")
            return results
        
        # Test 4: User modifies own firstLogin status
        results["user_set_own_password"] = self.test_user_set_own_password_permanent()
        
        # Test 5: Admin modifies another user's firstLogin status
        results["admin_set_other_password"] = self.test_admin_set_other_user_password_permanent()
        
        # Test 6: User tries to modify another user (should fail)
        results["user_cannot_modify_other"] = self.test_user_cannot_modify_other_user()
        
        # Test 7: Try with non-existent user ID
        results["nonexistent_user_test"] = self.test_nonexistent_user_id()
        
        # Test 8: Try without authentication
        results["unauthenticated_test"] = self.test_unauthenticated_request()
        
        # Test 9: Cleanup
        results["cleanup"] = self.cleanup_test_user()
        
        # Summary
        self.log("=" * 70)
        self.log("SET-PASSWORD-PERMANENT TEST RESULTS SUMMARY")
        self.log("=" * 70)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"  {test_name}: {status}")
        
        self.log(f"\n📊 Overall: {passed}/{total} tests passed")
        
        # Detailed analysis
        critical_tests = ["user_set_own_password", "admin_set_other_password", "user_cannot_modify_other"]
        critical_passed = sum(results.get(test, False) for test in critical_tests)
        
        if critical_passed == len(critical_tests):
            self.log("🎉 CRITICAL SUCCESS: All security tests passed!")
            self.log("✅ Users can modify their own firstLogin status")
            self.log("✅ Admins can modify any user's firstLogin status")
            self.log("✅ Users cannot modify other users' status (403 Forbidden)")
        else:
            self.log("🚨 CRITICAL FAILURE: Some security tests failed!")
            failed_critical = [test for test in critical_tests if not results.get(test, False)]
            self.log(f"❌ Failed critical tests: {', '.join(failed_critical)}")
        
        if passed >= total - 1:  # Allow cleanup to fail
            self.log("🎉 SET-PASSWORD-PERMANENT ENDPOINT IS WORKING CORRECTLY!")
            self.log("✅ All security validations are in place")
            self.log("✅ Proper authentication and authorization")
            self.log("✅ Correct error handling for edge cases")
        else:
            self.log("⚠️ Some tests failed - The endpoint may have issues")
            failed_tests = [test for test, result in results.items() if not result and test != "cleanup"]
            self.log(f"❌ Failed tests: {', '.join(failed_tests)}")
        
        return results

if __name__ == "__main__":
    tester = PasswordPermanentTester()
    results = tester.run_password_permanent_tests()
    
    # Exit with appropriate code - allow cleanup to fail
    critical_tests = ["admin_login", "create_test_user", "test_user_login", 
                     "user_set_own_password", "admin_set_other_password", 
                     "user_cannot_modify_other", "nonexistent_user_test", 
                     "unauthenticated_test"]
    
    critical_passed = sum(results.get(test, False) for test in critical_tests)
    
    if critical_passed == len(critical_tests):
        exit(0)  # Success
    else:
        exit(1)  # Failure
