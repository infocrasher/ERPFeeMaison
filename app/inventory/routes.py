"""
Routes pour le module d'inventaire
Module: app/inventory/routes.py
"""

from flask import render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from datetime import datetime, date
from sqlalchemy import and_, or_, desc, asc
from extensions import db
from models import Product, User
from app.inventory import inventory
from app.inventory.models import (
    Inventory, InventoryItem, InventorySnapshot, 
    InventoryStatus, VarianceLevel, AdjustmentReason
)
from app.inventory.forms import (
    CreateInventoryForm, InventoryItemForm, BulkInventoryForm,
    ValidateInventoryForm, InventorySearchForm, QuickCountForm,
    InventoryReportForm
)
from decorators import admin_required

@inventory.route('/')
@login_required
def index():
    """Page d'accueil du module inventaire"""
    
    # Formulaire de recherche
    search_form = InventorySearchForm()
    
    # Construire la requête de base
    query = Inventory.query
    
    # Appliquer les filtres si le formulaire est soumis
    if search_form.validate_on_submit():
        if search_form.year.data:
            query = query.filter(Inventory.year == int(search_form.year.data))
        if search_form.month.data:
            query = query.filter(Inventory.month == int(search_form.month.data))
        if search_form.status.data:
            query = query.filter(Inventory.status == search_form.status.data)
    
    # Récupérer les inventaires (les plus récents en premier)
    inventories = query.order_by(desc(Inventory.inventory_date)).all()
    
    # Statistiques rapides
    stats = {
        'total_inventories': Inventory.query.count(),
        'pending_inventories': Inventory.query.filter(
            Inventory.status.in_([InventoryStatus.EN_COURS, InventoryStatus.COMPLETE])
        ).count(),
        'current_month_inventory': Inventory.query.filter(
            and_(
                Inventory.month == datetime.now().month,
                Inventory.year == datetime.now().year
            )
        ).first()
    }
    
    return render_template('inventory/index.html', 
                         inventories=inventories,
                         search_form=search_form,
                         stats=stats)

@inventory.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    """Créer un nouvel inventaire"""
    
    form = CreateInventoryForm()
    
    if form.validate_on_submit():
        # Vérifier qu'il n'existe pas déjà un inventaire pour ce mois/année
        existing = Inventory.query.filter(
            and_(
                Inventory.month == form.inventory_date.data.month,
                Inventory.year == form.inventory_date.data.year
            )
        ).first()
        
        if existing:
            flash(f'Un inventaire existe déjà pour {existing.title}', 'warning')
            return redirect(url_for('inventory.view', id=existing.id))
        
        # Créer le nouvel inventaire
        new_inventory = Inventory(
            inventory_date=form.inventory_date.data,
            month=form.inventory_date.data.month,
            year=form.inventory_date.data.year,
            include_ingredients_magasin=form.include_ingredients_magasin.data,
            include_ingredients_local=form.include_ingredients_local.data,
            include_consommables=form.include_consommables.data,
            notes=form.notes.data,
            created_by_id=current_user.id
        )
        
        db.session.add(new_inventory)
        db.session.flush()  # Pour obtenir l'ID
        
        # Créer les lignes d'inventaire et les snapshots
        _create_inventory_items(new_inventory)
        
        db.session.commit()
        
        flash(f'Inventaire {new_inventory.title} créé avec succès', 'success')
        return redirect(url_for('inventory.view', id=new_inventory.id))
    
    return render_template('inventory/create.html', form=form)

