import os
from flask import Flask, url_for, render_template
from config import config_by_name
from extensions import db, migrate, login_manager, csrf
from datetime import datetime
from flask_wtf.csrf import generate_csrf

def create_app(config_name=None):
    app = Flask(__name__)

    if config_name is None:
        config_name = os.environ.get('FLASK_ENV') or 'default'
    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."

    from models import User
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    # --- PROCESSEURS DE CONTEXTE POUR LES VARIABLES GLOBALES ---
    @app.context_processor
    def inject_global_variables():
        """
        Injecte des variables globales dans tous les templates
        """
        try:
            # Variables toujours disponibles
            base_vars = {
                # Tokens CSRF
                'csrf_token': generate_csrf,
                'manual_csrf_token': generate_csrf,
                # Date courante
                'current_year': datetime.now().year,
            }
            
            # Variables nécessitant un context d'application
            with app.app_context():
                from models import Product
                
                # Statistiques pour dashboard (avec gestion d'erreur)
                try:
                    total_products = Product.query.count()
                    low_stock = Product.query.filter(Product.quantity_in_stock <= 5).count()
                    out_of_stock = Product.query.filter(Product.quantity_in_stock <= 0).count()
                    
                    base_vars.update({
                        'total_products_count': total_products,
                        'low_stock_products': low_stock,
                        'out_of_stock_products': out_of_stock,
                    })
                except Exception as e:
                    # En cas d'erreur DB, fournir des valeurs par défaut
                    app.logger.warning(f"Erreur context processor statistiques: {e}")
                    base_vars.update({
                        'total_products_count': 0,
                        'low_stock_products': 0,
                        'out_of_stock_products': 0,
                    })
            
            return base_vars
            
        except Exception as e:
            # Fallback minimal en cas d'erreur totale
            app.logger.error(f"Erreur context processor: {e}")
            return {
                'csrf_token': generate_csrf,
                'manual_csrf_token': generate_csrf,
                'current_year': datetime.now().year,
                'total_products_count': 0,
                'low_stock_products': 0,
                'out_of_stock_products': 0,
            }
    
    @app.template_filter('nl2br')
    def nl2br_filter(text):
        """Convertit les retours à la ligne en <br>"""
        if not text:
            return text
        from markupsafe import Markup
        return Markup(text.replace('\n', '<br>'))
    
    @app.template_filter('currency')
    def currency_filter(amount):
        """Formate un montant en devise"""
        if amount is None:
            return "0,00 DA"
        try:
            return f"{float(amount):,.2f} DA".replace(',', ' ')
        except (ValueError, TypeError):
            return "0,00 DA"
    
    @app.template_filter('format_number')
    def format_number_filter(value):
        """Formate un nombre avec des espaces comme séparateurs de milliers (format français)"""
        if value is None:
            return "0"
        try:
            # Convertir en entier ou float
            num = float(value)
            # Formater avec virgule comme séparateur de milliers
            formatted = f"{num:,.0f}".replace(',', ' ')
            return formatted
        except (ValueError, TypeError):
            return "0"
    
    @app.template_filter('stock_status')
    def stock_status_filter(quantity):
        """Retourne une classe CSS selon le niveau de stock"""
        try:
            qty = float(quantity) if quantity is not None else 0
            if qty <= 0:
                return 'text-danger'  # Rouge pour rupture
            elif qty <= 5:
                return 'text-warning'  # Orange pour stock bas
            else:
                return 'text-success'  # Vert pour stock OK
        except (ValueError, TypeError):
            return 'text-muted'
    
    # Filtres pour les factures PDF WeasyPrint
    from app.utils.filters import format_dzd, date_fr, montant_en_lettres_dzd, format_phone, truncate_text, capitalize_first
    app.jinja_env.filters['dzd'] = format_dzd
    app.jinja_env.filters['date_fr'] = date_fr
    app.jinja_env.filters['lettres_dzd'] = montant_en_lettres_dzd
    app.jinja_env.filters['format_phone'] = format_phone
    app.jinja_env.filters['truncate'] = truncate_text
    app.jinja_env.filters['capitalize_first'] = capitalize_first
    
    # Enregistrement des Blueprints
    from app.main.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.auth.routes import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from app.products.routes import products as products_blueprint
    app.register_blueprint(products_blueprint, url_prefix='/admin/products')

    from app.orders.routes import orders as orders_blueprint
    app.register_blueprint(orders_blueprint, url_prefix='/admin/orders')

    from app.recipes.routes import recipes as recipes_blueprint
    app.register_blueprint(recipes_blueprint, url_prefix='/admin/recipes')
    
    # ✅ CORRECTION : Import correct du blueprint stock
    from app.stock import bp as stock_blueprint
    app.register_blueprint(stock_blueprint, url_prefix='/admin/stock')

    from app.admin.routes import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    
    # ✅ AJOUT : Blueprint printer admin pour la gestion de l'imprimante
    from app.admin.printer_routes import printer_admin
    app.register_blueprint(printer_admin)
    
    # ✅ AJOUT : Blueprint profiles admin pour la gestion des profils
    from app.admin.profiles_routes import profiles_admin
    app.register_blueprint(profiles_admin, url_prefix='/admin')
    
    # ✅ AJOUT : Blueprint users admin pour la gestion des utilisateurs
    from app.admin.users_routes import users_admin
    app.register_blueprint(users_admin, url_prefix='/admin')

    # ✅ CORRECTION : Import correct du blueprint purchases
    from app.purchases import bp as purchases_blueprint
    app.register_blueprint(purchases_blueprint, url_prefix='/admin/purchases')

    # Blueprints spéciaux (existants)
    from app.routes import dashboard as unified_dashboard_routes  # noqa: F401
    from app.orders.dashboard_routes import dashboard_bp
    from app.delivery_zones import delivery_zones_bp
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(delivery_zones_bp)

    from app.orders.status_routes import status_bp
    app.register_blueprint(status_bp, url_prefix='/orders')

    from app.employees.routes import employees_bp
    app.register_blueprint(employees_bp, url_prefix='/employees')

    # ✅ AJOUT : Blueprint deliverymen pour la gestion des livreurs
    from app.deliverymen.routes import deliverymen_bp
    app.register_blueprint(deliverymen_bp, url_prefix='/admin')

    # ✅ AJOUT : Blueprint sales pour le module de vente
    from app.sales.routes import sales as sales_blueprint
    app.register_blueprint(sales_blueprint, url_prefix='/sales')
    
    # ✅ AJOUT : Import des modèles sales pour Flask-Migrate
    from app.sales import models as sales_models
    
    # ✅ AJOUT : Import des modèles deliverymen pour Flask-Migrate
    from app.deliverymen import models as deliverymen_models
    
    # ✅ AJOUT : Blueprint accounting pour la comptabilité
    from app.accounting import bp as accounting_blueprint
    # Import des routes après la création du blueprint
    from app.accounting import routes as accounting_routes
    
    # ✅ AJOUT : Module dashboards unifié
    from app.dashboards import dashboards_bp
    app.register_blueprint(dashboards_bp)
    app.register_blueprint(accounting_blueprint)
    
    # ✅ AJOUT : Import des modèles accounting pour Flask-Migrate
    from app.accounting import models as accounting_models

    # ✅ AJOUT : Blueprint ZKTeco pour la pointeuse
    from app.zkteco import zkteco as zkteco_blueprint
    app.register_blueprint(zkteco_blueprint, url_prefix='/zkteco')
    
    # ✅ AJOUT : Blueprint B2B pour la facturation B2B
    from app.b2b import b2b as b2b_blueprint
    app.register_blueprint(b2b_blueprint, url_prefix='/admin/b2b')
    


    # Gestionnaire d'erreurs personnalisés
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Commande CLI pour créer un admin
    @app.cli.command("create-admin")
    def create_admin():
        """Crée un utilisateur administrateur"""
        from models import User
        
        if User.query.filter_by(email="admin@example.com").first():
            print("L'utilisateur admin existe déjà.")
            return
        
        admin_user = User(username="admin", email="admin@example.com", role='admin')
        admin_user.set_password("password123")
        db.session.add(admin_user)
        db.session.commit()
        print("Utilisateur admin créé avec succès.")
        print("Email: admin@example.com")
        print("Mot de passe: password123")

    # Commande CLI pour les statistiques
    @app.cli.command("stats")
    def show_stats():
        """Affiche les statistiques de l'application"""
        from models import User, Product, Recipe, Order
        from app.employees.models import Employee
        
        print("=== STATISTIQUES FÉE MAISON ===")
        print(f"Utilisateurs: {User.query.count()}")
        print(f"Produits: {Product.query.count()}")
        print(f"Recettes: {Recipe.query.count()}")
        print(f"Commandes: {Order.query.count()}")
        print(f"Employés: {Employee.query.count()}")
        
        # Statistiques détaillées produits
        ingredients = Product.query.filter_by(product_type='ingredient').count()
        finished = Product.query.filter_by(product_type='finished').count()
        low_stock = Product.query.filter(Product.quantity_in_stock <= 5).count()
        
        print(f"\nProduits - Ingrédients: {ingredients}")
        print(f"Produits - Finis: {finished}")
        print(f"Produits - Stock bas: {low_stock}")

    # Initialiser le service d'impression
    try:
        from app.services.printer_service import get_printer_service
        printer_service = get_printer_service()
        print(f"\n🖨️ Service d'impression initialisé (Activé: {printer_service.config.enabled})")
    except Exception as e:
        print(f"\n⚠️ Erreur initialisation service impression: {e}")

    # Enregistrer les nouveaux blueprints clients et fournisseurs
    from app.suppliers import suppliers
    from app.customers import customers
    app.register_blueprint(suppliers)
    app.register_blueprint(customers)
    print("📋 Modules Clients et Fournisseurs enregistrés")

    # ✅ AJOUT : Blueprint inventory pour la gestion d'inventaire
    from app.inventory import inventory
    app.register_blueprint(inventory, url_prefix='/admin/inventory')
    
    # ✅ AJOUT : Import des modèles inventory pour Flask-Migrate
    from app.inventory import models as inventory_models
    print("📋 Module Inventaire enregistré")
    
    # ✅ AJOUT : Blueprint consumables pour la gestion des consommables
    from app.consumables import consumables
    app.register_blueprint(consumables, url_prefix='/admin/consumables')
    
    # ✅ AJOUT : Import des modèles consumables pour Flask-Migrate
    from app.consumables import models as consumables_models
    print("📦 Module Consommables enregistré")
    
    # ✅ AJOUT : Blueprint reports pour la génération de rapports
    from app.reports import reports
    app.register_blueprint(reports, url_prefix='/admin/reports')
    print("📊 Module Rapports enregistré")
    
    # ⏸️ MODULE AI DÉSACTIVÉ TEMPORAIREMENT (ralentit le dashboard)
    # Pour réactiver : décommenter les 3 lignes ci-dessous
    # from app.ai import ai
    # app.register_blueprint(ai, url_prefix='/ai')
    # print("🤖 Module AI enregistré (Prophet + LLM)")
    print("⏸️ Module AI désactivé (performance)")

    return app
