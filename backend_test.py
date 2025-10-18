#!/usr/bin/env python3
"""
Backend API Testing for GMAO Atlas Equipment Hierarchy System
Tests the equipment hierarchy management system endpoints
"""

import requests
import json
import sys
from typing import Dict, Any, Optional
from datetime import datetime

# Backend URL from frontend/.env
BASE_URL = "https://maintenance-hub-60.preview.emergentagent.com/api"

class EquipmentHierarchyTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.admin_token = None
        self.admin_user_id = None
        self.test_locations = []
        self.test_equipments = []
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
            
    def setup_test_location(self) -> Optional[str]:
        """Create a test location for equipment testing"""
        self.log("Creating test location...")
        
        location_data = {
            "nom": "Atelier Principal",
            "adresse": "123 Rue de l'Industrie",
            "ville": "Paris",
            "codePostal": "75001",
            "type": "Atelier"
        }
        
        response = self.make_request("POST", "/locations", location_data)
        
        if response.status_code == 200:
            location = response.json()
            location_id = location["id"]
            self.test_locations.append(location_id)
            self.log(f"✓ Test location created: {location_id}")
            return location_id
        else:
            self.log(f"✗ Failed to create test location: {response.status_code} - {response.text}", "ERROR")
            return None
            
    def test_create_parent_equipment(self, location_id: str) -> Optional[str]:
        """Test creating parent equipment without parent_id"""
        self.log("\n=== Testing POST /api/equipments - Parent Equipment ===")
        
        equipment_data = {
            "nom": "Machine Principale A",
            "categorie": "Machine de production",
            "emplacement_id": location_id,
            "statut": "OPERATIONNEL",
            "dateAchat": "2023-01-15T10:00:00Z",
            "coutAchat": 50000.0,
            "numeroSerie": "MP-A-001",
            "garantie": "2 ans"
        }
        
        response = self.make_request("POST", "/equipments", equipment_data)
        
        if response.status_code == 200:
            equipment = response.json()
            equipment_id = equipment["id"]
            self.test_equipments.append(equipment_id)
            
            # Verify parent equipment properties
            if equipment.get("parent_id") is None and equipment.get("hasChildren") == False:
                self.log(f"✓ Parent equipment created successfully: {equipment_id}")
                self.log(f"  - Name: {equipment['nom']}")
                self.log(f"  - Location: {equipment.get('emplacement', {}).get('nom', 'N/A')}")
                self.log(f"  - Parent ID: {equipment.get('parent_id', 'None')}")
                self.log(f"  - Has Children: {equipment.get('hasChildren', False)}")
                return equipment_id
            else:
                self.log(f"✗ Parent equipment properties incorrect", "ERROR")
                return None
        else:
            self.log(f"✗ Failed to create parent equipment: {response.status_code} - {response.text}", "ERROR")
            return None
        
    def test_create_sub_equipment_with_inheritance(self, parent_id: str) -> Optional[str]:
        """Test creating sub-equipment with location inheritance"""
        self.log("\n=== Testing POST /api/equipments - Sub-equipment with Location Inheritance ===")
        
        # Create sub-equipment WITHOUT specifying location_id (should inherit from parent)
        equipment_data = {
            "nom": "Sous-module A1",
            "categorie": "Composant",
            "parent_id": parent_id,
            "statut": "OPERATIONNEL",
            "dateAchat": "2023-02-15T10:00:00Z",
            "coutAchat": 5000.0,
            "numeroSerie": "SM-A1-001",
            "garantie": "1 an"
            # Note: NO emplacement_id specified - should inherit from parent
        }
        
        response = self.make_request("POST", "/equipments", equipment_data)
        
        if response.status_code == 200:
            equipment = response.json()
            equipment_id = equipment["id"]
            self.test_equipments.append(equipment_id)
            
            # Verify inheritance properties
            if (equipment.get("parent_id") == parent_id and 
                equipment.get("hasChildren") == False and
                equipment.get("emplacement") is not None):
                self.log(f"✓ Sub-equipment created with location inheritance: {equipment_id}")
                self.log(f"  - Name: {equipment['nom']}")
                self.log(f"  - Parent ID: {equipment.get('parent_id')}")
                self.log(f"  - Inherited Location: {equipment.get('emplacement', {}).get('nom', 'N/A')}")
                self.log(f"  - Has Children: {equipment.get('hasChildren', False)}")
                return equipment_id
            else:
                self.log(f"✗ Sub-equipment inheritance properties incorrect", "ERROR")
                self.log(f"  - Parent ID: {equipment.get('parent_id')} (expected: {parent_id})")
                self.log(f"  - Location: {equipment.get('emplacement')}")
                return None
        else:
            self.log(f"✗ Failed to create sub-equipment with inheritance: {response.status_code} - {response.text}", "ERROR")
            return None
            
    def test_create_sub_equipment_with_explicit_location(self, parent_id: str, location_id: str) -> Optional[str]:
        """Test creating sub-equipment with explicit location (no inheritance)"""
        self.log("\n=== Testing POST /api/equipments - Sub-equipment with Explicit Location ===")
        
        # Create another test location first
        location_data = {
            "nom": "Atelier Secondaire",
            "adresse": "456 Avenue de la Technologie",
            "ville": "Lyon",
            "codePostal": "69001",
            "type": "Atelier"
        }
        
        response = self.make_request("POST", "/locations", location_data)
        if response.status_code != 200:
            self.log(f"✗ Failed to create second location: {response.status_code}", "ERROR")
            return None
            
        second_location = response.json()
        second_location_id = second_location["id"]
        self.test_locations.append(second_location_id)
        
        # Create sub-equipment WITH explicit location_id (should NOT inherit)
        equipment_data = {
            "nom": "Sous-module A2",
            "categorie": "Composant",
            "parent_id": parent_id,
            "emplacement_id": second_location_id,  # Explicit location - different from parent
            "statut": "OPERATIONNEL",
            "dateAchat": "2023-03-15T10:00:00Z",
            "coutAchat": 3000.0,
            "numeroSerie": "SM-A2-001",
            "garantie": "1 an"
        }
        
        response = self.make_request("POST", "/equipments", equipment_data)
        
        if response.status_code == 200:
            equipment = response.json()
            equipment_id = equipment["id"]
            self.test_equipments.append(equipment_id)
            
            # Verify explicit location is used (not inherited)
            if (equipment.get("parent_id") == parent_id and 
                equipment.get("hasChildren") == False and
                equipment.get("emplacement", {}).get("id") == second_location_id):
                self.log(f"✓ Sub-equipment created with explicit location: {equipment_id}")
                self.log(f"  - Name: {equipment['nom']}")
                self.log(f"  - Parent ID: {equipment.get('parent_id')}")
                self.log(f"  - Explicit Location: {equipment.get('emplacement', {}).get('nom', 'N/A')}")
                self.log(f"  - Has Children: {equipment.get('hasChildren', False)}")
                return equipment_id
            else:
                self.log(f"✗ Sub-equipment explicit location properties incorrect", "ERROR")
                return None
        else:
            self.log(f"✗ Failed to create sub-equipment with explicit location: {response.status_code} - {response.text}", "ERROR")
            return None
        
    def test_get_equipments_with_hierarchy_info(self) -> bool:
        """Test GET /api/equipments with hasChildren and parent info"""
        self.log("\n=== Testing GET /api/equipments with Hierarchy Info ===")
        
        response = self.make_request("GET", "/equipments")
        
        if response.status_code == 200:
            equipments = response.json()
            self.log(f"✓ Successfully retrieved {len(equipments)} equipments")
            
            success = True
            parent_found = False
            child_found = False
            
            for equipment in equipments:
                equipment_id = equipment.get("id")
                
                # Check if this is one of our test equipments
                if equipment_id in self.test_equipments:
                    # Verify required hierarchy fields are present
                    if "hasChildren" not in equipment:
                        self.log(f"✗ Missing hasChildren field for equipment {equipment_id}", "ERROR")
                        success = False
                        continue
                        
                    # Check parent equipment (should have hasChildren = True if it has children)
                    if equipment.get("parent_id") is None:
                        parent_found = True
                        # This should be a parent - check if it has children
                        has_children = equipment.get("hasChildren", False)
                        self.log(f"  - Parent Equipment: {equipment.get('nom')} (hasChildren: {has_children})")
                        
                        if has_children:
                            self.log(f"    ✓ Parent correctly shows hasChildren = True")
                        else:
                            # This might be OK if no children were created yet
                            self.log(f"    ⚠ Parent shows hasChildren = False (may be correct if no children)")
                    else:
                        child_found = True
                        # This should be a child - verify parent info
                        parent_info = equipment.get("parent")
                        if parent_info and "id" in parent_info and "nom" in parent_info:
                            self.log(f"  - Child Equipment: {equipment.get('nom')} (parent: {parent_info.get('nom')})")
                            self.log(f"    ✓ Child has correct parent info")
                        else:
                            self.log(f"✗ Child equipment missing or incomplete parent info", "ERROR")
                            success = False
                            
            if not parent_found:
                self.log("⚠ No parent equipment found in results")
            if not child_found:
                self.log("⚠ No child equipment found in results")
                
            return success
        else:
            self.log(f"✗ Failed to get equipments: {response.status_code} - {response.text}", "ERROR")
            return False
        
    def test_get_equipment_detail(self) -> bool:
        """Test GET /api/equipments/{id} with parent and hasChildren info"""
        self.log("\n=== Testing GET /api/equipments/{id} ===")
        
        if not self.test_equipments:
            self.log("✗ No test equipments available", "ERROR")
            return False
            
        success = True
        
        for equipment_id in self.test_equipments:
            response = self.make_request("GET", f"/equipments/{equipment_id}")
            
            if response.status_code == 200:
                equipment = response.json()
                self.log(f"✓ Successfully retrieved equipment details: {equipment_id}")
                self.log(f"  - Name: {equipment.get('nom')}")
                self.log(f"  - Parent ID: {equipment.get('parent_id', 'None')}")
                self.log(f"  - Has Children: {equipment.get('hasChildren', False)}")
                
                # Verify required fields are present
                required_fields = ["id", "nom", "hasChildren"]
                for field in required_fields:
                    if field not in equipment:
                        self.log(f"✗ Missing required field {field}", "ERROR")
                        success = False
                        
                # If equipment has parent, verify parent info is included
                if equipment.get("parent_id"):
                    if "parent" not in equipment or not equipment["parent"]:
                        self.log(f"✗ Equipment has parent_id but missing parent info", "ERROR")
                        success = False
                    else:
                        parent_info = equipment["parent"]
                        if "id" not in parent_info or "nom" not in parent_info:
                            self.log(f"✗ Incomplete parent info", "ERROR")
                            success = False
                        else:
                            self.log(f"  - Parent Info: {parent_info.get('nom')} ({parent_info.get('id')})")
                            
            else:
                self.log(f"✗ Failed to get equipment details: {response.status_code} - {response.text}", "ERROR")
                success = False
                
        # Test with invalid equipment ID
        response = self.make_request("GET", "/equipments/invalid_id")
        if response.status_code == 404 or response.status_code == 400:
            self.log("✓ Correctly handled invalid equipment ID")
        else:
            self.log(f"✗ Should have returned 404/400 for invalid equipment ID: {response.status_code}", "ERROR")
            success = False
            
        return success
        
    def test_get_equipment_children(self) -> bool:
        """Test GET /api/equipments/{id}/children"""
        self.log("\n=== Testing GET /api/equipments/{id}/children ===")
        
        if not self.test_equipments:
            self.log("✗ No test equipments available", "ERROR")
            return False
            
        success = True
        parent_id = self.test_equipments[0]  # Use first equipment as parent
        
        response = self.make_request("GET", f"/equipments/{parent_id}/children")
        
        if response.status_code == 200:
            children = response.json()
            self.log(f"✓ Successfully retrieved children for equipment {parent_id}")
            self.log(f"  - Number of children: {len(children)}")
            
            # Verify each child has correct parent_id
            for child in children:
                if child.get("parent_id") != parent_id:
                    self.log(f"✗ Child {child.get('id')} has incorrect parent_id: {child.get('parent_id')}", "ERROR")
                    success = False
                else:
                    self.log(f"  - Child: {child.get('nom')} (ID: {child.get('id')})")
                    
                # Verify child has required hierarchy fields
                if "hasChildren" not in child:
                    self.log(f"✗ Child missing hasChildren field", "ERROR")
                    success = False
                    
                if "parent" not in child or not child["parent"]:
                    self.log(f"✗ Child missing parent info", "ERROR")
                    success = False
                    
        else:
            self.log(f"✗ Failed to get equipment children: {response.status_code} - {response.text}", "ERROR")
            success = False
            
        # Test with invalid equipment ID
        response = self.make_request("GET", "/equipments/invalid_id/children")
        if response.status_code == 404 or response.status_code == 400:
            self.log("✓ Correctly handled invalid equipment ID for children")
        else:
            self.log(f"✗ Should have returned 404/400 for invalid equipment ID: {response.status_code}", "ERROR")
            success = False
            
        return success
        
    def test_get_equipment_hierarchy(self) -> bool:
        """Test GET /api/equipments/{id}/hierarchy - Complete recursive hierarchy"""
        self.log("\n=== Testing GET /api/equipments/{id}/hierarchy ===")
        
        if not self.test_equipments:
            self.log("✗ No test equipments available", "ERROR")
            return False
            
        # First, create a 3-level hierarchy: parent -> child -> grandchild
        parent_id = self.test_equipments[0]
        
        # Create grandchild equipment (child of the first sub-equipment)
        if len(self.test_equipments) > 1:
            child_id = self.test_equipments[1]
            
            grandchild_data = {
                "nom": "Capteur A1-1",
                "categorie": "Capteur",
                "parent_id": child_id,
                "statut": "OPERATIONNEL",
                "dateAchat": "2023-04-15T10:00:00Z",
                "coutAchat": 500.0,
                "numeroSerie": "CAP-A1-1-001",
                "garantie": "6 mois"
            }
            
            response = self.make_request("POST", "/equipments", grandchild_data)
            if response.status_code == 200:
                grandchild = response.json()
                grandchild_id = grandchild["id"]
                self.test_equipments.append(grandchild_id)
                self.log(f"✓ Created grandchild equipment: {grandchild_id}")
            else:
                self.log(f"⚠ Failed to create grandchild equipment: {response.status_code}", "WARN")
        
        # Now test the hierarchy endpoint
        success = True
        response = self.make_request("GET", f"/equipments/{parent_id}/hierarchy")
        
        if response.status_code == 200:
            hierarchy = response.json()
            self.log(f"✓ Successfully retrieved hierarchy for equipment {parent_id}")
            
            # Verify root level
            if hierarchy.get("id") != parent_id:
                self.log(f"✗ Hierarchy root ID mismatch", "ERROR")
                success = False
            else:
                self.log(f"  - Root: {hierarchy.get('nom')} (ID: {hierarchy.get('id')})")
                
            # Verify children structure
            if "children" not in hierarchy:
                self.log(f"✗ Hierarchy missing children field", "ERROR")
                success = False
            else:
                children = hierarchy["children"]
                self.log(f"  - Direct children count: {len(children)}")
                
                # Check each child
                for child in children:
                    self.log(f"    - Child: {child.get('nom')} (ID: {child.get('id')})")
                    
                    # Check if child has its own children (grandchildren)
                    if "children" in child and len(child["children"]) > 0:
                        for grandchild in child["children"]:
                            self.log(f"      - Grandchild: {grandchild.get('nom')} (ID: {grandchild.get('id')})")
                            
                    # Verify hasChildren is correctly set
                    expected_has_children = "children" in child and len(child["children"]) > 0
                    actual_has_children = child.get("hasChildren", False)
                    if expected_has_children != actual_has_children:
                        self.log(f"✗ Child hasChildren mismatch: expected {expected_has_children}, got {actual_has_children}", "ERROR")
                        success = False
                        
        else:
            self.log(f"✗ Failed to get equipment hierarchy: {response.status_code} - {response.text}", "ERROR")
            success = False
            
        # Test with invalid equipment ID
        response = self.make_request("GET", "/equipments/invalid_id/hierarchy")
        if response.status_code == 404 or response.status_code == 400:
            self.log("✓ Correctly handled invalid equipment ID for hierarchy")
        else:
            self.log(f"✗ Should have returned 404/400 for invalid equipment ID: {response.status_code}", "ERROR")
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