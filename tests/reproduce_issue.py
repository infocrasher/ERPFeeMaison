
import pytest
from app import db
from models import Product, Recipe, RecipeIngredient, Order, OrderItem, Category
from app.employees.models import Employee

def test_stock_decrement_customer_order(admin_client, admin_user):
    """
    Test case to reproduce the issue where stock_comptoir is incorrectly decremented
    when a customer order is received (status changed to ready_at_shop).
    """
    # 1. Setup Data
    # Create Category
    category = Category(name="Test Category")
    db.session.add(category)
    db.session.commit()

    # Create Finished Product
    finished_product = Product(
        name="Finished Product",
        product_type="finished_product",
        unit="pièce",
        price=100.0,
        cost_price=50.0,
        stock_comptoir=20.0,  # Initial stock
        category=category
    )
    db.session.add(finished_product)
    
    # Create Ingredient Product
    ingredient = Product(
        name="Ingredient",
        product_type="raw_material",
        unit="kg",
        cost_price=10.0,
        stock_ingredients_magasin=100.0,
        category=category
    )
    db.session.add(ingredient)
    db.session.commit()

    # Create Recipe
    recipe = Recipe(
        name="Test Recipe",
        product_id=finished_product.id,
        yield_quantity=1,
        production_location="ingredients_magasin"
    )
    db.session.add(recipe)
    db.session.commit()

    # Add Ingredient to Recipe
    recipe_ingredient = RecipeIngredient(
        recipe_id=recipe.id,
        product_id=ingredient.id,
        quantity_needed=0.1, # 100g per unit
        unit="kg"
    )
    db.session.add(recipe_ingredient)
    db.session.commit()

    # Create Employee (needed for production)
    employee = Employee(name="Test Baker", role="production", is_active=True)
    db.session.add(employee)
    db.session.commit()

    # Create Customer Order
    order = Order(
        user_id=admin_user.id,
        order_type='customer_order',
        status='in_production',
        due_date=db.func.now(),
        delivery_option='pickup'
    )
    db.session.add(order)
    db.session.commit()

    # Add Item to Order
    order_item = OrderItem(
        order_id=order.id,
        product_id=finished_product.id,
        quantity=5.0,
        unit_price=100.0
    )
    db.session.add(order_item)
    db.session.commit()

    # Verify Initial State
    assert finished_product.stock_comptoir == 20.0
    print(f"Initial Stock Comptoir: {finished_product.stock_comptoir}")

    # 2. Execute Action: Change status to ready_at_shop
    # We simulate the POST request to the route
    # Flask test client handles list values if passed as a list
    response = admin_client.post(
        f'/orders/{order.id}/change-status-to-ready',
        data={
            'employee_ids[]': str(employee.id)
        },
        follow_redirects=False
    )

    # 3. Verify Result
    # assert response.status_code == 302 # Redirects on success
    
    # Refresh product from DB
    db.session.refresh(finished_product)
    
    print(f"Final Stock Comptoir: {finished_product.stock_comptoir}")
    
    # The bug is that it becomes 15.0 (20 - 5)
    # The expected behavior is that it remains 20.0
    if finished_product.stock_comptoir == 15.0:
        pytest.fail("BUG REPRODUCED: Stock comptoir was decremented by order quantity!")
    
    assert finished_product.stock_comptoir == 20.0

def test_stock_decrement_circular_dependency(admin_client, admin_user):
    """
    Test case where the ingredient IS the finished product (circular dependency).
    This might happen if the recipe is misconfigured.
    """
    # 1. Setup Data
    category = Category(name="Test Category 2")
    db.session.add(category)
    db.session.commit()

    # Create Finished Product
    finished_product = Product(
        name="Recursive Product",
        product_type="finished_product",
        unit="pièce",
        price=100.0,
        cost_price=50.0,
        stock_comptoir=20.0,
        category=category
    )
    db.session.add(finished_product)
    db.session.commit()

    # Create Recipe
    recipe = Recipe(
        name="Recursive Recipe",
        product_id=finished_product.id,
        yield_quantity=1,
        production_location="stock_comptoir" # Suspicious location
    )
    db.session.add(recipe)
    db.session.commit()

    # Add ITSELF as Ingredient
    recipe_ingredient = RecipeIngredient(
        recipe_id=recipe.id,
        product_id=finished_product.id,
        quantity_needed=1, 
        unit="pièce"
    )
    db.session.add(recipe_ingredient)
    db.session.commit()

    employee = Employee(name="Test Baker 2", role="production", is_active=True)
    db.session.add(employee)
    db.session.commit()

    order = Order(
        user_id=admin_user.id,
        order_type='customer_order',
        status='in_production',
        due_date=db.func.now(),
        delivery_option='pickup'
    )
    db.session.add(order)
    db.session.commit()

    order_item = OrderItem(
        order_id=order.id,
        product_id=finished_product.id,
        quantity=5.0,
        unit_price=100.0
    )
    db.session.add(order_item)
    db.session.commit()

    # 2. Execute Action
    response = admin_client.post(
        f'/orders/{order.id}/change-status-to-ready',
        data={
            'employee_ids[]': str(employee.id)
        },
        follow_redirects=False
    )

    # 3. Verify Result
    db.session.refresh(finished_product)
    print(f"Recursive Product Stock Comptoir: {finished_product.stock_comptoir}")
    
    # In this case, we EXPECT it to be decremented because it's an ingredient
    # BUT the code has a warning/check for this. Let's see if it prevents it.
    # If it becomes 15, then the check failed or was just a warning.
    
    # If the code logic (lines 93-96 in status_routes.py) executes, it WILL decrement.
    # So if this test results in 15, it confirms that circular dependency + bad location = bug.
