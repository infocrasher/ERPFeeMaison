import os
from flask import Flask, url_for, render_template
from config import config_by_name
from extensions import db, migrate, login_manager
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

    # ✅ CORRECTION : Import correct du blueprint purchases
    from app.purchases import bp as purchases_blueprint
    app.register_blueprint(purchases_blueprint, url_prefix='/admin/purchases')

    # Blueprints spéciaux (existants)
    from app.orders.dashboard_routes import dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

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

    return app
