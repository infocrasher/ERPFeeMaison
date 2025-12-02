"""
Routes pour la gestion des 4 stocks et transferts

Module: app/stock/routes.py

Auteur: ERP Fée Maison

"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Product, User
from .models import StockMovement, StockTransfer, StockTransferLine, StockLocationType, StockMovementType, TransferStatus
from .forms import StockAdjustmentForm, QuickStockEntryForm, StockTransferForm, MultiLocationAdjustmentForm
from decorators import admin_required
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta

# Import du blueprint depuis __init__.py
from . import bp as stock

# ==================== ROUTES EXISTANTES CONSERVÉES ====================

@stock.route('/overview')
@login_required
@admin_required
def overview():
    """Vue globale consolidée de tous les stocks"""
    products = Product.query.all()
    low_stock_fallback = current_app.config.get('LOW_STOCK_THRESHOLD', 5)
    
    location_configs = [
        {
            'key': 'magasin',
            'label': 'Réserve Magasin',
            'icon': 'bi bi-building',
            'gradient': 'gradient-magasin',
            'stock_attr': 'stock_ingredients_magasin',
            'value_attr': 'valeur_stock_ingredients_magasin',
            'threshold_attr': 'seuil_min_ingredients_magasin'
        },
        {
            'key': 'local',
            'label': 'Labo Local',
            'icon': 'bi bi-tools',
            'gradient': 'gradient-local',
            'stock_attr': 'stock_ingredients_local',
            'value_attr': 'valeur_stock_ingredients_local',
            'threshold_attr': 'seuil_min_ingredients_local'
        },
        {
            'key': 'comptoir',
            'label': 'Comptoir Vente',
            'icon': 'bi bi-shop',
            'gradient': 'gradient-comptoir',
            'stock_attr': 'stock_comptoir',
            'value_attr': 'valeur_stock_comptoir',
            'threshold_attr': 'seuil_min_comptoir'
        },
        {
            'key': 'consommables',
            'label': 'Consommables',
            'icon': 'bi bi-box',
            'gradient': 'gradient-consommables',
            'stock_attr': 'stock_consommables',
            'value_attr': 'valeur_stock_consommables',
            'threshold_attr': 'seuil_min_consommables'
        }
    ]
    
    summary_cards = []
    low_stock_rows = []
    critical_products = []
    value_distribution = []
    
    product_low_cache = {}
    
    total_value_global = 0
    
    for config in location_configs:
        qty_total = sum(float(getattr(p, config['stock_attr']) or 0) for p in products)
        value_total = sum(float(getattr(p, config['value_attr']) or 0) for p in products)
        total_value_global += value_total
        under_threshold_count = 0
        
        for product in products:
            stock_level = float(getattr(product, config['stock_attr']) or 0)
            threshold_value = getattr(product, config['threshold_attr'])
            threshold = float(threshold_value) if threshold_value is not None else float(low_stock_fallback)
            if threshold <= 0:
                continue
            if stock_level <= threshold:
                under_threshold_count += 1
                entry = product_low_cache.setdefault(product.id, {
                    'product': product,
                    'locations': {}
                })
                entry['locations'][config['key']] = {
                    'stock': stock_level,
                    'threshold': threshold
                }
        
        summary_cards.append({
            'key': config['key'],
            'label': config['label'],
            'icon': config['icon'],
            'gradient': config['gradient'],
            'quantity': qty_total,
            'value': value_total,
            'under_threshold': under_threshold_count
        })
        
        value_distribution.append({
            'label': config['label'],
            'value': value_total
        })
    
    low_stock_rows = sorted(product_low_cache.values(), key=lambda x: x['product'].name)
    
    for product in products:
        total_stock = (product.stock_comptoir or 0) + (product.stock_ingredients_local or 0) + \
                      (product.stock_ingredients_magasin or 0) + (product.stock_consommables or 0)
        if total_stock <= 0:
            critical_products.append(product)
    
    top_value_products = sorted(
        products,
        key=lambda p: float(p.total_stock_value or 0),
        reverse=True
    )[:8]
    
    total_deficit = sum(float(p.value_deficit_total or 0) for p in products)
    deficit_by_location = {
        'magasin': sum(float(p.deficit_stock_ingredients_magasin or 0) for p in products),
        'local': sum(float(p.deficit_stock_ingredients_local or 0) for p in products),
        'comptoir': sum(float(p.deficit_stock_comptoir or 0) for p in products),
        'consommables': sum(float(p.deficit_stock_consommables or 0) for p in products)
    }
    
    try:
        pending_transfers = StockTransfer.query.filter(
            StockTransfer.status.in_([TransferStatus.REQUESTED, TransferStatus.APPROVED])
        ).order_by(StockTransfer.created_at.desc()).limit(5).all()
    except Exception:
        pending_transfers = []
    
    try:
        from app.purchases.models import Purchase, PurchaseStatus
        pending_purchases = Purchase.query.filter(
            Purchase.status.in_([PurchaseStatus.REQUESTED, PurchaseStatus.APPROVED])
        ).order_by(Purchase.requested_date.desc()).limit(5).all()
    except Exception:
        pending_purchases = []
    
    return render_template(
        'stock/stock_overview.html',
        title="Vue Globale Stocks",
        summary_cards=summary_cards,
        low_stock_rows=low_stock_rows,
        critical_products=critical_products,
        value_distribution=value_distribution,
        total_value_global=total_value_global,
        top_value_products=top_value_products,
        total_products_count=len(products),
        total_deficit=total_deficit,
        deficit_by_location=deficit_by_location,
        pending_transfers=pending_transfers,
        pending_purchases=pending_purchases
    )

@stock.route('/quick_entry', methods=['GET', 'POST'])
@login_required
@admin_required
def quick_entry():
    """Réception rapide avec sélection de localisation"""
    form = QuickStockEntryForm()
    
    if form.validate_on_submit():
        product_obj = form.product.data
        quantity_received = form.quantity_received.data
        location_type = form.location_type.data
        
        # Mise à jour du stock selon la localisation
        if product_obj.update_stock_location(location_type, quantity_received):
            db.session.commit()
            
            # Création du mouvement de traçabilité
            from .models import update_stock_quantity
            update_stock_quantity(
                product_obj.id,
                getattr(StockLocationType, location_type.upper()),
                quantity_received,
                current_user.id,
                reason=f"Réception rapide - {form.reason.data or 'Arrivage marchandise'}"
            )
            
            flash(f'Stock {product_obj.get_location_display_name(location_type)} pour "{product_obj.name}" mis à jour : +{quantity_received}.', 'success')
        else:
            flash('Erreur lors de la mise à jour du stock.', 'danger')
            
        return redirect(url_for('stock.quick_entry'))
    
    return render_template('stock/quick_stock_entry.html', form=form, title='Réception Rapide Multi-Stocks')

@stock.route('/adjustment', methods=['GET', 'POST'])
@login_required
@admin_required
def adjustment():
    """Ajustement de stock avec sélection de localisation"""
    form = MultiLocationAdjustmentForm()
    
    if form.validate_on_submit():
        product_obj = form.product.data
        location_type = form.location_type.data
        quantity_change = form.quantity.data
        reason = form.reason.data
        
        # Récupération du stock actuel
        current_stock = product_obj.get_stock_by_location_type(location_type)
        new_stock = current_stock + quantity_change
        
        if new_stock < 0:
            flash(f'Le stock {product_obj.get_location_display_name(location_type)} de "{product_obj.name}" ne peut pas devenir négatif.', 'danger')
        else:
            # Mise à jour du stock
            if product_obj.update_stock_location(location_type, quantity_change):
                db.session.commit()
                
                # Création du mouvement de traçabilité
                from .models import update_stock_quantity
                update_stock_quantity(
                    product_obj.id,
                    getattr(StockLocationType, location_type.upper()),
                    quantity_change,
                    current_user.id,
                    reason=reason or "Ajustement manuel"
                )
                
                flash(f'Stock {product_obj.get_location_display_name(location_type)} de "{product_obj.name}" ajusté : {current_stock:+.2f} → {new_stock:.2f}.', 'success')
            else:
                flash('Erreur lors de l\'ajustement du stock.', 'danger')
                
        return redirect(url_for('stock.adjustment'))
    
    return render_template('stock/stock_adjustment_form.html', form=form, title='Ajustement Multi-Stocks')

# ==================== ROUTES DASHBOARD CORRIGÉES ====================

@stock.route('/dashboard/magasin')
@login_required
def dashboard_magasin():
    """Dashboard Stock Magasin - Interface Amel"""
    
    # Tous les ingrédients (pas seulement ceux en stock)
    all_ingredients = Product.query.filter(Product.product_type == 'ingredient').all()
    
    # Ingrédients par catégorie
    ingredients_by_category = {}
    for ingredient in all_ingredients:
        category_name = ingredient.category.name if ingredient.category else 'Sans catégorie'
        if category_name not in ingredients_by_category:
            ingredients_by_category[category_name] = []
        ingredients_by_category[category_name].append(ingredient)
    
    # ✅ CORRECTION : Trier les ingrédients - stock > 0 en haut, stock = 0 en bas
    for category_name in ingredients_by_category:
        ingredients_by_category[category_name].sort(
            key=lambda p: ((p.stock_ingredients_magasin or 0) > 0, (p.stock_ingredients_magasin or 0)),
            reverse=True
        )
    
    # Stock critique (rupture totale)
    critical_ingredients = [p for p in all_ingredients if (p.stock_ingredients_magasin or 0) <= 0]
    
    # ✅ CORRECTION : Suggestions d'achat avec calcul dynamique
    suggested_purchases = []
    for product in all_ingredients:
        stock_level = product.stock_ingredients_magasin or 0
        seuil = product.seuil_min_ingredients_magasin
        if seuil is None or seuil <= 0:
            continue  # Ignorer les produits sans seuil défini
        if stock_level <= seuil and stock_level > 0:
            # Calcul dynamique : quantité nécessaire pour atteindre 2x le seuil
            suggested_quantity = max(seuil * 2 - stock_level, seuil)
            suggested_purchases.append({
                'product_id': product.id,
                'product_name': product.name,
                'suggested_quantity': suggested_quantity,
                'unit': product.unit or 'unités'
            })
    
    # Calculs statistiques
    total_ingredients_magasin = len([p for p in all_ingredients if (p.stock_ingredients_magasin or 0) > 0])
    critical_stock_count = len(critical_ingredients)
    # ✅ CORRECTION : Utiliser valeur_stock_ingredients_magasin au lieu de stock × cost_price
    total_value = sum(float(p.valeur_stock_ingredients_magasin or 0) for p in all_ingredients)
    
    # ✅ CORRECTION : Requête réelle pour les achats en attente
    try:
        from app.purchases.models import Purchase, PurchaseStatus
        pending_purchases = Purchase.query.filter(
            Purchase.status.in_([PurchaseStatus.REQUESTED, PurchaseStatus.APPROVED])
        ).count()
    except Exception:
        pending_purchases = 0
    
    return render_template(
        'stock/dashboard_magasin.html',
        title="Dashboard Stock Magasin",
        # ✅ Variables templates corrigées
        ingredients_by_category=ingredients_by_category,
        critical_ingredients=critical_ingredients,
        suggested_purchases=suggested_purchases,
        total_ingredients_magasin=total_ingredients_magasin,
        critical_stock_count=critical_stock_count,
        pending_purchases=pending_purchases,
        total_value=f"{total_value:,.0f}"
    )

@stock.route('/dashboard/local')
@login_required  
def dashboard_local():
    """Dashboard Stock Local - Interface Rayan"""
    
    # Ingrédients avec stock local
    ingredients_local = Product.query.filter(
        Product.product_type == 'ingredient'
    ).all()
    
    # ✅ CORRECTION : Trier les ingrédients - stock > 0 en haut, stock = 0 en bas
    ingredients_local.sort(
        key=lambda p: ((p.stock_ingredients_local or 0) > 0, (p.stock_ingredients_local or 0)),
        reverse=True
    )
    
    # Ingrédients manquants pour production urgent
    missing_ingredients_urgent = []
    for product in ingredients_local:
        stock_level = product.stock_ingredients_local or 0
        seuil = product.seuil_min_ingredients_local or 10
        if stock_level <= 0:
            missing_ingredients_urgent.append({
                'name': product.name,
                'needed_quantity': seuil,
                'unit': product.unit or 'unités'
            })
    
    # Commandes en attente (simulation)
    from models import Order
    try:
        pending_orders = Order.query.filter(Order.status == 'pending').limit(5).all()
        current_time = datetime.utcnow()
    except:
        pending_orders = []
        current_time = datetime.utcnow()
    
    # Statistiques
    total_ingredients_local = len([p for p in ingredients_local if (p.stock_ingredients_local or 0) > 0])
    ingredients_needed = len(missing_ingredients_urgent)
    orders_pending = len(pending_orders)
    production_capacity = 85  # Pourcentage simulation
    
    # ✅ Calcul de la valeur totale du stock local
    total_value_local = sum(float(p.valeur_stock_ingredients_local or 0) for p in ingredients_local)
    
    return render_template(
        'stock/dashboard_local.html',
        title="Dashboard Stock Local",
        # ✅ Variables templates corrigées
        ingredients_local=ingredients_local,
        missing_ingredients_urgent=missing_ingredients_urgent,
        pending_orders=pending_orders,
        current_time=current_time,
        total_ingredients_local=total_ingredients_local,
        ingredients_needed=ingredients_needed,
        orders_pending=orders_pending,
        production_capacity=production_capacity,
        total_value=f"{total_value_local:,.0f}"  # ✅ Ajout de la valeur totale
    )

@stock.route('/dashboard/comptoir')
@login_required
def dashboard_comptoir():
    """Dashboard Stock Comptoir - Interface Yasmine"""
    
    # Produits finis
    all_products = Product.query.filter(Product.product_type == 'finished').all()
    
    # Produits par catégorie
    products_by_category = {}
    for product in all_products:
        category_name = product.category.name if product.category else 'Sans catégorie'
        if category_name not in products_by_category:
            products_by_category[category_name] = []
        products_by_category[category_name].append(product)
    
    # ✅ CORRECTION : Trier les produits - stock > 0 en haut, stock = 0 en bas
    for category_name in products_by_category:
        products_by_category[category_name].sort(
            key=lambda p: ((p.stock_comptoir or 0) > 0, (p.stock_comptoir or 0)),
            reverse=True
        )
    
    # Produits en rupture
    out_of_stock_products = [p for p in all_products if (p.stock_comptoir or 0) <= 0]
    
    # Ventes récentes (simulation)
    recent_sales = [
        {
            'product_name': 'Éclair au Chocolat',
            'quantity': 2,
            'total_amount': '800',
            'time_ago': 'Il y a 15 min'
        },
        {
            'product_name': 'Tarte aux Fraises',
            'quantity': 1,
            'total_amount': '1200',
            'time_ago': 'Il y a 1h'
        }
    ]
    
    # Statistiques
    total_products_comptoir = len([p for p in all_products if (p.stock_comptoir or 0) > 0])
    products_out_of_stock = len(out_of_stock_products)
    sales_today = 12  # Simulation
    revenue_today = '15750'  # Simulation
    
    # ✅ Calcul de la valeur totale du stock comptoir
    total_value_comptoir = sum(float(p.valeur_stock_comptoir or 0) for p in all_products)
    
    return render_template(
        'stock/dashboard_comptoir.html',
        title="Dashboard Stock Comptoir",
        # ✅ Variables templates corrigées
        products_by_category=products_by_category,
        out_of_stock_products=out_of_stock_products,
        recent_sales=recent_sales,
        total_products_comptoir=total_products_comptoir,
        products_out_of_stock=products_out_of_stock,
        sales_today=sales_today,
        revenue_today=revenue_today,
        total_value=f"{total_value_comptoir:,.0f}"  # ✅ Ajout de la valeur totale
    )

@stock.route('/dashboard/consommables')
@login_required
def dashboard_consommables():
    """Dashboard Stock Consommables - Interface Amel"""
    
    # Consommables
    all_consommables = Product.query.filter(Product.product_type == 'consommable').all()
    
    # Consommables par catégorie
    consumables_by_category = {}
    for consumable in all_consommables:
        category_name = consumable.category.name if consumable.category else 'Emballages'
        if category_name not in consumables_by_category:
            consumables_by_category[category_name] = []
        consumables_by_category[category_name].append(consumable)
    
    # ✅ CORRECTION : Trier les consommables - stock > 0 en haut, stock = 0 en bas
    for category_name in consumables_by_category:
        consumables_by_category[category_name].sort(
            key=lambda p: ((p.stock_consommables or 0) > 0, (p.stock_consommables or 0)),
            reverse=True
        )
    
    # ✅ CORRECTION : Suggestions d'ajustement avec calcul dynamique
    suggested_adjustments = []
    for product in all_consommables:
        stock_level = product.stock_consommables or 0
        seuil = product.seuil_min_consommables
        if seuil is None or seuil <= 0:
            continue  # Ignorer les produits sans seuil défini
        if stock_level <= seuil:
            # Calcul dynamique : quantité nécessaire pour atteindre 2x le seuil
            suggested_quantity = max(seuil * 2 - stock_level, seuil)
            suggested_adjustments.append({
                'product_id': product.id,
                'product_name': product.name,
                'estimated_consumption': suggested_quantity,
                'unit': product.unit or 'unités'
            })
    
    # Ajustements récents (simulation)
    recent_adjustments = [
        {
            'product_name': 'Sacs Papier 15cm',
            'quantity': 50,
            'reason': 'Réception fournisseur',
            'time_ago': 'Il y a 2h'
        },
        {
            'product_name': 'Étiquettes Prix',
            'quantity': -25,
            'reason': 'Consommation estimée',
            'time_ago': 'Hier'
        }
    ]
    
    # Statistiques
    total_consommables = len(all_consommables)
    critical_consommables = len([p for p in all_consommables if (p.stock_consommables or 0) <= 0])
    adjustments_this_month = 8  # Simulation
    estimated_consumption = 72  # Pourcentage simulation
    
    # ✅ Calcul de la valeur totale du stock consommables
    total_value_consommables = sum(float(p.valeur_stock_consommables or 0) for p in all_consommables)
    
    return render_template(
        'stock/dashboard_consommables.html',
        title="Dashboard Stock Consommables",
        # ✅ Variables templates corrigées
        consumables_by_category=consumables_by_category,
        suggested_adjustments=suggested_adjustments,
        recent_adjustments=recent_adjustments,
        total_consommables=total_consommables,
        critical_consommables=critical_consommables,
        adjustments_this_month=adjustments_this_month,
        estimated_consumption=estimated_consumption,
        total_value=f"{total_value_consommables:,.0f}"  # ✅ Ajout de la valeur totale
    )

# ==================== ROUTES GESTION DES TRANSFERTS ====================

@stock.route('/transfers')
@login_required
def transfers_list():
    """Liste des transferts entre stocks"""
    transfers = StockTransfer.query.order_by(StockTransfer.requested_date.desc()).all()
    
    return render_template(
        'stock/transfers.html',
        title="Gestion des Transferts",
        transfers=transfers
    )

@stock.route('/transfers/<int:transfer_id>')
@login_required
def view_transfer(transfer_id):
    """Voir les détails d'un transfert"""
    transfer = StockTransfer.query.get_or_404(transfer_id)
    
    return render_template(
        'stock/view_transfer.html',
        title=f"Transfert {transfer.reference}",
        transfer=transfer
    )

