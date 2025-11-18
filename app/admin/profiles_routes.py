# Fichier: app/admin/profiles_routes.py
# Routes pour la gestion des profils utilisateurs

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Profile, User
from decorators import admin_required
from datetime import datetime

profiles_admin = Blueprint('profiles_admin', __name__)

# Liste complète de toutes les permissions organisées par modules
ALL_PERMISSIONS = {
    'VENTES & CAISSE': {
        'ventes_pos': 'POS (Point de vente)',
        'ventes_historique': 'Historique ventes',
        'ventes_rapports': 'Rapports ventes',
        'caisse_ouverture': 'Ouverture caisse',
        'caisse_fermeture': 'Fermeture caisse',
        'caisse_sessions': 'Sessions caisse',
        'caisse_mouvements': 'Mouvements caisse',
        'caisse_statut': 'Statut caisse',
        'caisse_dettes_livreurs': 'Dettes livreurs',
        'caisse_paiement_dette': 'Paiement dette livreur',
        'caisse_cashout': 'Cashout (Dépôt banque)',
    },
    'COMMANDES': {
        'commandes_liste': 'Liste commandes',
        'commandes_creer_client': 'Créer commande client',
        'commandes_creer_production': 'Créer commande production',
        'commandes_voir': 'Voir commande',
        'commandes_modifier': 'Modifier commande',
        'commandes_changer_statut': 'Changer statut commande',
        'commandes_assigner_livreur': 'Assigner livreur',
        'commandes_encaisser': 'Encaisser commande',
        'commandes_dashboard_production': 'Dashboard production',
        'commandes_dashboard_shop': 'Dashboard shop',
        'commandes_alertes_ingredients': 'Alertes ingrédients',
    },
    'CLIENTS': {
        'clients_liste': 'Liste clients',
        'clients_creer': 'Créer client',
        'clients_modifier': 'Modifier client',
        'clients_voir': 'Voir client',
    },
    'B2B': {
        'b2b_clients_liste': 'Liste clients B2B',
        'b2b_clients_creer': 'Créer client B2B',
        'b2b_clients_modifier': 'Modifier client B2B',
        'b2b_clients_voir': 'Voir client B2B',
        'b2b_commandes_liste': 'Liste commandes B2B',
        'b2b_commandes_creer': 'Créer commande B2B',
        'b2b_commandes_modifier': 'Modifier commande B2B',
        'b2b_commandes_voir': 'Voir commande B2B',
        'b2b_factures_liste': 'Liste factures',
        'b2b_factures_creer': 'Créer facture',
        'b2b_factures_modifier': 'Modifier facture',
        'b2b_factures_voir': 'Voir facture',
        'b2b_factures_export_pdf': 'Exporter PDF',
        'b2b_factures_envoyer_email': 'Envoyer email',
    },
    'PRODUITS': {
        'produits_liste': 'Liste produits',
        'produits_creer': 'Créer produit',
        'produits_modifier': 'Modifier produit',
        'produits_voir': 'Voir produit',
        'produits_categories_liste': 'Liste catégories',
        'produits_categories_creer': 'Créer catégorie',
        'produits_categories_modifier': 'Modifier catégorie',
        'produits_categories_supprimer': 'Supprimer catégorie',
    },
    'RECETTES': {
        'recettes_liste': 'Liste recettes',
        'recettes_creer': 'Créer recette',
        'recettes_modifier': 'Modifier recette',
        'recettes_voir': 'Voir recette',
        'recettes_supprimer': 'Supprimer recette',
    },
    'STOCK': {
        'stock_vue_ensemble': 'Vue d\'ensemble stock',
        'stock_reception_rapide': 'Réception rapide',
        'stock_ajustement': 'Ajustement stock',
        'stock_dashboard_magasin': 'Dashboard magasin',
        'stock_dashboard_local': 'Dashboard local',
        'stock_dashboard_comptoir': 'Dashboard comptoir',
        'stock_dashboard_consommables': 'Dashboard consommables',
        'stock_transferts_liste': 'Liste transferts',
        'stock_transferts_creer': 'Créer transfert',
        'stock_transferts_voir': 'Voir transfert',
        'stock_transferts_valider': 'Valider transfert',
        'stock_historique_mouvements': 'Historique mouvements',
    },
    'CONSOMMABLES': {
        'consommables_dashboard': 'Dashboard consommables',
        'consommables_utilisations_liste': 'Liste utilisations',
        'consommables_utilisations_creer': 'Créer utilisation',
        'consommables_ajustements_liste': 'Liste ajustements',
        'consommables_ajustements_creer': 'Créer ajustement',
        'consommables_recettes_liste': 'Liste recettes',
        'consommables_recettes_creer': 'Créer recette',
        'consommables_categories_liste': 'Liste catégories',
        'consommables_categories_creer': 'Créer catégorie',
        'consommables_categories_voir': 'Voir catégorie',
    },
    'INVENTAIRE': {
        'inventaire_liste': 'Liste inventaires',
        'inventaire_creer': 'Créer inventaire',
        'inventaire_voir': 'Voir inventaire',
        'inventaire_compter': 'Compter par emplacement',
        'inventaire_valider': 'Valider inventaire',
        'inventaire_rapports': 'Rapports inventaire',
        'inventaire_hebdo_comptoir_liste': 'Liste inventaires hebdo',
        'inventaire_hebdo_comptoir_creer': 'Créer inventaire hebdo',
        'inventaire_hebdo_comptoir_voir': 'Voir inventaire hebdo',
    },
    'ACHATS': {
        'achats_liste': 'Liste achats',
        'achats_creer': 'Créer achat',
        'achats_modifier': 'Modifier achat',
        'achats_voir': 'Voir achat',
        'achats_marquer_paye': 'Marquer payé',
    },
    'FOURNISSEURS': {
        'fournisseurs_liste': 'Liste fournisseurs',
        'fournisseurs_creer': 'Créer fournisseur',
        'fournisseurs_modifier': 'Modifier fournisseur',
        'fournisseurs_voir': 'Voir fournisseur',
    },
    'DASHBOARDS': {
        'dashboards_journalier': 'Dashboard journalier',
        'dashboards_mensuel': 'Dashboard mensuel',
        'dashboards_production': 'Dashboard production',
        'dashboards_shop': 'Dashboard shop',
    },
    'RH & EMPLOYÉS': {
        'rh_employes_liste': 'Liste employés',
        'rh_employes_creer': 'Créer employé',
        'rh_employes_modifier': 'Modifier employé',
        'rh_employes_voir': 'Voir employé',
        'rh_pointage_dashboard': 'Dashboard pointage',
        'rh_pointage_direct': 'Pointage en direct',
        'rh_pointage_manuel': 'Pointage manuel',
        'rh_pointage_historique': 'Historique pointage',
        'rh_heures_liste': 'Liste heures',
        'rh_heures_creer': 'Créer heures',
        'rh_paie_dashboard': 'Dashboard paie',
        'rh_paie_calcul': 'Calcul paie',
        'rh_paie_bulletins': 'Bulletins',
        'rh_paie_resume_periode': 'Résumé période',
        'rh_analytics_employe': 'Analytics employé',
    },
    'COMPTABILITÉ': {
        'comptabilite_dashboard': 'Dashboard comptabilité',
        'comptabilite_plan_comptable_liste': 'Liste comptes',
        'comptabilite_plan_comptable_creer': 'Créer compte',
        'comptabilite_plan_comptable_modifier': 'Modifier compte',
        'comptabilite_plan_comptable_voir': 'Voir compte',
        'comptabilite_journaux_liste': 'Liste journaux',
        'comptabilite_journaux_creer': 'Créer journal',
        'comptabilite_journaux_voir': 'Voir journal',
        'comptabilite_ecritures_liste': 'Liste écritures',
        'comptabilite_ecritures_creer': 'Créer écriture',
        'comptabilite_ecritures_voir': 'Voir écriture',
        'comptabilite_exercices_liste': 'Liste exercices',
        'comptabilite_exercices_creer': 'Créer exercice',
        'comptabilite_depenses_liste': 'Liste dépenses',
        'comptabilite_depenses_creer': 'Créer dépense',
        'comptabilite_depenses_voir': 'Voir dépense',
        'comptabilite_rapports_balance': 'Balance générale',
        'comptabilite_rapports_compte_resultat': 'Compte de résultat',
        'comptabilite_rapports_etats_financiers': 'États financiers',
        'comptabilite_config': 'Configuration comptabilité',
    },
    'RAPPORTS': {
        'rapports_quotidiens_ventes': 'Ventes quotidiennes',
        'rapports_quotidiens_cout_revient': 'Coût de revient quotidien',
        'rapports_quotidiens_production': 'Production quotidienne',
        'rapports_quotidiens_alertes_stock': 'Alertes stock quotidiennes',
        'rapports_quotidiens_pertes': 'Pertes quotidiennes',
        'rapports_hebdomadaires_performance_produits': 'Performance produits',
        'rapports_hebdomadaires_rotation_stock': 'Rotation stock',
        'rapports_hebdomadaires_cout_main_oeuvre': 'Coût main d\'œuvre',
        'rapports_hebdomadaires_flux_tresorerie': 'Flux de trésorerie',
        'rapports_mensuels_marge_brute': 'Marge brute',
        'rapports_mensuels_profit_loss': 'Profit & Loss',
    },
    'LIVREURS': {
        'livreurs_liste': 'Liste livreurs',
        'livreurs_creer': 'Créer livreur',
        'livreurs_modifier': 'Modifier livreur',
        'livreurs_voir': 'Voir livreur',
    },
    'ZKTECO': {
        'zkteco_test': 'Test connexion',
        'zkteco_pointage': 'Récupérer pointage',
        'zkteco_employes': 'Récupérer employés',
    },
    'ADMINISTRATION': {
        'admin_dashboard': 'Dashboard admin',
        'admin_profils_liste': 'Liste profils',
        'admin_profils_creer': 'Créer profil',
        'admin_profils_modifier': 'Modifier profil',
        'admin_profils_supprimer': 'Supprimer profil',
        'admin_utilisateurs': 'Gestion utilisateurs',
        'admin_imprimante_dashboard': 'Dashboard imprimante',
        'admin_imprimante_config': 'Configuration imprimante',
    },
}


