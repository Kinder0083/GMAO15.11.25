#!/usr/bin/env python3
"""
Backend API Testing Script for GMAO Application
Tests the existing endpoints to verify they still work after recent changes
"""

import requests
import json
import os
from datetime import datetime

# Use internal backend URL for testing
BACKEND_URL = "http://localhost:8001/api"

# Test credentials
TEST_EMAIL = "admin@example.com"
TEST_PASSWORD = "password123"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_data = None
        
    def log(self, message, level="INFO"):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_login(self):
        """Test POST /api/auth/login"""
        self.log("Testing login endpoint...")
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.user_data = data.get("user")
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.token}"
                })
                
                self.log(f"✅ Login successful - User: {self.user_data.get('prenom')} {self.user_data.get('nom')}")
                return True
            else:
                self.log(f"❌ Login failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Login request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_get_work_orders(self):
        """Test GET /api/work-orders"""
        self.log("Testing get work orders endpoint...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/work-orders",
                timeout=10
            )
            
            if response.status_code == 200:
                work_orders = response.json()
                self.log(f"✅ Get work orders successful - Found {len(work_orders)} work orders")
                
                # Return first work order for status update test
                if work_orders:
                    return work_orders[0]
                else:
                    self.log("⚠️ No work orders found for status update test", "WARNING")
                    return None
            else:
                self.log(f"❌ Get work orders failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Get work orders request failed - Error: {str(e)}", "ERROR")
            return None
    
    def test_update_work_order_status(self, work_order):
        """Test PUT /api/work-orders/{id} with status update"""
        if not work_order:
            self.log("❌ Cannot test status update - No work order available", "ERROR")
            return False
            
        work_order_id = work_order.get("id")
        current_status = work_order.get("statut")
        
        self.log(f"Testing work order status update for ID: {work_order_id}")
        self.log(f"Current status: {current_status}")
        
        # Choose a different status for testing
        new_status = "EN_COURS" if current_status != "EN_COURS" else "EN_ATTENTE"
        
        try:
            response = self.session.put(
                f"{BACKEND_URL}/work-orders/{work_order_id}",
                json={"statut": new_status},
                timeout=10
            )
            
            if response.status_code == 200:
                updated_wo = response.json()
                updated_status = updated_wo.get("statut")
                self.log(f"✅ Work order status update successful - New status: {updated_status}")
                
                # Verify the status was actually changed
                if updated_status == new_status:
                    self.log("✅ Status change verified")
                    return True
                else:
                    self.log(f"⚠️ Status not changed as expected - Expected: {new_status}, Got: {updated_status}", "WARNING")
                    return False
            else:
                self.log(f"❌ Work order status update failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Work order status update request failed - Error: {str(e)}", "ERROR")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        self.log("=" * 60)
        self.log("STARTING BACKEND API TESTS")
        self.log("=" * 60)
        
        results = {
            "login": False,
            "get_work_orders": False,
            "update_work_order_status": False
        }
        
        # Test 1: Login
        results["login"] = self.test_login()
        
        if not results["login"]:
            self.log("❌ Cannot proceed with other tests - Login failed", "ERROR")
            return results
        
        # Test 2: Get work orders
        work_order = self.test_get_work_orders()
        results["get_work_orders"] = work_order is not None
        
        # Test 3: Update work order status
        results["update_work_order_status"] = self.test_update_work_order_status(work_order)
        
        # Summary
        self.log("=" * 60)
        self.log("TEST RESULTS SUMMARY")
        self.log("=" * 60)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name}: {status}")
        
        self.log(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 ALL TESTS PASSED - Backend endpoints are working correctly!")
        else:
            self.log("⚠️ Some tests failed - Check the logs above for details")
        
        return results

if __name__ == "__main__":
    tester = BackendTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if all(results.values()):
        exit(0)  # Success
    else:
        exit(1)  # Failure