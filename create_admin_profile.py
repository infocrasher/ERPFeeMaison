#!/usr/bin/env python3
"""
Script pour créer le profil Admin par défaut avec toutes les permissions
Usage: python create_admin_profile.py
"""

from app import create_app
from extensions import db
from models import Profile, User
from datetime import datetime, timezone

def create_admin_profile():
    """Créer le profil Admin avec toutes les permissions"""
    app = create_app()
    
    with app.app_context():
        # Vérifier si la table profiles existe
        try:
            # Test de connexion à la table
            Profile.query.first()
        except Exception as e:
            print("❌ ERREUR : La table 'profiles' n'existe pas encore.")
            print("    Vous devez d'abord appliquer la migration :")
            print("    flask db upgrade")
            print("")
            print(f"    Détails de l'erreur : {e}")
            return
        
        # Vérifier si le profil Admin existe déjà
        admin_profile = Profile.query.filter_by(name='Admin').first()
        
        if admin_profile:
            print("✅ Le profil Admin existe déjà.")
            return
        
        # Créer toutes les permissions (toutes activées pour Admin)
        all_permissions = {}
        
        # Liste complète des permissions (identique à profiles_routes.py)
        permissions_list = [
            # VENTES & CAISSE
            'ventes_pos', 'ventes_historique', 'ventes_rapports',
            'caisse_ouverture', 'caisse_fermeture', 'caisse_sessions',
            'caisse_mouvements', 'caisse_statut', 'caisse_dettes_livreurs',
            'caisse_paiement_dette', 'caisse_cashout',
            # COMMANDES
            'commandes_liste', 'commandes_creer_client', 'commandes_creer_production',
            'commandes_voir', 'commandes_modifier', 'commandes_changer_statut',
            'commandes_assigner_livreur', 'commandes_encaisser', 'commandes_dashboard_production',
            'commandes_dashboard_shop', 'commandes_alertes_ingredients',
            # CLIENTS
            'clients_liste', 'clients_creer', 'clients_modifier', 'clients_voir',
            # B2B
            'b2b_clients_liste', 'b2b_clients_creer', 'b2b_clients_modifier', 'b2b_clients_voir',
            'b2b_commandes_liste', 'b2b_commandes_creer', 'b2b_commandes_modifier', 'b2b_commandes_voir',
            'b2b_factures_liste', 'b2b_factures_creer', 'b2b_factures_modifier', 'b2b_factures_voir',
            'b2b_factures_export_pdf', 'b2b_factures_envoyer_email',
            # PRODUITS
            'produits_liste', 'produits_creer', 'produits_modifier', 'produits_voir',
            'produits_categories_liste', 'produits_categories_creer', 'produits_categories_modifier', 'produits_categories_supprimer',
            # RECETTES
            'recettes_liste', 'recettes_creer', 'recettes_modifier', 'recettes_voir', 'recettes_supprimer',
            # STOCK
            'stock_vue_ensemble', 'stock_reception_rapide', 'stock_ajustement',
            'stock_dashboard_magasin', 'stock_dashboard_local', 'stock_dashboard_comptoir',
            'stock_dashboard_consommables', 'stock_transferts_liste', 'stock_transferts_creer',
            'stock_transferts_voir', 'stock_transferts_valider', 'stock_historique_mouvements',
            # CONSOMMABLES
            'consommables_dashboard', 'consommables_utilisations_liste', 'consommables_utilisations_creer',
            'consommables_ajustements_liste', 'consommables_ajustements_creer', 'consommables_recettes_liste',
            'consommables_recettes_creer', 'consommables_categories_liste', 'consommables_categories_creer',
            'consommables_categories_voir',
            # INVENTAIRE
            'inventaire_liste', 'inventaire_creer', 'inventaire_voir', 'inventaire_compter',
            'inventaire_valider', 'inventaire_rapports', 'inventaire_hebdo_comptoir_liste',
            'inventaire_hebdo_comptoir_creer', 'inventaire_hebdo_comptoir_voir',
            # ACHATS
            'achats_liste', 'achats_creer', 'achats_modifier', 'achats_voir', 'achats_marquer_paye',
            # FOURNISSEURS
            'fournisseurs_liste', 'fournisseurs_creer', 'fournisseurs_modifier', 'fournisseurs_voir',
            # DASHBOARDS
            'dashboards_journalier', 'dashboards_mensuel', 'dashboards_production', 'dashboards_shop',
            # RH & EMPLOYÉS
            'rh_employes_liste', 'rh_employes_creer', 'rh_employes_modifier', 'rh_employes_voir',
            'rh_pointage_dashboard', 'rh_pointage_direct', 'rh_pointage_manuel', 'rh_pointage_historique',
            'rh_heures_liste', 'rh_heures_creer', 'rh_paie_dashboard', 'rh_paie_calcul',
            'rh_paie_bulletins', 'rh_paie_resume_periode', 'rh_analytics_employe',
            # COMPTABILITÉ
            'comptabilite_dashboard', 'comptabilite_plan_comptable_liste', 'comptabilite_plan_comptable_creer',
            'comptabilite_plan_comptable_modifier', 'comptabilite_plan_comptable_voir',
            'comptabilite_journaux_liste', 'comptabilite_journaux_creer', 'comptabilite_journaux_voir',
            'comptabilite_ecritures_liste', 'comptabilite_ecritures_creer', 'comptabilite_ecritures_voir',
            'comptabilite_exercices_liste', 'comptabilite_exercices_creer',
            'comptabilite_depenses_liste', 'comptabilite_depenses_creer', 'comptabilite_depenses_voir',
            'comptabilite_rapports_balance', 'comptabilite_rapports_compte_resultat',
            'comptabilite_rapports_etats_financiers', 'comptabilite_config',
            # RAPPORTS
            'rapports_quotidiens_ventes', 'rapports_quotidiens_cout_revient', 'rapports_quotidiens_production',
            'rapports_quotidiens_alertes_stock', 'rapports_quotidiens_pertes',
            'rapports_hebdomadaires_performance_produits', 'rapports_hebdomadaires_rotation_stock',
            'rapports_hebdomadaires_cout_main_oeuvre', 'rapports_hebdomadaires_flux_tresorerie',
            'rapports_mensuels_marge_brute', 'rapports_mensuels_profit_loss',
            # LIVREURS
            'livreurs_liste', 'livreurs_creer', 'livreurs_modifier', 'livreurs_voir',
            # ZKTECO
            'zkteco_test', 'zkteco_pointage', 'zkteco_employes',
            # ADMINISTRATION
            'admin_dashboard', 'admin_profils_liste', 'admin_profils_creer', 'admin_profils_modifier',
            'admin_profils_supprimer', 'admin_utilisateurs', 'admin_imprimante_dashboard', 'admin_imprimante_config',
        ]
        
        # Activer toutes les permissions pour Admin
        for perm in permissions_list:
            all_permissions[perm] = True
        
        # Créer le profil Admin
        admin_profile = Profile(
            name='Admin',
            description='Profil administrateur avec accès total à tous les modules',
            is_active=True,
            permissions=all_permissions,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.session.add(admin_profile)
        db.session.commit()
        
        print(f"✅ Profil Admin créé avec succès !")
        print(f"   - {len(all_permissions)} permissions activées")
        
        # Assigner le profil Admin à tous les utilisateurs avec role='admin'
        admin_users = User.query.filter_by(role='admin').all()
        if admin_users:
            for user in admin_users:
                user.profile_id = admin_profile.id
            db.session.commit()
            print(f"✅ {len(admin_users)} utilisateur(s) admin assigné(s) au profil Admin")

if __name__ == '__main__':
    create_admin_profile()

