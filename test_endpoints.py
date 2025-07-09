#!/usr/bin/env python3
"""
Test des endpoints des concepts de dashboard
"""

import requests
import sys

BASE_URL = "http://localhost:5000"

def test_endpoint(url, expected_codes=[200, 302]):
    """Teste un endpoint et retourne True si le code est attendu"""
    try:
        response = requests.get(url, allow_redirects=False)
        if response.status_code in expected_codes:
            print(f"✅ {url} -> {response.status_code}")
            return True
        else:
            print(f"❌ {url} -> {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {url} -> Erreur: {e}")
        return False

def main():
    print("🧪 Test des endpoints des concepts de dashboard")
    print("=" * 60)
    
    endpoints = [
        "/dashboard/concepts",
        "/dashboard/concept1", 
        "/dashboard/concept2",
        "/dashboard/concept3"
    ]
    
    results = []
    for endpoint in endpoints:
        url = BASE_URL + endpoint
        results.append(test_endpoint(url))
    
    print()
    print(f"📊 Résultats: {sum(results)}/{len(results)} endpoints fonctionnels")
    
    if all(results):
        print("🎉 Tous les endpoints fonctionnent correctement!")
        sys.exit(0)
    else:
        print("❌ Certains endpoints ont des erreurs.")
        sys.exit(1)

if __name__ == "__main__":
    main() 