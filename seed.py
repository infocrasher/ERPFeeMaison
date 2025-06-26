from app import create_app, db
from models import User, Category, Product, Unit, Recipe, RecipeIngredient
from decimal import Decimal

# Ce script doit être exécuté dans le contexte de l'application Flask
app = create_app()

def seed_data():
    with app.app_context():
        print("Nettoyage des anciennes données...")
        # L'ordre de suppression est important à cause des clés étrangères
        RecipeIngredient.query.delete()
        db.session.commit() # On commit après chaque delete pour être sûr
        
        # On supprime les items des commandes et achats avant les commandes/achats eux-mêmes
        # (Si tu as des OrderItem/PurchaseItem, il faut les supprimer avant Order/Purchase)
        from app.purchases.models import PurchaseItem
        from models import OrderItem
        OrderItem.query.delete()
        PurchaseItem.query.delete()
        db.session.commit()

        Recipe.query.delete()
        Product.query.delete()
        Category.query.delete()
        Unit.query.delete()
        Order.query.delete()

        from app.purchases.models import Purchase
        Purchase.query.delete()

        User.query.delete()
        db.session.commit()
        
        # --- 0. Création de l'utilisateur admin ---
        print("Création du compte administrateur...")
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@example.com',
                role='admin'
            )
            admin_user.set_password('admin') # REMPLACE PAR UN MOT DE PASSE SÉCURISÉ
            db.session.add(admin_user)
            db.session.commit()
            print("-> Utilisateur 'admin' créé avec le mot de passe 'admin'.")
        else:
            print("-> Utilisateur 'admin' existe déjà.")

        # --- 1. Création des Unités de Conditionnement ---
        print("Création des unités de conditionnement...")
        units = [
            # Poids (base g)
            Unit(name='Sac 25kg', base_unit='g', conversion_factor=25000),
            Unit(name='Sac 10kg', base_unit='g', conversion_factor=10000),
            Unit(name='Sachet 1kg', base_unit='g', conversion_factor=1000),
            Unit(name='Sachet 10g', base_unit='g', conversion_factor=10),
            # Volume (base ml)
            Unit(name='Bouteille 1L', base_unit='ml', conversion_factor=1000),
            Unit(name='Bidon 5L', base_unit='ml', conversion_factor=5000),
            # Pièce
            Unit(name='Paquet de 10 pièces', base_unit='pièce', conversion_factor=10),
            Unit(name='Pièce Individuelle', base_unit='pièce', conversion_factor=1),
        ]
        db.session.add_all(units)
        db.session.commit()
        print(f"-> {len(units)} unités créées.")

        # --- 2. Création des Catégories ---
        print("Création des catégories...")
        cat_farine = Category(name='Farines et Semoules')
        cat_epicerie = Category(name='Épicerie')
        cat_produit_fini = Category(name='Produits Finis Salés')
        db.session.add_all([cat_farine, cat_epicerie, cat_produit_fini])
        db.session.commit()
        print("-> 3 catégories créées.")
        
        # --- 3. Création des Produits (Ingrédients et Finis) ---
        print("Création des produits de test...")
        farine = Product(name='Farine T55', product_type='ingredient', unit='g', cost_price=Decimal('0.08'), category=cat_farine)
        huile = Product(name='Huile de Tournesol', product_type='ingredient', unit='ml', cost_price=Decimal('0.12'), category=cat_epicerie)
        levure = Product(name='Levure Chimique', product_type='ingredient', unit='g', cost_price=Decimal('0.6'), category=cat_epicerie)
        galette = Product(name='Galette Kabyle', product_type='finished', unit='pièce', price=Decimal('80.00'), category=cat_produit_fini)
        db.session.add_all([farine, huile, levure, galette])
        db.session.commit()
        print("-> 3 ingrédients et 1 produit fini créés.")

        # --- 4. Création de la Recette ---
        print("Création de la recette pour 'Galette Kabyle'...")
        recette_galette = Recipe(
            name="Recette Galette Kabyle",
            finished_product=galette,
            yield_quantity=10, 
            yield_unit='pièces',
            production_location='ingredients_magasin'
        )
        db.session.add(recette_galette)
        db.session.commit()

        ing_farine = RecipeIngredient(recipe=recette_galette, product=farine, quantity_needed=Decimal('5000.0'), unit='g')
        ing_huile = RecipeIngredient(recipe=recette_galette, product=huile, quantity_needed=Decimal('500.0'), unit='ml')
        ing_levure = RecipeIngredient(recipe=recette_galette, product=levure, quantity_needed=Decimal('20.0'), unit='g')
        db.session.add_all([ing_farine, ing_huile, ing_levure])
        db.session.commit()
        print("-> Recette et ses 3 ingrédients créés et liés.")
        
        print("\n🎉 Seed terminé ! La base de données est propre et prête pour les tests.")

if __name__ == '__main__':
    seed_data()