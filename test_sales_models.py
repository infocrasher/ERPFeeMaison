#!/usr/bin/env python3
"""
Script de test pour vérifier les modèles sales
"""
from app import create_app
from extensions import db
from app.sales.models import CashRegisterSession, CashMovement
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Vérifier que les modèles sont bien définis
        print("✅ Modèles sales importés avec succès!")
        print(f"   - CashRegisterSession: {CashRegisterSession.__tablename__}")
        print(f"   - CashMovement: {CashMovement.__tablename__}")
        
        # Vérifier que les tables existent en base
        result = db.session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('cash_register_session', 'cash_movement')"))
        tables = [row[0] for row in result]
        
        print("\n📋 Tables en base de données:")
        for table in ['cash_register_session', 'cash_movement']:
            if table in tables:
                print(f"   ✅ {table}")
            else:
                print(f"   ❌ {table} - MANQUANTE!")
        
        # Vérifier la structure des tables
        print("\n🔍 Structure des tables:")
        for table in ['cash_register_session', 'cash_movement']:
            if table in tables:
                result = db.session.execute(text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}' ORDER BY ordinal_position"))
                columns = [(row[0], row[1]) for row in result]
                print(f"\n   Table {table}:")
                for col_name, col_type in columns:
                    print(f"     - {col_name}: {col_type}")
        
        print("\n🎉 Vérification terminée avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc() 