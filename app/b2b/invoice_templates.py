# -*- coding: utf-8 -*-
"""
Générateur de templates pour les factures PDF
"""

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from decimal import Decimal
import io


class InvoiceTemplate:
    """Template de base pour les factures"""
    
    def __init__(self, config=None):
        self.config = config or self.get_default_config()
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def get_default_config(self):
        """Configuration par défaut pour Fée Maison"""
        return {
            'company': {
                'name': 'FÉE MAISON',
                'subtitle1': 'Restaurant • Traiteur • Pâtisserie',
                'subtitle2': 'Spécialités Algériennes & Orientales',
                'address': '',
                'phone': '',
                'email': '',
                'website': ''
            },
            'colors': {
                'primary': '#2E4057',      # Bleu marine
                'secondary': '#5A6C7D',    # Gris bleu
                'accent': '#D4AF37',       # Or
                'text': '#000000',         # Noir
                'background': '#F5F5F5'    # Gris clair
            },
            'fonts': {
                'header': 'Helvetica-Bold',
                'subtitle': 'Helvetica',
                'normal': 'Helvetica',
                'bold': 'Helvetica-Bold'
            },
            'sizes': {
                'header': 18,
                'subtitle': 12,
                'invoice_title': 16,
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
                'text1': 'Merci de votre confiance • Fée Maison',
                'text2': 'Conditions de paiement : 30 jours'
            },
            'currency': 'DA',
            'tax_rate': 0.19,
            'show_tax': True
        }
    
    def _create_custom_styles(self):
        """Créer les styles personnalisés"""
        # Style en-tête entreprise
        self.header_style = ParagraphStyle(
            'HeaderStyle',
            parent=self.styles['Normal'],
            fontSize=self.config['sizes']['header'],
            fontName=self.config['fonts']['header'],
            textColor=colors.HexColor(self.config['colors']['primary']),
            alignment=1,  # Centré
            spaceAfter=10
        )
        
        # Style sous-titre
        self.subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=self.styles['Normal'],
            fontSize=self.config['sizes']['subtitle'],
            fontName=self.config['fonts']['subtitle'],
            textColor=colors.HexColor(self.config['colors']['secondary']),
            alignment=1,  # Centré
            spaceAfter=20
        )
        
        # Style titre facture
        self.invoice_title_style = ParagraphStyle(
            'InvoiceTitleStyle',
            parent=self.styles['Normal'],
            fontSize=self.config['sizes']['invoice_title'],
            fontName=self.config['fonts']['bold'],
            textColor=colors.HexColor(self.config['colors']['accent']),
            alignment=1,  # Centré
            spaceAfter=15,
            borderWidth=1,
            borderColor=colors.HexColor(self.config['colors']['accent']),
            borderPadding=8
        )
        
        # Style informations
        self.info_style = ParagraphStyle(
            'InfoStyle',
            parent=self.styles['Normal'],
            fontSize=self.config['sizes']['normal'],
            fontName=self.config['fonts']['normal'],
            spaceAfter=5
        )
        
        # Style client
        self.client_style = ParagraphStyle(
            'ClientStyle',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName=self.config['fonts']['bold'],
            textColor=colors.HexColor(self.config['colors']['primary']),
            spaceAfter=8
        )
        
        # Style pied de page
        self.footer_style = ParagraphStyle(
            'FooterStyle',
            parent=self.styles['Normal'],
            fontSize=self.config['sizes']['small'],
            fontName=self.config['fonts']['normal'],
            textColor=colors.HexColor(self.config['colors']['secondary']),
            alignment=1,  # Centré
            spaceAfter=5
        )
    
    def generate_pdf(self, invoice):
        """Générer le PDF de la facture"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            topMargin=self.config['margins']['top']*inch,
            bottomMargin=self.config['margins']['bottom']*inch,
            leftMargin=self.config['margins']['left']*inch,
            rightMargin=self.config['margins']['right']*inch
        )
        
        story = []
        
        # En-tête
        story.extend(self._build_header())
        
        # Type de facture
        story.extend(self._build_invoice_title(invoice))
        
        # Informations facture et client
        story.extend(self._build_info_section(invoice))
        
        # Tableau des articles
        story.extend(self._build_items_table(invoice))
        
        # Notes
        story.extend(self._build_notes_section(invoice))
        
        # Pied de page
        story.extend(self._build_footer())
        
        # Générer le PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer
    
    def _build_header(self):
        """Construire l'en-tête"""
        elements = []
        
        # Nom de l'entreprise
        elements.append(Paragraph(self.config['company']['name'], self.header_style))
        
        # Sous-titres
        if self.config['company']['subtitle1']:
            elements.append(Paragraph(self.config['company']['subtitle1'], self.subtitle_style))
        
        if self.config['company']['subtitle2']:
            elements.append(Paragraph(self.config['company']['subtitle2'], self.subtitle_style))
        
        elements.append(Spacer(1, 10))
        
        # Ligne de séparation
        elements.append(HRFlowable(
            width="100%", 
            thickness=2, 
            color=colors.HexColor(self.config['colors']['accent'])
        ))
        elements.append(Spacer(1, 15))
        
        return elements
    
    def _build_invoice_title(self, invoice):
        """Construire le titre de la facture"""
        elements = []
        
        if invoice.invoice_type == 'proforma':
            title = "FACTURE PROFORMA"
        else:
            title = "FACTURE DÉFINITIVE"
        
        elements.append(Paragraph(title, self.invoice_title_style))
        
        return elements
    
    def _build_info_section(self, invoice):
        """Construire la section d'informations"""
        elements = []
        
        # Informations facture et client côte à côte
        info_data = [
            ['FACTURE:', invoice.invoice_number, 'CLIENT:', invoice.b2b_client.company_name],
            ['Date:', invoice.invoice_date.strftime('%d/%m/%Y'), 'Contact:', invoice.b2b_client.contact_person or '—'],
            ['Échéance:', invoice.due_date.strftime('%d/%m/%Y'), 'NIF:', invoice.b2b_client.tax_number or '—'],
            ['', '', 'Adresse:', invoice.b2b_client.address or '—']
        ]
        
        info_table = Table(info_data, colWidths=[80, 120, 80, 200])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (1, -1), self.config['fonts']['bold']),
            ('FONTNAME', (2, 0), (3, -1), self.config['fonts']['bold']),
            ('FONTSIZE', (0, 0), (-1, -1), self.config['sizes']['normal']),
            ('TEXTCOLOR', (0, 0), (1, -1), colors.HexColor(self.config['colors']['primary'])),
            ('TEXTCOLOR', (2, 0), (3, -1), colors.HexColor(self.config['colors']['primary'])),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 25))
        
        return elements
    
    def _build_items_table(self, invoice):
        """Construire le tableau des articles"""
        elements = []
        
        # En-tête du tableau
        data = [['DÉSIGNATION', 'QTÉ', 'PRIX UNITAIRE', 'MONTANT']]
        
        subtotal = Decimal('0.00')
        for item in invoice.invoice_items:
            # Formater la description pour les produits composés
            description = item.description
            if description and '\\n' in description:
                description = description.replace('\\n', '<br/>')
            
            # Formater les montants
            unit_price_formatted = f"{float(item.unit_price):,.0f} {self.config['currency']}"
            total_formatted = f"{float(item.total_price):,.0f} {self.config['currency']}"
            quantity_formatted = f"{float(item.quantity):g}"
            
            data.append([
                Paragraph(description, self.info_style),
                quantity_formatted,
                unit_price_formatted,
                total_formatted
            ])
            subtotal += item.total_price
        
        # Ligne de séparation avant totaux
        data.append(['', '', '', ''])
        
        # Totaux
        data.append(['', '', 'SOUS-TOTAL:', f"{float(subtotal):,.0f} {self.config['currency']}"])
        
        if self.config['show_tax']:
            tax_amount = subtotal * Decimal(str(self.config['tax_rate']))
            total_with_tax = subtotal + tax_amount
            data.append(['', '', f'TVA ({int(self.config["tax_rate"]*100)}%):', f"{float(tax_amount):,.0f} {self.config['currency']}"])
            data.append(['', '', 'TOTAL GÉNÉRAL:', f"{float(total_with_tax):,.0f} {self.config['currency']}"])
        else:
            data.append(['', '', 'TOTAL:', f"{float(subtotal):,.0f} {self.config['currency']}"])
        
        # Créer le tableau
        table = Table(data, colWidths=[280, 60, 100, 100])
        table.setStyle(self._get_table_style())
        
        elements.append(table)
        elements.append(Spacer(1, 25))
        
        return elements
    
    def _get_table_style(self):
        """Style du tableau des articles"""
        return TableStyle([
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.config['colors']['primary'])),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), self.config['fonts']['bold']),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            
            # Corps du tableau
            ('FONTNAME', (0, 1), (-1, -4), self.config['fonts']['normal']),
            ('FONTSIZE', (0, 1), (-1, -4), self.config['sizes']['normal']),
            ('ALIGN', (1, 1), (1, -4), 'CENTER'),  # Quantité centrée
            ('ALIGN', (2, 1), (-1, -4), 'RIGHT'),  # Prix et totaux à droite
            ('VALIGN', (0, 1), (-1, -4), 'TOP'),
            ('TOPPADDING', (0, 1), (-1, -4), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -4), 8),
            ('LEFTPADDING', (0, 1), (0, -4), 10),
            ('RIGHTPADDING', (-1, 1), (-1, -4), 10),
            
            # Ligne de séparation
            ('LINEBELOW', (0, -4), (-1, -4), 1, colors.HexColor(self.config['colors']['accent'])),
            
            # Totaux
            ('FONTNAME', (0, -3), (-1, -1), self.config['fonts']['bold']),
            ('FONTSIZE', (0, -3), (-1, -1), 11),
            ('ALIGN', (2, -3), (-1, -1), 'RIGHT'),
            ('BACKGROUND', (2, -1), (-1, -1), colors.HexColor(self.config['colors']['background'])),
            ('TEXTCOLOR', (2, -1), (-1, -1), colors.HexColor(self.config['colors']['primary'])),
            
            # Bordures
            ('GRID', (0, 0), (-1, -4), 0.5, colors.HexColor('#CCCCCC')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor(self.config['colors']['primary'])),
        ])
    
    def _build_notes_section(self, invoice):
        """Construire la section des notes"""
        elements = []
        
        if invoice.notes:
            elements.append(Paragraph("NOTES:", self.client_style))
            notes_style = ParagraphStyle(
                'NotesStyle',
                parent=self.styles['Normal'],
                fontSize=self.config['sizes']['normal'],
                fontName=self.config['fonts']['normal'],
                spaceAfter=10,
                leftIndent=10
            )
            elements.append(Paragraph(invoice.notes, notes_style))
            elements.append(Spacer(1, 15))
        
        return elements
    
    def _build_footer(self):
        """Construire le pied de page"""
        elements = []
        
        elements.append(Spacer(1, 20))
        elements.append(HRFlowable(
            width="100%", 
            thickness=1, 
            color=colors.HexColor('#CCCCCC')
        ))
        elements.append(Spacer(1, 10))
        
        if self.config['footer']['text1']:
            elements.append(Paragraph(self.config['footer']['text1'], self.footer_style))
        
        if self.config['footer']['text2']:
            elements.append(Paragraph(self.config['footer']['text2'], self.footer_style))
        
        return elements
    
    def get_filename(self, invoice):
        """Générer le nom de fichier"""
        if invoice.invoice_type == 'proforma':
            prefix = "FP"
        else:
            prefix = "FF"
        
        client_name = invoice.b2b_client.company_name.replace(' ', '_')
        date_str = invoice.invoice_date.strftime('%d%m%Y')
        
        return f"{prefix}_{client_name}_{date_str}.pdf"


