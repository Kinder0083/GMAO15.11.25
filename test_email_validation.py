#!/usr/bin/env python3

import sys
sys.path.append('/app/backend')

from models import UserBase, LoginRequest

def test_email_validation():
    print("Testing email validation...")
    
    # Test valid regular email
    try:
        user1 = UserBase(
            nom="Test", 
            prenom="User", 
            email="test@example.com"
        )
        print("✓ Regular email works:", user1.email)
    except Exception as e:
        print("✗ Regular email failed:", e)
    
    # Test valid .local email
    try:
        user2 = UserBase(
            nom="Test", 
            prenom="User", 
            email="admin@server.local"
        )
        print("✓ .local email works:", user2.email)
    except Exception as e:
        print("✗ .local email failed:", e)
    
    # Test invalid email
    try:
        user3 = UserBase(
            nom="Test", 
            prenom="User", 
            email="invalid-email"
        )
        print("✗ Invalid email should have failed but didn't:", user3.email)
    except Exception as e:
        print("✓ Invalid email correctly rejected:", e)
    
    # Test LoginRequest with .local
    try:
        login = LoginRequest(
            email="admin@server.local",
            password="test123"
        )
        print("✓ LoginRequest with .local works:", login.email)
    except Exception as e:
        print("✗ LoginRequest with .local failed:", e)

if __name__ == "__main__":
    test_email_validation()