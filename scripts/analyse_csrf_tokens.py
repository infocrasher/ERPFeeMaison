#!/usr/bin/env python3
"""
Script d'analyse des tokens CSRF dans les formulaires POST
Vérifie tous les templates pour identifier les formulaires sans protection CSRF
"""

import os
import re
from pathlib import Path
from collections import defaultdict

def find_post_forms(template_dir):
    """Trouve tous les formulaires POST dans les templates"""
    forms = []
    template_dir = Path(template_dir)
    
    for template_file in template_dir.rglob("*.html"):
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Chercher les formulaires POST
            post_form_pattern = r'<form[^>]*method=["\']POST["\'][^>]*>'
            matches = re.finditer(post_form_pattern, content, re.IGNORECASE)
            
            for match in matches:
                form_start = match.start()
                # Trouver la fin du formulaire (balise </form>)
                form_end = content.find('</form>', form_start)
                if form_end == -1:
                    form_end = len(content)
                
                form_content = content[form_start:form_end]
                
                # Vérifier si le token CSRF est présent
                has_csrf = bool(re.search(
                    r'csrf_token|CSRF|{{.*csrf_token.*}}',
                    form_content,
                    re.IGNORECASE
                ))
                
                # Extraire l'action du formulaire si présente
                action_match = re.search(r'action=["\']([^"\']+)["\']', form_content, re.IGNORECASE)
                action = action_match.group(1) if action_match else None
                
                forms.append({
                    'file': str(template_file.relative_to(template_dir)),
                    'line': content[:form_start].count('\n') + 1,
                    'has_csrf': has_csrf,
                    'action': action,
                    'form_tag': match.group(0)
                })
        except Exception as e:
            print(f"Erreur lecture {template_file}: {e}")
    
    return forms

def find_api_endpoints(app_dir):
    """Trouve tous les endpoints API POST qui nécessitent CSRF"""
    endpoints = []
    app_dir = Path(app_dir)
    
    for py_file in app_dir.rglob("*.py"):
        if '__pycache__' in str(py_file):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Chercher les routes POST
            route_pattern = r'@\w+\.route\(["\']([^"\']+)["\'][^)]*methods=\[.*?["\']POST["\'].*?\)'
            matches = re.finditer(route_pattern, content, re.IGNORECASE | re.DOTALL)
            
            for match in matches:
                route_path = match.group(1)
                
                # Vérifier si exempté de CSRF
                route_start = match.start()
                route_end = content.find('\n', route_start)
                route_line = content[route_start:route_end] if route_end != -1 else content[route_start:]
                
                is_exempt = '@csrf.exempt' in content[:route_start] or 'csrf.exempt' in route_line
                
                # Chercher la fonction associée
                func_match = re.search(r'def\s+(\w+)\s*\(', content[match.end():match.end()+200])
                func_name = func_match.group(1) if func_match else 'unknown'
                
                endpoints.append({
                    'file': str(py_file.relative_to(app_dir)),
                    'route': route_path,
                    'function': func_name,
                    'is_exempt': is_exempt,
                    'line': content[:match.start()].count('\n') + 1
                })
        except Exception as e:
            print(f"Erreur lecture {py_file}: {e}")
    
    return endpoints

def check_csrf_in_javascript(template_dir):
    """Vérifie les requêtes fetch/ajax POST dans le JavaScript"""
    js_requests = []
    template_dir = Path(template_dir)
    
    for template_file in template_dir.rglob("*.html"):
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Chercher les requêtes fetch POST
            fetch_pattern = r'fetch\(["\']([^"\']+)["\'][^)]*method:\s*["\']POST["\']'
            matches = re.finditer(fetch_pattern, content, re.IGNORECASE | re.DOTALL)
            
            for match in matches:
                url = match.group(1)
                request_start = match.start()
                # Chercher le contexte autour (1000 caractères)
                context_start = max(0, request_start - 500)
                context_end = min(len(content), match.end() + 500)
                context = content[context_start:context_end]
                
                # Vérifier si X-CSRFToken est présent
                has_csrf_header = bool(re.search(
                    r'X-CSRFToken|X-Csrf-Token|csrf_token|getCsrfToken',
                    context,
                    re.IGNORECASE
                ))
                
                js_requests.append({
                    'file': str(template_file.relative_to(template_dir)),
                    'url': url,
                    'has_csrf': has_csrf_header,
                    'line': content[:request_start].count('\n') + 1
                })
        except Exception as e:
            print(f"Erreur lecture {template_file}: {e}")
    
    return js_requests