@stock.route('/transfers/create', methods=['GET', 'POST'])
@login_required
def create_transfer():
    """Création d'un nouveau transfert"""
    form = StockTransferForm()
    
    # DEBUG: Log pour comprendre le problème
    if request.method == 'POST':
        current_app.logger.info(f"DEBUG - Form submitted")
        current_app.logger.info(f"DEBUG - Form is valid: {form.validate_on_submit()}")
        if not form.validate():
            current_app.logger.error(f"DEBUG - Form errors: {form.errors}")
            flash(f'Erreurs de validation: {form.errors}', 'danger')
    
    if form.validate_on_submit():
        # Création du transfert principal
        transfer = StockTransfer(
            source_location=getattr(StockLocationType, form.source_location.data.upper()),
            destination_location=getattr(StockLocationType, form.destination_location.data.upper()),
            requested_by_id=current_user.id,
            reason=form.reason.data,
            notes=form.notes.data,
            priority=form.priority.data
        )
        
        db.session.add(transfer)
        db.session.flush()  # Pour obtenir l'ID du transfert
        
        # Ajout des lignes de transfert
        for line_form in form.transfer_lines:
            product_obj = line_form.product.data
            quantity_requested = line_form.quantity_requested.data
            
            if product_obj and quantity_requested and quantity_requested > 0:
                transfer_line = StockTransferLine(
                    transfer_id=transfer.id,
                    product_id=product_obj.id,
                    quantity_requested=quantity_requested,
                    unit_cost=float(product_obj.cost_price or 0.0),
                    notes=line_form.notes.data or ''
                )
                
                db.session.add(transfer_line)
        
        db.session.commit()
        flash(f'Transfert {transfer.reference} créé avec succès.', 'success')
        return redirect(url_for('stock.transfers_list'))
    
    return render_template(
        'stock/create_transfer.html',
        title="Créer un Transfert",
        form=form
    )

