"""
Routes pour la gestion des fournisseurs
"""

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_

from . import suppliers
from .forms import SupplierForm, SupplierSearchForm
from models import db, Supplier
from app.purchases.models import Purchase
from decorators import admin_required


@suppliers.route('/')
@login_required
@admin_required
def list_suppliers():
    """Liste des fournisseurs avec recherche"""
    search_form = SupplierSearchForm()
    
    # Construire la requête de base
    query = Supplier.query
    
    # Appliquer les filtres de recherche
    if request.method == 'GET' and request.args.get('search'):
        search_term = request.args.get('search', '').strip()
        supplier_type = request.args.get('supplier_type', '')
        is_active = request.args.get('is_active', '')
        
        # Pré-remplir le formulaire
        search_form.search.data = search_term
        search_form.supplier_type.data = supplier_type
        search_form.is_active.data = is_active
        
        # Filtrer par terme de recherche
        if search_term:
            query = query.filter(
                or_(
                    Supplier.company_name.ilike(f'%{search_term}%'),
                    Supplier.contact_person.ilike(f'%{search_term}%'),
                    Supplier.phone.ilike(f'%{search_term}%'),
                    Supplier.email.ilike(f'%{search_term}%')
                )
            )
        
        # Filtrer par type
        if supplier_type:
            query = query.filter(Supplier.supplier_type == supplier_type)
        
        # Filtrer par statut
        if is_active:
            query = query.filter(Supplier.is_active == (is_active == 'true'))
    
    # Ordonner et paginer
    suppliers_list = query.order_by(Supplier.company_name).all()
    
    return render_template('suppliers/list.html', 
                         suppliers=suppliers_list, 
                         search_form=search_form)


@suppliers.route('/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_supplier():
    """Créer un nouveau fournisseur"""
    form = SupplierForm()
    
    if form.validate_on_submit():
        try:
            supplier = Supplier(
                company_name=form.company_name.data,
                contact_person=form.contact_person.data,
                email=form.email.data,
                phone=form.phone.data,
                address=form.address.data,
                tax_number=form.tax_number.data,
                payment_terms=form.payment_terms.data or 30,
                bank_details=form.bank_details.data,
                supplier_type=form.supplier_type.data,
                notes=form.notes.data,
                is_active=form.is_active.data
            )
            
            db.session.add(supplier)
            db.session.commit()
            
            flash(f'Fournisseur "{supplier.company_name}" créé avec succès.', 'success')
            return redirect(url_for('suppliers.view_supplier', supplier_id=supplier.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création du fournisseur: {str(e)}', 'danger')
    
    return render_template('suppliers/form.html', form=form, title='Nouveau Fournisseur')


@suppliers.route('/<int:supplier_id>')
@login_required
@admin_required
def view_supplier(supplier_id):
    """Voir les détails d'un fournisseur"""
    supplier = Supplier.query.get_or_404(supplier_id)
    
    # Récupérer les achats récents
    recent_purchases = supplier.purchases.order_by(
        db.text('created_at DESC')
    ).limit(10).all()
    
    return render_template('suppliers/view.html', 
                         supplier=supplier, 
                         recent_purchases=recent_purchases)


@suppliers.route('/<int:supplier_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_supplier(supplier_id):
    """Modifier un fournisseur"""
    supplier = Supplier.query.get_or_404(supplier_id)
    form = SupplierForm(obj=supplier)
    
    if form.validate_on_submit():
        try:
            form.populate_obj(supplier)
            db.session.commit()
            
            flash(f'Fournisseur "{supplier.company_name}" modifié avec succès.', 'success')
            return redirect(url_for('suppliers.view_supplier', supplier_id=supplier.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification: {str(e)}', 'danger')
    
    return render_template('suppliers/form.html', 
                         form=form, 
                         supplier=supplier,
                         title=f'Modifier {supplier.company_name}')


@suppliers.route('/<int:supplier_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_supplier_status(supplier_id):
    """Activer/désactiver un fournisseur"""
    supplier = Supplier.query.get_or_404(supplier_id)
    
    try:
        supplier.is_active = not supplier.is_active
        db.session.commit()
        
        status = "activé" if supplier.is_active else "désactivé"
        flash(f'Fournisseur "{supplier.company_name}" {status}.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors du changement de statut: {str(e)}', 'danger')
    
    return redirect(url_for('suppliers.view_supplier', supplier_id=supplier.id))


@suppliers.route('/<int:supplier_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_supplier(supplier_id):
    """Supprimer un fournisseur"""
    supplier = Supplier.query.get_or_404(supplier_id)
    
    # Vérifier s'il y a des achats associés
    purchases_count = supplier.purchases.count()
    if purchases_count > 0:
        flash(f'Impossible de supprimer "{supplier.company_name}" car il a {purchases_count} achat(s) associé(s).', 'danger')
        return redirect(url_for('suppliers.view_supplier', supplier_id=supplier.id))
    
    try:
        company_name = supplier.company_name
        db.session.delete(supplier)
        db.session.commit()
        flash(f'Fournisseur "{company_name}" supprimé avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression: {str(e)}', 'danger')
    
    return redirect(url_for('suppliers.list_suppliers'))


@suppliers.route('/api/search')
@login_required
def api_search_suppliers():
    """API pour recherche de fournisseurs (auto-complétion)"""
    query = request.args.get('q', '').strip()
    limit = int(request.args.get('limit', 10))
    
    if not query or len(query) < 2:
        return jsonify([])
    
    suppliers_list = Supplier.query.filter(
        Supplier.is_active == True,
        or_(
            Supplier.company_name.ilike(f'%{query}%'),
            Supplier.contact_person.ilike(f'%{query}%')
        )
    ).limit(limit).all()
    
    results = []
    for supplier in suppliers_list:
        results.append({
            'id': supplier.id,
            'company_name': supplier.company_name,
            'contact_person': supplier.contact_person,
            'phone': supplier.phone,
            'email': supplier.email,
            'text': f"{supplier.company_name} ({supplier.contact_person or 'N/A'})"
        })
    
    return jsonify(results)


@suppliers.route('/api/details/<int:supplier_id>')
@login_required
def api_supplier_details(supplier_id):
    """API pour récupérer les détails d'un fournisseur"""
    supplier = Supplier.query.get_or_404(supplier_id)
    
    return jsonify({
        'id': supplier.id,
        'company_name': supplier.company_name,
        'contact_person': supplier.contact_person,
        'phone': supplier.phone,
        'email': supplier.email,
        'address': supplier.address,
        'tax_number': supplier.tax_number,
        'payment_terms': supplier.payment_terms,
        'supplier_type': supplier.supplier_type,
        'is_active': supplier.is_active
    })
