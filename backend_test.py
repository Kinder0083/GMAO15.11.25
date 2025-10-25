#!/usr/bin/env python3
"""
Backend API Testing Script for GMAO Application
Tests the new Improvement Requests and Improvements functionality
"""

import requests
import json
import os
from datetime import datetime, timedelta

# Use the correct backend URL from frontend .env
BACKEND_URL = "https://gmao-improve.preview.emergentagent.com/api"

# Test credentials from review request
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
    
    # ==================== IMPROVEMENT REQUESTS TESTS ====================
    
    def test_create_improvement_request(self):
        """Test POST /api/improvement-requests - Create a new improvement request"""
        self.log("Testing create improvement request endpoint...")
        
        request_data = {
            "titre": "Amélioration système éclairage",
            "description": "Demande d'amélioration pour moderniser le système d'éclairage du bâtiment principal",
            "priorite": "MOYENNE",
            "type_demande": "AMELIORATION_INFRASTRUCTURE",
            "demandeur": "Jean Dupont",
            "service_demandeur": "Maintenance",
            "justification": "Réduction de la consommation énergétique et amélioration de l'éclairage"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/improvement-requests",
                json=request_data,
                timeout=10
            )
            
            if response.status_code == 201:
                request = response.json()
                self.log(f"✅ Create improvement request successful - ID: {request.get('id')}, Title: {request.get('titre')}")
                return request
            else:
                self.log(f"❌ Create improvement request failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Create improvement request failed - Error: {str(e)}", "ERROR")
            return None
    
    def test_get_improvement_requests(self):
        """Test GET /api/improvement-requests - Get all improvement requests"""
        self.log("Testing get improvement requests endpoint...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/improvement-requests",
                timeout=10
            )
            
            if response.status_code == 200:
                requests_list = response.json()
                self.log(f"✅ Get improvement requests successful - Found {len(requests_list)} requests")
                return requests_list
            else:
                self.log(f"❌ Get improvement requests failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Get improvement requests failed - Error: {str(e)}", "ERROR")
            return None
    
    def test_convert_to_improvement(self, request_id, assignee_id=None, date_limite=None):
        """Test POST /api/improvement-requests/{id}/convert-to-improvement - Convert request to improvement"""
        self.log(f"Testing convert improvement request {request_id} to improvement...")
        
        convert_data = {}
        if assignee_id:
            convert_data["assignee_id"] = assignee_id
        if date_limite:
            convert_data["date_limite"] = date_limite
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/improvement-requests/{request_id}/convert-to-improvement",
                json=convert_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                improvement_id = result.get('improvement_id')
                improvement_numero = result.get('improvement_numero')
                self.log(f"✅ Convert to improvement successful - Improvement ID: {improvement_id}, Number: {improvement_numero}")
                
                # Verify improvement number is >= 7000
                if improvement_numero and int(improvement_numero) >= 7000:
                    self.log(f"✅ Improvement number validation passed - Number {improvement_numero} >= 7000")
                else:
                    self.log(f"❌ Improvement number validation failed - Number {improvement_numero} < 7000", "ERROR")
                
                return result
            else:
                self.log(f"❌ Convert to improvement failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Convert to improvement failed - Error: {str(e)}", "ERROR")
            return None
    
    def test_get_improvement_request_details(self, request_id):
        """Test GET /api/improvement-requests/{id} - Get improvement request details"""
        self.log(f"Testing get improvement request details {request_id}...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/improvement-requests/{request_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                request = response.json()
                self.log(f"✅ Get improvement request details successful - Title: {request.get('titre')}")
                return request
            else:
                self.log(f"❌ Get improvement request details failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Get improvement request details failed - Error: {str(e)}", "ERROR")
            return None
    
    def test_get_statistics(self, meter_id, period="month"):
        """Test GET /api/meters/{meter_id}/statistics - Get meter statistics"""
        self.log(f"Testing get statistics for meter {meter_id}...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/meters/{meter_id}/statistics?period={period}",
                timeout=10
            )
            
            if response.status_code == 200:
                stats = response.json()
                self.log(f"✅ Get statistics successful - Total consumption: {stats.get('total_consommation')}, Total cost: {stats.get('total_cout')}")
                return stats
            else:
                self.log(f"❌ Get statistics failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Get statistics request failed - Error: {str(e)}", "ERROR")
            return None
    
    def verify_consumption_calculation(self, readings):
        """Verify that consumption calculation is working correctly"""
        self.log("Verifying consumption calculations...")
        
        if len(readings) < 2:
            self.log("⚠️ Need at least 2 readings to verify consumption calculation", "WARNING")
            return True
        
        # Sort readings by date
        sorted_readings = sorted(readings, key=lambda x: x['date_releve'])
        
        for i in range(1, len(sorted_readings)):
            current = sorted_readings[i]
            previous = sorted_readings[i-1]
            
            expected_consumption = current['valeur'] - previous['valeur']
            actual_consumption = current.get('consommation', 0)
            
            if abs(expected_consumption - actual_consumption) > 0.01:  # Allow small floating point differences
                self.log(f"❌ Consumption calculation error - Expected: {expected_consumption}, Got: {actual_consumption}", "ERROR")
                return False
        
        self.log("✅ Consumption calculations are correct")
        return True
    
    def verify_cost_calculation(self, readings, expected_unit_price):
        """Verify that cost calculation is working correctly"""
        self.log("Verifying cost calculations...")
        
        for reading in readings:
            consumption = reading.get('consommation', 0)
            cost = reading.get('cout', 0)
            unit_price = reading.get('prix_unitaire', 0)
            
            if consumption > 0 and unit_price:
                expected_cost = consumption * unit_price
                if abs(expected_cost - cost) > 0.01:  # Allow small floating point differences
                    self.log(f"❌ Cost calculation error - Expected: {expected_cost}, Got: {cost}", "ERROR")
                    return False
        
        self.log("✅ Cost calculations are correct")
        return True
    
    def test_delete_reading(self, reading_id):
        """Test DELETE /api/readings/{reading_id} - Delete a reading"""
        self.log(f"Testing delete reading {reading_id}...")
        
        try:
            response = self.session.delete(
                f"{BACKEND_URL}/readings/{reading_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Delete reading successful - {result.get('message')}")
                return True
            else:
                self.log(f"❌ Delete reading failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Delete reading request failed - Error: {str(e)}", "ERROR")
            return False
    
    def test_meter_soft_delete(self, meter_id):
        """Test DELETE /api/meters/{meter_id} - Soft delete a meter"""
        self.log(f"Testing soft delete meter {meter_id}...")
        
        try:
            response = self.session.delete(
                f"{BACKEND_URL}/meters/{meter_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Soft delete meter successful - {result.get('message')}")
                return True
            else:
                self.log(f"❌ Soft delete meter failed - Status: {response.status_code}, Response: {response.text}", "ERROR")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Soft delete meter request failed - Error: {str(e)}", "ERROR")
            return False
    
    def run_all_tests(self):
        """Run all backend tests for meters functionality"""
        self.log("=" * 60)
        self.log("STARTING METERS (COMPTEURS) API TESTS")
        self.log("=" * 60)
        
        results = {
            "login": False,
            "create_meter": False,
            "get_meters": False,
            "create_first_reading": False,
            "create_second_reading": False,
            "get_readings": False,
            "get_statistics": False,
            "consumption_calculation": False,
            "cost_calculation": False,
            "delete_reading": False,
            "soft_delete_meter": False
        }
        
        # Test 1: Login
        results["login"] = self.test_login()
        
        if not results["login"]:
            self.log("❌ Cannot proceed with other tests - Login failed", "ERROR")
            return results
        
        # Test 2: Create meter
        meter = self.test_create_meter()
        results["create_meter"] = meter is not None
        
        if not meter:
            self.log("❌ Cannot proceed with reading tests - Meter creation failed", "ERROR")
            return results
        
        meter_id = meter["id"]
        
        # Test 3: Get meters
        meters = self.test_get_meters()
        results["get_meters"] = meters is not None and len(meters) > 0
        
        # Test 4: Create first reading
        first_reading = self.test_create_reading(meter_id, 1000.0, "Premier relevé")
        results["create_first_reading"] = first_reading is not None
        
        # Test 5: Create second reading (to test consumption calculation)
        second_reading = self.test_create_reading(meter_id, 1150.0, "Deuxième relevé")
        results["create_second_reading"] = second_reading is not None
        
        # Test 6: Get readings
        readings = self.test_get_readings(meter_id)
        results["get_readings"] = readings is not None and len(readings) >= 2
        
        # Test 7: Get statistics
        stats = self.test_get_statistics(meter_id, "month")
        results["get_statistics"] = stats is not None
        
        # Test 8: Verify consumption calculation
        if readings:
            results["consumption_calculation"] = self.verify_consumption_calculation(readings)
        
        # Test 9: Verify cost calculation
        if readings:
            results["cost_calculation"] = self.verify_cost_calculation(readings, 0.15)
        
        # Test 10: Delete a reading
        if readings and len(readings) > 0:
            reading_to_delete = readings[0]["id"]
            results["delete_reading"] = self.test_delete_reading(reading_to_delete)
        
        # Test 11: Soft delete the meter
        if meter:
            results["soft_delete_meter"] = self.test_meter_soft_delete(meter_id)
        
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
            self.log("🎉 ALL METERS TESTS PASSED - New compteurs functionality is working correctly!")
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