@inventory.route('/<int:id>')
@login_required
def view(id):
    """Voir les détails d'un inventaire"""
    
    inventory_obj = Inventory.query.get_or_404(id)
    
    # Statistiques de l'inventaire
    items = inventory_obj.items.all()
    stats = {
        'total_items': len(items),
        'counted_items': len([item for item in items if item.is_counted]),
        'items_with_variance': len([item for item in items if item.has_variance]),
        'critical_variances': len([item for item in items if item.variance_level == VarianceLevel.CRITIQUE]),
        'total_variance_value': sum([item.variance_value or 0 for item in items])
    }
    
    # Grouper les items par emplacement
    items_by_location = {}
    for item in items:
        if item.location_type not in items_by_location:
            items_by_location[item.location_type] = []
        items_by_location[item.location_type].append(item)
    
    return render_template('inventory/view.html', 
                         inventory=inventory_obj,
                         items_by_location=items_by_location,
                         stats=stats)

@inventory.route('/<int:id>/count/<location>')
@login_required
def count_location(id, location):
    """Interface de saisie pour un emplacement donné"""
    
    inventory_obj = Inventory.query.get_or_404(id)
    
    # Vérifier que l'inventaire peut être modifié
    if not inventory_obj.can_be_edited():
        flash('Cet inventaire ne peut plus être modifié', 'error')
        return redirect(url_for('inventory.view', id=id))
    
    # Vérifier que l'emplacement est valide pour cet inventaire
    if location not in inventory_obj.locations_list:
        flash('Emplacement non inclus dans cet inventaire', 'error')
        return redirect(url_for('inventory.view', id=id))
    
    # Récupérer les items pour cet emplacement
    items = inventory_obj.items.filter(
        InventoryItem.location_type == location
    ).join(Product).order_by(Product.name).all()
    
    # Statistiques de l'emplacement
    location_stats = {
        'total_items': len(items),
        'counted_items': len([item for item in items if item.is_counted]),
        'progress_percentage': (len([item for item in items if item.is_counted]) / len(items) * 100) if items else 0
    }
    
    # Noms d'emplacements pour l'affichage
    location_names = {
        'ingredients_magasin': 'Magasin (Labo A)',
        'ingredients_local': 'Local (Labo B)',
        'consommables': 'Consommables'
    }
    
    return render_template('inventory/count_location.html',
                         inventory=inventory_obj,
                         location=location,
                         location_name=location_names.get(location, location),
                         items=items,
                         stats=location_stats)

@inventory.route('/item/<int:item_id>/count', methods=['GET', 'POST'])
@login_required
def count_item(item_id):
    """Saisir le stock physique pour un item"""
    
    item = InventoryItem.query.get_or_404(item_id)
    
    # Vérifier que l'inventaire peut être modifié
    if not item.inventory.can_be_edited():
        flash('Cet inventaire ne peut plus être modifié', 'error')
        return redirect(url_for('inventory.view', id=item.inventory_id))
    
    form = InventoryItemForm(obj=item)
    
    if form.validate_on_submit():
        # Mettre à jour les données
        item.physical_stock = form.physical_stock.data
        item.adjustment_reason = form.adjustment_reason.data if form.adjustment_reason.data else None
        item.notes = form.notes.data
        item.counted_at = datetime.utcnow()
        item.counted_by_id = current_user.id
        
        # Calculer l'écart
        item.calculate_variance()
        
        db.session.commit()
        
        flash(f'Stock physique enregistré pour {item.product.name}', 'success')
        
        # Rediriger vers le prochain item non compté de cet emplacement
        next_item = item.inventory.items.filter(
            and_(
                InventoryItem.location_type == item.location_type,
                InventoryItem.physical_stock.is_(None),
                InventoryItem.id > item.id
            )
        ).first()
        
        if next_item:
            return redirect(url_for('inventory.count_item', item_id=next_item.id))
        else:
            return redirect(url_for('inventory.count_location', 
                                  id=item.inventory_id, 
                                  location=item.location_type))
    
    return render_template('inventory/count_item.html', item=item, form=form)

