#!/usr/bin/env python3
"""
Backend API Testing for GMAO Atlas Permissions System
Tests the permissions management system endpoints
"""

import requests
import json
import sys
from typing import Dict, Any, Optional

# Backend URL from frontend/.env
BASE_URL = "https://maintenance-hub-60.preview.emergentagent.com/api"

class PermissionsAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.admin_token = None
        self.admin_user_id = None
        self.test_users = []
        self.session = requests.Session()
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages"""
        print(f"[{level}] {message}")
        
    def make_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None, token: str = None) -> requests.Response:
        """Make HTTP request with proper headers"""
        url = f"{self.base_url}{endpoint}"
        
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)
            
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        elif self.admin_token:
            request_headers["Authorization"] = f"Bearer {self.admin_token}"
            
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=request_headers)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, headers=request_headers)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, headers=request_headers)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=request_headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            self.log(f"{method} {endpoint} -> {response.status_code}")
            return response
        except Exception as e:
            self.log(f"Request failed: {e}", "ERROR")
            raise
            
    def setup_admin_user(self) -> bool:
        """Create or login as admin user"""
        self.log("Setting up admin user...")
        
        # Try to login first
        login_data = {
            "email": "admin@example.com",
            "password": "password123"
        }
        
        response = self.make_request("POST", "/auth/login", login_data, token=None)
        
        if response.status_code == 200:
            data = response.json()
            self.admin_token = data["access_token"]
            self.admin_user_id = data["user"]["id"]
            self.log(f"Admin login successful. User ID: {self.admin_user_id}")
            return True
        elif response.status_code == 401:
            # Admin doesn't exist, create it
            self.log("Admin user not found, creating...")
            register_data = {
                "nom": "Admin",
                "prenom": "System",
                "email": "admin@example.com",
                "telephone": "+33123456789",
                "password": "password123",
                "role": "ADMIN"
            }
            
            response = self.make_request("POST", "/auth/register", register_data, token=None)
            if response.status_code == 200:
                self.log("Admin user created successfully")
                # Now login
                return self.setup_admin_user()
            else:
                self.log(f"Failed to create admin user: {response.status_code} - {response.text}", "ERROR")
                return False
        else:
            self.log(f"Login failed: {response.status_code} - {response.text}", "ERROR")
            return False
            
    def test_register_with_permissions(self) -> bool:
        """Test POST /api/auth/register with default permissions"""
        self.log("\n=== Testing POST /api/auth/register with permissions ===")
        
        test_cases = [
            {
                "role": "VISUALISEUR",
                "email": "viewer@test.com",
                "expected_permissions": {
                    "dashboard": {"view": True, "edit": False, "delete": False},
                    "workOrders": {"view": True, "edit": False, "delete": False}
                }
            },
            {
                "role": "TECHNICIEN", 
                "email": "tech@test.com",
                "expected_permissions": {
                    "dashboard": {"view": True, "edit": False, "delete": False},
                    "workOrders": {"view": True, "edit": True, "delete": False}
                }
            },
            {
                "role": "ADMIN",
                "email": "admin2@test.com", 
                "expected_permissions": {
                    "dashboard": {"view": True, "edit": True, "delete": True},
                    "workOrders": {"view": True, "edit": True, "delete": True}
                }
            }
        ]
        
        success = True
        for case in test_cases:
            register_data = {
                "nom": "Test",
                "prenom": "User",
                "email": case["email"],
                "telephone": "+33987654321",
                "password": "testpass123",
                "role": case["role"]
            }
            
            response = self.make_request("POST", "/auth/register", register_data, token=None)
            
            if response.status_code == 200:
                user_data = response.json()
                self.test_users.append(user_data["id"])
                
                # Check if permissions are included in response
                if "permissions" in user_data:
                    permissions = user_data["permissions"]
                    for module, expected_perms in case["expected_permissions"].items():
                        if module in permissions:
                            actual_perms = permissions[module]
                            for perm_type, expected_value in expected_perms.items():
                                if actual_perms.get(perm_type) != expected_value:
                                    self.log(f"Permission mismatch for {case['role']} {module}.{perm_type}: expected {expected_value}, got {actual_perms.get(perm_type)}", "ERROR")
                                    success = False
                        else:
                            self.log(f"Module {module} missing in permissions for {case['role']}", "ERROR")
                            success = False
                    self.log(f"✓ User {case['email']} created with role {case['role']} and correct permissions")
                else:
                    self.log(f"✗ Permissions not included in register response for {case['role']}", "ERROR")
                    success = False
            else:
                self.log(f"✗ Failed to register {case['role']} user: {response.status_code} - {response.text}", "ERROR")
                success = False
                
        return success
        
    def test_invite_user(self) -> bool:
        """Test POST /api/users/invite"""
        self.log("\n=== Testing POST /api/users/invite ===")
        
        success = True
        
        # Test 1: Invite VISUALISEUR
        invite_data = {
            "nom": "Dupont",
            "prenom": "Jean",
            "email": "jean.dupont@company.com",
            "telephone": "+33123456789",
            "role": "VISUALISEUR"
        }
        
        response = self.make_request("POST", "/users/invite", invite_data)
        
        if response.status_code == 200:
            user_data = response.json()
            self.test_users.append(user_data["id"])
            self.log(f"✓ VISUALISEUR invited successfully: {user_data['email']}")
            
            # Verify default permissions for VISUALISEUR
            if "permissions" in user_data:
                perms = user_data["permissions"]
                if perms.get("dashboard", {}).get("view") != True or perms.get("dashboard", {}).get("edit") != False:
                    self.log("✗ Incorrect default permissions for VISUALISEUR", "ERROR")
                    success = False
                else:
                    self.log("✓ Default permissions correct for VISUALISEUR")
        else:
            self.log(f"✗ Failed to invite VISUALISEUR: {response.status_code} - {response.text}", "ERROR")
            success = False
            
        # Test 2: Invite TECHNICIEN
        invite_data = {
            "nom": "Martin",
            "prenom": "Sophie",
            "email": "sophie.martin@company.com", 
            "telephone": "+33987654321",
            "role": "TECHNICIEN"
        }
        
        response = self.make_request("POST", "/users/invite", invite_data)
        
        if response.status_code == 200:
            user_data = response.json()
            self.test_users.append(user_data["id"])
            self.log(f"✓ TECHNICIEN invited successfully: {user_data['email']}")
            
            # Verify default permissions for TECHNICIEN
            if "permissions" in user_data:
                perms = user_data["permissions"]
                if (perms.get("workOrders", {}).get("view") != True or 
                    perms.get("workOrders", {}).get("edit") != True or 
                    perms.get("workOrders", {}).get("delete") != False):
                    self.log("✗ Incorrect default permissions for TECHNICIEN", "ERROR")
                    success = False
                else:
                    self.log("✓ Default permissions correct for TECHNICIEN")
        else:
            self.log(f"✗ Failed to invite TECHNICIEN: {response.status_code} - {response.text}", "ERROR")
            success = False
            
        # Test 3: Invite ADMIN
        invite_data = {
            "nom": "Durand",
            "prenom": "Pierre",
            "email": "pierre.durand@company.com",
            "telephone": "+33555666777", 
            "role": "ADMIN"
        }
        
        response = self.make_request("POST", "/users/invite", invite_data)
        
        if response.status_code == 200:
            user_data = response.json()
            self.test_users.append(user_data["id"])
            self.log(f"✓ ADMIN invited successfully: {user_data['email']}")
            
            # Verify default permissions for ADMIN
            if "permissions" in user_data:
                perms = user_data["permissions"]
                if (perms.get("dashboard", {}).get("view") != True or 
                    perms.get("dashboard", {}).get("edit") != True or 
                    perms.get("dashboard", {}).get("delete") != True):
                    self.log("✗ Incorrect default permissions for ADMIN", "ERROR")
                    success = False
                else:
                    self.log("✓ Default permissions correct for ADMIN")
        else:
            self.log(f"✗ Failed to invite ADMIN: {response.status_code} - {response.text}", "ERROR")
            success = False
            
        # Test 4: Try to invite existing email (should fail)
        response = self.make_request("POST", "/users/invite", invite_data)
        
        if response.status_code == 400:
            self.log("✓ Correctly rejected duplicate email invitation")
        else:
            self.log(f"✗ Should have rejected duplicate email: {response.status_code}", "ERROR")
            success = False
            
        return success
        
    def test_get_user_permissions(self) -> bool:
        """Test GET /api/users/{user_id}/permissions"""
        self.log("\n=== Testing GET /api/users/{user_id}/permissions ===")
        
        if not self.test_users:
            self.log("✗ No test users available", "ERROR")
            return False
            
        success = True
        user_id = self.test_users[0]  # Use first test user
        
        response = self.make_request("GET", f"/users/{user_id}/permissions")
        
        if response.status_code == 200:
            permissions = response.json()
            self.log(f"✓ Successfully retrieved permissions for user {user_id}")
            
            # Verify structure
            required_modules = ["dashboard", "workOrders", "assets", "preventiveMaintenance", 
                              "inventory", "locations", "vendors", "reports"]
            required_perms = ["view", "edit", "delete"]
            
            for module in required_modules:
                if module not in permissions:
                    self.log(f"✗ Missing module {module} in permissions", "ERROR")
                    success = False
                else:
                    for perm in required_perms:
                        if perm not in permissions[module]:
                            self.log(f"✗ Missing permission {perm} in module {module}", "ERROR")
                            success = False
                            
            if success:
                self.log("✓ Permissions structure is correct")
        else:
            self.log(f"✗ Failed to get user permissions: {response.status_code} - {response.text}", "ERROR")
            success = False
            
        # Test with invalid user ID
        response = self.make_request("GET", "/users/invalid_id/permissions")
        if response.status_code == 404 or response.status_code == 400:
            self.log("✓ Correctly handled invalid user ID")
        else:
            self.log(f"✗ Should have returned 404/400 for invalid user ID: {response.status_code}", "ERROR")
            success = False
            
        return success
        
    def test_update_user_permissions(self) -> bool:
        """Test PUT /api/users/{user_id}/permissions"""
        self.log("\n=== Testing PUT /api/users/{user_id}/permissions ===")
        
        if not self.test_users:
            self.log("✗ No test users available", "ERROR")
            return False
            
        success = True
        user_id = self.test_users[0]  # Use first test user
        
        # Test 1: Update permissions as admin
        update_data = {
            "permissions": {
                "dashboard": {"view": True, "edit": True, "delete": False},
                "workOrders": {"view": True, "edit": True, "delete": True},
                "assets": {"view": True, "edit": False, "delete": False},
                "preventiveMaintenance": {"view": True, "edit": False, "delete": False},
                "inventory": {"view": True, "edit": False, "delete": False},
                "locations": {"view": True, "edit": False, "delete": False},
                "vendors": {"view": True, "edit": False, "delete": False},
                "reports": {"view": True, "edit": False, "delete": False}
            }
        }
        
        response = self.make_request("PUT", f"/users/{user_id}/permissions", update_data)
        
        if response.status_code == 200:
            user_data = response.json()
            self.log(f"✓ Successfully updated permissions for user {user_id}")
            
            # Verify the update
            if "permissions" in user_data:
                perms = user_data["permissions"]
                if (perms.get("workOrders", {}).get("delete") == True and 
                    perms.get("assets", {}).get("edit") == False):
                    self.log("✓ Permissions updated correctly")
                else:
                    self.log("✗ Permissions not updated as expected", "ERROR")
                    success = False
        else:
            self.log(f"✗ Failed to update permissions: {response.status_code} - {response.text}", "ERROR")
            success = False
            
        # Test 2: Try to modify own permissions (should fail)
        response = self.make_request("PUT", f"/users/{self.admin_user_id}/permissions", update_data)
        
        if response.status_code == 400:
            self.log("✓ Correctly prevented admin from modifying own permissions")
        else:
            self.log(f"✗ Should have prevented self-permission modification: {response.status_code}", "ERROR")
            success = False
            
        return success
        
    def test_delete_user(self) -> bool:
        """Test DELETE /api/users/{user_id}"""
        self.log("\n=== Testing DELETE /api/users/{user_id} ===")
        
        if not self.test_users:
            self.log("✗ No test users available", "ERROR")
            return False
            
        success = True
        
        # Test 1: Try to delete self (should fail)
        response = self.make_request("DELETE", f"/users/{self.admin_user_id}")
        
        if response.status_code == 400:
            self.log("✓ Correctly prevented admin from deleting themselves")
        else:
            self.log(f"✗ Should have prevented self-deletion: {response.status_code}", "ERROR")
            success = False
            
        # Test 2: Delete another user (should succeed)
        if len(self.test_users) > 1:
            user_to_delete = self.test_users[-1]  # Use last test user
            response = self.make_request("DELETE", f"/users/{user_to_delete}")
            
            if response.status_code == 200:
                self.log(f"✓ Successfully deleted user {user_to_delete}")
                self.test_users.remove(user_to_delete)
            else:
                self.log(f"✗ Failed to delete user: {response.status_code} - {response.text}", "ERROR")
                success = False
        else:
            self.log("⚠ Skipping user deletion test - not enough test users")
            
        # Test 3: Try to delete non-existent user
        response = self.make_request("DELETE", "/users/nonexistent_id")
        if response.status_code == 404 or response.status_code == 400:
            self.log("✓ Correctly handled deletion of non-existent user")
        else:
            self.log(f"✗ Should have returned 404/400 for non-existent user: {response.status_code}", "ERROR")
            success = False
            
        return success
        
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all permission system tests"""
        self.log("Starting GMAO Atlas Permissions System Tests...")
        self.log(f"Backend URL: {self.base_url}")
        
        results = {}
        
        # Setup
        if not self.setup_admin_user():
            self.log("Failed to setup admin user. Aborting tests.", "ERROR")
            return {"setup": False}
            
        # Run tests
        results["register_with_permissions"] = self.test_register_with_permissions()
        results["invite_user"] = self.test_invite_user()
        results["get_user_permissions"] = self.test_get_user_permissions()
        results["update_user_permissions"] = self.test_update_user_permissions()
        results["delete_user"] = self.test_delete_user()
        
        # Summary
        self.log("\n" + "="*50)
        self.log("TEST RESULTS SUMMARY")
        self.log("="*50)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            self.log(f"{test_name}: {status}")
            if result:
                passed += 1
                
        self.log(f"\nOverall: {passed}/{total} tests passed")
        
        return results

def main():
    """Main test execution"""
    tester = PermissionsAPITester()
    results = tester.run_all_tests()
    
    # Exit with error code if any tests failed
    if not all(results.values()):
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()