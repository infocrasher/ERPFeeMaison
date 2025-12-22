from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from decimal import Decimal
import io
import os
import re

class InvoiceTemplate:
    def __init__(self, config=None):
        self.config = config or self.get_default_config()
        self._register_fonts()
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _register_fonts(self):
        """Enregistrer les polices personnalisées si disponibles"""
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        
        # Le chemin exact vers la police Brotherhood
        font_path = 'static/fonts/Brotherhood_Script.ttf'
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('Brotherhood_Script', font_path))
                self.config['fonts']['header'] = 'Brotherhood_Script'
            except Exception as e:
                print(f"Erreur enregistrement police: {e}")
        else:
            self.config['fonts']['header'] = 'Helvetica-Bold'

    def _create_custom_styles(self):
        """Créer les styles ParagraphStyle personnalisés"""
        self.header_style = ParagraphStyle(
            'HeaderStyle',
            parent=self.styles['Normal'],
            fontSize=32 if self.config['fonts']['header'] == 'BrotherhoodScript' else 24,
            fontName=self.config['fonts']['header'],
            textColor=colors.HexColor(self.config['colors']['primary']),
            alignment=0,
            spaceAfter=5
        )
        
        self.subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=self.styles['Normal'],
            fontSize=self.config['sizes']['subtitle'],
            fontName=self.config['fonts']['subtitle'],
            textColor=colors.HexColor(self.config['colors']['secondary']),
            alignment=0,
            spaceAfter=2
        )
        
        self.info_style = ParagraphStyle(
            'InfoStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName=self.config['fonts']['normal'],
            leading=12
        )
        
        self.footer_style = ParagraphStyle(
            'FooterStyle',
            parent=self.styles['Normal'],
            fontSize=8,
            fontName=self.config['fonts']['normal'],
            textColor=colors.HexColor('#666666'),
            alignment=1
        )

    def get_default_config(self):
        return {
            'company': {
                'name': 'Fée Maison',
                'subtitle1': 'Traiteur',
                'subtitle2': '',
                'address': '183 cooperative ERRAHMA, Dely Brahim Alger',
                'phone': '0556250370',
                'email': '',
                'website': '',
                'logo': 'app/static/img/logo-feemaison.png'
            },
            'colors': {
                'primary': '#2E4057',
                'secondary': '#666666',
                'accent': '#B08050',
                'background': '#F4F4F9'
            },
            'fonts': {
                'header': 'Helvetica-Bold',
                'subtitle': 'Helvetica-Oblique',
                'normal': 'Helvetica',
                'bold': 'Helvetica-Bold'
            },
            'sizes': {
                'header': 24,
                'subtitle': 12,
                'normal': 10
            },
            'margins': {
                'left': 0.5,
                'right': 0.5,
                'top': 0.5,
                'bottom': 0.5
            },
            'currency': 'DZD',
            'tax_rate': 0.00,
            'show_tax': False
        }

    def number_to_french_words(self, number):
        """Convertisseur manuel de nombres en lettres (Français)"""
        units = ["", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf"]
        teens = ["dix", "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf"]
        tens = ["", "dix", "vingt", "trente", "quarante", "cinquante", "soixante", "soixante-dix", "quatre-vingt", "quatre-vingt-dix"]
        
        def _convert_below_100(n):
            if n < 10: return units[n]
            if 10 <= n < 20: return teens[n-10]
            if n < 70:
                t, u = divmod(n, 10)
                if u == 0: return tens[t]
                if u == 1: return f"{tens[t]}-et-un"
                return f"{tens[t]}-{units[u]}"
            if 70 <= n < 80:
                return f"soixante-{'et-onze' if n==71 else teens[n-70]}"
            if 80 <= n < 90:
                t, u = divmod(n, 10)
                return f"quatre-vingt{'' if u==0 else '-' + units[u]}"
            if 90 <= n < 100:
                return f"quatre-vingt-{teens[n-90]}"
            return ""

        def _convert_below_1000(n):
            if n == 0: return ""
            h, r = divmod(n, 100)
            if h == 0: return _convert_below_100(r)
            prefix = "cent" if h == 1 else f"{units[h]}-cent"
            if r == 0: return prefix + ("s" if h > 1 else "")
            return f"{prefix}-{_convert_below_100(r)}"

        if number == 0: return "zéro"
        
        res = []
        millions, rest = divmod(int(number), 1000000)
        if millions > 0:
            res.append(f"{_convert_below_1000(millions)} million{'s' if millions > 1 else ''}")
        
        thousands, rest = divmod(rest, 1000)
        if thousands > 0:
            if thousands == 1:
                res.append("mille")
            else:
                res.append(f"{_convert_below_1000(thousands)} mille")
        
        if rest > 0:
            res.append(_convert_below_1000(rest))
            
        return " ".join(res).replace("- -", "-").strip()

    def generate_pdf(self, invoice, output_path=None):
        if output_path is None:
            output_path = io.BytesIO()
            
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=self.config['margins']['right']*inch,
            leftMargin=self.config['margins']['left']*inch,
            topMargin=self.config['margins']['top']*inch,
            bottomMargin=self.config['margins']['bottom']*inch
        )
        
        elements = []
        # On ne met plus le header dans les éléments mais on laisse de l'espace en haut
        elements.append(Spacer(1, 1.3*inch))
        elements.extend(self._build_info_section(invoice))
        elements.extend(self._build_items_table(invoice))
        elements.extend(self._build_closing_sentence(invoice))
        
        # Passer l'objet invoice au doc pour que les callbacks puissent y accéder
        doc.invoice = invoice
        
        # Le header et le footer sont dessinés via onPage pour la pleine largeur
        doc.build(elements, 
                  onFirstPage=lambda c, d: (self._draw_header(c, d), self._draw_footer(c, d)), 
                  onLaterPages=lambda c, d: (self._draw_header(c, d), self._draw_footer(c, d)))
        
        # Si on utilise un buffer, il faut revenir au début avant de le renvoyer
        if isinstance(output_path, io.BytesIO):
            output_path.seek(0)
            
        return output_path

    def _draw_header(self, canvas, doc):
        """Dessiner l'en-tête en pleine largeur"""
        canvas.saveState()
        invoice = doc.invoice
        from reportlab.platypus import Image as RLImage
        
        # Rectangle de fond
        page_width = doc.width + doc.leftMargin + doc.rightMargin
        header_height = 1.3 * inch
        canvas.setFillColor(colors.HexColor(self.config['colors']['accent']))
        canvas.rect(0, A4[1] - header_height, page_width, header_height, stroke=0, fill=1)
        
        # Logo
        logo_path = self.config['company'].get('logo')
        logo = None
        if logo_path and os.path.exists(logo_path):
            try:
                # Logo qui prend toute la hauteur (avec un petit padding vertical de 5pts)
                logo_size = header_height - 10
                logo = RLImage(logo_path, width=logo_size, height=logo_size)
            except: pass

        # Styles
        title_style = ParagraphStyle(
            'TitleStyleFull',
            fontName='Helvetica-Bold',
            fontSize=22 if invoice.invoice_type == 'proforma' else 28,
            textColor=colors.whitesmoke,
            alignment=2
        )
        
        header_text = [
            Paragraph(f"{self.config['company']['name']}", 
                      ParagraphStyle('H1Full', fontName=self.config['fonts']['header'], fontSize=28, textColor=colors.whitesmoke, leading=32)),
            Paragraph(f"{self.config['company']['subtitle1']}", 
                      ParagraphStyle('H2Full', fontName=self.config['fonts']['subtitle'], fontSize=12, textColor=colors.whitesmoke, leading=14)),
            Paragraph(f"Adresse {self.config['company']['address']}<br/>{self.config['company']['phone']}", 
                      ParagraphStyle('HInfoFull', fontName=self.config['fonts']['normal'], fontSize=10, textColor=colors.whitesmoke, leading=12))
        ]

        # Titre dynamique
        title_text = "Facture Proforma" if invoice.invoice_type == 'proforma' else "Facture"
        
        # Construction de la table pour le contenu du header
        data = [[logo or "", header_text, Paragraph(title_text, title_style)]]
        header_table = Table(data, colWidths=[1.3*inch, 3.8*inch, page_width - 5.1*inch - 30])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        w, h = header_table.wrap(page_width, header_height)
        header_table.drawOn(canvas, 0, A4[1] - header_height)
        
        canvas.restoreState()

    def _build_info_section(self, invoice):
        elements = []
        client = invoice.b2b_client
        
        client_lines = [Paragraph("<b>Facturé à:</b>", self.info_style)]
        if client:
            client_lines.append(Paragraph(client.company_name or "", self.info_style))
            
            # Identifiants fiscaux (afficher uniquement ceux qui sont renseignés)
            fiscal_ids = []
            if client.rc_number:
                fiscal_ids.append(f"RC: {client.rc_number}")
            if client.tax_number:
                fiscal_ids.append(f"NIF: {client.tax_number}")
            if client.nis_number:
                fiscal_ids.append(f"NIS: {client.nis_number}")
            if client.ai_number:
                fiscal_ids.append(f"AI: {client.ai_number}")
            
            # Afficher les identifiants sur des lignes séparées pour plus de clarté
            for fiscal_id in fiscal_ids:
                client_lines.append(Paragraph(fiscal_id, self.info_style))
            
            if client.address:
                client_lines.append(Paragraph(client.address, self.info_style))
        
        # Traduction des modes de paiement
        payment_mapping = {
            'cheque': 'Par Chèque',
            'espece': 'En Espèces',
            'virement': 'Par Virement',
            'traite': 'Par Traite'
        }
        payment_method = payment_mapping.get(invoice.payment_method, invoice.payment_method or "Chèque")
        
        invoice_lines = [
            Paragraph(f"<b>N de facture :</b> {invoice.invoice_number}", self.info_style),
            Paragraph(f"<b>Date :</b> {invoice.invoice_date.strftime('%d/%m/%Y')}", self.info_style),
            Paragraph(f"<b>Paiement :</b> {payment_method}", self.info_style)
        ]
        
        data = [[client_lines, invoice_lines]]
        info_table = Table(data, colWidths=[4.5*inch, 3.0*inch])
        info_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 25))
        return elements

    def _build_items_table(self, invoice):
        elements = []
        data = [['Jour', 'DESIGNATION', 'Quantité', 'PRIX UNIT HT', 'MONTANT HT']]
        
        items = sorted(invoice.invoice_items, key=lambda x: (x.section or "", x.id))
        
        last_jour = None
        for item in items:
            date_match = re.search(r'(\d{2}/\d{2}/\d{4})', item.section or "")
            current_jour = date_match.group(1) if date_match else ""
            
            # Ne pas répéter la date si c'est la même
            display_jour = current_jour if current_jour != last_jour else ""
            last_jour = current_jour
            
            description = item.description.replace('\\n', '<br/>')
            
            data.append([
                display_jour,
                Paragraph(description, self.info_style),
                f"{float(item.quantity):g}",
                f"{float(item.unit_price):,.0f}",
                f"{float(item.total_price):,.0f}"
            ])
            
        data.append(['', '', '', 'MONTANT HT', f"{float(invoice.total_amount):,.00f}"])
        data.append(['', '', '', 
                     Paragraph("<b>TOTAL</b>", ParagraphStyle('Tot', fontName=self.config['fonts']['bold'], textColor=colors.whitesmoke, alignment=1)), 
                     Paragraph(f"<b>{float(invoice.total_amount):,.00f} DZD</b>", ParagraphStyle('TotVal', fontName=self.config['fonts']['bold'], textColor=colors.whitesmoke, alignment=1))])
        
        table = Table(data, colWidths=[1.0*inch, 3.0*inch, 1.0*inch, 1.25*inch, 1.25*inch])
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('GRID', (0, 0), (-1, -3), 0.5, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), self.config['fonts']['bold']),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (3, -1), (4, -1), colors.HexColor('#B08050')),
            ('GRID', (3, -2), (4, -1), 1, colors.black),
            ('ALIGN', (3, -2), (4, -1), 'CENTER'),
            ('BACKGROUND', (3, -2), (4, -2), colors.whitesmoke),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 40))
        return elements

    def _build_closing_sentence(self, invoice):
        amount_words = self.number_to_french_words(int(invoice.total_amount))
        sentence = f"« Arrêtée la présente facture à la somme de : {amount_words} dinars algériens. »"
        return [Paragraph(sentence, self.info_style), Spacer(1, 50)]

    def _draw_footer(self, canvas, doc):
        """Dessiner le pied de page tout en bas de la page"""
        canvas.saveState()
        
        # Définition du style du footer
        footer_style = ParagraphStyle('Footer', 
                                     fontName=self.config['fonts']['normal'], 
                                     fontSize=9, # Légèrement plus petit pour tenir sur une ligne
                                     textColor=colors.whitesmoke, 
                                     alignment=1, 
                                     leading=12)
        
        # Fusion des informations sur une seule ligne
        footer_line = "RC N° : 16/00 - 4954376 A18 / NIF: 185160600384161 / AI : 16235191021 / RIB: 021 00010115041061025 BIC: SOGEDZAL"
        
        # Création d'une table pour le fond coloré et le texte
        footer_content = [
            [Paragraph(footer_line, footer_style)],
            [Paragraph("TEL: 00213 556 25 03 70 - Merci de Votre Confiance", footer_style)]
        ]
        footer_table = Table(footer_content, colWidths=[doc.width + doc.leftMargin + doc.rightMargin])
        footer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#B08050')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        # Calculer la position (tout en bas)
        w, h = footer_table.wrap(doc.width, doc.height)
        footer_table.drawOn(canvas, 0, 0)
        
        canvas.restoreState()

    def get_filename(self, invoice):
        """Générer le nom de fichier"""
        if invoice.invoice_type == 'proforma':
            prefix = "FP"
        else:
            prefix = "FF"
        
        client_name = invoice.b2b_client.company_name.replace(' ', '_')
        date_str = invoice.invoice_date.strftime('%d%m%Y')
        
        return f"{prefix}_{client_name}_{date_str}.pdf"

def get_fee_maison_template():
    return InvoiceTemplate()