@inventory.route('/<int:id>/complete', methods=['POST'])
@login_required
@admin_required
def complete(id):
    """Marquer un inventaire comme terminé"""
    
    inventory_obj = Inventory.query.get_or_404(id)
    
    if inventory_obj.status != InventoryStatus.EN_COURS:
        flash('Cet inventaire ne peut pas être marqué comme terminé', 'error')
        return redirect(url_for('inventory.view', id=id))
    
    # Vérifier que tous les items ont été comptés
    uncounted_items = inventory_obj.items.filter(
        InventoryItem.physical_stock.is_(None)
    ).count()
    
    if uncounted_items > 0:
        flash(f'Il reste {uncounted_items} produits non comptés', 'warning')
        return redirect(url_for('inventory.view', id=id))
    
    # Marquer comme terminé
    inventory_obj.status = InventoryStatus.COMPLETE
    inventory_obj.completed_at = datetime.utcnow()
    
    # Mettre à jour les statistiques
    inventory_obj.update_statistics()
    
    db.session.commit()
    
    flash('Inventaire marqué comme terminé', 'success')
    return redirect(url_for('inventory.view', id=id))

@inventory.route('/<int:id>/validate', methods=['GET', 'POST'])
@login_required
@admin_required
def validate(id):
    """Valider un inventaire et appliquer les ajustements"""
    
    inventory_obj = Inventory.query.get_or_404(id)
    
    if not inventory_obj.can_be_validated():
        flash('Cet inventaire ne peut pas être validé', 'error')
        return redirect(url_for('inventory.view', id=id))
    
    form = ValidateInventoryForm()
    
    if form.validate_on_submit():
        # Appliquer les ajustements si demandé
        if form.apply_adjustments.data:
            adjusted_count = 0
            for item in inventory_obj.items:
                if item.apply_adjustment():
                    adjusted_count += 1
        
        # Marquer comme validé
        inventory_obj.status = InventoryStatus.VALIDE
        inventory_obj.validated_at = datetime.utcnow()
        inventory_obj.validated_by_id = current_user.id
        
        if form.validation_notes.data:
            if inventory_obj.notes:
                inventory_obj.notes += f"\n\nValidation: {form.validation_notes.data}"
            else:
                inventory_obj.notes = f"Validation: {form.validation_notes.data}"
        
        db.session.commit()
        
        if form.apply_adjustments.data:
            flash(f'Inventaire validé et {adjusted_count} ajustements appliqués', 'success')
        else:
            flash('Inventaire validé sans appliquer les ajustements', 'info')
        
        return redirect(url_for('inventory.view', id=id))
    
    # Calculer les ajustements à appliquer
    items_to_adjust = [item for item in inventory_obj.items if item.has_variance and not item.adjustment_applied]
    
    return render_template('inventory/validate.html', 
                         inventory=inventory_obj, 
                         form=form,
                         items_to_adjust=items_to_adjust)

@inventory.route('/api/search_products')
@login_required
def api_search_products():
    """API pour rechercher des produits (pour l'interface mobile)"""
    
    query = request.args.get('q', '').strip()
    location = request.args.get('location', '')
    
    if len(query) < 2:
        return jsonify([])
    
    # Rechercher les produits
    products = Product.query.filter(
        Product.name.ilike(f'%{query}%')
    ).limit(10).all()
    
    results = []
    for product in products:
        # Récupérer le stock selon l'emplacement
        if location == 'ingredients_magasin':
            current_stock = product.stock_ingredients_magasin
        elif location == 'ingredients_local':
            current_stock = product.stock_ingredients_local
        elif location == 'consommables':
            current_stock = product.stock_consommables
        else:
            current_stock = 0.0
        
        results.append({
            'id': product.id,
            'name': product.name,
            'unit': product.unit,
            'current_stock': current_stock,
            'cost_price': float(product.cost_price) if product.cost_price else 0.0
        })
    
    return jsonify(results)

