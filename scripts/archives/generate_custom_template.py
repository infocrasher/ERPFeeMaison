#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de template de facture personnalisé
Utilise ce script pour créer des templates de factures sur mesure
"""

import json
import os
from datetime import datetime

def create_custom_template():
    """Assistant interactif pour créer un template personnalisé"""
    
    print("🎨 Générateur de Template de Facture Fée Maison")
    print("=" * 50)
    
    # Configuration de l'entreprise
    print("\n📋 INFORMATIONS ENTREPRISE")
    company_name = input("Nom de l'entreprise [FÉE MAISON]: ") or "FÉE MAISON"
    subtitle1 = input("Sous-titre 1 [Restaurant • Traiteur • Pâtisserie]: ") or "Restaurant • Traiteur • Pâtisserie"
    subtitle2 = input("Sous-titre 2 [Spécialités Algériennes & Orientales]: ") or "Spécialités Algériennes & Orientales"
    
    # Couleurs
    print("\n🎨 COULEURS")
    print("Couleurs suggérées:")
    print("1. Classique: Bleu marine (#2E4057) + Or (#D4AF37)")
    print("2. Moderne: Noir (#000000) + Gris (#666666)")
    print("3. Élégant: Bleu indigo (#1A237E) + Orange (#FF6F00)")
    print("4. Personnalisé")
    
    color_choice = input("Choix (1-4) [1]: ") or "1"
    
    if color_choice == "1":
        colors = {
            'primary': '#2E4057',
            'secondary': '#5A6C7D',
            'accent': '#D4AF37',
            'text': '#000000',
            'background': '#F5F5F5'
        }
    elif color_choice == "2":
        colors = {
            'primary': '#000000',
            'secondary': '#666666',
            'accent': '#999999',
            'text': '#000000',
            'background': '#F8F8F8'
        }
    elif color_choice == "3":
        colors = {
            'primary': '#1A237E',
            'secondary': '#3F51B5',
            'accent': '#FF6F00',
            'text': '#000000',
            'background': '#FFF3E0'
        }
    else:
        print("Couleurs personnalisées (format #RRGGBB):")
        colors = {
            'primary': input("Couleur principale [#2E4057]: ") or '#2E4057',
            'secondary': input("Couleur secondaire [#5A6C7D]: ") or '#5A6C7D',
            'accent': input("Couleur d'accent [#D4AF37]: ") or '#D4AF37',
            'text': input("Couleur du texte [#000000]: ") or '#000000',
            'background': input("Couleur d'arrière-plan [#F5F5F5]: ") or '#F5F5F5'
        }
    
    # Tailles de police
    print("\n📝 TAILLES DE POLICE")
    print("Tailles suggérées:")
    print("1. Standard: En-tête 18, Titre 16, Normal 10")
    print("2. Compact: En-tête 16, Titre 14, Normal 9")
    print("3. Grand: En-tête 20, Titre 18, Normal 11")
    print("4. Personnalisé")
    
    size_choice = input("Choix (1-4) [1]: ") or "1"
    
    if size_choice == "1":
        sizes = {'header': 18, 'subtitle': 12, 'invoice_title': 16, 'normal': 10, 'small': 9}
    elif size_choice == "2":
        sizes = {'header': 16, 'subtitle': 11, 'invoice_title': 14, 'normal': 9, 'small': 8}
    elif size_choice == "3":
        sizes = {'header': 20, 'subtitle': 13, 'invoice_title': 18, 'normal': 11, 'small': 10}
    else:
        sizes = {
            'header': int(input("Taille en-tête [18]: ") or "18"),
            'subtitle': int(input("Taille sous-titre [12]: ") or "12"),
            'invoice_title': int(input("Taille titre facture [16]: ") or "16"),
            'normal': int(input("Taille texte normal [10]: ") or "10"),
            'small': int(input("Taille petit texte [9]: ") or "9")
        }
    
    # Pied de page
    print("\n📄 PIED DE PAGE")
    footer1 = input("Texte 1 [Merci de votre confiance • Fée Maison]: ") or "Merci de votre confiance • Fée Maison"
    footer2 = input("Texte 2 [Conditions de paiement : 30 jours]: ") or "Conditions de paiement : 30 jours"
    
    # Options
    print("\n⚙️ OPTIONS")
    show_tax = input("Afficher la TVA? (o/n) [o]: ").lower() or "o"
    tax_rate = float(input("Taux de TVA (ex: 0.19 pour 19%) [0.19]: ") or "0.19")
    currency = input("Devise [DA]: ") or "DA"
    
    # Créer la configuration
    config = {
        'company': {
            'name': company_name,
            'subtitle1': subtitle1,
            'subtitle2': subtitle2,
            'address': '',
            'phone': '',
            'email': '',
            'website': ''
        },
        'colors': colors,
        'fonts': {
            'header': 'Helvetica-Bold',
            'subtitle': 'Helvetica',
            'normal': 'Helvetica',
            'bold': 'Helvetica-Bold'
        },
        'sizes': sizes,
        'margins': {
            'top': 0.5,
            'bottom': 0.5,
            'left': 0.5,
            'right': 0.5
        },
        'footer': {
            'text1': footer1,
            'text2': footer2
        },
        'currency': currency,
        'tax_rate': tax_rate,
        'show_tax': show_tax == 'o'
    }
    
    # Sauvegarder
    template_name = input("\nNom du template: ").strip().replace(" ", "_").lower()
    if not template_name:
        template_name = f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    filename = f"templates/template_{template_name}.json"
    os.makedirs("templates", exist_ok=True)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Template sauvegardé: {filename}")
    
    # Générer le code Python
    generate_template_code(template_name, config)
    
    return config

def generate_template_code(name, config):
    """Générer le code Python pour le template"""
    
    code = f'''def get_{name}_template():
    """Template personnalisé: {name}"""
    config = {json.dumps(config, indent=4, ensure_ascii=False)}
    return InvoiceTemplate(config)
'''
    
    code_filename = f"templates/template_{name}.py"
    with open(code_filename, 'w', encoding='utf-8') as f:
        f.write("from app.b2b.invoice_templates import InvoiceTemplate\n\n")
        f.write(code)
    
    print(f"✅ Code Python généré: {code_filename}")
    
    # Instructions d'intégration
    print(f"""
