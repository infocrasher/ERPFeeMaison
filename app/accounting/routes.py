"""
Routes pour le module comptabilité
"""

from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from extensions import db
from decorators import admin_required
from datetime import datetime, date, timedelta
from sqlalchemy import and_, or_, func

from . import bp
from .models import (Account, Journal, JournalEntry, JournalEntryLine, 
                     FiscalYear, AccountType, AccountNature, JournalType)
from .forms import (AccountForm, JournalForm, JournalEntryForm, FiscalYearForm,
                    AccountSearchForm, JournalEntrySearchForm, ExpenseForm)


@bp.route('/')
@login_required
@admin_required
def dashboard():
    """Dashboard principal de la comptabilité avec KPIs avancés"""
    from .services import DashboardService
    from datetime import date
    
    # Calculer les KPIs principaux
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    # KPIs principaux
    ca_jour = DashboardService.get_daily_revenue(today)
    ca_hier = DashboardService.get_daily_revenue(yesterday)
    ca_mensuel = DashboardService.get_monthly_revenue()
    charges_mensuelles = DashboardService.get_monthly_expenses()
    benefice_net = ca_mensuel - charges_mensuelles
    solde_caisse = DashboardService.get_cash_balance()
    solde_banque = DashboardService.get_bank_balance()
    tresorerie_totale = solde_caisse + solde_banque
    
    # Tendance CA jour (comparaison avec hier)
    if ca_hier > 0:
        ca_jour_tendance = ((ca_jour - ca_hier) / ca_hier) * 100
    else:
        ca_jour_tendance = 0 if ca_jour == 0 else 100
    
    # Données pour les graphiques
    revenue_trend = DashboardService.get_daily_revenue_trend(30)
    expense_breakdown = DashboardService.get_expense_breakdown()
    recent_transactions = DashboardService.get_recent_transactions(10)
    
    # Calcul des ratios
    ratios = DashboardService.calculate_ratios(ca_mensuel, charges_mensuelles)
    
    # Statistiques générales (pour compatibilité)
    total_accounts = Account.query.filter_by(is_active=True).count()
    total_journals = Journal.query.filter_by(is_active=True).count()
    total_entries = JournalEntry.query.count()
    validated_entries = JournalEntry.query.filter_by(is_validated=True).count()
    
    # Exercice courant
    current_fiscal_year = FiscalYear.query.filter_by(is_current=True).first()
    
    # Objectif mensuel depuis la configuration
    from .models import BusinessConfig
    config = BusinessConfig.get_current()
    objectif_mensuel = float(config.monthly_objective)
    progression_objectif = (ca_mensuel / objectif_mensuel * 100) if objectif_mensuel > 0 else 0
    
    # Données pour le template
    dashboard_data = {
        'kpis': {
            'ca_jour': ca_jour,
            'ca_jour_tendance': ca_jour_tendance,
            'ca_mensuel': ca_mensuel,
            'charges_mensuelles': charges_mensuelles,
            'benefice_net': benefice_net,
            'tresorerie_totale': tresorerie_totale,
            'solde_caisse': solde_caisse,
            'solde_banque': solde_banque,
            'objectif_mensuel': objectif_mensuel,
            'progression_objectif': progression_objectif
        },
        'charts': {
            'revenue_trend': revenue_trend,
            'expense_breakdown': expense_breakdown
        },
        'ratios': ratios,
        'recent_transactions': recent_transactions,
        'stats': {
            'total_accounts': total_accounts,
            'total_journals': total_journals,
            'total_entries': total_entries,
            'validated_entries': validated_entries,
            'current_fiscal_year': current_fiscal_year
        }
    }
    
    return render_template('accounting/dashboard.html', **dashboard_data)


