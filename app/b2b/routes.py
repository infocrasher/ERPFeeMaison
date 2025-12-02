"""
Routes pour le module B2B
"""

from flask import render_template, request, redirect, url_for, flash, jsonify, send_file, current_app
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from decimal import Decimal
import io
import csv
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from sqlalchemy import func, and_

from . import b2b
from .forms import B2BClientForm, B2BOrderForm, InvoiceForm, EmailTemplateForm
from models import db, B2BClient, B2BOrder, B2BOrderItem, Invoice, InvoiceItem, Product, User
from decorators import admin_required


# ==================== CLIENTS B2B ====================

@b2b.route('/clients')
@login_required
@admin_required
def list_clients():
    """Liste des clients B2B"""
    clients = B2BClient.query.order_by(B2BClient.company_name).all()
    return render_template('b2b/clients/list.html', clients=clients)


@b2b.route('/clients/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_client():
    """Créer un nouveau client B2B"""
    form = B2BClientForm()
    
    if form.validate_on_submit():
        client = B2BClient(
            company_name=form.company_name.data,
            contact_person=form.contact_person.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            tax_number=form.tax_number.data,
            payment_terms=form.payment_terms.data,
            credit_limit=form.credit_limit.data or 0.0,
            is_active=form.is_active.data
        )
        
        db.session.add(client)
        db.session.commit()
        
        flash(f'Client B2B "{client.company_name}" créé avec succès !', 'success')
        return redirect(url_for('b2b.list_clients'))
    
    return render_template('b2b/clients/form.html', form=form, title="Nouveau client B2B")


@b2b.route('/clients/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_client(client_id):
    """Modifier un client B2B"""
    client = B2BClient.query.get_or_404(client_id)
    form = B2BClientForm(obj=client)
    
    if form.validate_on_submit():
        client.company_name = form.company_name.data
        client.contact_person = form.contact_person.data
        client.email = form.email.data
        client.phone = form.phone.data
        client.address = form.address.data
        client.tax_number = form.tax_number.data
        client.payment_terms = form.payment_terms.data
        client.credit_limit = form.credit_limit.data or 0.0
        client.is_active = form.is_active.data
        
        db.session.commit()
        flash(f'Client B2B "{client.company_name}" modifié avec succès !', 'success')
        return redirect(url_for('b2b.list_clients'))
    
    return render_template('b2b/clients/form.html', form=form, client=client, title="Modifier le client")


@b2b.route('/clients/<int:client_id>')
@login_required
@admin_required
def view_client(client_id):
    """Voir les détails d'un client B2B"""
    client = B2BClient.query.get_or_404(client_id)
    orders = client.orders.order_by(B2BOrder.created_at.desc()).limit(10).all()
    invoices = client.invoices.order_by(Invoice.created_at.desc()).limit(10).all()
    
    return render_template('b2b/clients/view.html', client=client, orders=orders, invoices=invoices)


# ==================== COMMANDES B2B ====================

@b2b.route('/orders')
@login_required
@admin_required
def list_orders():
    """Liste des commandes B2B"""
    status_filter = request.args.get('status', '')
    client_filter = request.args.get('client', '')
    
    query = B2BOrder.query.join(B2BClient)
    
    if status_filter:
        query = query.filter(B2BOrder.status == status_filter)
    
    if client_filter:
        query = query.filter(B2BClient.id == int(client_filter))
    
    orders = query.order_by(B2BOrder.created_at.desc()).all()
    clients = B2BClient.query.filter_by(is_active=True).order_by(B2BClient.company_name).all()
    
    return render_template('b2b/orders/list.html', orders=orders, clients=clients)


@b2b.route('/orders/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_order():
    """Créer une nouvelle commande B2B"""
    form = B2BOrderForm()
    
    if form.validate_on_submit():
        # ✅ CORRECTION : Initialiser order_date explicitement
        # Créer la commande
        order = B2BOrder(
            b2b_client_id=form.b2b_client_id.data,
            user_id=current_user.id,
            order_date=date.today(),  # ✅ Ajouté
            delivery_date=form.delivery_date.data,
            is_multi_day=form.is_multi_day.data,
            period_start=form.period_start.data if form.is_multi_day.data else None,
            period_end=form.period_end.data if form.is_multi_day.data else None,
            notes=form.notes.data
        )
        
        # Générer le numéro de commande
        order.generate_order_number()
        
        db.session.add(order)
        db.session.flush()  # Pour obtenir l'ID de la commande
        
        # Ajouter les items
        for item_data in form.items.data:
            product_value = item_data.get('product')
            if product_value:
                if product_value == 'composite':
                    # Produit composé - utiliser la description pour stocker les détails
                    item = B2BOrderItem(
                        b2b_order_id=order.id,
                        product_id=None,  # Pas de produit spécifique pour un composé
                        quantity=item_data['quantity'],
                        unit_price=item_data['unit_price'],
                        description=item_data.get('description', '')
                    )
                else:
                    # Produit simple
                    item = B2BOrderItem(
                        b2b_order_id=order.id,
                        product_id=int(product_value),
                        quantity=item_data['quantity'],
                        unit_price=item_data['unit_price'],
                        description=item_data.get('description', '')
                    )
                
                db.session.add(item)
        
        # Calculer le montant total
        order.calculate_total_amount()
        
        db.session.commit()
        
        flash(f'Commande B2B "{order.order_number}" créée avec succès !', 'success')
        return redirect(url_for('b2b.view_order', order_id=order.id))
    
    return render_template('b2b/orders/form.html', form=form, title="Nouvelle commande B2B")


@b2b.route('/orders/<int:order_id>')
@login_required
@admin_required
def view_order(order_id):
    """Voir les détails d'une commande B2B"""
    order = B2BOrder.query.get_or_404(order_id)
    return render_template('b2b/orders/view.html', order=order)


@b2b.route('/orders/<int:order_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_order(order_id):
    """Modifier une commande B2B"""
    order = B2BOrder.query.get_or_404(order_id)
    
    if order.status not in ['pending']:
        flash('Seules les commandes en attente peuvent être modifiées', 'warning')
        return redirect(url_for('b2b.view_order', order_id=order.id))
    
    form = B2BOrderForm(obj=order)
    
    if form.validate_on_submit():
        order.b2b_client_id = form.b2b_client_id.data
        order.delivery_date = form.delivery_date.data
        order.is_multi_day = form.is_multi_day.data
        order.period_start = form.period_start.data if form.is_multi_day.data else None
        order.period_end = form.period_end.data if form.is_multi_day.data else None
        order.notes = form.notes.data
        
        # Supprimer les anciens items
        order.items.delete()
        
        # Ajouter les nouveaux items
        for item_data in form.items.data:
            product_value = item_data.get('product')
            if product_value:
                if product_value == 'composite':
                    # Produit composé - utiliser la description pour stocker les détails
                    item = B2BOrderItem(
                        b2b_order_id=order.id,
                        product_id=None,  # Pas de produit spécifique pour un composé
                        quantity=item_data['quantity'],
                        unit_price=item_data['unit_price'],
                        description=item_data.get('description', '')
                    )
                else:
                    # Produit simple
                    item = B2BOrderItem(
                        b2b_order_id=order.id,
                        product_id=int(product_value),
                        quantity=item_data['quantity'],
                        unit_price=item_data['unit_price'],
                        description=item_data.get('description', '')
                    )
                
                db.session.add(item)
        
        # Recalculer le montant total
        order.calculate_total_amount()
        
        db.session.commit()
        flash(f'Commande B2B "{order.order_number}" modifiée avec succès !', 'success')
        return redirect(url_for('b2b.view_order', order_id=order.id))
    
    return render_template('b2b/orders/form.html', form=form, order=order, title="Modifier la commande")


@b2b.route('/orders/<int:order_id>/status', methods=['POST'])
@login_required
@admin_required
def change_order_status(order_id):
    """Changer le statut d'une commande B2B"""
    order = B2BOrder.query.get_or_404(order_id)
    new_status = request.form.get('status')
    
    if new_status in ['pending', 'in_production', 'ready_at_shop', 'delivered', 'completed', 'cancelled']:
        order.status = new_status
        db.session.commit()
        flash(f'Statut de la commande changé vers "{order.get_status_display()}"', 'success')
    
    return redirect(url_for('b2b.view_order', order_id=order.id))


# ==================== FACTURES ====================

@b2b.route('/invoices')
@login_required
@admin_required
def list_invoices():
    """Liste des factures"""
    status_filter = request.args.get('status', '')
    type_filter = request.args.get('type', '')
    
    query = Invoice.query.join(B2BClient)
    
    if status_filter:
        query = query.filter(Invoice.status == status_filter)
    
    if type_filter:
        query = query.filter(Invoice.invoice_type == type_filter)
    
    invoices = query.order_by(Invoice.created_at.desc()).all()
    
    return render_template('b2b/invoices/list.html', invoices=invoices)


@b2b.route('/invoices/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_invoice():
    """Créer une nouvelle facture"""
    form = InvoiceForm()
    
    # ✅ CORRECTION : Récupérer les paramètres client et order depuis l'URL
    client_id = request.args.get('client', type=int)
    order_id = request.args.get('order', type=int)
    
    # Pré-remplir le client si fourni
    if request.method == 'GET' and client_id:
        form.b2b_client_id.data = client_id
        client = B2BClient.query.get(client_id)
        if client and client.payment_terms > 0:
            form.due_date.data = date.today() + timedelta(days=client.payment_terms)
    
    if form.validate_on_submit():
        # Créer la facture
        invoice = Invoice(
            b2b_client_id=form.b2b_client_id.data,
            invoice_type=form.invoice_type.data,
            invoice_date=form.invoice_date.data,
            due_date=form.due_date.data,
            notes=form.notes.data
        )
        
        # Générer le numéro de facture
        invoice.generate_invoice_number()
        
        db.session.add(invoice)
        db.session.flush()  # Pour obtenir l'ID de la facture
        
        # ✅ CORRECTION : Si une commande est liée, l'ajouter automatiquement
        if order_id:
            order = B2BOrder.query.get(order_id)
            if order and order.b2b_client_id == invoice.b2b_client_id:
                # Ajouter la relation commande-facture
                invoice.b2b_orders.append(order)
                
                # Créer les lignes de facture à partir de la commande
                for item in order.items:
                    # Gestion correcte des produits composés
                    if item.product_id is None:
                        # Produit composé
                        item_description = item.description or "Produit composé (détails non spécifiés)"
                    else:
                        # Produit simple
                        item_description = item.description or item.product.name
                    
                    invoice_item = InvoiceItem(
                        invoice_id=invoice.id,
                        product_id=item.product_id,
                        description=item_description,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                        total_price=item.subtotal
                    )
                    db.session.add(invoice_item)
                
                # Calculer les montants
                invoice.calculate_amounts()
        
        db.session.commit()
        
        flash(f'Facture "{invoice.invoice_number}" créée avec succès !', 'success')
        # ✅ CORRECTION : Rediriger vers la vue de la facture au lieu de l'édition
        return redirect(url_for('b2b.view_invoice', invoice_id=invoice.id))
    
    return render_template('b2b/invoices/form.html', form=form, title="Nouvelle facture")


@b2b.route('/invoices/<int:invoice_id>')
@login_required
@admin_required
def view_invoice(invoice_id):
    """Voir une facture"""
    invoice = Invoice.query.get_or_404(invoice_id)
    return render_template('b2b/invoices/view.html', invoice=invoice)


@b2b.route('/invoices/<int:invoice_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_invoice(invoice_id):
    """Modifier une facture"""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    if invoice.status not in ['draft']:
        flash('Seules les factures en brouillon peuvent être modifiées', 'warning')
        return redirect(url_for('b2b.view_invoice', invoice_id=invoice.id))
    
    if request.method == 'POST':
        # Ajouter des commandes à la facture
        order_ids = request.form.getlist('order_ids')
        if order_ids:
            orders = B2BOrder.query.filter(B2BOrder.id.in_(order_ids)).all()
            
            # ✅ CORRECTION : Vérifier que les commandes ne sont pas déjà facturées ailleurs
            for order in orders:
                # Vérifier si déjà facturée dans une autre facture
                if order.invoices.count() > 0:
                    existing_invoice = order.invoices.first()
                    flash(f'Commande {order.order_number} est déjà facturée dans {existing_invoice.invoice_number}', 'warning')
                    continue
                
                # Ajouter la relation commande-facture
                if order not in invoice.b2b_orders:
                    invoice.b2b_orders.append(order)
            
            # Créer les lignes de facture à partir des commandes
            for order in orders:
                # ✅ CORRECTION : Vérifier que la commande n'est pas déjà dans une autre facture
                if order.invoices.count() > 1:  # Plus d'une facture (la nôtre)
                    continue
                
                for item in order.items:
                    # ✅ CORRECTION : Vérifier si l'item existe déjà dans la facture (éviter doublons)
                    # Construire la description correctement pour produits composés
                    if item.product_id is None:
                        # Produit composé
                        item_description = item.description or "Produit composé (détails non spécifiés)"
                    else:
                        # Produit simple
                        item_description = item.description or item.product.name
                    
                    # Vérifier si un item similaire existe déjà
                    existing_item = InvoiceItem.query.filter_by(
                        invoice_id=invoice.id,
                        product_id=item.product_id,
                        description=item_description
                    ).first()
                    
                    if not existing_item:
                        # ✅ CORRECTION : Gestion correcte des produits composés
                        invoice_item = InvoiceItem(
                            invoice_id=invoice.id,
                            product_id=item.product_id,
                            description=item_description,
                            quantity=item.quantity,
                            unit_price=item.unit_price,
                            total_price=item.subtotal
                        )
                        db.session.add(invoice_item)
            
            invoice.calculate_amounts()
            db.session.commit()
            flash('Commandes ajoutées à la facture avec succès !', 'success')
        
        return redirect(url_for('b2b.view_invoice', invoice_id=invoice.id))
    
    # Récupérer les commandes disponibles pour ce client
    available_orders = B2BOrder.query.filter(
        B2BOrder.b2b_client_id == invoice.b2b_client_id,
        B2BOrder.status.in_(['completed', 'delivered']),
        ~B2BOrder.invoices.any()  # Pas déjà facturées
    ).all()
    
    return render_template('b2b/invoices/edit.html', invoice=invoice, available_orders=available_orders)


@b2b.route('/invoices/<int:invoice_id>/status', methods=['POST'])
@login_required
@admin_required
def change_invoice_status(invoice_id):
    """Changer le statut d'une facture"""
    invoice = Invoice.query.get_or_404(invoice_id)
    new_status = request.form.get('status')
    
    if new_status in ['draft', 'sent', 'paid', 'overdue', 'cancelled']:
        invoice.status = new_status
        
        if new_status == 'paid':
            invoice.payment_date = date.today()
            
            # ✅ CORRECTION : Intégration comptable pour facture payée
            try:
                from app.accounting.services import AccountingIntegrationService
                AccountingIntegrationService.create_sale_entry(
                    order_id=None,  # Pas de commande normale
                    sale_amount=float(invoice.total_amount),
                    payment_method=invoice.payment_method or 'cheque',
                    description=f'Facture B2B {invoice.invoice_number} - {invoice.b2b_client.company_name}'
                )
                flash(f'Facture marquée comme payée et intégrée à la comptabilité', 'success')
            except Exception as e:
                current_app.logger.error(f"Erreur intégration comptable facture B2B (invoice_id={invoice.id}): {e}", exc_info=True)
                flash(f'Facture marquée comme payée (erreur intégration comptable)', 'warning')
        else:
            flash(f'Statut de la facture changé vers "{invoice.get_status_display()}"', 'success')
        
        db.session.commit()
    
    return redirect(url_for('b2b.view_invoice', invoice_id=invoice.id))


# ==================== EXPORT ET EMAIL ====================

@b2b.route('/invoices/<int:invoice_id>/export/pdf')
@login_required
@admin_required
def export_invoice_pdf(invoice_id):
    """Exporter une facture en PDF"""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Créer le PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Centré
    )
    
    # En-tête
    story.append(Paragraph("FÉE MAISON", title_style))
    story.append(Paragraph("Restaurant & Traiteur", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Informations de la facture
    if invoice.invoice_type == 'proforma':
        story.append(Paragraph("FACTURE PROFORMA", styles['Heading2']))
    else:
        story.append(Paragraph("FACTURE", styles['Heading2']))
    
    story.append(Paragraph(f"Numéro: {invoice.invoice_number}", styles['Normal']))
    story.append(Paragraph(f"Date: {invoice.invoice_date.strftime('%d/%m/%Y')}", styles['Normal']))
    story.append(Paragraph(f"Échéance: {invoice.due_date.strftime('%d/%m/%Y')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Informations client
    story.append(Paragraph("CLIENT:", styles['Heading3']))
    story.append(Paragraph(invoice.b2b_client.company_name, styles['Normal']))
    if invoice.b2b_client.contact_person:
        story.append(Paragraph(f"Contact: {invoice.b2b_client.contact_person}", styles['Normal']))
    if invoice.b2b_client.address:
        story.append(Paragraph(f"Adresse: {invoice.b2b_client.address}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Tableau des articles
    data = [['Description', 'Quantité', 'Prix unitaire', 'Total']]
    for item in invoice.invoice_items:
        data.append([
            item.description,
            str(item.quantity),
            f"{item.unit_price:.2f} DA",
            f"{item.total_price:.2f} DA"
        ])
    
    # Totaux
    data.append(['', '', 'Sous-total:', f"{invoice.subtotal:.2f} DA"])
    data.append(['', '', 'TVA (19%):', f"{invoice.tax_amount:.2f} DA"])
    data.append(['', '', 'Total:', f"{invoice.total_amount:.2f} DA"])
    
    table = Table(data, colWidths=[200, 60, 80, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -3), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Notes
    if invoice.notes:
        story.append(Paragraph("Notes:", styles['Heading3']))
        story.append(Paragraph(invoice.notes, styles['Normal']))
    
    # Générer le PDF
    doc.build(story)
    buffer.seek(0)
    
    filename = f"facture_{invoice.invoice_number}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')


@b2b.route('/invoices/<int:invoice_id>/email', methods=['GET', 'POST'])
@login_required
@admin_required
def send_invoice_email(invoice_id):
    """Envoyer une facture par email"""
    invoice = Invoice.query.get_or_404(invoice_id)
    form = EmailTemplateForm()
    
    # Pré-remplir le formulaire
    if request.method == 'GET':
        form.subject.data = f"Facture {invoice.invoice_number} - Fée Maison"
        form.message.data = f"""Bonjour,

Veuillez trouver ci-joint notre facture {invoice.invoice_number} d'un montant de {invoice.total_amount:.2f} DA.

Date d'échéance : {invoice.due_date.strftime('%d/%m/%Y')}

Pour toute question, n'hésitez pas à nous contacter.

Cordialement,
L'équipe Fée Maison"""
    
    if form.validate_on_submit():
        # TODO: Implémenter l'envoi d'email
        # Pour l'instant, on simule l'envoi
        flash('Email envoyé avec succès ! (Simulation)', 'success')
        return redirect(url_for('b2b.view_invoice', invoice_id=invoice.id))
    
    return render_template('b2b/invoices/email.html', form=form, invoice=invoice)


# ==================== API POUR AJAX ====================

@b2b.route('/api/clients')
@login_required
def api_clients():
    """API pour récupérer les clients B2B"""
    clients = B2BClient.query.filter_by(is_active=True).order_by(B2BClient.company_name).all()
    return jsonify([{
        'id': c.id,
        'name': c.company_name,
        'payment_terms': c.payment_terms
    } for c in clients])


@b2b.route('/api/products')
@login_required
def api_products():
    """API pour récupérer les produits finis"""
    products = Product.query.filter_by(product_type='finished').order_by(Product.name).all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'price': float(p.price or 0),
        'unit': p.unit
    } for p in products]) 