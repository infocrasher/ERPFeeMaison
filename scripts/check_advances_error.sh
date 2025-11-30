#!/bin/bash
# Script pour vérifier les erreurs sur la page advances

echo "🔍 VÉRIFICATION DES ERREURS - PAGE ADVANCES"
echo "=========================================="
echo ""

# 1. Vérifier les logs d'erreur récents
echo "📋 1. Dernières erreurs dans les logs Flask/Gunicorn :"
echo "---------------------------------------------------"
sudo tail -n 50 /var/log/erp/error.log | grep -A 10 -B 5 "advances\|SalaryAdvance\|manage_advances" || echo "Aucune erreur spécifique trouvée dans les logs"
echo ""

# 2. Vérifier les logs systemd
echo "📋 2. Dernières erreurs dans systemd :"
echo "-------------------------------------"
sudo journalctl -u erp-fee-maison -n 50 --no-pager | grep -A 10 -B 5 "advances\|SalaryAdvance\|manage_advances\|Error\|Exception\|Traceback" || echo "Aucune erreur spécifique trouvée"
echo ""

# 3. Vérifier que la table existe
echo "📋 3. Vérification de la table salary_advances :"
echo "-----------------------------------------------"
sudo -u postgres psql fee_maison_db -c "\d salary_advances" 2>&1
echo ""

# 4. Vérifier les données dans la table
echo "📋 4. Nombre d'enregistrements dans salary_advances :"
echo "---------------------------------------------------"
sudo -u postgres psql fee_maison_db -c "SELECT COUNT(*) FROM salary_advances;" 2>&1
echo ""

# 5. Vérifier les relations (foreign keys)
echo "📋 5. Vérification des foreign keys :"
echo "------------------------------------"
sudo -u postgres psql fee_maison_db -c "
SELECT 
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
  AND tc.table_name = 'salary_advances';
" 2>&1
echo ""

# 6. Tester une requête simple
echo "📋 6. Test de requête SQLAlchemy (simulation) :"
echo "----------------------------------------------"
sudo -u postgres psql fee_maison_db -c "
SELECT sa.id, sa.employee_id, e.name, sa.amount, sa.advance_date 
FROM salary_advances sa 
LEFT JOIN employees e ON sa.employee_id = e.id 
LIMIT 5;
" 2>&1
echo ""

echo "✅ Vérification terminée"
echo ""
echo "💡 Pour voir les logs en temps réel :"
echo "   sudo tail -f /var/log/erp/error.log"
echo "   sudo journalctl -u erp-fee-maison -f"