@inventory.route('/<int:id>/report')
@login_required
def report(id):
    """Générer un rapport d'inventaire"""
    
    inventory_obj = Inventory.query.get_or_404(id)
    
    # Récupérer tous les items avec écarts
    items_with_variance = inventory_obj.items.filter(
        InventoryItem.variance != 0
    ).join(Product).order_by(
        InventoryItem.location_type,
        Product.name
    ).all()
    
    # Grouper par niveau d'écart
    items_by_level = {
        VarianceLevel.CRITIQUE: [],
        VarianceLevel.NORMAL: [],
        VarianceLevel.OK: []
    }
    
    for item in items_with_variance:
        if item.variance_level:
            items_by_level[item.variance_level].append(item)
    
    # Statistiques détaillées
    detailed_stats = {
        'total_variance_value': sum([item.variance_value or 0 for item in items_with_variance]),
        'positive_variances': len([item for item in items_with_variance if item.variance > 0]),
        'negative_variances': len([item for item in items_with_variance if item.variance < 0]),
        'by_location': {}
    }
    
    # Statistiques par emplacement
    for location in inventory_obj.locations_list:
        location_items = [item for item in items_with_variance if item.location_type == location]
        detailed_stats['by_location'][location] = {
            'count': len(location_items),
            'value': sum([item.variance_value or 0 for item in location_items])
        }
    
    return render_template('inventory/report.html',
                         inventory=inventory_obj,
                         items_by_level=items_by_level,
                         stats=detailed_stats)

def _create_inventory_items(inventory_obj):
    """Créer les lignes d'inventaire et les snapshots pour un inventaire"""
    
    # Récupérer tous les produits qui ont du stock dans les emplacements concernés
    products = Product.query.all()
    
    for product in products:
        # Créer un snapshot du produit
        snapshot = InventorySnapshot(
            inventory_id=inventory_obj.id,
            product_id=product.id,
            stock_ingredients_magasin=product.stock_ingredients_magasin,
            stock_ingredients_local=product.stock_ingredients_local,
            stock_consommables=product.stock_consommables,
            cost_price=product.cost_price,
            total_value=product.stock_value_total
        )
        db.session.add(snapshot)
        
        # Créer les lignes d'inventaire pour chaque emplacement inclus
        locations_to_check = [
            ('ingredients_magasin', product.stock_ingredients_magasin),
            ('ingredients_local', product.stock_ingredients_local),
            ('consommables', product.stock_consommables)
        ]
        
        for location_type, stock_value in locations_to_check:
            # Vérifier si cet emplacement est inclus dans l'inventaire
            include_location = getattr(inventory_obj, f'include_{location_type}', False)
            
            # Créer une ligne même si le stock est à 0 (pour permettre la saisie)
            if include_location:
                item = InventoryItem(
                    inventory_id=inventory_obj.id,
                    product_id=product.id,
                    location_type=location_type,
                    theoretical_stock=stock_value,  # stock_value contient la valeur réelle du stock
                    unit_cost=product.cost_price
                )
                db.session.add(item)

# Routes pour la gestion des invendus quotidiens

@inventory.route('/waste/daily')
@login_required
@admin_required
def daily_waste_index():
    """Liste des déclarations d'invendus quotidiens"""
    from app.inventory.models import DailyWaste
    from app.inventory.forms import DailyWasteForm
    from datetime import datetime, timedelta
    from sqlalchemy import func, extract
    
    # Gestion des filtres par période
    period = request.args.get('period', '30')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Calculer les dates selon la période
    today = datetime.now().date()
    
    if period == '7':
        start_date = today - timedelta(days=7)
        end_date = today
    elif period == '30':
        start_date = today - timedelta(days=30)
        end_date = today
    elif period == 'month':
        start_date = today.replace(day=1)
        end_date = today
    elif period == 'last_month':
        if today.month == 1:
            start_date = today.replace(year=today.year-1, month=12, day=1)
        else:
            start_date = today.replace(month=today.month-1, day=1)
        end_date = today.replace(day=1) - timedelta(days=1)
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
        end_date = today
    elif period == 'custom' and start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        # Par défaut : 30 derniers jours
        start_date = today - timedelta(days=30)
        end_date = today
    
    # Récupérer les déclarations selon la période
    waste_declarations = DailyWaste.query.filter(
        DailyWaste.waste_date >= start_date,
        DailyWaste.waste_date <= end_date
    ).order_by(DailyWaste.waste_date.desc()).all()
    
    # Statistiques
    total_waste_value = sum([w.value_lost for w in waste_declarations])
    waste_by_reason = {}
    for waste in waste_declarations:
        reason = waste.reason
        if reason not in waste_by_reason:
            waste_by_reason[reason] = {'count': 0, 'value': 0.0}
        waste_by_reason[reason]['count'] += 1
        waste_by_reason[reason]['value'] += waste.value_lost
    
    # Données pour les graphiques
    weekly_data = get_weekly_waste_data(start_date, end_date)
    monthly_data = get_monthly_waste_data(start_date, end_date)
    
    return render_template('inventory/daily_waste_index.html',
                         waste_declarations=waste_declarations,
                         total_waste_value=total_waste_value,
                         waste_by_reason=waste_by_reason,
                         weekly_data=weekly_data,
                         monthly_data=monthly_data,
                         period=period,
                         start_date=start_date,
                         end_date=end_date)