@stock.route('/transfers/<int:transfer_id>/request', methods=['POST'])
@login_required
def request_transfer(transfer_id):
    """Passer un transfert de DRAFT à REQUESTED"""
    transfer = StockTransfer.query.get_or_404(transfer_id)
    
    if transfer.status == TransferStatus.DRAFT:
        transfer.status = TransferStatus.REQUESTED
        db.session.commit()
        flash(f'Transfert {transfer.reference} envoyé pour approbation.', 'success')
    else:
        flash('Ce transfert ne peut pas être envoyé.', 'danger')
        
    return redirect(url_for('stock.view_transfer', transfer_id=transfer.id))

@stock.route('/transfers/<int:transfer_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_transfer(transfer_id):
    """Approbation d'un transfert"""
    transfer = StockTransfer.query.get_or_404(transfer_id)
    
    if transfer.approve(current_user.id):
        db.session.commit()
        flash(f'Transfert {transfer.reference} approuvé.', 'success')
    else:
        flash('Impossible d\'approuver ce transfert.', 'danger')
        
    return redirect(url_for('stock.view_transfer', transfer_id=transfer.id))

@stock.route('/transfers/<int:transfer_id>/complete', methods=['POST'])
@login_required
def complete_transfer(transfer_id):
    """Finalisation d'un transfert avec mise à jour des stocks"""
    transfer = StockTransfer.query.get_or_404(transfer_id)
    
    if not transfer.can_be_completed:
        flash('Ce transfert ne peut pas être finalisé.', 'danger')
        return redirect(url_for('stock.transfers_list'))
    
    try:
        # Traitement de chaque ligne de transfert
        for line in transfer.transfer_lines:
            product = line.product
            quantity = line.quantity_requested
            
            # Mapping des Enum vers les clés de stock (avec prefix stock_)
            location_map = {
                'INGREDIENTS_MAGASIN': 'stock_ingredients_magasin',
                'INGREDIENTS_LOCAL': 'stock_ingredients_local',
                'COMPTOIR': 'stock_comptoir',
                'CONSOMMABLES': 'stock_consommables'
            }
            
            source_stock_key = location_map.get(transfer.source_location.name, f'stock_{transfer.source_location.value}')
            dest_stock_key = location_map.get(transfer.destination_location.name, f'stock_{transfer.destination_location.value}')
            
            # Vérification du stock source
            # Convertir la valeur de l'Enum (ex: "ingredients_local") pour get_stock_by_location_type
            source_location_type = transfer.source_location.value
            source_stock = product.get_stock_by_location_type(source_location_type)
            
            if source_stock < quantity:
                flash(f'Stock insuffisant pour {product.name} (disponible: {source_stock}, demandé: {quantity}).', 'danger')
                db.session.rollback()
                return redirect(url_for('stock.transfers_list'))
            
            # Décrémentation stock source
            product.update_stock_by_location(source_stock_key, -quantity)
            
            # Incrémentation stock destination
            product.update_stock_by_location(dest_stock_key, quantity)
            
            # Ajouter le produit à la session pour s'assurer qu'il est suivi
            db.session.add(product)
            
            current_app.logger.info(f"DEBUG - Transfert {transfer.reference}: {product.name} -{quantity} ({source_stock_key}) +{quantity} ({dest_stock_key})")
            
            # Création des mouvements de traçabilité
            # Mouvement sortie
            movement_out = StockMovement(
                product_id=product.id,
                stock_location=transfer.source_location,
                movement_type=StockMovementType.TRANSFERT_SORTIE,
                quantity=-quantity,
                unit_cost=line.unit_cost,
                user_id=current_user.id,
                transfer_id=transfer.id,
                reason=f"Transfert {transfer.reference} - Sortie"
            )
            db.session.add(movement_out)
            
            # Mouvement entrée
            movement_in = StockMovement(
                product_id=product.id,
                stock_location=transfer.destination_location,
                movement_type=StockMovementType.TRANSFERT_ENTREE,
                quantity=quantity,
                unit_cost=line.unit_cost,
                user_id=current_user.id,
                transfer_id=transfer.id,
                reason=f"Transfert {transfer.reference} - Entrée"
            )
            db.session.add(movement_in)
            
            # Mise à jour de la ligne de transfert
            line.quantity_transferred = quantity
        
        # Finalisation du transfert
        transfer.complete(current_user.id)
        db.session.commit()
        
        flash(f'Transfert {transfer.reference} finalisé avec succès.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la finalisation du transfert: {str(e)}', 'danger')
    
    return redirect(url_for('stock.transfers_list'))

# ==================== ROUTES API/AJAX ====================

@stock.route('/api/stock_levels/<int:product_id>')
@login_required
def api_stock_levels(product_id):
    """API pour récupérer les niveaux de stock d'un produit"""
    product = Product.query.get_or_404(product_id)
    
    return jsonify({
        'comptoir': product.stock_comptoir,
        'ingredients_local': product.stock_ingredients_local,
        'ingredients_magasin': product.stock_ingredients_magasin,
        'consommables': product.stock_consommables,
        'total': product.total_stock_all_locations,
        'low_stock_locations': product.get_low_stock_locations()
    })

@stock.route('/api/movements_history/<int:product_id>')
@login_required
def api_movements_history(product_id):
    """API pour l'historique des mouvements d'un produit"""
    movements = StockMovement.query.filter_by(product_id=product_id)\
        .order_by(StockMovement.created_at.desc())\
        .limit(20).all()
    
    movements_data = []
    for movement in movements:
        movements_data.append({
            'reference': movement.reference,
            'date': movement.created_at.strftime('%d/%m/%Y %H:%M'),
            'type': movement.movement_type.value,
            'location': movement.stock_location.value,
            'quantity': movement.quantity,
            'stock_after': movement.stock_after,
            'reason': movement.reason,
            'user': movement.user.username if movement.user else 'N/A'
        })
    
    return jsonify(movements_data)
