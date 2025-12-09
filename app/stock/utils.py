"""
Utilitaires pour le calcul de la valeur stock
"""
from models import Product


def calculate_total_stock_value():
    """
    Calcule la valeur totale du stock EXACTEMENT comme dans stock overview.
    Filtre par type de produit pour chaque emplacement.
    
    Returns:
        float: Valeur totale du stock en DA
    """
    products = Product.query.all()
    
    # Même logique que stock overview
    location_configs = [
        {
            'product_type': 'ingredient',
            'value_attr': 'valeur_stock_ingredients_magasin'
        },
        {
            'product_type': 'ingredient',
            'value_attr': 'valeur_stock_ingredients_local'
        },
        {
            'product_type': 'finished',
            'value_attr': 'valeur_stock_comptoir'
        },
        {
            'product_type': 'consommable',
            'value_attr': 'valeur_stock_consommables'
        }
    ]
    
    total_value = 0.0
    for config in location_configs:
        filtered_products = [p for p in products if p.product_type == config['product_type']]
        value_total = sum(float(getattr(p, config['value_attr']) or 0) for p in filtered_products)
        total_value += value_total
    
    return total_value