def get_weekly_waste_data(start_date, end_date):
    """Génère les données hebdomadaires pour les graphiques"""
    from app.inventory.models import DailyWaste
    from models import Product
    from datetime import datetime, timedelta
    from sqlalchemy import func, extract
    
    # Récupérer les données par semaine
    weekly_stats = DailyWaste.query.filter(
        DailyWaste.waste_date >= start_date,
        DailyWaste.waste_date <= end_date
    ).with_entities(
        func.date_trunc('week', DailyWaste.waste_date).label('week'),
        func.sum(DailyWaste.quantity * Product.cost_price).label('total_value')
    ).join(Product, DailyWaste.product_id == Product.id).group_by('week').order_by('week').all()
    
    labels = []
    values = []
    
    for stat in weekly_stats:
        week_start = stat.week.date()
        labels.append(f"Sem. {week_start.strftime('%d/%m')}")
        values.append(float(stat.total_value or 0))
    
    return {'labels': labels, 'values': values}

def get_monthly_waste_data(start_date, end_date):
    """Génère les données mensuelles pour les graphiques"""
    from app.inventory.models import DailyWaste
    from models import Product
    from datetime import datetime
    from sqlalchemy import func, extract
    
    # Récupérer les données par mois
    monthly_stats = DailyWaste.query.filter(
        DailyWaste.waste_date >= start_date,
        DailyWaste.waste_date <= end_date
    ).with_entities(
        extract('year', DailyWaste.waste_date).label('year'),
        extract('month', DailyWaste.waste_date).label('month'),
        func.sum(DailyWaste.quantity * Product.cost_price).label('total_value')
    ).join(Product, DailyWaste.product_id == Product.id).group_by('year', 'month').order_by('year', 'month').all()
    
    labels = []
    values = []
    
    for stat in monthly_stats:
        month_name = datetime(2000, int(stat.month), 1).strftime('%B')
        labels.append(f"{month_name} {int(stat.year)}")
        values.append(float(stat.total_value or 0))
    
    return {'labels': labels, 'values': values}