@profiles_admin.route('/profiles')
@login_required
@admin_required
def list_profiles():
    """Liste des profils"""
    profiles = Profile.query.order_by(Profile.name).all()
    return render_template('admin/profiles/list.html', 
                         profiles=profiles,
                         title='Gestion des Profils')


@profiles_admin.route('/profiles/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_profile():
    """Créer un nouveau profil"""
    if request.method == 'POST':
        try:
            # Récupérer les permissions depuis le formulaire
            permissions = {}
            for module_name, module_perms in ALL_PERMISSIONS.items():
                for perm_key, perm_label in module_perms.items():
                    if request.form.get(f'perm_{perm_key}') == 'on':
                        permissions[perm_key] = True
                    else:
                        permissions[perm_key] = False
            
            # Créer le profil
            profile = Profile(
                name=request.form.get('name'),
                description=request.form.get('description', ''),
                is_active=request.form.get('is_active') == 'on',
                permissions=permissions,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(profile)
            db.session.commit()
            
            flash(f'Profil "{profile.name}" créé avec succès !', 'success')
            return redirect(url_for('profiles_admin.list_profiles'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création : {str(e)}', 'error')
    
    return render_template('admin/profiles/form.html',
                         profile=None,
                         all_permissions=ALL_PERMISSIONS,
                         title='Nouveau Profil',
                         action='Créer')


@profiles_admin.route('/profiles/<int:profile_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile(profile_id):
    """Modifier un profil"""
    profile = Profile.query.get_or_404(profile_id)
    
    if request.method == 'POST':
        try:
            # Récupérer les permissions depuis le formulaire
            permissions = {}
            for module_name, module_perms in ALL_PERMISSIONS.items():
                for perm_key, perm_label in module_perms.items():
                    if request.form.get(f'perm_{perm_key}') == 'on':
                        permissions[perm_key] = True
                    else:
                        permissions[perm_key] = False
            
            # Mettre à jour le profil
            profile.name = request.form.get('name')
            profile.description = request.form.get('description', '')
            profile.is_active = request.form.get('is_active') == 'on'
            profile.permissions = permissions
            profile.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash(f'Profil "{profile.name}" modifié avec succès !', 'success')
            return redirect(url_for('profiles_admin.list_profiles'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification : {str(e)}', 'error')
    
    return render_template('admin/profiles/form.html',
                         profile=profile,
                         all_permissions=ALL_PERMISSIONS,
                         title=f'Modifier Profil - {profile.name}',
                         action='Modifier')


@profiles_admin.route('/profiles/<int:profile_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_profile(profile_id):
    """Supprimer un profil"""
    profile = Profile.query.get_or_404(profile_id)
    
    # Vérifier qu'aucun utilisateur n'utilise ce profil
    users_count = User.query.filter_by(profile_id=profile_id).count()
    if users_count > 0:
        flash(f'Impossible de supprimer le profil "{profile.name}" car {users_count} utilisateur(s) l\'utilise(nt).', 'error')
        return redirect(url_for('profiles_admin.list_profiles'))
    
    try:
        db.session.delete(profile)
        db.session.commit()
        flash(f'Profil "{profile.name}" supprimé avec succès !', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression : {str(e)}', 'error')
    
    return redirect(url_for('profiles_admin.list_profiles'))


@profiles_admin.route('/profiles/<int:profile_id>')
@login_required
@admin_required
def view_profile(profile_id):
    """Voir les détails d'un profil"""
    profile = Profile.query.get_or_404(profile_id)
    users = User.query.filter_by(profile_id=profile_id).all()
    
    return render_template('admin/profiles/view.html',
                         profile=profile,
                         users=users,
                         all_permissions=ALL_PERMISSIONS,
                         title=f'Profil - {profile.name}')


