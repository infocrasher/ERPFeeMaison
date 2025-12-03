#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simple de traçage pour identifier les modifications du stock_comptoir.
Utilise le monkey patching pour intercepter toutes les modifications.
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Sauvegarder la fonction setattr originale
_original_setattr = setattr

# Liste pour stocker les traces
_traces = []

def _traced_setattr(obj, name, value):
    """Version tracée de setattr"""
    if name == 'stock_comptoir' and hasattr(obj, '__class__') and obj.__class__.__name__ == 'Product':
        import traceback
        stack = traceback.extract_stack()
        
        # Obtenir la valeur avant modification
        old_value = getattr(obj, 'stock_comptoir', None)
        
        # Obtenir les informations de l'appelant
        if len(stack) >= 2:
            caller = stack[-2]
        else:
            caller = stack[-1] if stack else None
        
        trace = {
            'product_id': getattr(obj, 'id', None),
            'product_name': getattr(obj, 'name', None),
            'old_value': old_value,
            'new_value': value,
            'file': caller.filename if caller else 'unknown',
            'line': caller.lineno if caller else 0,
            'function': caller.name if caller else 'unknown',
            'code': caller.line if caller else 'unknown'
        }
        
        _traces.append(trace)
        
        print(f"\n{'='*80}")
        print(f"🔍 MODIFICATION DÉTECTÉE: stock_comptoir")
        print(f"{'='*80}")
        print(f"Produit: {trace['product_name']} (ID: {trace['product_id']})")
        print(f"Ancienne valeur: {old_value}")
        print(f"Nouvelle valeur: {value}")
        print(f"Changement: {value - (old_value or 0)}")
        print(f"Fichier: {trace['file']}:{trace['line']}")
        print(f"Fonction: {trace['function']}")
        print(f"Code: {trace['code']}")
        print(f"{'='*80}\n")
    
    return _original_setattr(obj, name, value)

def patch_setattr():
    """Patche setattr pour tracer les modifications"""
    import builtins
    builtins.setattr = _traced_setattr
    print("✅ setattr a été patché pour le traçage")

def unpatch_setattr():
    """Restaure setattr original"""
    import builtins
    builtins.setattr = _original_setattr
    print("✅ setattr a été restauré")

def get_traces():
    """Retourne toutes les traces collectées"""
    return _traces

def clear_traces():
    """Efface toutes les traces"""
    global _traces
    _traces = []

if __name__ == '__main__':
    print("Script de traçage du stock_comptoir")
    print("Utilisez ce script en l'important dans votre code:")
    print("  from scripts.trace_simple_stock import patch_setattr, get_traces, unpatch_setattr")
    print("  patch_setattr()")
    print("  # ... votre code ...")
    print("  traces = get_traces()")
    print("  unpatch_setattr()")