@inventory.route('/waste/daily/declare', methods=['GET', 'POST'])
@login_required
@admin_required
def declare_daily_waste():
    """Déclarer des invendus quotidiens (multi-produits)"""
    from app.inventory.models import DailyWaste
    from app.inventory.forms import DailyWasteForm
    from models import Product
    
    form = DailyWasteForm()
    
    # Récupérer tous les produits avec stock comptoir
    products = Product.query.filter(Product.stock_comptoir > 0).order_by(Product.name).all()
    product_choices = [('', '-- Sélectionner un produit --')] + [
        (p.id, f"{p.name} - {p.format_quantity_display(p.stock_comptoir)}")
        for p in products
    ]
    
    # Remplir les choix pour chaque ligne
    for line_form in form.lines:
        line_form.product_id.choices = product_choices
    
    if form.validate_on_submit():
        waste_count = 0
        total_value = 0.0
        errors = []
        
        # Traiter chaque ligne
        for i, line in enumerate(form.lines.entries):
            # Ignorer les lignes vides
            product_id = line.product_id.data
            quantity = line.quantity.data
            reason = line.reason.data
            
            # Vérifier que tous les champs obligatoires sont remplis
            if not product_id or not quantity or not reason or reason == '':
                continue
            
            product = Product.query.get(product_id)
            if not product:
                errors.append(f"Ligne {i+1}: Produit introuvable")
                continue
            
            # Vérifier le stock disponible
            if quantity > product.stock_comptoir:
                flash(f'⚠️ {product.name}: Quantité déclarée ({quantity}) supérieure au stock disponible ({product.stock_comptoir}). Stock ajusté à 0.', 'warning')
                actual_quantity = product.stock_comptoir
                product.stock_comptoir = 0
            else:
                actual_quantity = quantity
                product.stock_comptoir -= actual_quantity
            
            # Créer la déclaration
            waste = DailyWaste(
                waste_date=form.waste_date.data,
                product_id=product.id,
                quantity=actual_quantity,
                reason=reason,
                notes=line.notes.data or form.global_notes.data,
                declared_by_id=current_user.id
            )
            
            db.session.add(waste)
            db.session.add(product)
            
            waste_count += 1
            total_value += waste.value_lost
        
        if errors:
            for error in errors:
                flash(error, 'danger')
        
        if waste_count > 0:
            try:
                db.session.commit()
                flash(f'✅ {waste_count} invendu(s) déclaré(s) pour une valeur totale de {total_value:.2f} DA', 'success')
                return redirect(url_for('inventory.daily_waste_index'))
            except Exception as e:
                db.session.rollback()
                flash(f'Erreur lors de l\'enregistrement : {str(e)}', 'danger')
        else:
            flash('Aucun invendu n\'a été déclaré. Veuillez remplir au moins une ligne complète.', 'warning')
    
    # Préparer les données des produits pour JavaScript
    products_data = {
        p.id: {
            'name': p.name,
            'unit': p.unit,
            'stock': float(p.stock_comptoir),
            'cost_price': float(p.cost_price) if p.cost_price else 0
        }
        for p in products
    }
    
    return render_template('inventory/declare_daily_waste.html', 
                         form=form, 
                         products_data=products_data)

# Routes pour l'inventaire hebdomadaire du comptoir

@inventory.route('/weekly/comptoir')
@login_required
@admin_required
def weekly_comptoir_index():
    """Liste des inventaires hebdomadaires du comptoir"""
    from app.inventory.models import WeeklyComptoirInventory
    from app.inventory.forms import WeeklyComptoirSearchForm
    
    form = WeeklyComptoirSearchForm()
    
    # Remplir les choix d'année et de semaine
    current_year = datetime.now().year
    form.year.choices = [(str(y), str(y)) for y in range(current_year, current_year - 3, -1)]
    form.year.choices.insert(0, ('', 'Toutes les années'))
    
    # Générer les choix de semaines
    form.week.choices = [('', 'Toutes les semaines')] + [(str(i), f'Semaine {i}') for i in range(1, 54)]
    
    inventories = WeeklyComptoirInventory.query.order_by(WeeklyComptoirInventory.inventory_date.desc())
    
    if form.validate_on_submit():
        if form.year.data:
            inventories = inventories.filter(WeeklyComptoirInventory.year == int(form.year.data))
        if form.week.data:
            inventories = inventories.filter(WeeklyComptoirInventory.week_number == int(form.week.data))
        if form.status.data:
            inventories = inventories.filter(WeeklyComptoirInventory.status == form.status.data)
    
    inventories = inventories.all()
    
    return render_template('inventory/weekly_comptoir_index.html',
                         inventories=inventories,
                         form=form)

