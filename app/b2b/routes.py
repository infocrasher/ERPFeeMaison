"""
Routes pour le module B2B
"""

from flask import render_template, request, redirect, url_for, flash, jsonify, send_file, current_app
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from decimal import Decimal
import io
import csv
import json
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
from .invoice_templates import get_fee_maison_template


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
            # Identifiants fiscaux
            rc_number=form.rc_number.data,
            tax_number=form.tax_number.data,
            nis_number=form.nis_number.data,
            ai_number=form.ai_number.data,
            # Conditions commerciales
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
        # Identifiants fiscaux
        client.rc_number = form.rc_number.data
        client.tax_number = form.tax_number.data
        client.nis_number = form.nis_number.data
        client.ai_number = form.ai_number.data
        # Conditions commerciales
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
            is_multi_day=False,
            period_start=None,
            period_end=None,
            notes=form.notes.data
        )
        
        # Générer le numéro de commande
        order.generate_order_number()
        
        db.session.add(order)
        db.session.flush()  # Pour obtenir l'ID de la commande
        
        # Ajouter les items
        for item_data in form.items.data:
            product_value = item_data.get('product')
            
            # Gestion de la composition (JSON)
            composition_data = None
            if item_data.get('composition'):
                try:
                    composition_data = json.loads(item_data['composition'])
                except Exception as e:
                    current_app.logger.error(f"Erreur parsing composition: {e}")
                    composition_data = None

            if product_value:
                if product_value == 'composite':
                    # Produit composé - utiliser la description pour stocker les détails
                    item = B2BOrderItem(
                        b2b_order_id=order.id,
                        product_id=None,  # Pas de produit spécifique pour un composé
                        quantity=item_data['quantity'],
                        unit_price=item_data['unit_price'],
                        description=item_data.get('description', ''),
                        composition=composition_data
                    )
                else:
                    # Produit simple
                    item = B2BOrderItem(
                        b2b_order_id=order.id,
                        product_id=int(product_value),
                        quantity=item_data['quantity'],
                        unit_price=item_data['unit_price'],
                        description=item_data.get('description', ''),
                        composition=composition_data
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
    
    # Pré-remplir les items existants (GET uniquement)
    if request.method == 'GET':
        # Vider les entrées existantes du formulaire
        form.items.entries = []
        form.items.last_index = -1  # ✅ Réinitialiser l'index du FieldList
        
        # Charger les produits pour les choix du select
        from models import Product
        products = Product.query.filter_by(product_type='finished').order_by(Product.name).all()
        product_choices = [('', '-- Choisir un produit --'), ('composite', '🧩 Produit composé')]
        for product in products:
            price = product.price or 0.0
            label = f"{product.name} ({price:.2f} DA / {product.unit})"
            product_choices.append((str(product.id), label))
        
        # Ajouter chaque item existant au formulaire
        for item in order.items.all():
            form.items.append_entry()
            entry = form.items.entries[-1]
            entry.form.product.choices = product_choices
            
            if item.product_id:
                # Produit simple
                entry.form.product.data = str(item.product_id)
            else:
                # Produit composé
                entry.form.product.data = 'composite'
            
            entry.form.quantity.data = item.quantity
            entry.form.unit_price.data = item.unit_price
            entry.form.description.data = item.description or ''
            
            # Sérialiser la composition en JSON si présente
            if item.composition:
                entry.form.composition.data = json.dumps(item.composition) if isinstance(item.composition, list) else item.composition
    
    if form.validate_on_submit():
        order.b2b_client_id = form.b2b_client_id.data
        order.delivery_date = form.delivery_date.data
        order.is_multi_day = False
        order.period_start = None
        order.period_end = None
        order.notes = form.notes.data
        
        # Supprimer les anciens items
        order.items.delete()
        db.session.flush()  # ✅ Synchroniser avant d'ajouter les nouveaux items
        
        # Ajouter les nouveaux items
        for item_data in form.items.data:
            product_value = item_data.get('product')
            if product_value:
                # Gestion de la composition (JSON)
                composition_data = None
                if item_data.get('composition'):
                    try:
                        composition_data = json.loads(item_data['composition'])
                    except Exception as e:
                        current_app.logger.error(f"Erreur parsing composition: {e}")
                        composition_data = None

                if product_value == 'composite':
                    # Produit composé - utiliser la description pour stocker les détails
                    item = B2BOrderItem(
                        b2b_order_id=order.id,
                        product_id=None,  # Pas de produit spécifique pour un composé
                        quantity=item_data['quantity'],
                        unit_price=item_data['unit_price'],
                        description=item_data.get('description', ''),
                        composition=composition_data
                    )
                else:
                    # Produit simple
                    item = B2BOrderItem(
                        b2b_order_id=order.id,
                        product_id=int(product_value),
                        quantity=item_data['quantity'],
                        unit_price=item_data['unit_price'],
                        description=item_data.get('description', ''),
                        composition=composition_data
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
        old_status = order.status
        order.status = new_status
        
        # Gestion du stock lors de la livraison
        if old_status != 'delivered' and new_status == 'delivered':
            # Déstockage
            try:
                for item in order.items:
                    # Traiter la composition si elle existe (Prioritaire)
                    if item.composition:
                        try:
                            components = item.composition if isinstance(item.composition, list) else json.loads(item.composition)
                            for comp in components:
                                comp_id = comp.get('product_id')
                                comp_qty = float(comp.get('quantity') or 0) * float(item.quantity) # Qty unitaire * Qty commande
                                
                                product = Product.query.get(comp_id)
                                if product:
                                    # Déterminer l'emplacement de stock (Logique simplifiée)
                                    # Produits finis -> Comptoir, Ingrédients -> Magasin
                                    location = 'stock_comptoir' if product.product_type == 'finished' else 'stock_ingredients_magasin'
                                    product.update_stock_by_location(location, -comp_qty)
                        except Exception as e:
                            current_app.logger.error(f"Erreur déstockage composition item {item.id}: {e}")
                    
                    # Sinon traiter le produit simple (si pas de produit_id, c'est une box vide ou mal configurée)
                    elif item.product_id:
                        product = Product.query.get(item.product_id)
                        if product:
                            location = 'stock_comptoir' if product.product_type == 'finished' else 'stock_ingredients_magasin'
                            product.update_stock_by_location(location, -float(item.quantity))
                            
                flash(f'Statut changé vers "Livrée" - Stock mis à jour', 'success')
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Erreur lors de la mise à jour du stock: {e}")
                flash(f'Erreur lors du déstockage: {str(e)}', 'error')
                return redirect(url_for('b2b.view_order', order_id=order.id))

        db.session.commit()
        if new_status != 'delivered': # Si ce n'était pas une livraison (message générique)
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
    order_items_for_form = []
    
    # Récupérer les paramètres client et order depuis l'URL
    client_id = request.args.get('client', type=int)
    order_ids = request.args.getlist('order', type=int)
    
    initial_data = {}
    
    # Pré-remplir les données (GET uniquement)
    if request.method == 'GET':
        if client_id:
            initial_data['b2b_client_id'] = client_id
            client = B2BClient.query.get(client_id)
            if client and client.payment_terms > 0:
                initial_data['due_date'] = date.today() + timedelta(days=client.payment_terms)
        
        if order_ids:
            items_data = []
            orders = B2BOrder.query.filter(B2BOrder.id.in_(order_ids)).all()
            
            # Trier les commandes par date de livraison pour que la facture soit chronologique
            orders.sort(key=lambda x: x.delivery_date)
            
            for order in orders:
                if not client_id or order.b2b_client_id == client_id:
                    if 'b2b_client_id' not in initial_data:
                        initial_data['b2b_client_id'] = order.b2b_client_id
                        client_id = order.b2b_client_id  # Pour les prochaines commandes
                        
                    section_name = f"Livraison du {order.delivery_date.strftime('%d/%m/%Y')} ({order.order_number})"
                    
                    for item in order.items:
                        # Construction de la description
                        base_name = item.product.name if item.product else (item.description or "Produit composé")
                            
                        # Ajouter les détails de la composition si présents
                        details = ""
                        if item.composition:
                            try:
                                comps = item.composition if isinstance(item.composition, list) else json.loads(item.composition)
                                comp_strs = []
                                for c in comps:
                                    qty = float(c.get('quantity', 0))
                                    name = c.get('name', 'Inconnu')
                                    if qty == 1:
                                        comp_strs.append(name)
                                    else:
                                        comp_strs.append(f"{qty:g}x {name}")
                                if comp_strs:
                                    details = f" ({', '.join(comp_strs)})"
                            except Exception as e:
                                current_app.logger.error(f"Erreur formatage composition: {e}")
                        
                        manual_desc = f" - {item.description}" if item.description and item.description != base_name else ""
                        desc = f"{base_name}{details}{manual_desc}"
                        
                        item_data = {
                            'description': desc,
                            'quantity': item.quantity,
                            'unit_price': item.unit_price,
                            'section': section_name
                        }
                        items_data.append(item_data)
                
            if items_data:
                initial_data['invoice_items'] = items_data
                order_items_for_form = items_data

    # Initialiser le formulaire avec les données de la requête (POST) ou les données initiales (GET)
    if request.method == 'POST':
        form = InvoiceForm()
    else:
        form = InvoiceForm(data=initial_data)

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
        
        # Ajouter les items depuis le formulaire
        for item_data in form.invoice_items.data:
            quantity = item_data.get('quantity', 0)
            unit_price = item_data.get('unit_price', 0)
            
            invoice_item = InvoiceItem(
                invoice_id=invoice.id,
                description=item_data.get('description', ''),
                quantity=quantity,
                unit_price=unit_price,
                total_price=quantity * unit_price,
                section=item_data.get('section')
            )
            db.session.add(invoice_item)

        # Lier les commandes si présentes dans l'URL (pour traçabilité)
        if order_ids:
            orders = B2BOrder.query.filter(B2BOrder.id.in_(order_ids)).all()
            for order in orders:
                if order.b2b_client_id == invoice.b2b_client_id:
                    if order not in invoice.b2b_orders:
                        invoice.b2b_orders.append(order)
                
        # Calculer les montants
        invoice.calculate_amounts()
        
        db.session.commit()
        
        flash(f'Facture "{invoice.invoice_number}" créée avec succès !', 'success')
        return redirect(url_for('b2b.view_invoice', invoice_id=invoice.id))
    
    return render_template('b2b/invoices/form.html', form=form, title="Nouvelle facture", order_items_for_form=order_items_for_form)


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
                        # Déterminer la section (date de livraison)
                        section_name = f"Livraison du {order.delivery_date.strftime('%d/%m/%Y')} ({order.order_number})"
                        
                        invoice_item = InvoiceItem(
                            invoice_id=invoice.id,
                            product_id=item.product_id,
                            description=item_description,
                            quantity=item.quantity,
                            unit_price=item.unit_price,
                            total_price=item.subtotal,
                            section=section_name
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
    
    # Utiliser le template Fée Maison
    template = get_fee_maison_template()
    buffer = template.generate_pdf(invoice)
    filename = template.get_filename(invoice)
    
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