# Templates prédéfinis
def get_fee_maison_template():
    """Template par défaut Fée Maison"""
    return InvoiceTemplate()


def get_minimal_template():
    """Template minimal"""
    config = {
        'company': {
            'name': 'FÉE MAISON',
            'subtitle1': 'Restaurant & Traiteur',
            'subtitle2': '',
        },
        'colors': {
            'primary': '#000000',
            'secondary': '#666666',
            'accent': '#999999',
            'text': '#000000',
            'background': '#F8F8F8'
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
            'top': 0.5,
            'bottom': 0.5,
            'left': 0.5,
            'right': 0.5
        },
        'footer': {
            'text1': 'Merci de votre confiance',
            'text2': ''
        },
        'currency': 'DA',
        'tax_rate': 0.19,
        'show_tax': True
    }
    return InvoiceTemplate(config)


def get_elegant_template():
    """Template élégant"""
    config = {
        'company': {
            'name': 'FÉE MAISON',
            'subtitle1': 'Restaurant • Traiteur • Pâtisserie',
            'subtitle2': 'Cuisine Authentique & Raffinée',
        },
        'colors': {
            'primary': '#1A237E',      # Bleu indigo
            'secondary': '#3F51B5',    # Bleu
            'accent': '#FF6F00',       # Orange
            'text': '#000000',
            'background': '#FFF3E0'    # Orange très clair
        },
        'fonts': {
            'header': 'Helvetica-Bold',
            'subtitle': 'Helvetica',
            'normal': 'Helvetica',
            'bold': 'Helvetica-Bold'
        },
        'sizes': {
            'header': 20,
            'subtitle': 13,
            'invoice_title': 18,
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
            'text1': '✨ Merci de votre confiance • Fée Maison ✨',
            'text2': 'Conditions de paiement : 30 jours'
        },
        'currency': 'DA',
        'tax_rate': 0.19,
        'show_tax': True
    }
    return InvoiceTemplate(config)