@inventory.route('/weekly/comptoir/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_weekly_comptoir():
    """Créer un inventaire hebdomadaire du comptoir"""
    from app.inventory.models import WeeklyComptoirInventory, WeeklyComptoirItem
    from app.inventory.forms import WeeklyComptoirInventoryForm
    from models import Product
    import calendar
    
    form = WeeklyComptoirInventoryForm()
    
    if form.validate_on_submit():
        # Calculer le numéro de semaine
        inventory_date = form.inventory_date.data
        week_number = inventory_date.isocalendar()[1]
        year = inventory_date.year
        
        # Vérifier s'il existe déjà un inventaire pour cette semaine
        existing = WeeklyComptoirInventory.query.filter(
            WeeklyComptoirInventory.week_number == week_number,
            WeeklyComptoirInventory.year == year
        ).first()
        
        if existing:
            flash(f'Un inventaire existe déjà pour la semaine {week_number} de {year}', 'warning')
            return redirect(url_for('inventory.weekly_comptoir_index'))
        
        # Créer l'inventaire
        inventory = WeeklyComptoirInventory(
            inventory_date=inventory_date,
            week_number=week_number,
            year=year,
            notes=form.notes.data,
            created_by_id=current_user.id
        )
        
        db.session.add(inventory)
        db.session.flush()  # Pour obtenir l'ID
        
        # Créer les items pour tous les produits avec du stock comptoir
        products = Product.query.filter(Product.stock_comptoir > 0).all()
        
        for product in products:
            item = WeeklyComptoirItem(
                inventory_id=inventory.id,
                product_id=product.id,
                theoretical_stock=product.stock_comptoir,
                unit_cost=product.cost_price
            )
            db.session.add(item)
        
        db.session.commit()
        
        flash(f'Inventaire hebdomadaire créé pour la semaine {week_number} de {year}', 'success')
        return redirect(url_for('inventory.weekly_comptoir_view', id=inventory.id))
    
    return render_template('inventory/create_weekly_comptoir.html', form=form)

@inventory.route('/weekly/comptoir/<int:id>')
@login_required
@admin_required
def weekly_comptoir_view(id):
    """Voir un inventaire hebdomadaire du comptoir"""
    from app.inventory.models import WeeklyComptoirInventory
    
    inventory = WeeklyComptoirInventory.query.get_or_404(id)
    
    # Statistiques
    items = inventory.items.all()
    stats = {
        'total_items': len(items),
        'counted_items': len([item for item in items if item.is_counted]),
        'items_with_variance': len([item for item in items if item.has_variance]),
        'total_variance_value': sum([item.variance_value or 0 for item in items])
    }
    
    return render_template('inventory/weekly_comptoir_view.html',
                         inventory=inventory,
                         items=items,
                         stats=stats)

@inventory.route('/weekly/comptoir/item/<int:item_id>/count', methods=['GET', 'POST'])
@login_required
@admin_required
def count_weekly_comptoir_item(item_id):
    """Saisir le stock physique pour un item d'inventaire hebdomadaire"""
    from app.inventory.models import WeeklyComptoirItem
    from app.inventory.forms import WeeklyComptoirItemForm
    
    item = WeeklyComptoirItem.query.get_or_404(item_id)
    
    if not item.inventory.can_be_edited():
        flash('Cet inventaire ne peut plus être modifié', 'error')
        return redirect(url_for('inventory.weekly_comptoir_view', id=item.inventory_id))
    
    form = WeeklyComptoirItemForm(obj=item)
    
    if form.validate_on_submit():
        item.physical_stock = form.physical_stock.data
        item.notes = form.notes.data
        item.counted_at = datetime.utcnow()
        item.counted_by_id = current_user.id
        
        # Calculer l'écart
        item.calculate_variance()
        
        db.session.commit()
        
        flash(f'Stock physique enregistré pour {item.product.name}', 'success')
        return redirect(url_for('inventory.weekly_comptoir_view', id=item.inventory_id))
    
    return render_template('inventory/count_weekly_comptoir_item.html',
                         item=item,
                         form=form)
