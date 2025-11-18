# -*- coding: utf-8 -*-
"""
Générateur de factures PDF avec WeasyPrint
Style calqué sur les factures originales de Fée Maison
"""

from flask import render_template, url_for, request, current_app
from weasyprint import HTML
from decimal import Decimal
import os


def _get_payment_method_display(payment_method):
    """Convertir le code de mode de paiement en texte d'affichage"""
    methods = {
        'cheque': 'Par chèque',
        'espece': 'En espèces',
        'virement': 'Par virement',
        'traite': 'Par traite'
    }
    return methods.get(payment_method, 'Par chèque')


def generate_fee_maison_pdf(invoice):
    """Générer une facture PDF avec le design original Fée Maison
    
    Args:
        invoice: Objet Invoice de la base de données
        
    Returns:
        bytes: Contenu du PDF généré
    """
    
    # Préparer les données pour le template
    invoice_data = {
        "number": invoice.invoice_number,
        "date": invoice.invoice_date,
        "type": invoice.invoice_type,
        "seller": {
            "name": "Fée Maison",
            "address_lines": [
                "183 coopérative ERRAHMA",
                "Dely Brahim - Alger"
            ],
            "tel": "05 56 25 03 70",
            "nif": "185160600384161",
            "rc": "16/00-0010775800",
            "email": "Feemaison.de@gmail.com",
            "logo_url": url_for('static', filename='img/feemaison-logo-noir.png', _external=False),
        },
        "buyer": {
            "name": invoice.b2b_client.company_name,
            "address_lines": [
                line.strip() for line in (invoice.b2b_client.address or "").split('\n') 
                if line.strip()
            ],
            "contact": invoice.b2b_client.contact_person,
            "phone": invoice.b2b_client.phone,
            "email": invoice.b2b_client.email,
            "tax_number": invoice.b2b_client.tax_number,
        },
        "payment_mode": _get_payment_method_display(invoice.payment_method),
        "lines": [],
        "currency": "DZD",
        "notes": invoice.notes,
        "due_date": invoice.due_date
    }
    
    # Préparer les lignes de facture
    total_ht = Decimal('0.00')
    for item in invoice.invoice_items:
        line_data = {
            "designation": item.description,
            "qty": item.quantity,
            "unit_price": item.unit_price,
            "amount": item.total_price
        }
        invoice_data["lines"].append(line_data)
        total_ht += item.total_price
    
    # Pas de TVA - Non assujetti
    tva_rate = Decimal('0.00')  # 0%
    tva_amount = Decimal('0.00')
    total_ttc = total_ht  # Pas de TVA
    
    # Générer le HTML avec le template
    html = render_template(
        "invoices/fee_maison_original.html",
        invoice=invoice_data,
        total_ht=total_ht,
        tva_rate=tva_rate,
        tva_amount=tva_amount,
        total_ttc=total_ttc,
        show_tva=False  # Non assujetti TVA
    )
    
    # Générer le PDF avec WeasyPrint
    try:
        pdf = HTML(string=html, base_url=request.url_root).write_pdf()
        return pdf
    except Exception as e:
        current_app.logger.error(f"Erreur génération PDF WeasyPrint: {e}")
        raise


def generate_fee_maison_signed_pdf(invoice):
    """Générer une facture PDF avec cachet et signature
    
    Args:
        invoice: Objet Invoice de la base de données
        
    Returns:
        bytes: Contenu du PDF généré
    """
    
    # Préparer les données pour le template (identique à l'original)
    invoice_data = {
        "number": invoice.invoice_number,
        "date": invoice.invoice_date,
        "type": invoice.invoice_type,
        "seller": {
            "name": "Fée Maison",
            "address_lines": [
                "183 coopérative ERRAHMA",
                "Dely Brahim - Alger"
            ],
            "tel": "05 56 25 03 70",
            "nif": "185160600384161",
            "rc": "16/00-0010775800",
            "email": "Feemaison.de@gmail.com",
            "logo_url": url_for('static', filename='img/feemaison-logo-noir.png', _external=False),
        },
        "buyer": {
            "name": invoice.b2b_client.company_name,
            "address_lines": [
                line.strip() for line in (invoice.b2b_client.address or "").split('\n') 
                if line.strip()
            ],
            "contact": invoice.b2b_client.contact_person,
            "phone": invoice.b2b_client.phone,
            "email": invoice.b2b_client.email,
            "tax_number": invoice.b2b_client.tax_number,
        },
        "payment_mode": _get_payment_method_display(invoice.payment_method),
        "lines": [],
        "currency": "DZD",
        "notes": invoice.notes,
        "due_date": invoice.due_date
    }
    
    # Préparer les lignes de facture
    total_ht = Decimal('0.00')
    for item in invoice.invoice_items:
        line_data = {
            "designation": item.description,
            "qty": item.quantity,
            "unit_price": item.unit_price,
            "amount": item.total_price
        }
        invoice_data["lines"].append(line_data)
        total_ht += item.total_price
    
    # Pas de TVA - Non assujetti
    tva_rate = Decimal('0.00')
    tva_amount = Decimal('0.00')
    total_ttc = total_ht
    
    # Générer le HTML avec le template signé
    html = render_template(
        "invoices/fee_maison_signed.html",
        invoice=invoice_data,
        total_ht=total_ht,
        tva_rate=tva_rate,
        tva_amount=tva_amount,
        total_ttc=total_ttc,
        show_tva=False
    )
    
    # Générer le PDF avec WeasyPrint
    try:
        pdf = HTML(string=html, base_url=request.url_root).write_pdf()
        return pdf
    except Exception as e:
        current_app.logger.error(f"Erreur génération PDF WeasyPrint (signé): {e}")
        raise


def get_filename(invoice, template_type="standard"):
    """Générer le nom de fichier pour la facture
    
    Args:
        invoice: Objet Invoice
        template_type: Type de template ('standard' ou 'signed')
        
    Returns:
        str: Nom de fichier formaté
    """
    if invoice.invoice_type == 'proforma':
        prefix = "FP"
    else:
        prefix = "FF"
    
    # Nettoyer le nom du client pour le fichier
    client_name = invoice.b2b_client.company_name
    client_name = "".join(c for c in client_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    client_name = client_name.replace(' ', '_')
    
    date_str = invoice.invoice_date.strftime('%d%m%Y')
    
    # Ajouter suffixe selon le type
    suffix = "_SIGN" if template_type == "signed" else ""
    
    return f"{prefix}_{client_name}_{date_str}{suffix}.pdf"


def check_logo_exists():
    """Vérifier si le logo existe dans static/img/
    
    Returns:
        bool: True si le logo existe
    """
    logo_path = os.path.join(current_app.static_folder, 'img', 'logo-feemaison.png')
    return os.path.exists(logo_path)


def get_rib_info():
    """Informations bancaires RIB pour Fée Maison
    
    Returns:
        dict: Informations RIB
    """
    return {
        "banque": "BNA - Banque Nationale d'Algérie",
        "agence": "Dely Brahim",
        "rib": "00100000123456789012",
        "ccp": "123456789012 - Clé: 12"
    }
