from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user
from app.sales.models import CashRegisterSession

def admin_required(f):
    """
    Décorateur qui vérifie si l'utilisateur actuel est un administrateur.
    Doit être utilisé APRÈS @login_required.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # current_user.is_authenticated est déjà vérifié par @login_required
        # mais une double vérification ne fait pas de mal, ou on peut la retirer si @login_required est toujours avant.
        if not current_user.is_authenticated or not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            abort(403)  # Accès interdit
        return f(*args, **kwargs)
    return decorated_function

def role_required(role_name):
    """
    Décorateur générique pour vérifier un rôle spécifique.
    Usage: @role_required('admin') ou @role_required('manager')
    Doit être utilisé APRÈS @login_required.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # ✅ CORRECTION : Utilise current_user.role directement au lieu de has_role()
            if not current_user.is_authenticated or not hasattr(current_user, 'role') or current_user.role != role_name:
                abort(403) # Accès interdit
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_open_cash_session(f):
    """
    Décorateur pour vérifier qu'une session de caisse est ouverte
    Redirige vers la page d'ouverture de caisse si aucune session n'est ouverte
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Vérifier s'il y a une session de caisse ouverte
        session = CashRegisterSession.query.filter_by(is_open=True).first()
        if not session:
            flash('Aucune session de caisse ouverte. Veuillez ouvrir une session avant de continuer.', 'warning')
            return redirect(url_for('sales.open_cash_register'))
        return f(*args, **kwargs)
    return decorated_function

def require_closed_cash_session(f):
    """
    Décorateur pour vérifier qu'aucune session de caisse n'est ouverte
    Utilisé pour l'ouverture de caisse
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Vérifier s'il y a déjà une session de caisse ouverte
        session = CashRegisterSession.query.filter_by(is_open=True).first()
        if session:
            flash('Une session de caisse est déjà ouverte. Veuillez la fermer avant d\'en ouvrir une nouvelle.', 'warning')
            return redirect(url_for('sales.list_cash_sessions'))
        return f(*args, **kwargs)
    return decorated_function
