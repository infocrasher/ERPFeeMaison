-- Script de diagnostic et correction des punch_type dans attendance_records
-- Problème: la pointeuse ZKTeco envoie parfois 0/1 au lieu de 'in'/'out'

-- 1. DIAGNOSTIC: Vérifier les valeurs actuelles de punch_type
SELECT 
    punch_type, 
    COUNT(*) as count 
FROM attendance_records 
GROUP BY punch_type 
ORDER BY count DESC;

-- 2. Voir les enregistrements problématiques
SELECT 
    ar.id,
    e.name as employee_name,
    ar.timestamp,
    ar.punch_type,
    ar.raw_data
FROM attendance_records ar
JOIN employees e ON ar.employee_id = e.id
WHERE ar.punch_type NOT IN ('in', 'out')
ORDER BY ar.timestamp DESC
LIMIT 20;

-- 3. CORRECTION: Convertir les punch_type numériques en strings
-- 0 = in, 1 = out

-- Corriger '0' -> 'in'
UPDATE attendance_records 
SET punch_type = 'in' 
WHERE punch_type = '0' OR punch_type = 0::text;

-- Corriger '1' -> 'out'
UPDATE attendance_records 
SET punch_type = 'out' 
WHERE punch_type = '1' OR punch_type = 1::text;

-- 4. Vérification après correction
SELECT 
    punch_type, 
    COUNT(*) as count 
FROM attendance_records 
GROUP BY punch_type 
ORDER BY count DESC;

