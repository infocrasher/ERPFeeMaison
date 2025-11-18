# -*- coding: utf-8 -*-
"""
Exemple de template personnalisé pour Fée Maison
Copier cette fonction dans app/b2b/invoice_templates.py pour l'utiliser
"""

from app.b2b.invoice_templates import InvoiceTemplate

def get_ramadan_template():
    """Template spécial Ramadan avec couleurs dorées"""
    config = {
        'company': {
            'name': 'FÉE MAISON',
            'subtitle1': 'Restaurant • Traiteur • Pâtisserie',
            'subtitle2': '🌙 Spécial Ramadan Kareem 🌟',
        },
        'colors': {
            'primary': '#8E6A00',      # Or foncé
            'secondary': '#B8860B',    # Or moyen  
            'accent': '#FFD700',       # Or brillant
            'text': '#000000',
            'background': '#FFFAF0'    # Blanc cassé
        },
        'fonts': {
            'header': 'Helvetica-Bold',
            'subtitle': 'Helvetica',
            'normal': 'Helvetica',
            'bold': 'Helvetica-Bold'
        },
        'sizes': {
            'header': 19,
            'subtitle': 13,
            'invoice_title': 17,
            'normal': 10,
            'small': 9
        },
        'margins': {
            'top': 0.5,
            'bottom': 0.5,
            'left': 0.5,
            'right': 0.5
        },
        'footer': {
            'text1': '🌙 Ramadan Kareem • Que ce mois soit béni • Fée Maison 🌟',
            'text2': 'Conditions de paiement : 30 jours'
        },
        'currency': 'DA',
        'tax_rate': 0.19,
        'show_tax': True
    }
    return InvoiceTemplate(config)


def get_corporate_template():
    """Template corporate sobre pour grandes entreprises"""
    config = {
        'company': {
            'name': 'FÉE MAISON',
            'subtitle1': 'Professional Catering Services',
            'subtitle2': 'Corporate & Events Solutions',
        },
        'colors': {
            'primary': '#263238',      # Bleu gris foncé
            'secondary': '#37474F',    # Bleu gris
            'accent': '#607D8B',       # Bleu gris clair
            'text': '#000000',
            'background': '#FAFAFA'    # Gris très clair
        },
        'fonts': {
            'header': 'Helvetica-Bold',
            'subtitle': 'Helvetica',
            'normal': 'Helvetica',
            'bold': 'Helvetica-Bold'
        },
        'sizes': {
            'header': 16,
            'subtitle': 11,
            'invoice_title': 14,
            'normal': 9,
            'small': 8
        },
        'margins': {
            'top': 0.6,
            'bottom': 0.6,
            'left': 0.6,
            'right': 0.6
        },
        'footer': {
            'text1': 'Professional Catering • Fée Maison',
            'text2': 'Payment terms: 30 days net'
        },
        'currency': 'DA',
        'tax_rate': 0.19,
        'show_tax': True
    }
    return InvoiceTemplate(config)


def get_wedding_template():
    """Template élégant pour mariages et événements"""
    config = {
        'company': {
            'name': 'FÉE MAISON',
            'subtitle1': '💐 Traiteur de Prestige 💐',
            'subtitle2': 'Mariages • Réceptions • Événements',
        },
        'colors': {
            'primary': '#880E4F',      # Rose foncé
            'secondary': '#AD1457',    # Rose
            'accent': '#E91E63',       # Rose vif
            'text': '#000000',
            'background': '#FCE4EC'    # Rose très clair
        },
        'fonts': {
            'header': 'Helvetica-Bold',
            'subtitle': 'Helvetica',
            'normal': 'Helvetica',
            'bold': 'Helvetica-Bold'
        },
        'sizes': {
            'header': 20,
            'subtitle': 14,
            'invoice_title': 18,
            'normal': 11,
            'small': 10
        },
        'margins': {
            'top': 0.4,
            'bottom': 0.4,
            'left': 0.4,
            'right': 0.4
        },
        'footer': {
            'text1': '💕 Merci de nous faire confiance pour votre jour spécial 💕',
            'text2': 'Conditions de paiement : 50% à la commande, solde J-7'
        },
        'currency': 'DA',
        'tax_rate': 0.19,
        'show_tax': True
    }
    return InvoiceTemplate(config)

# Instructions d'intégration :
# 
# 1. Copier les fonctions souhaitées dans app/b2b/invoice_templates.py
# 
# 2. Dans app/b2b/routes.py, ajouter les imports :
#    from .invoice_templates import get_ramadan_template, get_corporate_template, get_wedding_template
# 
# 3. Ajouter dans le dictionnaire templates :
#    templates = {
#        'default': get_fee_maison_template,
#        'minimal': get_minimal_template,
#        'elegant': get_elegant_template,
#        'ramadan': get_ramadan_template,
#        'corporate': get_corporate_template,
#        'wedding': get_wedding_template,
#    }
# 
# 4. Dans app/templates/b2b/invoices/view.html, ajouter les options :
#    <li><a class="dropdown-item" href="{{ url_for('b2b.export_invoice_pdf_template', invoice_id=invoice.id, template_name='ramadan') }}">
#        <i class="bi bi-star me-2"></i>Template Ramadan
#    </a></li>
#    <li><a class="dropdown-item" href="{{ url_for('b2b.export_invoice_pdf_template', invoice_id=invoice.id, template_name='corporate') }}">
#        <i class="bi bi-building me-2"></i>Template Corporate
#    </a></li>
#    <li><a class="dropdown-item" href="{{ url_for('b2b.export_invoice_pdf_template', invoice_id=invoice.id, template_name='wedding') }}">
#        <i class="bi bi-heart me-2"></i>Template Mariage
#    </a></li>
# 
# 5. Redémarrer l'application Flask
# 
# URLs d'accès :
# - /admin/b2b/invoices/{id}/export/pdf/ramadan
# - /admin/b2b/invoices/{id}/export/pdf/corporate  
# - /admin/b2b/invoices/{id}/export/pdf/wedding

