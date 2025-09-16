#!/usr/bin/env python3
"""
Test script for Food Premi API endpoints
Tests all major endpoints to verify functionality
"""

import requests
import json
from datetime import datetime

def test_endpoint(method, url, data=None, description=""):
    """Test an API endpoint"""
    print(f"\n[TEST] Testing: {description}")
    print(f"       {method} {url}")

    try:
        if method == 'GET':
            response = requests.get(url, timeout=5)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=5)
        elif method == 'PUT':
            response = requests.put(url, json=data, timeout=5)
        else:
            print(f"       [ERROR] Unsupported method: {method}")
            return False

        print(f"       Status: {response.status_code}")

        if response.status_code < 400:
            try:
                result = response.json()
                if result.get('success', True):
                    print(f"       [SUCCESS]: {result.get('message', 'OK')}")
                    if 'data' in result:
                        print(f"       Data count: {len(result['data']) if isinstance(result['data'], list) else 'object'}")
                    return True
                else:
                    print(f"       [API ERROR]: {result.get('error', 'Unknown error')}")
                    return False
            except:
                print(f"       [SUCCESS]: Non-JSON response")
                return True
        else:
            print(f"       [HTTP ERROR]: {response.text[:100] if response.text else 'No response'}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"       [CONNECTION ERROR]: Server not running on port 5000")
        return False
    except Exception as e:
        print(f"       [ERROR]: {str(e)}")
        return False

def main():
    base_url = "http://localhost:5000"

    print("=" * 60)
    print("FOOD PREMI API ENDPOINT TESTING")
    print("=" * 60)

    tests = [
        # Basic endpoints
        ("GET", f"{base_url}/", {}, "Home/Root endpoint"),
        ("GET", f"{base_url}/health", {}, "Health check endpoint"),

        # Menu endpoints
        ("GET", f"{base_url}/api/menu", {}, "Get all menu items"),
        ("GET", f"{base_url}/api/categories", {}, "Get menu categories"),

        # Offers endpoint
        ("GET", f"{base_url}/api/offers", {}, "Get all offers"),

        # Blog endpoints
        ("GET", f"{base_url}/api/blogs", {}, "Get all blog posts"),

        # Admin dashboard
        ("GET", f"{base_url}/api/admin/summary", {}, "Admin dashboard summary"),

        # Seed admin
        ("POST", f"{base_url}/api/seed-admin", {"email": "test@admin.com", "password": "admin123"}, "Seed admin user"),
    ]

    passed = 0
    total = len(tests)

    for method, url, data, description in tests:
        if test_endpoint(method, url, data, description):
            passed += 1

    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")

    if passed == total:
        print("ALL TESTS PASSED! System is working correctly.")
    else:
        print(f"{total - passed} tests failed. Please check the issues above.")

    print("=" * 60)

if __name__ == "__main__":
    main()