@bp.route('/config', methods=['GET', 'POST'])
@login_required
@admin_required
def business_config():
    """Configuration des objectifs et paramètres métier"""
    from .models import BusinessConfig
    from .forms import BusinessConfigForm
    
    config = BusinessConfig.get_current()
    form = BusinessConfigForm(obj=config)
    
    if form.validate_on_submit():
        config.monthly_objective = form.monthly_objective.data
        config.daily_objective = form.daily_objective.data
        config.yearly_objective = form.yearly_objective.data
        config.stock_rotation_days = form.stock_rotation_days.data
        config.quality_target_percent = form.quality_target_percent.data
        config.standard_work_hours_per_day = form.standard_work_hours_per_day.data
        config.updated_by_id = current_user.id
        
        db.session.commit()
        flash('Configuration mise à jour avec succès!', 'success')
        return redirect(url_for('accounting.business_config'))
    
    return render_template('accounting/config.html', form=form, config=config, title="Configuration Métier")


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
                    description=line_data['line_description']
                )
                db.session.add(line)
                total_debit += line.debit_amount
                total_credit += line.credit_amount
        
        # Vérifier l'équilibre
        if total_debit != total_credit:
            flash('L\'écriture n\'est pas équilibrée. Débit total : {:.2f}, Crédit total : {:.2f}'.format(
                total_debit, total_credit), 'error')
            db.session.rollback()
            accounts = Account.query.filter_by(is_active=True, is_detail=True).order_by(Account.code).all()
            return render_template('accounting/entries/form.html',
                                 form=form,
                                 accounts=accounts,
                                 title="Nouvelle écriture")
        
        entry.total_amount = total_debit
        db.session.commit()
        
        flash(f'Écriture {entry.reference} créée avec succès.', 'success')
        return redirect(url_for('accounting.view_entry', entry_id=entry.id))
    
    # Charger les comptes pour le template
    accounts = Account.query.filter_by(is_active=True, is_detail=True).order_by(Account.code).all()
    
    return render_template('accounting/entries/form.html',
                         form=form,
                         accounts=accounts,
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
                    description=line_data['line_description']
                )
                db.session.add(line)
                total_debit += line.debit_amount
                total_credit += line.credit_amount
        
        # Vérifier l'équilibre
        if total_debit != total_credit:
            flash('L\'écriture n\'est pas équilibrée. Débit total : {:.2f}, Crédit total : {:.2f}'.format(
                total_debit, total_credit), 'error')
            db.session.rollback()
            accounts = Account.query.filter_by(is_active=True, is_detail=True).order_by(Account.code).all()
            return render_template('accounting/entries/form.html',
                                 form=form,
                                 entry=entry,
                                 accounts=accounts,
                                 title="Modifier l'écriture")
        
        entry.total_amount = total_debit
        db.session.commit()
        
        flash(f'Écriture {entry.reference} modifiée avec succès.', 'success')
        return redirect(url_for('accounting.view_entry', entry_id=entry.id))
    
    # Charger les comptes pour le template
    accounts = Account.query.filter_by(is_active=True, is_detail=True).order_by(Account.code).all()
    
    return render_template('accounting/entries/form.html',
                         form=form,
                         entry=entry,
                         accounts=accounts,
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


@bp.route('/treasury/set-initial-balances', methods=['GET', 'POST'])
@login_required
@admin_required
def set_initial_balances():
    """Définir les soldes initiaux de caisse et banque via écritures comptables d'ouverture"""
    from app.accounting.models import Account, Journal, JournalEntry, JournalEntryLine, JournalType
    from decimal import Decimal
    
    if request.method == 'POST':
        initial_cash = Decimal(str(request.form.get('initial_cash', 0)))
        initial_bank = Decimal(str(request.form.get('initial_bank', 0)))
        
        # Vérifier si des écritures d'ouverture existent déjà
        existing_opening = JournalEntry.query.filter(
            JournalEntry.reference.like('OUVERTURE-%')
        ).first()
        
        if existing_opening:
            flash('Des soldes initiaux ont déjà été définis. Supprimez d\'abord l\'écriture d\'ouverture existante.', 'warning')
            return redirect(url_for('accounting.set_initial_balances'))
        
        # Récupérer ou créer les comptes
        cash_account = Account.query.filter_by(code='530').first()
        if not cash_account:
            cash_account = Account(
                code='530',
                name='Caisse',
                account_type=AccountType.CLASSE_5,
                account_nature=AccountNature.DEBIT
            )
            db.session.add(cash_account)
            db.session.flush()
        
        bank_account = Account.query.filter_by(code='512').first()
        if not bank_account:
            bank_account = Account(
                code='512',
                name='Banque',
                account_type=AccountType.CLASSE_5,
                account_nature=AccountNature.DEBIT
            )
            db.session.add(bank_account)
            db.session.flush()
        
        # Récupérer ou créer le compte Capital/Réserves pour équilibrer (compte 101)
        capital_account = Account.query.filter_by(code='101').first()
        if not capital_account:
            capital_account = Account(
                code='101',
                name='Capital',
                account_type=AccountType.CLASSE_1,
                account_nature=AccountNature.CREDIT
            )
            db.session.add(capital_account)
            db.session.flush()
        
        # Récupérer ou créer le journal des opérations diverses
        journal = Journal.query.filter_by(journal_type=JournalType.OPERATIONS_DIVERSES).first()
        if not journal:
            journal = Journal(
                code='OD',
                name='Opérations Diverses',
                journal_type=JournalType.OPERATIONS_DIVERSES
            )
            db.session.add(journal)
            db.session.flush()
        
        # Créer l'écriture d'ouverture
        total_initial = initial_cash + initial_bank
        
        if total_initial > 0:
            entry = JournalEntry(
                journal_id=journal.id,
                entry_date=date.today(),
                description='Écriture d\'ouverture - Soldes initiaux caisse et banque',
                reference=f'OUVERTURE-{datetime.now().strftime("%Y%m%d%H%M%S")}',
                created_by_id=current_user.id,
                is_validated=True
            )
            entry.generate_reference()
            db.session.add(entry)
            db.session.flush()
            
            # Ligne 1: Débit Caisse
            if initial_cash > 0:
                cash_line = JournalEntryLine(
                    entry_id=entry.id,
                    account_id=cash_account.id,
                    debit_amount=initial_cash,
                    credit_amount=0,
                    description='Solde initial caisse',
                    line_number=1
                )
                db.session.add(cash_line)
            
            # Ligne 2: Débit Banque
            if initial_bank > 0:
                bank_line = JournalEntryLine(
                    entry_id=entry.id,
                    account_id=bank_account.id,
                    debit_amount=initial_bank,
                    credit_amount=0,
                    description='Solde initial banque',
                    line_number=2 if initial_cash > 0 else 1
                )
                db.session.add(bank_line)
            
            # Ligne 3: Crédit Capital (pour équilibrer)
            capital_line = JournalEntryLine(
                entry_id=entry.id,
                account_id=capital_account.id,
                debit_amount=0,
                credit_amount=total_initial,
                description='Solde initial - Capital',
                line_number=3 if (initial_cash > 0 and initial_bank > 0) else 2
            )
            db.session.add(capital_line)
            
            entry.validated_at = datetime.utcnow()
            entry.validated_by_id = current_user.id
        
        db.session.commit()
        flash(f'Soldes initiaux définis : Caisse {initial_cash} DZD, Banque {initial_bank} DZD', 'success')
        return redirect(url_for('accounting.dashboard'))
    
    # Récupérer les soldes actuels (calculés depuis les écritures)
    cash_account = Account.query.filter_by(code='530').first()
    bank_account = Account.query.filter_by(code='512').first()
    
    initial_cash = float(cash_account.balance or 0) if cash_account else 0
    initial_bank = float(bank_account.balance or 0) if bank_account else 0
    
    return render_template('accounting/set_initial_balances.html', 
                         initial_cash=initial_cash, 
                         initial_bank=initial_bank)

@bp.route('/treasury/adjust-cash', methods=['POST'])
@login_required
@admin_required
def adjust_cash():
    """Ajuster le solde de caisse (ajout ou retrait)"""
    from app.sales.models import CashRegisterSession, CashMovement
    
    amount = float(request.form.get('amount', 0))
    operation = request.form.get('operation', 'add')  # 'add' ou 'remove'
    reason = request.form.get('reason', 'Ajustement manuel')
    
    session = CashRegisterSession.query.filter_by(is_open=True).first()
    if not session:
        flash('Aucune session de caisse ouverte', 'error')
        return redirect(url_for('accounting.dashboard'))
    
    # Créer le mouvement de caisse
    movement_type = 'entrée' if operation == 'add' else 'sortie'
    movement = CashMovement(
        session_id=session.id,
        created_at=datetime.utcnow(),
        type=movement_type,
        amount=amount,
        reason=f'Ajustement caisse - {reason}',
        notes=f'{"Ajout" if operation == "add" else "Retrait"} manuel de {amount} DZD',
        employee_id=current_user.id
    )
    
    db.session.add(movement)
    db.session.commit()
    
    flash(f'{"Ajout" if operation == "add" else "Retrait"} de {amount} DZD en caisse effectué', 'success')
    return redirect(url_for('accounting.dashboard'))

@bp.route('/treasury/adjust-bank', methods=['GET', 'POST'])
@login_required
@admin_required
def adjust_bank():
    """Ajuster le solde bancaire (ajout ou retrait)"""
    # Si GET, rediriger vers le dashboard avec un message
    if request.method == 'GET':
        flash('Veuillez utiliser le bouton "Ajuster Banque" depuis le dashboard.', 'info')
        return redirect(url_for('accounting.dashboard'))
    
    from app.accounting.models import Account, Journal, JournalEntry, JournalEntryLine, JournalType
    from decimal import Decimal
    
    amount = Decimal(str(request.form.get('amount', 0)))
    operation = request.form.get('operation', 'add')  # 'add' ou 'remove'
    reason = request.form.get('reason', 'Ajustement manuel')
    
    bank_account = Account.query.filter_by(code='512').first()
    if not bank_account:
        flash('Compte banque non trouvé', 'error')
        return redirect(url_for('accounting.dashboard'))
    
    # Récupérer le journal de banque
    journal = Journal.query.filter_by(journal_type=JournalType.BANQUE).first()
    if not journal:
        # Créer le journal BQ s'il n'existe pas
        journal = Journal(
            code='BQ',
            name='Journal de Banque',
            journal_type=JournalType.BANQUE
        )
        db.session.add(journal)
        db.session.flush()
    
    # Compte d'ajustement (Produits divers pour ajout, Charges diverses pour retrait)
    if operation == 'add':
        adjustment_account = Account.query.filter_by(code='758').first()  # Produits divers
        if not adjustment_account:
            flash('Compte "Produits divers" (758) non trouvé', 'error')
            return redirect(url_for('accounting.dashboard'))
    else:
        adjustment_account = Account.query.filter_by(code='658').first()  # Charges diverses
        if not adjustment_account:
            flash('Compte "Charges diverses" (658) non trouvé', 'error')
            return redirect(url_for('accounting.dashboard'))
    
    # Créer l'écriture comptable d'ajustement
    entry = JournalEntry(
        journal_id=journal.id,
        entry_date=date.today(),
        description=f'Ajustement bancaire - {reason}',
        reference=f'AJUST-BANK-{datetime.now().strftime("%Y%m%d%H%M%S")}',
        created_by_id=current_user.id,
        is_validated=True  # Valider automatiquement les ajustements
    )
    
    # Générer la référence
    entry.generate_reference()
    
    db.session.add(entry)
    db.session.flush()
    
    if operation == 'add':
        # Ajout : Débiter banque (512), Créditer produits divers (758)
        debit_line = JournalEntryLine(
            entry_id=entry.id,
            account_id=bank_account.id,
            debit_amount=amount,
            credit_amount=0,
            description=f'Ajout bancaire - {reason}',
            line_number=1
        )
        credit_line = JournalEntryLine(
            entry_id=entry.id,
            account_id=adjustment_account.id,
            debit_amount=0,
            credit_amount=amount,
            description=f'Ajustement bancaire - {reason}',
            line_number=2
        )
    else:
        # Retrait : Débiter charges diverses (658), Créditer banque (512)
        debit_line = JournalEntryLine(
            entry_id=entry.id,
            account_id=adjustment_account.id,
            debit_amount=amount,
            credit_amount=0,
            description=f'Ajustement bancaire - {reason}',
            line_number=1
        )
        credit_line = JournalEntryLine(
            entry_id=entry.id,
            account_id=bank_account.id,
            debit_amount=0,
            credit_amount=amount,
            description=f'Retrait bancaire - {reason}',
            line_number=2
        )
    
    entry.validated_at = datetime.utcnow()
    entry.validated_by_id = current_user.id
    
    db.session.add(debit_line)
    db.session.add(credit_line)
    db.session.commit()
    
    flash(f'{"Ajout" if operation == "add" else "Retrait"} de {amount} DZD en banque effectué', 'success')
    return redirect(url_for('accounting.dashboard'))

@bp.route('/expenses/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_expense():
    """Créer une nouvelle charge/dépense"""
    from .forms import ExpenseForm
    
    form = ExpenseForm()
    
    if form.validate_on_submit():
        # Créer automatiquement l'écriture comptable
        from .models import Journal, Account
        
        # Récupérer le journal des achats/charges
        journal = Journal.query.filter_by(code='AC').first()
        if not journal:
            # Créer le journal AC s'il n'existe pas
            journal = Journal(
                code='AC',
                name='Achats et Charges',
                journal_type='PURCHASES'
            )
            db.session.add(journal)
            db.session.flush()
        
        # Récupérer les comptes
        expense_account = Account.query.filter_by(code=form.category.data).first()
        
        if form.payment_method.data == 'cash':
            payment_account = Account.query.filter_by(code='530').first()  # Caisse
            # Vérifier qu'une session de caisse est ouverte
            from app.sales.models import CashRegisterSession, CashMovement
            cash_session = CashRegisterSession.query.filter_by(is_open=True).first()
            if not cash_session:
                flash('Erreur : Aucune session de caisse ouverte. Veuillez ouvrir une session de caisse avant de payer une charge en espèces.', 'error')
                from .services import DashboardService
                bank_balance = DashboardService.get_bank_balance()
                return render_template('accounting/expenses/form.html', 
                                     form=form,
                                     bank_balance=bank_balance,
                                     title="Nouvelle Dépense")
        elif form.payment_method.data == 'bank':
            payment_account = Account.query.filter_by(code='512').first()  # Banque
        
        if not expense_account or not payment_account:
            flash('Erreur : Comptes comptables non trouvés. Veuillez créer les comptes nécessaires.', 'error')
            from .services import DashboardService
            bank_balance = DashboardService.get_bank_balance()
            return render_template('accounting/expenses/form.html', 
                                 form=form,
                                 bank_balance=bank_balance,
                                 title="Nouvelle Dépense")
        
        # Préparer la description avec précision si applicable
        description = form.description.data
        if form.other_category.data:
            description = f"{form.description.data} - {form.other_category.data}"
        
        # Créer l'écriture
        entry = JournalEntry(
            journal_id=journal.id,
            entry_date=form.date.data,
            description=description,
            reference=form.reference.data,
            created_by_id=current_user.id
        )
        
        # Générer la référence automatique
        entry.generate_reference()
        
        db.session.add(entry)
        db.session.flush()
        
        # Ligne débit (charge)
        debit_line = JournalEntryLine(
            entry_id=entry.id,
            account_id=expense_account.id,
            debit_amount=form.amount.data,
            credit_amount=0,
            description=description,
            line_number=1
        )
        
        # Ligne crédit (paiement)
        credit_line = JournalEntryLine(
            entry_id=entry.id,
            account_id=payment_account.id,
            debit_amount=0,
            credit_amount=form.amount.data,
            description=f"Paiement {form.payment_method.data}",
            line_number=2
        )
        
        db.session.add(debit_line)
        db.session.add(credit_line)
        
        # Si paiement en caisse, créer un mouvement de caisse
        if form.payment_method.data == 'cash':
            from app.sales.models import CashRegisterSession, CashMovement
            cash_session = CashRegisterSession.query.filter_by(is_open=True).first()
            if cash_session:
                # Préparer la description pour le mouvement de caisse
                movement_description = description
                if form.supplier.data:
                    movement_description = f"{description} - {form.supplier.data}"
                
                # Créer le mouvement de caisse (sortie)
                cash_movement = CashMovement(
                    session_id=cash_session.id,
                    created_at=datetime.utcnow(),
                    type='sortie',
                    amount=float(form.amount.data),
                    reason=f'Paiement charge - {form.category.data}',
                    notes=movement_description,
                    employee_id=current_user.id
                )
                db.session.add(cash_movement)
                db.session.flush()  # Pour obtenir l'ID du mouvement
                
                # Intégration comptable automatique pour le mouvement de caisse
                try:
                    from .services import AccountingIntegrationService
                    AccountingIntegrationService.create_cash_movement_entry(
                        cash_movement_id=cash_movement.id,
                        amount=float(form.amount.data),
                        movement_type='out',
                        description=f'Paiement charge - {movement_description}'
                    )
                except Exception as e:
                    current_app.logger.error(f"Erreur intégration comptable mouvement caisse (cash_movement_id={cash_movement.id}): {e}", exc_info=True)
                    # On continue même si l'intégration comptable échoue
        
        # Valider automatiquement si payé
        if form.is_paid.data:
            entry.is_validated = True
            entry.validated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Message flash selon le mode de paiement
        payment_method_label = 'Caisse' if form.payment_method.data == 'cash' else 'Banque'
        flash(f'Dépense de {form.amount.data} DZD enregistrée avec succès. Déduite de la {payment_method_label.lower()}.', 'success')
        return redirect(url_for('accounting.list_expenses'))
    
    # Récupérer le solde bancaire pour l'affichage
    from .services import DashboardService
    bank_balance = DashboardService.get_bank_balance()
    
    return render_template('accounting/expenses/form.html', 
                         form=form,
                         bank_balance=bank_balance,
                         title="Nouvelle Dépense")


@bp.route('/bank-statement')
@login_required
@admin_required
def bank_statement():
    """État de la banque avec solde et historique des mouvements"""
    from .services import DashboardService
    from sqlalchemy import desc
    
    # Calculer le solde bancaire actuel
    bank_balance = DashboardService.get_bank_balance()
    
    # Récupérer tous les mouvements bancaires (compte 512)
    bank_account = Account.query.filter_by(code='512').first()
    
    if not bank_account:
        flash('Compte bancaire (512) non trouvé. Veuillez créer le compte bancaire.', 'error')
        return redirect(url_for('accounting.dashboard'))
    
    # Récupérer toutes les lignes d'écriture du compte banque avec la relation entry chargée
    # Le backref 'entry' est défini dans JournalEntry.lines avec backref='entry'
    # Utiliser une jointure explicite pour charger les données de JournalEntry
    bank_movements = db.session.query(JournalEntryLine, JournalEntry)\
                                          .join(JournalEntry, JournalEntryLine.entry_id == JournalEntry.id)\
                                          .filter(JournalEntryLine.account_id == bank_account.id)\
                                          .order_by(desc(JournalEntry.entry_date), desc(JournalEntry.id))\
                                          .all()
    
    # Extraire seulement les lignes (movements) et associer les entries
    movements_list = []
    for line, entry in bank_movements:
        # Attacher l'entry à la ligne pour que movement.entry fonctionne
        line.entry = entry
        movements_list.append(line)
    
    bank_movements = movements_list
    
    # Calculer le solde cumulé pour chaque mouvement
    movements_with_balance = []
    running_balance = 0
    
    # Calculer d'abord le solde total
    for movement in reversed(bank_movements):  # Ordre chronologique pour le calcul
        if movement.debit_amount:
            running_balance += float(movement.debit_amount)
        if movement.credit_amount:
            running_balance -= float(movement.credit_amount)
    
    # Maintenant créer la liste avec les soldes (ordre anti-chronologique pour l'affichage)
    current_balance = running_balance
    for movement in bank_movements:
        # Déterminer le type de mouvement
        movement_type = "Entrée" if movement.debit_amount else "Sortie"
        amount = float(movement.debit_amount or movement.credit_amount)
        
        # Catégoriser le mouvement
        # Utiliser 'entry' (backref défini dans le modèle JournalEntry.lines avec backref='entry')
        entry = movement.entry
        description = (entry.description or '').lower() if entry and entry.description else ''
        if 'salaire' in description or 'paiement salaire' in description:
            category = "Salaire"
            icon = "bi-person-check"
            color = "text-warning"
        elif 'achat' in description or 'charge' in description or 'dépense' in description:
            category = "Charge/Achat"
            icon = "bi-cart"
            color = "text-danger"
        elif 'vente' in description or 'encaissement' in description:
            category = "Vente"
            icon = "bi-cash-coin"
            color = "text-success"
        elif 'ajustement' in description or 'correction' in description:
            category = "Ajustement"
            icon = "bi-gear"
            color = "text-info"
        else:
            category = "Autre"
            icon = "bi-arrow-left-right"
            color = "text-secondary"
        
        movements_with_balance.append({
            'movement': movement,
            'type': movement_type,
            'amount': amount,
            'category': category,
            'icon': icon,
            'color': color,
            'balance': current_balance,
            'date': entry.entry_date,
            'reference': entry.reference or '',
            'description': entry.description or ''
        })
        
        # Ajuster le solde pour le mouvement précédent
        if movement.debit_amount:
            current_balance -= float(movement.debit_amount)
        if movement.credit_amount:
            current_balance += float(movement.credit_amount)
    
    # Statistiques
    total_entries = sum(m['amount'] for m in movements_with_balance if m['type'] == 'Entrée')
    total_exits = sum(m['amount'] for m in movements_with_balance if m['type'] == 'Sortie')
    
    # Mouvements par catégorie
    categories_stats = {}
    for movement in movements_with_balance:
        cat = movement['category']
        if cat not in categories_stats:
            categories_stats[cat] = {'count': 0, 'amount': 0}
        categories_stats[cat]['count'] += 1
        categories_stats[cat]['amount'] += movement['amount']
    
    return render_template('accounting/bank_statement.html',
                         bank_balance=bank_balance,
                         movements=movements_with_balance,
                         total_entries=total_entries,
                         total_exits=total_exits,
                         categories_stats=categories_stats,
                         title="État de la Banque")


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
    """Balance générale avec calcul du résultat net"""
    
    # Récupérer tous les comptes de détail avec leurs soldes
    accounts = Account.query.filter_by(is_detail=True, is_active=True).order_by(Account.code).all()
    
    balance_data = []
    total_debit = 0
    total_credit = 0
    
    # Variables pour le calcul du résultat net
    total_produits = 0  # Classe 7
    total_charges = 0   # Classe 6
    
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
            
            # Calcul du résultat net
            if account.code.startswith('7'):  # Comptes de produits
                total_produits += abs(balance)
            elif account.code.startswith('6'):  # Comptes de charges
                total_charges += abs(balance)
    
    # Calcul du résultat net
    resultat_net = total_produits - total_charges
    
    # Déterminer si c'est un bénéfice ou une perte
    resultat_type = "Bénéfice" if resultat_net > 0 else "Perte" if resultat_net < 0 else "Équilibre"
    
    return render_template('accounting/trial_balance.html',
                         balance_data=balance_data,
                         total_debit=total_debit,
                         total_credit=total_credit,
                         total_produits=total_produits,
                         total_charges=total_charges,
                         resultat_net=abs(resultat_net),
                         resultat_type=resultat_type)


@bp.route('/reports/profit-loss')
@login_required
@admin_required
def profit_loss():
    """Compte de résultat (Profit & Loss)"""
    
    # Récupérer tous les comptes de produits (classe 7) et charges (classe 6)
    accounts = Account.query.filter_by(is_detail=True, is_active=True).order_by(Account.code).all()
    
    produits_data = []
    charges_data = []
    total_produits = 0
    total_charges = 0
    
    for account in accounts:
        balance = account.balance
        if balance is not None and balance != 0:
            if account.code.startswith('7'):  # Comptes de produits
                produits_data.append({
                    'account': account,
                    'balance': abs(balance)
                })
                total_produits += abs(balance)
            elif account.code.startswith('6'):  # Comptes de charges
                charges_data.append({
                    'account': account,
                    'balance': abs(balance)
                })
                total_charges += abs(balance)
    
    # Calcul du résultat net
    resultat_net = total_produits - total_charges
    resultat_type = "Bénéfice" if resultat_net > 0 else "Perte" if resultat_net < 0 else "Équilibre"
    
    return render_template('accounting/profit_loss.html',
                         produits_data=produits_data,
                         charges_data=charges_data,
                         total_produits=total_produits,
                         total_charges=total_charges,
                         resultat_net=abs(resultat_net),
                         resultat_type=resultat_type)


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