# pyright: reportCallIssue=false, reportAttributeAccessIssue=false
"""

Routes pour la gestion des achats fournisseurs avec système d'unités et paiement

Module: app/purchases/routes.py

Auteur: ERP Fée Maison

"""

from flask import render_template, redirect, url_for, flash, request, jsonify, current_app, abort
from flask_login import login_required, current_user
from extensions import db
from .models import Purchase, PurchaseItem, PurchaseStatus, PurchaseUrgency
from .forms import (PurchaseForm, MarkAsPaidForm, PurchaseApprovalForm, PurchaseReceiptForm,
PurchaseSearchForm, QuickPurchaseForm, PurchaseReceiptItemForm)
from decorators import admin_required
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, timedelta
import json
import pytz
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Optional

# ### DEBUT DE LA MODIFICATION ###
# Import direct des modèles en haut du fichier pour la clarté et la robustesse.
# La fonction `get_main_models` a été supprimée.
from models import Product, Unit
# ### FIN DE LA MODIFICATION ###

# Import du blueprint depuis __init__.py
from . import bp as purchases


# ==================== ROUTES PRINCIPALES CRUD ====================

@purchases.route('/', methods=['GET', 'POST'])
@login_required
def list_purchases():
    """Liste de tous les achats avec filtres et statut paiement"""
    form = PurchaseSearchForm()
    
    # Construction de la requête de base
    query = Purchase.query
    
    payment_filter = request.args.get('payment_status', 'all')
    if payment_filter == 'unpaid':
        query = query.filter(Purchase.is_paid == False)
    elif payment_filter == 'paid':
        query = query.filter(Purchase.is_paid == True)

    # ✅ CORRECTION : Gérer les filtres en GET et POST
    if request.method == 'POST' and form.validate_on_submit():
        if form.search_term.data:
            search = f"%{form.search_term.data}%"
            # ✅ CORRECTION : Recherche aussi dans les noms de produits via PurchaseItem
            query = query.outerjoin(PurchaseItem).outerjoin(Product).filter(or_(
                Purchase.reference.ilike(search),
                Purchase.supplier_name.ilike(search),
                Purchase.notes.ilike(search),
                Product.name.ilike(search)  # Recherche dans les noms de produits
            )).distinct()
        if form.status_filter.data != 'all':
            query = query.filter(Purchase.status == PurchaseStatus(form.status_filter.data))
        if form.urgency_filter.data != 'all':
            query = query.filter(Purchase.urgency == PurchaseUrgency(form.urgency_filter.data))
        if form.supplier_filter.data:
            supplier_search = f"%{form.supplier_filter.data}%"
            # type: ignore[attr-defined] - Purchase.supplier_name est une colonne SQLAlchemy
            query = query.filter(Purchase.supplier_name.ilike(supplier_search))
    elif request.method == 'GET':
        # Gérer aussi les filtres via GET (pour les liens et la pagination)
        search_term = request.args.get('search_term', '')
        status_filter = request.args.get('status_filter', 'all')
        urgency_filter = request.args.get('urgency_filter', 'all')
        supplier_filter = request.args.get('supplier_filter', '')
        
        if search_term:
            search = f"%{search_term}%"
            # ✅ CORRECTION : Recherche aussi dans les noms de produits via PurchaseItem
            query = query.outerjoin(PurchaseItem).outerjoin(Product).filter(or_(
                Purchase.reference.ilike(search),
                Purchase.supplier_name.ilike(search),
                Purchase.notes.ilike(search),
                Product.name.ilike(search)  # Recherche dans les noms de produits
            )).distinct()
        if status_filter != 'all':
            query = query.filter(Purchase.status == PurchaseStatus(status_filter))
        if urgency_filter != 'all':
            query = query.filter(Purchase.urgency == PurchaseUrgency(urgency_filter))
        if supplier_filter:
            supplier_search = f"%{supplier_filter}%"
            query = query.filter(Purchase.supplier_name.ilike(supplier_search))

    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('PURCHASES_PER_PAGE', 20)
    # ✅ Le distinct() dans la requête évite déjà les duplications
    purchases_list = query.order_by(desc(Purchase.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )

    stats = {
        'total_purchases': Purchase.query.count(),
        'pending_approval': Purchase.query.filter(
            Purchase.status.in_([PurchaseStatus.DRAFT, PurchaseStatus.REQUESTED])
        ).count(),
        'unpaid_purchases': Purchase.query.filter(Purchase.is_paid == False).count(),
        'paid_purchases': Purchase.query.filter(Purchase.is_paid == True).count(),
        'overdue': len([p for p in Purchase.query.all() if p.is_overdue()])
    }

    suppliers_list = db.session.query(Purchase.supplier_name).distinct().all()
    suppliers_list = [s[0] for s in suppliers_list if s[0]]

    return render_template(
        'purchases/list_purchases.html',
        title="Gestion des Achats",
        purchases=purchases_list,
        form=form,
        stats=stats,
        total_purchases=stats['total_purchases'],
        pending_purchases=stats['pending_approval'],
        unpaid_purchases=stats['unpaid_purchases'],
        paid_purchases=stats['paid_purchases'],
        total_amount_month=0,
        suppliers_count=len(suppliers_list),
        suppliers_list=suppliers_list,
        pagination=purchases_list,
        current_payment_filter=payment_filter
    )

@purchases.route('/new', methods=['GET', 'POST'])
@login_required
def new_purchase():
    """Création d'un nouveau bon d'achat avec PMP, gestion des consommables, calculs en Decimal et atomicité."""
    form = PurchaseForm(request.form) if request.method == 'POST' else PurchaseForm()

    if form.validate_on_submit():
        try:
            local_tz = pytz.timezone('Europe/Paris')
            naive_date = form.requested_date.data
            if naive_date is None:
                raise ValueError("La date de demande est requise.")
            aware_date = local_tz.localize(naive_date)
            
            purchase = Purchase(
                supplier_name=form.supplier_name.data,
                supplier_contact=form.supplier_contact.data,
                supplier_phone=form.supplier_phone.data,
                supplier_email=form.supplier_email.data,
                supplier_address=form.supplier_address.data,
                expected_delivery_date=form.expected_delivery_date.data,
                urgency=PurchaseUrgency(form.urgency.data),
                payment_terms=form.payment_terms.data,
                shipping_cost=Decimal(form.shipping_cost.data or '0.0'),
                tax_amount=Decimal(form.tax_amount.data or '0.0'),
                notes=form.notes.data,
                internal_notes=form.internal_notes.data,
                terms_conditions=form.terms_conditions.data,
                requested_date=aware_date,
                requested_by_id=current_user.id,
                is_paid=False,
                status=PurchaseStatus.RECEIVED
            )
            db.session.add(purchase)
            db.session.flush()

            items_added = 0
            product_ids = request.form.getlist('items[][product_id]')
            quantities = request.form.getlist('items[][quantity_ordered]')
            prices = request.form.getlist('items[][unit_price]')
            unit_ids = request.form.getlist('items[][unit]')
            stock_locations = request.form.getlist('items[][stock_location]')
            
            for i in range(len(product_ids)):
                if not product_ids[i] or not quantities[i] or not prices[i] or not unit_ids[i]:
                    continue

                product_id = int(product_ids[i])
                product = Product.query.get(product_id)
                
                if not product:
                     raise ValueError(f"Produit avec l'ID {product_id} non trouvé.")

                # Vérifier que le produit est achetable (ingrédient, consommable, ou produit fini avec can_be_purchased)
                is_purchasable = (
                    product.product_type in ['ingredient', 'consommable'] or
                    (product.product_type == 'finished' and product.can_be_purchased == True)
                )
                if not is_purchasable:
                    raise ValueError(f"Le produit '{product.name}' n'est pas achetable.")

                quantity_ordered = Decimal(quantities[i])
                price_per_unit_achat = Decimal(prices[i])
                unit_id = int(unit_ids[i])
                unit_object = Unit.query.get(unit_id)

                if not unit_object or quantity_ordered <= 0 or price_per_unit_achat < 0:
                    raise ValueError(f"Données invalides pour la ligne du produit {product.name}.")

                quantity_in_base_unit = float(quantity_ordered * unit_object.conversion_factor)
                
                # Calculer price_per_base_unit AVANT les blocs if/elif
                conversion_factor = Decimal(unit_object.conversion_factor)
                if conversion_factor == 0:
                    raise ValueError(f"Le facteur de conversion pour l'unité '{unit_object.name}' ne peut pas être zéro.")
                price_per_base_unit = price_per_unit_achat / conversion_factor
                
                # DEBUG: Log des données avant mise à jour
                debug_info = f"DEBUG - Produit: {product.name}, Stock avant: {product.stock_ingredients_magasin} (magasin), {product.stock_ingredients_local} (local), Quantité à ajouter: {quantity_in_base_unit}"
                current_app.logger.info(debug_info)
                
                if product.product_type == 'consommable':
                    stock_location = 'stock_consommables'
                    purchase_value = Decimal(quantity_in_base_unit) * price_per_base_unit
                    
                    current_app.logger.info(f"DEBUG - Mise à jour consommable: {stock_location}")
                    current_app.logger.info(f"DEBUG - Valeur d'achat: {purchase_value}")
                    
                    product.update_stock_by_location(
                        stock_location,
                        quantity_in_base_unit,
                        unit_cost_override=price_per_base_unit
                    )
                    
                    # ✅ CORRECTION : Recalculer le PMP
                    total_qty_decimal = Decimal(str(product.total_stock_all_locations or 0))
                    total_value_decimal = Decimal(str(product.total_stock_value or 0))
                    
                    if total_qty_decimal > 0:
                        new_cost_price = (total_value_decimal / total_qty_decimal).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
                        product.cost_price = new_cost_price
                    else:
                        product.cost_price = Decimal(str(price_per_base_unit))
                
                elif product.product_type == 'ingredient':
                    # Mapping des localisations vers les attributs de stock
                    location_mapping = {
                        'ingredients_magasin': 'stock_ingredients_magasin',
                        'ingredients_local': 'stock_ingredients_local',
                        'comptoir': 'stock_comptoir',
                        'consommables': 'stock_consommables'
                    }
                    stock_location_key = location_mapping.get(stock_locations[i], 'stock_ingredients_magasin')
                    
                    # ✅ CORRECTION : Calculer la valeur d'achat AVANT la mise à jour
                    purchase_value = Decimal(quantity_in_base_unit) * price_per_base_unit
                    
                    # Sauvegarder les valeurs AVANT pour le calcul du PMP
                    stock_before = Decimal(str(getattr(product, stock_location_key.replace('stock_', 'stock_'), 0) or 0))
                    total_stock_before = Decimal(str(product.total_stock_all_locations or 0))
                    total_value_before = Decimal(str(product.total_stock_value or 0))
                    deficit_before = Decimal(str(getattr(product, stock_location_key.replace('stock_', 'deficit_stock_'), 0) or 0))

                    current_app.logger.info(f"DEBUG - Mise à jour ingrédient: {stock_location_key}")
                    current_app.logger.info(f"DEBUG - Stock avant: {stock_before}, Valeur totale avant: {total_value_before}, Déficit avant: {deficit_before}")
                    current_app.logger.info(f"DEBUG - Quantité à ajouter: {quantity_in_base_unit}, Prix unitaire: {price_per_base_unit}, Valeur d'achat: {purchase_value}")
                    
                    # ✅ CORRECTION : Utiliser update_stock_by_location avec le prix d'achat
                    product.update_stock_by_location(
                        stock_location_key,
                        quantity_in_base_unit,
                        unit_cost_override=price_per_base_unit
                    )
                    
                    # ✅ CORRECTION : Recalculer le PMP basé sur la valeur totale / quantité totale
                    # La valeur totale a déjà été mise à jour par update_stock_by_location
                    total_qty_decimal = Decimal(str(product.total_stock_all_locations or 0))
                    total_value_decimal = Decimal(str(product.total_stock_value or 0))
                    
                    if total_qty_decimal > 0:
                        # PMP = Valeur totale / Quantité totale
                        new_cost_price = (total_value_decimal / total_qty_decimal).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
                        product.cost_price = new_cost_price
                        current_app.logger.info(f"DEBUG - PMP recalculé: {new_cost_price} DA (Valeur totale: {total_value_decimal}, Quantité totale: {total_qty_decimal})")
                    else:
                        # Si stock total = 0, utiliser le prix d'achat comme nouveau PMP
                        product.cost_price = Decimal(str(price_per_base_unit))
                        current_app.logger.info(f"DEBUG - Stock total = 0, PMP défini au prix d'achat: {price_per_base_unit}")
                
                elif product.product_type == 'finished':
                    # ✅ CORRECTION : Traitement des produits finis achetables
                    # Pour les produits finis achetables, mettre dans stock_comptoir
                    stock_location = 'stock_comptoir'
                    purchase_value = Decimal(quantity_in_base_unit) * price_per_base_unit
                    
                    current_app.logger.info(f"DEBUG - Mise à jour produit fini achetable: {stock_location}")
                    current_app.logger.info(f"DEBUG - Valeur d'achat: {purchase_value}")
                    
                    product.update_stock_by_location(
                        stock_location,
                        quantity_in_base_unit,
                        unit_cost_override=price_per_base_unit
                    )
                    
                    # ✅ CORRECTION : Recalculer le PMP
                    total_qty_decimal = Decimal(str(product.total_stock_all_locations or 0))
                    total_value_decimal = Decimal(str(product.total_stock_value or 0))
                    
                    if total_qty_decimal > 0:
                        new_cost_price = (total_value_decimal / total_qty_decimal).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
                        product.cost_price = new_cost_price
                    else:
                        product.cost_price = Decimal(str(price_per_base_unit))
                
                # DEBUG: Log des données après mise à jour
                debug_after = f"DEBUG - Stock après: {product.stock_ingredients_magasin} (magasin), {product.stock_ingredients_local} (local), Valeur totale: {product.total_stock_value}"
                current_app.logger.info(debug_after)
                current_app.logger.info("---")

                purchase_item = PurchaseItem(
                    purchase_id=purchase.id,
                    product_id=product.id,
                    quantity_ordered=Decimal(quantity_in_base_unit),
                    unit_price=price_per_base_unit,
                    original_quantity=quantity_ordered,
                    original_unit_id=unit_id,
                    original_unit_price=price_per_unit_achat,
                    stock_location=stock_locations[i]
                )
                db.session.add(purchase_item)
                items_added += 1

            if items_added == 0:
                raise ValueError("Le bon d'achat doit contenir au moins un article valide.")

            purchase.calculate_totals()
            db.session.commit()
            
            flash(f'Bon d\'achat {purchase.reference} créé avec succès. Le stock et le coût moyen pondéré ont été mis à jour.', 'success')
            return redirect(url_for('purchases.view_purchase', id=purchase.id))

        except (ValueError, InvalidOperation, IndexError, TypeError) as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur lors de la création de l'achat : {e}", exc_info=True)
            flash(f"ECHEC : Le bon d'achat n'a pas été créé. Une erreur est survenue. Veuillez vérifier toutes les lignes. ({e})", 'danger')

    available_products = Product.query.filter(
        or_(
            Product.product_type.in_(['ingredient', 'consommable']),
            (Product.product_type == 'finished') & (Product.can_be_purchased == True)
        )
    ).all()
    available_units = Unit.query.filter_by(is_active=True).order_by(Unit.display_order).all()

    return render_template('purchases/new_purchase.html', form=form, title='Nouveau Bon d\'Achat',
                           available_products=available_products, available_units=available_units)

@purchases.route('/<int:id>')
@login_required
def view_purchase(id):
    purchase = Purchase.query.get_or_404(id)
    if not current_user.is_admin and purchase.requested_by_id != current_user.id:
        flash('Vous n\'avez pas l\'autorisation de voir ce bon d\'achat.', 'danger')
        return redirect(url_for('purchases.list_purchases'))
    return render_template(
        'purchases/view_purchase.html',
        title=f"Bon d'Achat {purchase.reference}",
        purchase=purchase
    )

@purchases.route('/<int:id>/mark_paid', methods=['GET', 'POST'])
@login_required
@admin_required
def mark_as_paid(id):
    purchase = Purchase.query.get_or_404(id)
    if purchase.is_paid:
        flash('Ce bon d\'achat est déjà marqué comme payé.', 'info')
        return redirect(url_for('purchases.view_purchase', id=id))

    form = MarkAsPaidForm()
    if form.validate_on_submit():
        purchase.is_paid = True
        purchase.payment_date = form.payment_date.data
        purchase.payment_method = form.payment_method.data
        
        # Intégration comptable automatique
        try:
            from app.accounting.services import AccountingIntegrationService
            AccountingIntegrationService.create_purchase_entry(
                purchase_id=purchase.id,
                purchase_amount=float(purchase.total_amount),
                payment_method=form.payment_method.data,  # Utiliser la valeur du formulaire
                description=f'Achat {purchase.reference} - {purchase.supplier_name}',
                payment_date=form.payment_date.data  # Utiliser la date de paiement du formulaire
            )
            current_app.logger.info(f"Écriture comptable créée pour bon d'achat {purchase.reference} (ACH-{purchase.id})")
        except ValueError as e:
            # Erreur attendue (écriture existe déjà)
            current_app.logger.warning(f"Écriture comptable existe déjà pour ACH-{purchase.id}: {e}")
            flash(f'Attention : {str(e)}', 'warning')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur intégration comptable achat (purchase_id={purchase.id}): {e}", exc_info=True)
            flash(f'Erreur lors de la création de l\'écriture comptable : {e}', 'error')
            return redirect(url_for('purchases.view_purchase', id=id))
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur lors du commit : {e}", exc_info=True)
            flash(f'Erreur lors de l\'enregistrement : {e}', 'error')
            return redirect(url_for('purchases.view_purchase', id=id))
        payment_date_str = form.payment_date.data.strftime("%d/%m/%Y") if form.payment_date.data else "date inconnue"
        flash(f'Bon d\'achat {purchase.reference} marqué comme payé le {payment_date_str}.', 'success')
        return redirect(url_for('purchases.view_purchase', id=id))
    
    return render_template(
        'purchases/mark_paid.html',
        purchase=purchase,
        form=form,
        title=f'Marquer comme Payé - {purchase.reference}'
    )

@purchases.route('/<int:id>/mark_unpaid', methods=['POST'])
@login_required
@admin_required
def mark_as_unpaid(id):
    purchase = Purchase.query.get_or_404(id)
    
    # Suppression de l'écriture comptable correspondante AVANT de modifier le bon
    try:
        from app.accounting.models import JournalEntry, JournalEntryLine
        entry = JournalEntry.query.filter_by(reference=f"ACH-{purchase.id}").first()
        if entry:
            # Si l'écriture est validée, la dévalider d'abord
            if entry.is_validated:
                entry.is_validated = False
                entry.validated_at = None
                entry.validated_by_id = None
                current_app.logger.info(f"Écriture comptable ACH-{purchase.id} dévalidée avant suppression.")
            
            # Supprimer les lignes d'écriture
            JournalEntryLine.query.filter_by(entry_id=entry.id).delete()
            # Supprimer l'écriture
            db.session.delete(entry)
            current_app.logger.info(f"Écriture comptable ACH-{purchase.id} supprimée suite au marquage non payé.")
        else:
            current_app.logger.warning(f"Aucune écriture comptable trouvée pour ACH-{purchase.id}")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur lors de la suppression de l'écriture comptable ACH-{purchase.id}: {e}", exc_info=True)
        flash(f'Erreur lors de la suppression de l\'écriture comptable : {e}', 'error')
        return redirect(url_for('purchases.view_purchase', id=id))
    
    # Modifier le bon d'achat
    purchase.is_paid = False
    purchase.payment_date = None
    purchase.payment_method = None
    
    try:
        db.session.commit()
        flash(f'Bon d\'achat {purchase.reference} marqué comme non payé (écriture comptable supprimée).', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur lors du commit : {e}", exc_info=True)
        flash(f'Erreur lors de la mise à jour : {e}', 'error')
    
    return redirect(url_for('purchases.view_purchase', id=id))

@purchases.route('/<int:id>/cancel', methods=['POST'])
@login_required
@admin_required
def cancel_purchase(id):
    purchase = Purchase.query.get_or_404(id)
    if purchase.status == PurchaseStatus.CANCELLED:
        flash('Ce bon d\'achat est déjà annulé.', 'info')
        return redirect(url_for('purchases.view_purchase', id=id))

    if purchase.status != PurchaseStatus.RECEIVED:
        flash(f"Un achat avec le statut '{purchase.status.value}' ne peut être annulé de cette manière car il n'a pas impacté le stock.", 'warning')
        purchase.status = PurchaseStatus.CANCELLED
        db.session.commit()
        flash(f'Bon d\'achat {purchase.reference} annulé.', 'success')
        return redirect(url_for('purchases.view_purchase', id=id))

    try:
        for item in purchase.items:
            product = item.product
            if not product:
                continue

            quantity_to_reverse = float(item.quantity_ordered)
            
            if product.product_type == 'consommable':
                product.update_stock_by_location('consommables', -quantity_to_reverse)

            elif product.product_type == 'ingredient':
                product.update_stock_by_location(item.stock_location, -quantity_to_reverse)
                value_to_reverse = item.quantity_ordered * item.unit_price
                product.total_stock_value = (product.total_stock_value or Decimal('0.0')) - value_to_reverse
                
                new_total_stock_qty = Decimal(product.total_stock_all_locations)
                if new_total_stock_qty > 0:
                    if product.total_stock_value < 0:
                        product.total_stock_value = Decimal('0.0')
                    product.cost_price = product.total_stock_value / new_total_stock_qty
                else:
                    product.total_stock_value = Decimal('0.0')
                    product.cost_price = Decimal('0.0')
        
        purchase.status = PurchaseStatus.CANCELLED
        db.session.commit()
        flash(f'Bon d\'achat {purchase.reference} annulé. Le stock et sa valeur ont été corrigés.', 'success')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur lors de l'annulation de l'achat {id}: {e}", exc_info=True)
        flash(f"ECHEC de l'annulation. Une erreur est survenue: {e}", "danger")

    return redirect(url_for('purchases.view_purchase', id=id))

@purchases.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_purchase(id):
    """Modification d'un bon d'achat avec support des unités et cohérence stock/valeur"""
    purchase = Purchase.query.get_or_404(id)

    if not current_user.is_admin and purchase.requested_by_id != current_user.id:
        flash('Vous n\'avez pas l\'autorisation de modifier ce bon d\'achat.', 'danger')
        return redirect(url_for('purchases.list_purchases'))

    if purchase.status not in [PurchaseStatus.DRAFT, PurchaseStatus.REQUESTED, PurchaseStatus.RECEIVED]:
        flash('Ce bon d\'achat ne peut plus être modifié dans son état actuel.', 'warning')
        return redirect(url_for('purchases.view_purchase', id=id))

    form = PurchaseForm(obj=purchase)
    
    if form.validate_on_submit():
        try:
            purchase.requested_date = form.requested_date.data

            # === ÉTAPE 1: ANNULER L'IMPACT DE L'ANCIEN ACHAT (si RECEIVED) ===
            if purchase.status == PurchaseStatus.RECEIVED:
                current_app.logger.info(f"DEBUG - Annulation de l'impact de l'ancien achat {purchase.reference}")
                
                for item in purchase.items:
                    if not item.product:
                        continue
                    
                    product = item.product
                    quantity_to_reverse = float(item.quantity_ordered)
                    value_to_reverse = item.quantity_ordered * item.unit_price
                    
                    current_app.logger.info(f"DEBUG - Annulation: {product.name}, Quantité: {quantity_to_reverse}, Valeur: {value_to_reverse}")
                    
                    # Mapping des localisations vers les attributs de stock
                    location_mapping = {
                        'ingredients_magasin': 'stock_ingredients_magasin',
                        'ingredients_local': 'stock_ingredients_local',
                        'comptoir': 'stock_comptoir',
                        'consommables': 'stock_consommables'
                    }
                    
                    stock_location_key = location_mapping.get(item.stock_location, 'stock_ingredients_magasin')
                    
                    if product.product_type == 'consommable':
                        # Pour les consommables, on décrémente seulement le stock
                        product.update_stock_by_location('stock_consommables', -quantity_to_reverse)
                        current_app.logger.info(f"DEBUG - Consommable annulé: {product.name}, Stock après: {product.stock_consommables}")
                    
                    elif product.product_type == 'ingredient':
                        # Pour les ingrédients, on décrémente stock ET valeur
                        product.update_stock_by_location(stock_location_key, -quantity_to_reverse)
                        product.total_stock_value = (product.total_stock_value or Decimal('0.0')) - value_to_reverse
                        
                        # Décrémenter la valeur par emplacement
                        if stock_location_key == "stock_ingredients_magasin":
                            product.valeur_stock_ingredients_magasin = float(getattr(product, "valeur_stock_ingredients_magasin", 0.0)) - float(value_to_reverse)
                        elif stock_location_key == "stock_ingredients_local":
                            product.valeur_stock_ingredients_local = float(getattr(product, "valeur_stock_ingredients_local", 0.0)) - float(value_to_reverse)
                        
                        # Recalculer le PMP
                        new_total_stock_qty = Decimal(product.total_stock_all_locations)
                        if new_total_stock_qty > 0:
                            if product.total_stock_value < 0:
                                product.total_stock_value = Decimal('0.0')
                            product.cost_price = product.total_stock_value / new_total_stock_qty
                        else:
                            product.total_stock_value = Decimal('0.0')
                            product.cost_price = Decimal('0.0')
                        
                        current_app.logger.info(f"DEBUG - Ingrédient annulé: {product.name}, Stock après: {getattr(product, stock_location_key)}, Valeur totale: {product.total_stock_value}, PMP: {product.cost_price}")
            
            # === ÉTAPE 2: METTRE À JOUR LES INFORMATIONS DU BON D'ACHAT ===
            purchase.supplier_name = form.supplier_name.data
            purchase.supplier_contact = form.supplier_contact.data
            purchase.supplier_phone = form.supplier_phone.data
            purchase.supplier_email = form.supplier_email.data
            purchase.supplier_address = form.supplier_address.data
            purchase.expected_delivery_date = form.expected_delivery_date.data
            purchase.urgency = PurchaseUrgency(form.urgency.data)
            purchase.payment_terms = form.payment_terms.data
            purchase.shipping_cost = Decimal(form.shipping_cost.data or '0.0')
            purchase.tax_amount = Decimal(form.tax_amount.data or '0.0')
            purchase.notes = form.notes.data
            purchase.internal_notes = form.internal_notes.data
            purchase.terms_conditions = form.terms_conditions.data

            # === ÉTAPE 3: SUPPRIMER LES ANCIENNES LIGNES ===
            PurchaseItem.query.filter_by(purchase_id=purchase.id).delete()

            # === ÉTAPE 4: CRÉER LES NOUVELLES LIGNES ET APPLIQUER L'IMPACT ===
            items_added = 0
            product_ids = request.form.getlist('items[][product_id]')
            quantities = request.form.getlist('items[][quantity_ordered]')
            prices = request.form.getlist('items[][unit_price]')
            unit_ids = request.form.getlist('items[][unit]')
            stock_locations = request.form.getlist('items[][stock_location]')
            
            for i in range(len(product_ids)):
                if not product_ids[i] or not quantities[i] or not prices[i] or not unit_ids[i]:
                    continue

                product_id = int(product_ids[i])
                product = Product.query.get(product_id)
                
                if not product:
                    raise ValueError(f"Produit avec l'ID {product_id} non trouvé.")

                # Vérifier que le produit est achetable (ingrédient, consommable, ou produit fini avec can_be_purchased)
                is_purchasable = (
                    product.product_type in ['ingredient', 'consommable'] or
                    (product.product_type == 'finished' and product.can_be_purchased == True)
                )
                if not is_purchasable:
                    raise ValueError(f"Le produit '{product.name}' n'est pas achetable.")

                quantity_ordered = Decimal(quantities[i])
                price_per_unit_achat = Decimal(prices[i])
                unit_id = int(unit_ids[i])
                unit_object = Unit.query.get(unit_id)

                if not unit_object or quantity_ordered <= 0 or price_per_unit_achat < 0:
                    raise ValueError(f"Données invalides pour la ligne du produit {product.name}.")

                quantity_in_base_unit = float(quantity_ordered * unit_object.conversion_factor)
                
                # Calculer price_per_base_unit AVANT les blocs if/elif
                conversion_factor = Decimal(unit_object.conversion_factor)
                if conversion_factor == 0:
                    raise ValueError(f"Le facteur de conversion pour l'unité '{unit_object.name}' ne peut pas être zéro.")
                price_per_base_unit = price_per_unit_achat / conversion_factor
                
                # DEBUG: Log des données avant mise à jour
                debug_info = f"DEBUG - Produit: {product.name}, Stock avant: {product.stock_ingredients_magasin} (magasin), {product.stock_ingredients_local} (local), Quantité à ajouter: {quantity_in_base_unit}"
                current_app.logger.info(debug_info)
                
                if product.product_type == 'consommable':
                    stock_location = 'stock_consommables'
                    purchase_value = Decimal(quantity_in_base_unit) * price_per_base_unit
                    
                    current_app.logger.info(f"DEBUG - Mise à jour consommable: {stock_location}")
                    current_app.logger.info(f"DEBUG - Valeur d'achat: {purchase_value}")
                    
                    # ✅ CORRECTION : Passer le prix d'achat à update_stock_by_location
                    product.update_stock_by_location(
                        stock_location,
                        quantity_in_base_unit,
                        unit_cost_override=price_per_base_unit
                    )
                    
                    # ✅ CORRECTION : Recalculer le PMP
                    total_qty_decimal = Decimal(str(product.total_stock_all_locations or 0))
                    total_value_decimal = Decimal(str(product.total_stock_value or 0))
                    
                    if total_qty_decimal > 0:
                        new_cost_price = (total_value_decimal / total_qty_decimal).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
                        product.cost_price = new_cost_price
                    else:
                        product.cost_price = Decimal(str(price_per_base_unit))
                
                elif product.product_type == 'ingredient':
                    # Mapping des localisations vers les attributs de stock
                    location_mapping = {
                        'ingredients_magasin': 'stock_ingredients_magasin',
                        'ingredients_local': 'stock_ingredients_local',
                        'comptoir': 'stock_comptoir',
                        'consommables': 'stock_consommables'
                    }
                    stock_location_key = location_mapping.get(stock_locations[i], 'stock_ingredients_magasin')
                    
                    # ✅ CORRECTION : Calculer la valeur d'achat
                    purchase_value = Decimal(quantity_in_base_unit) * price_per_base_unit

                    current_app.logger.info(f"DEBUG - Mise à jour ingrédient: {stock_location_key}")
                    current_app.logger.info(f"DEBUG - Valeur d'achat: {purchase_value}")
                    
                    # ✅ CORRECTION : Passer le prix d'achat à update_stock_by_location
                    product.update_stock_by_location(
                        stock_location_key,
                        quantity_in_base_unit,
                        unit_cost_override=price_per_base_unit
                    )
                    
                    # ✅ CORRECTION : Recalculer le PMP basé sur la valeur totale / quantité totale
                    total_qty_decimal = Decimal(str(product.total_stock_all_locations or 0))
                    total_value_decimal = Decimal(str(product.total_stock_value or 0))
                    
                    if total_qty_decimal > 0:
                        new_cost_price = (total_value_decimal / total_qty_decimal).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
                        product.cost_price = new_cost_price
                        current_app.logger.info(f"DEBUG - PMP recalculé: {new_cost_price} DA (Valeur totale: {total_value_decimal}, Quantité totale: {total_qty_decimal})")
                    else:
                        product.cost_price = Decimal(str(price_per_base_unit))
                        current_app.logger.info(f"DEBUG - Stock total = 0, PMP défini au prix d'achat: {price_per_base_unit}")
                
                elif product.product_type == 'finished':
                    # ✅ CORRECTION : Traitement des produits finis achetables
                    # Pour les produits finis achetables, mettre dans stock_comptoir
                    stock_location = 'stock_comptoir'
                    purchase_value = Decimal(quantity_in_base_unit) * price_per_base_unit
                    
                    current_app.logger.info(f"DEBUG - Mise à jour produit fini achetable: {stock_location}")
                    current_app.logger.info(f"DEBUG - Valeur d'achat: {purchase_value}")
                    
                    # ✅ CORRECTION : Utiliser update_stock_by_location avec le prix d'achat
                    product.update_stock_by_location(
                        stock_location,
                        quantity_in_base_unit,
                        unit_cost_override=price_per_base_unit
                    )
                    
                    # ✅ CORRECTION : Recalculer le PMP
                    total_qty_decimal = Decimal(str(product.total_stock_all_locations or 0))
                    total_value_decimal = Decimal(str(product.total_stock_value or 0))
                    
                    if total_qty_decimal > 0:
                        new_cost_price = (total_value_decimal / total_qty_decimal).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
                        product.cost_price = new_cost_price
                        current_app.logger.info(f"DEBUG - PMP recalculé: {new_cost_price} DA (Valeur totale: {total_value_decimal}, Quantité totale: {total_qty_decimal})")
                    else:
                        product.cost_price = Decimal(str(price_per_base_unit))
                        current_app.logger.info(f"DEBUG - Stock total = 0, PMP défini au prix d'achat: {price_per_base_unit}")
                
                # DEBUG: Log des données après mise à jour
                debug_after = f"DEBUG - Stock après: {product.stock_ingredients_magasin} (magasin), {product.stock_ingredients_local} (local), Valeur totale: {product.total_stock_value}"
                current_app.logger.info(debug_after)
                current_app.logger.info("---")

                purchase_item = PurchaseItem(
                    purchase_id=purchase.id,
                    product_id=product.id,
                    quantity_ordered=Decimal(quantity_in_base_unit),
                    unit_price=price_per_base_unit,
                    original_quantity=quantity_ordered,
                    original_unit_id=unit_id,
                    original_unit_price=price_per_unit_achat,
                    stock_location=stock_locations[i]
                )
                db.session.add(purchase_item)
                items_added += 1

            if items_added == 0:
                raise ValueError("Le bon d'achat doit contenir au moins un article valide.")

            purchase.calculate_totals()
            
            # === ÉTAPE 5: METTRE À JOUR L'ÉCRITURE COMPTABLE SI LE BON EST PAYÉ ===
            if purchase.is_paid and purchase.payment_method:
                try:
                    from app.accounting.models import JournalEntry, JournalEntryLine, Account
                    entry = JournalEntry.query.filter_by(reference=f"ACH-{purchase.id}").first()
                    
                    if entry:
                        # Récupérer les comptes selon le mode de paiement
                        if purchase.payment_method == 'bank':
                            credit_account = Account.query.filter_by(code='512').first()  # Banque
                        elif purchase.payment_method == 'cash':
                            credit_account = Account.query.filter_by(code='530').first()  # Caisse
                        else:  # credit
                            credit_account = Account.query.filter_by(code='401').first()  # Fournisseurs
                        
                        debit_account = Account.query.filter_by(code='601').first()  # Achats
                        
                        if credit_account and debit_account:
                            # Trouver les lignes d'écriture
                            bank_line = JournalEntryLine.query.filter_by(
                                entry_id=entry.id,
                                account_id=credit_account.id
                            ).first()
                            
                            purchase_line = JournalEntryLine.query.filter_by(
                                entry_id=entry.id,
                                account_id=debit_account.id
                            ).first()
                            
                            if bank_line and purchase_line:
                                # Mettre à jour les montants
                                nouveau_montant = float(purchase.total_amount)
                                bank_line.credit_amount = Decimal(str(nouveau_montant))
                                purchase_line.debit_amount = Decimal(str(nouveau_montant))
                                
                                # Dévalider l'écriture si elle était validée (car modifiée)
                                if entry.is_validated:
                                    entry.is_validated = False
                                    entry.validated_at = None
                                    entry.validated_by_id = None
                                
                                current_app.logger.info(f"Écriture comptable ACH-{purchase.id} mise à jour : {nouveau_montant} DA")
                            else:
                                current_app.logger.warning(f"Lignes d'écriture non trouvées pour ACH-{purchase.id}")
                        else:
                            current_app.logger.warning(f"Comptes comptables non trouvés pour mise à jour ACH-{purchase.id}")
                    else:
                        current_app.logger.warning(f"Écriture comptable non trouvée pour ACH-{purchase.id} (bon payé mais pas d'écriture)")
                except Exception as e:
                    # Ne pas bloquer la modification du bon si l'écriture comptable échoue
                    current_app.logger.error(f"Erreur lors de la mise à jour de l'écriture comptable ACH-{purchase.id}: {e}", exc_info=True)
            
            db.session.commit()
            
            flash(f'Bon d\'achat {purchase.reference} modifié avec succès. Le stock et le coût moyen pondéré ont été mis à jour.', 'success')
            return redirect(url_for('purchases.view_purchase', id=purchase.id))

        except (ValueError, InvalidOperation, IndexError, TypeError) as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur lors de la modification de l'achat : {e}", exc_info=True)
            flash(f"ECHEC : Le bon d'achat n'a pas été modifié. Une erreur est survenue. Veuillez vérifier toutes les lignes. ({e})", 'danger')

    available_products = Product.query.filter(
        or_(
            Product.product_type.in_(['ingredient', 'consommable']),
            (Product.product_type == 'finished') & (Product.can_be_purchased == True)
        )
    ).all()
    available_units = Unit.query.filter_by(is_active=True).order_by(Unit.display_order).all()
    return render_template(
        'purchases/edit_purchase.html',
        form=form,
        purchase=purchase,
        title=f'Modifier Bon d\'Achat {purchase.reference}',
        available_products=available_products,
        available_units=available_units
    )


# ==================== ROUTES API/AJAX ====================

@purchases.route('/api/products_search')
@login_required
def api_products_search():
    """API de recherche de produits pour l'auto-complétion"""
    search_term = request.args.get('q', '')
    if len(search_term) < 2:
        return jsonify([])
    
    products = Product.query.filter(
        and_(
            Product.name.ilike(f'%{search_term}%'),
            or_(
                Product.product_type.in_(['ingredient', 'consommable']),
                (Product.product_type == 'finished') & (Product.can_be_purchased == True)
            )
        )
    ).limit(20).all()

    results = []
    for product in products:
        results.append({
            'id': product.id,
            'name': product.name,
            'unit': product.unit,
            'cost_price': float(product.cost_price or 0),
            'stock_magasin': product.stock_ingredients_magasin,
            'stock_local': product.stock_ingredients_local
        })
    return jsonify(results)

@purchases.route('/api/pending_count')
@login_required
@admin_required
def api_pending_count():
    """API pour le nombre d'achats en attente d'approbation"""
    count = Purchase.query.filter(
        Purchase.status.in_([PurchaseStatus.DRAFT, PurchaseStatus.REQUESTED])
    ).count()
    return jsonify({'count': count})

@purchases.route('/api/products/<int:product_id>/units')
@login_required
def api_product_units(product_id):
    """API pour récupérer les unités disponibles pour un produit"""
    product = Product.query.get_or_404(product_id)
    units = Unit.query.filter_by(is_active=True).order_by(Unit.display_order).all()
    
    results = []
    for unit in units:
        results.append({
            'id': unit.id,
            'name': unit.name,
            'base_unit': unit.base_unit,
            'conversion_factor': float(unit.conversion_factor),
            'unit_type': unit.unit_type
        })
    return jsonify(results)

# ==================== ROUTE DE TEST TEMPORAIRE ====================

@purchases.route('/test_stock_update')
@login_required
@admin_required
def test_stock_update():
    """Route de test pour vérifier la mise à jour du stock"""
    try:
        # Test avec un produit existant
        product = Product.query.filter_by(product_type='ingredient').first()
        if not product:
            return "Aucun produit de type 'ingredient' trouvé"
        
        # Affichage avant
        before_magasin = product.stock_ingredients_magasin
        before_local = product.stock_ingredients_local
        before_value = product.total_stock_value
        
        # Test de mise à jour
        test_quantity = 10.0
        product.update_stock_by_location('ingredients_magasin', test_quantity)
        
        # Affichage après
        after_magasin = product.stock_ingredients_magasin
        after_local = product.stock_ingredients_local
        after_value = product.total_stock_value
        
        # Commit pour sauvegarder
        db.session.commit()
        
        result = f"""
        <h2>Test de mise à jour du stock</h2>
        <p><strong>Produit:</strong> {product.name}</p>
        <p><strong>Stock magasin avant:</strong> {before_magasin}</p>
        <p><strong>Stock magasin après:</strong> {after_magasin}</p>
        <p><strong>Stock local avant:</strong> {before_local}</p>
        <p><strong>Stock local après:</strong> {after_local}</p>
        <p><strong>Valeur totale avant:</strong> {before_value}</p>
        <p><strong>Valeur totale après:</strong> {after_value}</p>
        <p><strong>Quantité ajoutée:</strong> {test_quantity}</p>
        <p><strong>Différence magasin:</strong> {after_magasin - before_magasin}</p>
        """
        
        return result
        
    except Exception as e:
        return f"Erreur: {str(e)}"