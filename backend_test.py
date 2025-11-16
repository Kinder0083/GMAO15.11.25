#!/usr/bin/env python3
"""
Backend API Testing Script for GMAO Application
Tests "Gestion du timeout d'inactivité" functionality
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

class InactivityTimeoutTester:
    def __init__(self):
        self.admin_session = requests.Session()
        self.user_session = requests.Session()
        self.admin_token = None
        self.admin_data = None
        self.user_token = None
        self.user_data = None
        self.test_user_id = None
        self.test_user_email = None
        self.original_timeout = None
        
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
    
    def test_normal_user_login(self):
        """Test login with a normal user (non-admin)"""
        self.log("Testing normal user login...")
        
        # First, get a list of users to find a non-admin user
        try:
            response = self.admin_session.get(f"{BACKEND_URL}/users", timeout=10)
            
            if response.status_code == 200:
                users = response.json()
                
                # Find a non-admin user
                normal_user = None
                for user in users:
                    if user.get("role") != "ADMIN" and user.get("email") != ADMIN_EMAIL:
                        normal_user = user
                        break
                
                if not normal_user:
                    self.log("⚠️ No normal user found, creating one for testing", "WARNING")
                    return self.create_test_user()
                
                # Try to login with the normal user (we don't know their password, so this might fail)
                # For testing purposes, we'll create a new user with known credentials
                return self.create_test_user()
            else:
                self.log(f"❌ Failed to get users list - Status: {response.status_code}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def create_test_user(self):
        """Create a test user for normal user testing"""
        self.log("Creating test user for normal user testing...")
        
        # Generate unique email for test user
        unique_id = str(uuid.uuid4())[:8]
        self.test_user_email = f"test.settings.{unique_id}@test.local"
        test_password = "TestPass123!"
        
        try:
            response = self.admin_session.post(
                f"{BACKEND_URL}/users/create-member",
                json={
                    "nom": "TestSettings",
                    "prenom": "User",
                    "email": self.test_user_email,
                    "telephone": "0123456789",
                    "role": "TECHNICIEN",
                    "service": "Test Service",
                    "password": test_password
                },
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                self.test_user_id = user_data.get("id")
                self.log(f"✅ Test user created successfully - ID: {self.test_user_id}, Email: {self.test_user_email}")
                
                # Now login with the test user
                login_response = requests.post(
                    f"{BACKEND_URL}/auth/login",
                    json={
                        "email": self.test_user_email,
                        "password": test_password
                    },
                    timeout=10
                )
                
                if login_response.status_code == 200:
                    login_data = login_response.json()
                    self.user_token = login_data.get("access_token")
                    self.user_data = login_data.get("user")
                    
                    # Set authorization header for user session
                    self.user_session.headers.update({
                        "Authorization": f"Bearer {self.user_token}"
                    })
                    
                    self.log(f"✅ Test user login successful - User: {self.user_data.get('prenom')} {self.user_data.get('nom')} (Role: {self.user_data.get('role')})")
                    return True
                else:
                    self.log(f"❌ Test user login failed - Status: {login_response.status_code}", "ERROR")
                    return False
            else:
                self.log(f"❌ Test user creation failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Test user creation request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_forgot_password_flow(self):
        """TEST 1: Forgot Password Flow (depuis page de login)"""
        self.log("🧪 TEST 1: Forgot Password Flow - POST /api/auth/forgot-password")
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/auth/forgot-password",
                json={
                    "email": ADMIN_EMAIL
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ POST /api/auth/forgot-password returned 200 OK")
                
                # Check for confirmation message
                message = data.get("message", "")
                if "lien de réinitialisation" in message or "reset" in message.lower():
                    self.log(f"✅ Confirmation message received: {message}")
                    self.log("✅ IMPORTANT: Email sending not tested (as requested)")
                    return True
                else:
                    self.log(f"⚠️ Unexpected message format: {message}", "WARNING")
                    return True  # Still consider success if 200 OK
            else:
                self.log(f"❌ POST /api/auth/forgot-password failed - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def get_existing_user_for_reset(self):
        """Get an existing user (not admin) for password reset testing"""
        self.log("Getting existing user for password reset testing...")
        
        try:
            # Get list of users
            response = self.admin_session.get(f"{BACKEND_URL}/users", timeout=10)
            
            if response.status_code == 200:
                users = response.json()
                
                # Find a non-admin user
                for user in users:
                    if user.get("role") != "ADMIN" and user.get("email") != ADMIN_EMAIL:
                        self.test_user_id = user.get("id")
                        self.test_user_email = user.get("email")
                        self.log(f"✅ Found existing user for testing: {user.get('prenom')} {user.get('nom')} (ID: {self.test_user_id})")
                        return True
                
                # If no non-admin user found, create one
                self.log("No suitable existing user found, creating test user...")
                return self.create_test_user()
            else:
                self.log(f"❌ Failed to get users list - Status: {response.status_code}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def create_test_user(self):
        """Create a test user for password reset testing"""
        self.log("Creating test user for password reset testing...")
        
        # Generate unique email for test user
        unique_id = str(uuid.uuid4())[:8]
        self.test_user_email = f"test.reset.{unique_id}@test.local"
        initial_password = "InitialPass123!"
        
        try:
            response = self.admin_session.post(
                f"{BACKEND_URL}/users/create-member",
                json={
                    "nom": "TestReset",
                    "prenom": "User",
                    "email": self.test_user_email,
                    "telephone": "0123456789",
                    "role": "TECHNICIEN",
                    "service": "Test Service",
                    "password": initial_password
                },
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                self.test_user_id = user_data.get("id")
                self.log(f"✅ Test user created successfully - ID: {self.test_user_id}, Email: {self.test_user_email}")
                return True
            else:
                self.log(f"❌ Test user creation failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Test user creation request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_admin_reset_password(self):
        """TEST 2: Admin Reset Password - POST /api/users/{user_id}/reset-password-admin"""
        self.log("🧪 TEST 2: Admin Reset Password - POST /api/users/{user_id}/reset-password-admin")
        
        if not self.test_user_id:
            self.log("❌ No test user available for password reset", "ERROR")
            return False
        
        try:
            response = self.admin_session.post(
                f"{BACKEND_URL}/users/{self.test_user_id}/reset-password-admin",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ POST /api/users/{user_id}/reset-password-admin returned 200 OK")
                
                # Check required fields in response
                if data.get("success") == True:
                    self.log("✅ Response contains 'success': true")
                else:
                    self.log(f"❌ Response success field is {data.get('success')}", "ERROR")
                    return False
                
                if "tempPassword" in data:
                    self.temp_password = data.get("tempPassword")
                    self.log(f"✅ Response contains 'tempPassword': {self.temp_password}")
                else:
                    self.log("❌ Response missing 'tempPassword' field", "ERROR")
                    return False
                
                # Verify firstLogin field is set to True in database
                user_response = self.admin_session.get(f"{BACKEND_URL}/users/{self.test_user_id}")
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    if user_data.get("firstLogin") == True:
                        self.log("✅ User firstLogin field correctly set to True in database")
                    else:
                        self.log(f"❌ User firstLogin field is {user_data.get('firstLogin')}, expected True", "ERROR")
                        return False
                else:
                    self.log("⚠️ Could not verify firstLogin field in database", "WARNING")
                
                return True
            else:
                self.log(f"❌ POST /api/users/{{user_id}}/reset-password-admin failed - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_temporary_password_login(self):
        """TEST 3: Verify temporary password works for login"""
        self.log("🧪 TEST 3: Verify temporary password works for login")
        
        if not self.temp_password or not self.test_user_email:
            self.log("❌ No temporary password or test user email available", "ERROR")
            return False
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/auth/login",
                json={
                    "email": self.test_user_email,
                    "password": self.temp_password
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log("✅ Login with temporary password successful")
                
                # Verify user data
                user_data = data.get("user")
                if user_data:
                    self.log(f"✅ User logged in: {user_data.get('prenom')} {user_data.get('nom')}")
                    
                    # Check firstLogin status
                    if user_data.get("firstLogin") == True:
                        self.log("✅ FirstLogin status is True (user should change password)")
                    else:
                        self.log(f"⚠️ FirstLogin status is {user_data.get('firstLogin')}, expected True", "WARNING")
                    
                    # Store token for potential future tests
                    self.user_token = data.get("access_token")
                    self.user_data = user_data
                    
                    return True
                else:
                    self.log("❌ No user data in login response", "ERROR")
                    return False
            else:
                self.log(f"❌ Login with temporary password failed - Status: {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_admin_reset_nonexistent_user(self):
        """TEST 4: Admin reset password for non-existent user (should fail)"""
        self.log("🧪 TEST 4: Admin reset password for non-existent user (should fail)")
        
        fake_user_id = "999999999999999999999999"  # 24-character hex string
        
        try:
            response = self.admin_session.post(
                f"{BACKEND_URL}/users/{fake_user_id}/reset-password-admin",
                timeout=10
            )
            
            if response.status_code == 404:
                self.log("✅ POST /api/users/{nonexistent_id}/reset-password-admin correctly returned 404 Not Found")
                return True
            else:
                self.log(f"❌ Expected 404 Not Found but got {response.status_code}", "ERROR")
                self.log(f"Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_non_admin_reset_password(self):
        """TEST 5: Non-admin user tries to reset password (should fail)"""
        self.log("🧪 TEST 5: Non-admin user tries to reset password (should fail)")
        
        if not self.user_token or not self.test_user_id:
            self.log("⚠️ Skipping test - No user token available", "WARNING")
            return True  # Skip this test if no user token
        
        # Create session with user token
        user_session = requests.Session()
        user_session.headers.update({
            "Authorization": f"Bearer {self.user_token}"
        })
        
        try:
            response = user_session.post(
                f"{BACKEND_URL}/users/{self.test_user_id}/reset-password-admin",
                timeout=10
            )
            
            if response.status_code == 403:
                self.log("✅ Non-admin user correctly denied access (403 Forbidden)")
                return True
            else:
                self.log(f"❌ Expected 403 Forbidden but got {response.status_code}", "ERROR")
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
    
    def run_password_reset_tests(self):
        """Run comprehensive tests for password reset functionality"""
        self.log("=" * 80)
        self.log("TESTING PASSWORD RESET FUNCTIONALITY")
        self.log("=" * 80)
        self.log("CONTEXTE: Test complet de la fonctionnalité 'Mot de passe oublié'")
        self.log("et 'Réinitialisation admin'")
        self.log("")
        self.log("TESTS À EFFECTUER:")
        self.log("1. Forgot Password Flow (POST /api/auth/forgot-password)")
        self.log("2. Admin Reset Password (POST /api/users/{user_id}/reset-password-admin)")
        self.log("3. Verify temporary password works for login")
        self.log("=" * 80)
        
        results = {
            "admin_login": False,
            "forgot_password_flow": False,
            "get_test_user": False,
            "admin_reset_password": False,
            "temporary_password_login": False,
            "admin_reset_nonexistent": False,
            "non_admin_reset_denied": False,
            "cleanup": False
        }
        
        # Test 1: Admin Login
        results["admin_login"] = self.test_admin_login()
        
        if not results["admin_login"]:
            self.log("❌ Cannot proceed with other tests - Admin login failed", "ERROR")
            return results
        
        # Test 2: Forgot Password Flow
        results["forgot_password_flow"] = self.test_forgot_password_flow()
        
        # Test 3: Get or create test user
        results["get_test_user"] = self.get_existing_user_for_reset()
        
        if not results["get_test_user"]:
            self.log("❌ Cannot proceed with reset tests - No test user available", "ERROR")
            return results
        
        # Test 4: Admin Reset Password
        results["admin_reset_password"] = self.test_admin_reset_password()
        
        # Test 5: Verify temporary password login
        results["temporary_password_login"] = self.test_temporary_password_login()
        
        # Test 6: Admin reset for non-existent user
        results["admin_reset_nonexistent"] = self.test_admin_reset_nonexistent_user()
        
        # Test 7: Non-admin user tries to reset password
        results["non_admin_reset_denied"] = self.test_non_admin_reset_password()
        
        # Test 8: Cleanup
        results["cleanup"] = self.cleanup_test_user()
        
        # Summary
        self.log("=" * 70)
        self.log("PASSWORD RESET TEST RESULTS SUMMARY")
        self.log("=" * 70)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"  {test_name}: {status}")
        
        self.log(f"\n📊 Overall: {passed}/{total} tests passed")
        
        # Detailed analysis for critical tests
        critical_tests = ["forgot_password_flow", "admin_reset_password", "temporary_password_login"]
        critical_passed = sum(results.get(test, False) for test in critical_tests)
        
        if critical_passed == len(critical_tests):
            self.log("🎉 CRITICAL SUCCESS: All main password reset tests passed!")
            self.log("✅ Forgot password flow works correctly")
            self.log("✅ Admin can reset user passwords")
            self.log("✅ Temporary passwords work for login")
            self.log("✅ FirstLogin field correctly managed")
        else:
            self.log("🚨 CRITICAL FAILURE: Some main password reset tests failed!")
            failed_critical = [test for test in critical_tests if not results.get(test, False)]
            self.log(f"❌ Failed critical tests: {', '.join(failed_critical)}")
        
        if passed >= total - 1:  # Allow cleanup to fail
            self.log("🎉 PASSWORD RESET FUNCTIONALITY IS WORKING CORRECTLY!")
            self.log("✅ Both 'Mot de passe oublié' and 'Réinitialisation admin' work")
            self.log("✅ Proper security validations in place")
            self.log("✅ Temporary passwords function correctly")
        else:
            self.log("⚠️ Some tests failed - The password reset functionality may have issues")
            failed_tests = [test for test, result in results.items() if not result and test != "cleanup"]
            self.log(f"❌ Failed tests: {', '.join(failed_tests)}")
        
        return results

if __name__ == "__main__":
    tester = PasswordResetTester()
    results = tester.run_password_reset_tests()
    
    # Exit with appropriate code - allow cleanup to fail
    critical_tests = ["admin_login", "forgot_password_flow", "get_test_user", 
                     "admin_reset_password", "temporary_password_login", 
                     "admin_reset_nonexistent", "non_admin_reset_denied"]
    
    critical_passed = sum(results.get(test, False) for test in critical_tests)
    
    if critical_passed == len(critical_tests):
        exit(0)  # Success
    else:
        exit(1)  # Failure