"""
Routes pour le module comptabilité
"""

from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from decorators import admin_required
from datetime import datetime, date
from sqlalchemy import and_, or_, func

from . import bp
from .models import (Account, Journal, JournalEntry, JournalEntryLine, 
                     FiscalYear, AccountType, AccountNature, JournalType)
from .forms import (AccountForm, JournalForm, JournalEntryForm, FiscalYearForm,
                    AccountSearchForm, JournalEntrySearchForm)


@bp.route('/')
@login_required
@admin_required
def dashboard():
    """Dashboard principal de la comptabilité"""
    
    # Statistiques générales
    total_accounts = Account.query.filter_by(is_active=True).count()
    total_journals = Journal.query.filter_by(is_active=True).count()
    total_entries = JournalEntry.query.count()
    validated_entries = JournalEntry.query.filter_by(is_validated=True).count()
    
    # Exercice courant
    current_fiscal_year = FiscalYear.query.filter_by(is_current=True).first()
    
    # Dernières écritures
    recent_entries = JournalEntry.query.order_by(JournalEntry.created_at.desc()).limit(5).all()
    
    # Comptes avec soldes les plus importants
    accounts_with_balance = []
    for account in Account.query.filter_by(is_detail=True, is_active=True).limit(10):
        balance = account.balance
        if balance and abs(balance) > 0:
            accounts_with_balance.append({
                'account': account,
                'balance': balance
            })
    
    # Trier par valeur absolue du solde
    accounts_with_balance.sort(key=lambda x: abs(x['balance']), reverse=True)
    accounts_with_balance = accounts_with_balance[:5]
    
    # Calculer les KPIs pour le dashboard
    kpis = {
        'ca_mensuel': 0,  # À calculer à partir des ventes
        'charges_mensuelles': 0,  # À calculer à partir des comptes de classe 6
        'benefice_net': 0,  # CA - Charges
        'solde_caisse': 0  # À calculer à partir du compte caisse
    }
    
    # TODO: Implémenter le calcul des KPIs réels
    # Pour l'instant, on met des valeurs par défaut
    
    return render_template('accounting/dashboard.html',
                         total_accounts=total_accounts,
                         total_journals=total_journals,
                         total_entries=total_entries,
                         validated_entries=validated_entries,
                         current_fiscal_year=current_fiscal_year,
                         recent_entries=recent_entries,
                         accounts_with_balance=accounts_with_balance,
                         kpis=kpis)


# ==================== GESTION DES COMPTES ====================

@bp.route('/accounts')
@login_required
@admin_required
def list_accounts():
    """Liste des comptes comptables"""
    form = AccountSearchForm()
    
    query = Account.query
    
    # Filtres de recherche
    if form.validate_on_submit() or request.method == 'GET':
        if form.search.data:
            search_term = f"%{form.search.data}%"
            query = query.filter(or_(
                Account.code.ilike(search_term),
                Account.name.ilike(search_term)
            ))
        
        if form.account_type.data:
            query = query.filter(Account.account_type == AccountType(form.account_type.data))
        
        if form.is_active.data:
            is_active = form.is_active.data == '1'
            query = query.filter(Account.is_active == is_active)
    
    accounts = query.order_by(Account.code).all()
    
    return render_template('accounting/accounts/list.html',
                         accounts=accounts,
                         form=form)