def main():
    base_dir = Path(__file__).parent.parent
    template_dir = base_dir / 'app' / 'templates'
    app_dir = base_dir / 'app'
    
    print("=" * 80)
    print("ANALYSE COMPLÈTE DES TOKENS CSRF")
    print("=" * 80)
    print()
    
    # 1. Analyser les formulaires HTML
    print("1. ANALYSE DES FORMULAIRES POST HTML")
    print("-" * 80)
    forms = find_post_forms(template_dir)
    
    forms_with_csrf = [f for f in forms if f['has_csrf']]
    forms_without_csrf = [f for f in forms if not f['has_csrf']]
    
    print(f"Total formulaires POST trouvés: {len(forms)}")
    print(f"✅ Avec token CSRF: {len(forms_with_csrf)}")
    print(f"❌ Sans token CSRF: {len(forms_without_csrf)}")
    print()
    
    if forms_without_csrf:
        print("⚠️  FORMULAIRES SANS TOKEN CSRF:")
        print()
        for form in forms_without_csrf:
            print(f"  ❌ {form['file']}:{form['line']}")
            if form['action']:
                print(f"     Action: {form['action']}")
            print(f"     Tag: {form['form_tag'][:80]}...")
            print()
    
    # 2. Analyser les endpoints API
    print("2. ANALYSE DES ENDPOINTS API POST")
    print("-" * 80)
    endpoints = find_api_endpoints(app_dir)
    
    exempt_endpoints = [e for e in endpoints if e['is_exempt']]
    protected_endpoints = [e for e in endpoints if not e['is_exempt']]
    
    print(f"Total endpoints POST trouvés: {len(endpoints)}")
    print(f"✅ Protégés CSRF: {len(protected_endpoints)}")
    print(f"⚠️  Exemptés CSRF: {len(exempt_endpoints)}")
    print()
    
    if exempt_endpoints:
        print("⚠️  ENDPOINTS EXEMPTÉS DE CSRF:")
        print()
        for endpoint in exempt_endpoints:
            print(f"  ⚠️  {endpoint['file']}:{endpoint['line']}")
            print(f"     Route: {endpoint['route']}")
            print(f"     Fonction: {endpoint['function']}")
            print()
    
    # 3. Analyser les requêtes JavaScript
    print("3. ANALYSE DES REQUÊTES FETCH/AJAX POST")
    print("-" * 80)
    js_requests = check_csrf_in_javascript(template_dir)
    
    js_with_csrf = [r for r in js_requests if r['has_csrf']]
    js_without_csrf = [r for r in js_requests if not r['has_csrf']]
    
    print(f"Total requêtes fetch POST trouvées: {len(js_requests)}")
    print(f"✅ Avec header CSRF: {len(js_with_csrf)}")
    print(f"❌ Sans header CSRF: {len(js_without_csrf)}")
    print()
    
    if js_without_csrf:
        print("⚠️  REQUÊTES FETCH SANS HEADER CSRF:")
        print()
        for req in js_without_csrf:
            print(f"  ❌ {req['file']}:{req['line']}")
            print(f"     URL: {req['url']}")
            print()
    
    # 4. Résumé
    print("=" * 80)
    print("RÉSUMÉ")
    print("=" * 80)
    print(f"Formulaires HTML sans CSRF: {len(forms_without_csrf)}")
    print(f"Endpoints API exemptés: {len(exempt_endpoints)}")
    print(f"Requêtes JS sans CSRF: {len(js_without_csrf)}")
    print()
    
    total_issues = len(forms_without_csrf) + len(js_without_csrf)
    if total_issues > 0:
        print(f"⚠️  TOTAL PROBLÈMES IDENTIFIÉS: {total_issues}")
    else:
        print("✅ Aucun problème identifié !")

if __name__ == '__main__':
    main()

