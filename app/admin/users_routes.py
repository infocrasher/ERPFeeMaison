# Fichier: app/admin/users_routes.py
# Routes pour la gestion des utilisateurs

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional
from extensions import db
from models import User, Profile
from decorators import admin_required

users_admin = Blueprint('users_admin', __name__)


class UserForm(FlaskForm):
    """Formulaire pour créer/modifier un utilisateur"""
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[Optional(), Length(min=6)])
    password_confirm = PasswordField('Confirmer le mot de passe', validators=[EqualTo('password', message='Les mots de passe doivent correspondre')])
    role = SelectField('Rôle', choices=[('admin', 'Administrateur'), ('user', 'Utilisateur')], default='user')
    profile_id = SelectField('Profil', coerce=int, validators=[Optional()])


@users_admin.route('/users')
@login_required
@admin_required
def list_users():
    """Liste des utilisateurs"""
    users = User.query.order_by(User.username).all()
    return render_template('admin/users/list.html', 
                         users=users,
                         title='Gestion des Utilisateurs')


@users_admin.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    """Créer un nouvel utilisateur"""
    form = UserForm()
    
    # Charger la liste des profils
    profiles = Profile.query.filter_by(is_active=True).order_by(Profile.name).all()
    form.profile_id.choices = [(0, 'Aucun profil')] + [(p.id, p.name) for p in profiles]
    
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                # Vérifier si l'username existe déjà
                if User.query.filter_by(username=form.username.data).first():
                    flash(f'Le nom d\'utilisateur "{form.username.data}" existe déjà.', 'error')
                    return render_template('admin/users/form.html', form=form, user=None, title='Nouvel Utilisateur', action='Créer')
                
                # Vérifier si l'email existe déjà
                if User.query.filter_by(email=form.email.data).first():
                    flash(f'L\'email "{form.email.data}" est déjà utilisé.', 'error')
                    return render_template('admin/users/form.html', form=form, user=None, title='Nouvel Utilisateur', action='Créer')
                
                # Créer l'utilisateur
                user = User(
                    username=form.username.data,
                    email=form.email.data,
                    role=form.role.data,
                    profile_id=form.profile_id.data if form.profile_id.data else None,
                )
                
                # Définir le mot de passe
                if form.password.data:
                    user.set_password(form.password.data)
                else:
                    flash('Un mot de passe est requis pour créer un utilisateur.', 'error')
                    return render_template('admin/users/form.html', form=form, user=None, title='Nouvel Utilisateur', action='Créer')
                
                db.session.add(user)
                db.session.commit()
                
                flash(f'Utilisateur "{user.username}" créé avec succès !', 'success')
                return redirect(url_for('users_admin.list_users'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Erreur lors de la création : {str(e)}', 'error')
        else:
            # Afficher les erreurs de validation
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'Erreur {field}: {error}', 'error')
    
    return render_template('admin/users/form.html',
                         form=form,
                         user=None,
                         title='Nouvel Utilisateur',
                         action='Créer')


@users_admin.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Modifier un utilisateur"""
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    
    # Charger la liste des profils
    profiles = Profile.query.filter_by(is_active=True).order_by(Profile.name).all()
    form.profile_id.choices = [(0, 'Aucun profil')] + [(p.id, p.name) for p in profiles]
    
    # Ajuster la valeur actuelle du profil
    if user.profile_id:
        form.profile_id.data = user.profile_id
    
    # Rendre le champ password optionnel pour la modification
    form.password.validators = [Optional(), Length(min=6)]
    form.password_confirm.validators = [Optional(), EqualTo('password', message='Les mots de passe doivent correspondre')]
    
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                # Vérifier si l'username existe déjà (sauf pour l'utilisateur actuel)
                existing_user = User.query.filter_by(username=form.username.data).first()
                if existing_user and existing_user.id != user.id:
                    flash(f'Le nom d\'utilisateur "{form.username.data}" existe déjà.', 'error')
                    return render_template('admin/users/form.html', form=form, user=user, title=f'Modifier Utilisateur - {user.username}', action='Modifier')
                
                # Vérifier si l'email existe déjà (sauf pour l'utilisateur actuel)
                existing_email = User.query.filter_by(email=form.email.data).first()
                if existing_email and existing_email.id != user.id:
                    flash(f'L\'email "{form.email.data}" est déjà utilisé.', 'error')
                    return render_template('admin/users/form.html', form=form, user=user, title=f'Modifier Utilisateur - {user.username}', action='Modifier')
                
                # Mettre à jour l'utilisateur
                user.username = form.username.data
                user.email = form.email.data
                user.role = form.role.data
                user.profile_id = form.profile_id.data if form.profile_id.data else None
                
                # Mettre à jour le mot de passe si fourni
                if form.password.data:
                    user.set_password(form.password.data)
                
                db.session.commit()
                
                flash(f'Utilisateur "{user.username}" modifié avec succès !', 'success')
                return redirect(url_for('users_admin.list_users'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Erreur lors de la modification : {str(e)}', 'error')
        else:
            # Afficher les erreurs de validation
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'Erreur {field}: {error}', 'error')
    
    return render_template('admin/users/form.html',
                         form=form,
                         user=user,
                         title=f'Modifier Utilisateur - {user.username}',
                         action='Modifier')


@users_admin.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Supprimer un utilisateur"""
    user = User.query.get_or_404(user_id)
    
    # Empêcher la suppression de l'utilisateur actuel
    if user.id == current_user.id:
        flash('Vous ne pouvez pas supprimer votre propre compte.', 'error')
        return redirect(url_for('users_admin.list_users'))
    
    try:
        username = user.username
        db.session.delete(user)
        db.session.commit()
        flash(f'Utilisateur "{username}" supprimé avec succès !', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression : {str(e)}', 'error')
    
    return redirect(url_for('users_admin.list_users'))


@users_admin.route('/users/<int:user_id>')
@login_required
@admin_required
def view_user(user_id):
    """Voir les détails d'un utilisateur"""
    user = User.query.get_or_404(user_id)
    
    return render_template('admin/users/view.html',
                         user=user,
                         title=f'Utilisateur - {user.username}')