@bp.route('/accounts/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_account():
    """Créer un nouveau compte"""
    form = AccountForm()
    
    if form.validate_on_submit():
        account = Account(
            code=form.code.data,
            name=form.name.data,
            account_type=AccountType(form.account_type.data),
            account_nature=AccountNature(form.account_nature.data),
            parent_id=form.parent_id.data if form.parent_id.data != 0 else None,
            description=form.description.data,
            is_active=form.is_active.data,
            is_detail=form.is_detail.data
        )
        
        # Calculer le niveau hiérarchique
        if account.parent_id:
            parent = Account.query.get(account.parent_id)
            account.level = parent.level + 1
        else:
            account.level = 1
        
        db.session.add(account)
        db.session.commit()
        
        flash(f'Compte {account.code} créé avec succès.', 'success')
        return redirect(url_for('accounting.list_accounts'))
    
    return render_template('accounting/accounts/form.html',
                         form=form,
                         title="Nouveau compte")


@bp.route('/accounts/<int:account_id>')
@login_required
@admin_required
def view_account(account_id):
    """Voir les détails d'un compte"""
    account = Account.query.get_or_404(account_id)
    
    # Dernières écritures du compte
    recent_lines = JournalEntryLine.query.filter_by(account_id=account_id)\
                                        .join(JournalEntry)\
                                        .order_by(JournalEntry.entry_date.desc())\
                                        .limit(20).all()
    
    return render_template('accounting/accounts/view.html',
                         account=account,
                         recent_lines=recent_lines)


@bp.route('/accounts/<int:account_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_account(account_id):
    """Modifier un compte"""
    account = Account.query.get_or_404(account_id)
    form = AccountForm(obj=account)
    
    if form.validate_on_submit():
        account.code = form.code.data
        account.name = form.name.data
        account.account_type = AccountType(form.account_type.data)
        account.account_nature = AccountNature(form.account_nature.data)
        account.parent_id = form.parent_id.data if form.parent_id.data != 0 else None
        account.description = form.description.data
        account.is_active = form.is_active.data
        account.is_detail = form.is_detail.data
        
        # Recalculer le niveau hiérarchique
        if account.parent_id:
            parent = Account.query.get(account.parent_id)
            account.level = parent.level + 1
        else:
            account.level = 1
        
        db.session.commit()
        
        flash(f'Compte {account.code} modifié avec succès.', 'success')
        return redirect(url_for('accounting.view_account', account_id=account.id))
    
    return render_template('accounting/accounts/form.html',
                         form=form,
                         account=account,
                         title="Modifier le compte")


@bp.route('/accounts/<int:account_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_account(account_id):
    """Supprimer un compte"""
    account = Account.query.get_or_404(account_id)
    
    # Vérifier si le compte est utilisé dans des écritures
    entry_lines = JournalEntryLine.query.filter_by(account_id=account_id).first()
    if entry_lines:
        flash('Impossible de supprimer ce compte : il est utilisé dans des écritures comptables.', 'error')
        return redirect(url_for('accounting.list_accounts'))
    
    # Vérifier si le compte a des sous-comptes
    children = Account.query.filter_by(parent_id=account_id).first()
    if children:
        flash('Impossible de supprimer ce compte : il contient des sous-comptes.', 'error')
        return redirect(url_for('accounting.list_accounts'))
    
    db.session.delete(account)
    db.session.commit()
    
    flash(f'Compte {account.code} supprimé avec succès.', 'success')
    return redirect(url_for('accounting.list_accounts'))


# ==================== GESTION DES JOURNAUX ====================

@bp.route('/journals')
@login_required
@admin_required
def list_journals():
    """Liste des journaux comptables"""
    journals = Journal.query.order_by(Journal.code).all()
    
    return render_template('accounting/journals/list.html',
                         journals=journals)


@bp.route('/journals/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_journal():
    """Créer un nouveau journal"""
    form = JournalForm()
    
    if form.validate_on_submit():
        journal = Journal(
            code=form.code.data,
            name=form.name.data,
            journal_type=JournalType(form.journal_type.data),
            description=form.description.data,
            is_active=form.is_active.data,
            sequence_number=1
        )
        
        db.session.add(journal)
        db.session.commit()
        
        flash(f'Journal {journal.code} créé avec succès.', 'success')
        return redirect(url_for('accounting.list_journals'))
    
    return render_template('accounting/journals/form.html',
                         form=form,
                         title="Nouveau journal")


@bp.route('/journals/<int:journal_id>')
@login_required
@admin_required
def view_journal(journal_id):
    """Voir les détails d'un journal"""
    journal = Journal.query.get_or_404(journal_id)
    
    # Dernières écritures du journal
    recent_entries = JournalEntry.query.filter_by(journal_id=journal_id)\
                                      .order_by(JournalEntry.entry_date.desc())\
                                      .limit(20).all()
    
    return render_template('accounting/journals/view.html',
                         journal=journal,
                         recent_entries=recent_entries)


@bp.route('/journals/<int:journal_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_journal(journal_id):
    """Modifier un journal"""
    journal = Journal.query.get_or_404(journal_id)
    form = JournalForm(obj=journal)
    
    if form.validate_on_submit():
        journal.code = form.code.data
        journal.name = form.name.data
        journal.journal_type = JournalType(form.journal_type.data)
        journal.description = form.description.data
        journal.is_active = form.is_active.data
        
        db.session.commit()
        
        flash(f'Journal {journal.code} modifié avec succès.', 'success')
        return redirect(url_for('accounting.view_journal', journal_id=journal.id))
    
    return render_template('accounting/journals/form.html',
                         form=form,
                         journal=journal,
                         title="Modifier le journal")


@bp.route('/journals/<int:journal_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_journal(journal_id):
    """Supprimer un journal"""
    journal = Journal.query.get_or_404(journal_id)
    
    # Vérifier si le journal est utilisé dans des écritures
    entries = JournalEntry.query.filter_by(journal_id=journal_id).first()
    if entries:
        flash('Impossible de supprimer ce journal : il contient des écritures comptables.', 'error')
        return redirect(url_for('accounting.list_journals'))
    
    db.session.delete(journal)
    db.session.commit()
    
    flash(f'Journal {journal.code} supprimé avec succès.', 'success')
    return redirect(url_for('accounting.list_journals'))


# ==================== GESTION DES ÉCRITURES ====================

@bp.route('/entries')
@login_required
@admin_required
def list_entries():
    """Liste des écritures comptables"""
    form = JournalEntrySearchForm()
    
    query = JournalEntry.query
    
    # Filtres de recherche
    if form.validate_on_submit() or request.method == 'GET':
        if form.search.data:
            search_term = f"%{form.search.data}%"
            query = query.filter(or_(
                JournalEntry.reference.ilike(search_term),
                JournalEntry.description.ilike(search_term)
            ))
        
        if form.journal_id.data:
            query = query.filter(JournalEntry.journal_id == form.journal_id.data)
        
        if form.date_from.data:
            query = query.filter(JournalEntry.entry_date >= form.date_from.data)
        
        if form.date_to.data:
            query = query.filter(JournalEntry.entry_date <= form.date_to.data)
        
        if form.is_validated.data:
            is_validated = form.is_validated.data == '1'
            query = query.filter(JournalEntry.is_validated == is_validated)
    
    entries = query.order_by(JournalEntry.entry_date.desc()).all()
    
    return render_template('accounting/entries/list.html',
                         entries=entries,
                         form=form)


@bp.route('/entries/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_entry():
    """Créer une nouvelle écriture comptable"""
    form = JournalEntryForm()
    
    if form.validate_on_submit():
        entry = JournalEntry(
            journal_id=form.journal_id.data,
            entry_date=form.entry_date.data,
            reference=form.reference.data,
            description=form.description.data,
            created_by=current_user.id
        )
        
        db.session.add(entry)
        db.session.flush()  # Pour obtenir l'ID de l'écriture
        
        # Ajouter les lignes d'écriture
        total_debit = 0
        total_credit = 0
        
        for line_data in form.lines.data:
            if line_data['account_id'] and (line_data['debit_amount'] or line_data['credit_amount']):
                line = JournalEntryLine(
                    entry_id=entry.id,
                    account_id=line_data['account_id'],
                    debit_amount=line_data['debit_amount'] or 0,
                    credit_amount=line_data['credit_amount'] or 0,
                    description=line_data['description']
                )
                db.session.add(line)
                total_debit += line.debit_amount
                total_credit += line.credit_amount
        
        # Vérifier l'équilibre
        if total_debit != total_credit:
            flash('L\'écriture n\'est pas équilibrée. Débit total : {:.2f}, Crédit total : {:.2f}'.format(
                total_debit, total_credit), 'error')
            db.session.rollback()
            return render_template('accounting/entries/form.html',
                                 form=form,
                                 title="Nouvelle écriture")
        
        entry.total_amount = total_debit
        db.session.commit()
        
        flash(f'Écriture {entry.reference} créée avec succès.', 'success')
        return redirect(url_for('accounting.view_entry', entry_id=entry.id))
    
    return render_template('accounting/entries/form.html',
                         form=form,
                         title="Nouvelle écriture")


@bp.route('/entries/<int:entry_id>')
@login_required
@admin_required
def view_entry(entry_id):
    """Voir les détails d'une écriture"""
    entry = JournalEntry.query.get_or_404(entry_id)
    
    return render_template('accounting/entries/view.html',
                         entry=entry)


@bp.route('/entries/<int:entry_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_entry(entry_id):
    """Modifier une écriture comptable"""
    entry = JournalEntry.query.get_or_404(entry_id)
    
    # Vérifier si l'écriture est validée
    if entry.is_validated:
        flash('Impossible de modifier une écriture validée.', 'error')
        return redirect(url_for('accounting.view_entry', entry_id=entry.id))
    
    form = JournalEntryForm(obj=entry)
    
    if form.validate_on_submit():
        entry.journal_id = form.journal_id.data
        entry.entry_date = form.entry_date.data
        entry.reference = form.reference.data
        entry.description = form.description.data
        
        # Supprimer les anciennes lignes
        JournalEntryLine.query.filter_by(entry_id=entry.id).delete()
        
        # Ajouter les nouvelles lignes
        total_debit = 0
        total_credit = 0
        
        for line_data in form.lines.data:
            if line_data['account_id'] and (line_data['debit_amount'] or line_data['credit_amount']):
                line = JournalEntryLine(
                    entry_id=entry.id,
                    account_id=line_data['account_id'],
                    debit_amount=line_data['debit_amount'] or 0,
                    credit_amount=line_data['credit_amount'] or 0,
                    description=line_data['description']
                )
                db.session.add(line)
                total_debit += line.debit_amount
                total_credit += line.credit_amount
        
        # Vérifier l'équilibre
        if total_debit != total_credit:
            flash('L\'écriture n\'est pas équilibrée. Débit total : {:.2f}, Crédit total : {:.2f}'.format(
                total_debit, total_credit), 'error')
            db.session.rollback()
            return render_template('accounting/entries/form.html',
                                 form=form,
                                 entry=entry,
                                 title="Modifier l'écriture")
        
        entry.total_amount = total_debit
        db.session.commit()
        
        flash(f'Écriture {entry.reference} modifiée avec succès.', 'success')
        return redirect(url_for('accounting.view_entry', entry_id=entry.id))
    
    return render_template('accounting/entries/form.html',
                         form=form,
                         entry=entry,
                         title="Modifier l'écriture")


@bp.route('/entries/<int:entry_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_entry(entry_id):
    """Supprimer une écriture comptable"""
    entry = JournalEntry.query.get_or_404(entry_id)
    
    # Vérifier si l'écriture est validée
    if entry.is_validated:
        flash('Impossible de supprimer une écriture validée.', 'error')
        return redirect(url_for('accounting.list_entries'))
    
    # Supprimer les lignes d'écriture
    JournalEntryLine.query.filter_by(entry_id=entry.id).delete()
    
    # Supprimer l'écriture
    db.session.delete(entry)
    db.session.commit()
    
    flash(f'Écriture {entry.reference} supprimée avec succès.', 'success')
    return redirect(url_for('accounting.list_entries'))


@bp.route('/entries/<int:entry_id>/validate', methods=['POST'])
@login_required
@admin_required
def validate_entry(entry_id):
    """Valider une écriture comptable"""
    entry = JournalEntry.query.get_or_404(entry_id)
    
    if entry.is_validated:
        flash('Cette écriture est déjà validée.', 'warning')
        return redirect(url_for('accounting.view_entry', entry_id=entry.id))
    
    # Vérifier l'équilibre
    total_debit = sum(line.debit_amount for line in entry.lines)
    total_credit = sum(line.credit_amount for line in entry.lines)
    
    if total_debit != total_credit:
        flash('Impossible de valider une écriture non équilibrée.', 'error')
        return redirect(url_for('accounting.view_entry', entry_id=entry.id))
    
    if not entry.lines:
        flash('Impossible de valider une écriture sans lignes.', 'error')
        return redirect(url_for('accounting.view_entry', entry_id=entry.id))
    
    entry.is_validated = True
    entry.validated_at = datetime.utcnow()
    entry.validated_by = current_user.id
    
    db.session.commit()
    
    flash(f'Écriture {entry.reference} validée avec succès.', 'success')
    return redirect(url_for('accounting.view_entry', entry_id=entry.id))


# ==================== GESTION DES EXERCICES ====================

@bp.route('/fiscal-years')
@login_required
@admin_required
def list_fiscal_years():
    """Liste des exercices comptables"""
    fiscal_years = FiscalYear.query.order_by(FiscalYear.start_date.desc()).all()
    
    return render_template('accounting/periods/list.html',
                         fiscal_years=fiscal_years)


@bp.route('/fiscal-years/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_fiscal_year():
    """Créer un nouvel exercice comptable"""
    form = FiscalYearForm()
    
    if form.validate_on_submit():
        # Désactiver l'exercice courant s'il y en a un
        if form.is_current.data:
            FiscalYear.query.filter_by(is_current=True).update({'is_current': False})
        
        fiscal_year = FiscalYear(
            name=form.name.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            is_current=form.is_current.data,
            is_closed=False
        )
        
        db.session.add(fiscal_year)
        db.session.commit()
        
        flash(f'Exercice {fiscal_year.name} créé avec succès.', 'success')
        return redirect(url_for('accounting.list_fiscal_years'))
    
    return render_template('accounting/periods/form.html',
                         form=form,
                         title="Nouvel exercice")


# Alias pour compatibilité avec les templates
@bp.route('/periods')
@login_required
@admin_required
def list_periods():
    """Alias pour list_fiscal_years"""
    return list_fiscal_years()


@bp.route('/periods/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_period():
    """Alias pour new_fiscal_year"""
    return new_fiscal_year()


@bp.route('/periods/<int:period_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_period(period_id):
    """Modifier un exercice comptable"""
    fiscal_year = FiscalYear.query.get_or_404(period_id)
    
    if fiscal_year.is_closed:
        flash('Impossible de modifier un exercice clôturé.', 'error')
        return redirect(url_for('accounting.list_fiscal_years'))
    
    form = FiscalYearForm(obj=fiscal_year)
    
    if form.validate_on_submit():
        # Désactiver l'exercice courant s'il y en a un
        if form.is_current.data and not fiscal_year.is_current:
            FiscalYear.query.filter_by(is_current=True).update({'is_current': False})
        
        fiscal_year.name = form.name.data
        fiscal_year.start_date = form.start_date.data
        fiscal_year.end_date = form.end_date.data
        fiscal_year.is_current = form.is_current.data
        
        db.session.commit()
        
        flash(f'Exercice {fiscal_year.name} modifié avec succès.', 'success')
        return redirect(url_for('accounting.list_fiscal_years'))
    
    return render_template('accounting/periods/form.html',
                         form=form,
                         fiscal_year=fiscal_year,
                         title="Modifier l'exercice")


@bp.route('/periods/<int:period_id>/close', methods=['POST'])
@login_required
@admin_required
def close_period(period_id):
    """Clôturer un exercice comptable"""
    fiscal_year = FiscalYear.query.get_or_404(period_id)
    
    if fiscal_year.is_closed:
        flash('Cet exercice est déjà clôturé.', 'warning')
        return redirect(url_for('accounting.list_fiscal_years'))
    
    if fiscal_year.is_current:
        flash('Impossible de clôturer l\'exercice courant.', 'error')
        return redirect(url_for('accounting.list_fiscal_years'))
    
    fiscal_year.is_closed = True
    fiscal_year.closed_at = datetime.utcnow()
    fiscal_year.closed_by = current_user.id
    
    db.session.commit()
    
    flash(f'Exercice {fiscal_year.name} clôturé avec succès.', 'success')
    return redirect(url_for('accounting.list_fiscal_years'))


# ==================== GESTION DES CHARGES/DÉPENSES ====================

@bp.route('/expenses')
@login_required
@admin_required
def list_expenses():
    """Liste des charges et dépenses"""
    # Pour l'instant, on affiche les écritures de type charge (classe 6)
    expense_entries = JournalEntry.query.join(JournalEntryLine).join(Account)\
                                       .filter(Account.code.startswith('6'))\
                                       .order_by(JournalEntry.entry_date.desc()).all()
    
    return render_template('accounting/expenses/list.html',
                         expenses=expense_entries)


@bp.route('/expenses/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_expense():
    """Créer une nouvelle charge/dépense"""
    # Rediriger vers la création d'écriture avec un journal de type charge
    return redirect(url_for('accounting.new_entry'))


@bp.route('/expenses/<int:expense_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_expense(expense_id):
    """Modifier une charge/dépense"""
    # Rediriger vers l'édition d'écriture
    return redirect(url_for('accounting.edit_entry', entry_id=expense_id))


@bp.route('/expenses/<int:expense_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_expense(expense_id):
    """Supprimer une charge/dépense"""
    # Rediriger vers la suppression d'écriture
    return delete_entry(expense_id)


# ==================== RAPPORTS ====================

@bp.route('/reports')
@login_required
@admin_required
def reports():
    """Page des rapports comptables"""
    return render_template('accounting/reports.html')


@bp.route('/reports/trial-balance')
@login_required
@admin_required
def trial_balance():
    """Balance générale"""
    
    # Récupérer tous les comptes de détail avec leurs soldes
    accounts = Account.query.filter_by(is_detail=True, is_active=True).order_by(Account.code).all()
    
    balance_data = []
    total_debit = 0
    total_credit = 0
    
    for account in accounts:
        balance = account.balance
        if balance is not None and balance != 0:
            if balance > 0:
                debit_balance = balance
                credit_balance = 0
                total_debit += debit_balance
            else:
                debit_balance = 0
                credit_balance = abs(balance)
                total_credit += credit_balance
            
            balance_data.append({
                'account': account,
                'debit_balance': debit_balance,
                'credit_balance': credit_balance
            })
    
    return render_template('accounting/trial_balance.html',
                         balance_data=balance_data,
                         total_debit=total_debit,
                         total_credit=total_credit)


# ==================== API ====================

@bp.route('/api/accounts')
@login_required
@admin_required
def api_accounts():
    """API pour rechercher des comptes (autocomplétion)"""
    search = request.args.get('search', '')
    limit = request.args.get('limit', 10, type=int)
    
    query = Account.query.filter(Account.is_active == True)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(or_(
            Account.code.ilike(search_term),
            Account.name.ilike(search_term)
        ))
    
    accounts = query.limit(limit).all()
    
    return jsonify([{
        'id': account.id,
        'code': account.code,
        'name': account.name,
        'full_name': f"{account.code} - {account.name}"
    } for account in accounts]) 