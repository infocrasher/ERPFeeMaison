# -*- coding: utf-8 -*-
"""
Filtres utilitaires pour les templates de factures
"""

from decimal import Decimal, ROUND_HALF_UP
from num2words import num2words
import re


def format_dzd(value):
    """Formater un montant en DZD avec séparateurs et virgule décimale
    Exemple: 79200.50 -> "79 200,50"
    """
    if value is None:
        return "0,00"
    
    try:
        # Convertir en Decimal pour éviter les erreurs de précision
        q = Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Formater avec séparateurs de milliers
        s = f"{float(q):,.2f}"
        
        # Convertir point en virgule et virgule en espace pour format français
        s = s.replace(",", "X").replace(".", ",").replace("X", " ")
        
        return s
    except (ValueError, TypeError, Decimal.InvalidOperation):
        return "0,00"


def date_fr(dt):
    """Formater une date au format français DD/MM/YYYY"""
    if dt is None:
        return ""
    
    try:
        return dt.strftime('%d/%m/%Y')
    except (AttributeError, ValueError):
        return str(dt)


def montant_en_lettres_dzd(value):
    """Convertir un montant en dinars en toutes lettres
    Exemple: 79200.50 -> "soixante-dix-neuf mille deux cents dinars et cinquante centimes"
    """
    if value is None:
        return "zéro dinars"
    
    try:
        # Convertir en Decimal
        q = Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        dinars = int(q)
        centimes = int((q - dinars) * 100)
        
        # Partie dinars
        if dinars == 0:
            dinars_text = "zéro"
        else:
            dinars_text = num2words(dinars, lang='fr')
        
        # Construire le texte final
        if centimes > 0:
            centimes_text = num2words(centimes, lang='fr')
            if dinars <= 1:
                if centimes <= 1:
                    return f"{dinars_text} dinar et {centimes_text} centime"
                else:
                    return f"{dinars_text} dinar et {centimes_text} centimes"
            else:
                if centimes <= 1:
                    return f"{dinars_text} dinars et {centimes_text} centime"
                else:
                    return f"{dinars_text} dinars et {centimes_text} centimes"
        else:
            if dinars <= 1:
                return f"{dinars_text} dinar"
            else:
                return f"{dinars_text} dinars"
                
    except (ValueError, TypeError, Decimal.InvalidOperation):
        return "montant invalide"


def format_phone(phone):
    """Formater un numéro de téléphone
    Exemple: "0556250370" -> "05 56 25 03 70"
    """
    if not phone:
        return ""
    
    # Supprimer les espaces et tirets existants
    phone_clean = re.sub(r'[^\d]', '', str(phone))
    
    # Formater selon le nombre de chiffres
    if len(phone_clean) == 10:
        return f"{phone_clean[:2]} {phone_clean[2:4]} {phone_clean[4:6]} {phone_clean[6:8]} {phone_clean[8:]}"
    elif len(phone_clean) == 9:
        return f"{phone_clean[:2]} {phone_clean[2:4]} {phone_clean[4:6]} {phone_clean[6:8]} {phone_clean[8:]}"
    else:
        return phone


def truncate_text(text, max_length=50):
    """Tronquer un texte avec des points de suspension"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."


def capitalize_first(text):
    """Mettre en majuscule la première lettre seulement"""
    if not text:
        return ""
    
    return text[0].upper() + text[1:].lower() if len(text) > 1 else text.upper()