📝 INSTRUCTIONS D'INTÉGRATION:

1. Copier la fonction dans app/b2b/invoice_templates.py
2. Ajouter l'import dans routes.py:
   from .invoice_templates import get_{name}_template

3. Ajouter dans le dictionnaire des templates:
   '{name}': get_{name}_template

4. Redémarrer l'application Flask

5. Utiliser l'URL:
   /admin/b2b/invoices/{{invoice_id}}/export/pdf/{name}
""")

def preview_template_colors():
    """Aperçu des combinaisons de couleurs"""
    
    combinations = [
        {
            'name': 'Classique Fée Maison',
            'primary': '#2E4057',
            'secondary': '#5A6C7D', 
            'accent': '#D4AF37'
        },
        {
            'name': 'Moderne Monochrome',
            'primary': '#000000',
            'secondary': '#666666',
            'accent': '#999999'
        },
        {
            'name': 'Élégant Indigo',
            'primary': '#1A237E',
            'secondary': '#3F51B5',
            'accent': '#FF6F00'
        },
        {
            'name': 'Nature Verte',
            'primary': '#2E7D32',
            'secondary': '#4CAF50',
            'accent': '#FFC107'
        },
        {
            'name': 'Luxe Bordeaux',
            'primary': '#8E24AA',
            'secondary': '#BA68C8',
            'accent': '#FFD54F'
        }
    ]
    
    print("🎨 APERÇU DES COULEURS")
    print("=" * 40)
    
    for i, combo in enumerate(combinations, 1):
        print(f"{i}. {combo['name']}")
        print(f"   Principale: {combo['primary']}")
        print(f"   Secondaire: {combo['secondary']}")
        print(f"   Accent: {combo['accent']}")
        print()

if __name__ == "__main__":
    print("Options:")
    print("1. Créer un template personnalisé")
    print("2. Aperçu des couleurs")
    
    choice = input("Choix (1-2): ")
    
    if choice == "1":
        create_custom_template()
    elif choice == "2":
        preview_template_colors()
    else:
        print("Option invalide")

