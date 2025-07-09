# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Order, Product, Recipe  # ✅ CORRECTION : Recipe est dans models.py principal
from app.employees.models import Employee    # ✅ Seul Employee est dans un module séparé
from datetime import datetime, date
from extensions import db

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/home')
def hello_world():
    return render_template('main/home.html', title="Accueil")

@main.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal avec statistiques"""
    
    # Calcul des statistiques pour l'affichage
    today = date.today()
    
    # Compter les commandes d'aujourd'hui
    orders_today = Order.query.filter(
        db.func.date(Order.created_at) == today
    ).count()
    
    # Compter les employés actifs
    employees_count = Employee.query.filter(Employee.is_active == True).count()
    
    # Compter les produits
    products_count = Product.query.count()
    
    # Compter les recettes
    recipes_count = Recipe.query.count()
    
    return render_template('main/dashboard.html', 
                         title="Tableau de Bord",
                         orders_today=orders_today,
                         employees_count=employees_count,
                         products_count=products_count,
                         recipes_count=recipes_count)

# ==========================================
# ROUTES POUR LES CONCEPTS DE DASHBOARD
# ==========================================

@main.route('/dashboard/concepts')
@login_required
def dashboard_concepts_index():
    """Page d'index pour naviguer entre les concepts de dashboard"""
    return render_template('main/dashboard_concepts_index.html', 
                         title="Concepts Dashboard")

@main.route('/dashboard/concept1')
@login_required
def dashboard_concept1():
    """Dashboard Concept 1 - Template pour test"""
    
    # Calcul des statistiques pour l'affichage
    today = date.today()
    
    # KPI de base
    orders_today = Order.query.filter(
        db.func.date(Order.created_at) == today
    ).count()
    
    employees_count = Employee.query.filter(Employee.is_active == True).count()
    products_count = Product.query.count()
    recipes_count = Recipe.query.count()
    
    return render_template('main/dashboard_concept1.html', 
                         title="Dashboard Concept 1",
                         orders_today=orders_today,
                         employees_count=employees_count,
                         products_count=products_count,
                         recipes_count=recipes_count)

@main.route('/dashboard/concept2')
@login_required
def dashboard_concept2():
    """Dashboard Concept 2 - Template pour test"""
    
    # Calcul des statistiques pour l'affichage
    today = date.today()
    
    # KPI de base
    orders_today = Order.query.filter(
        db.func.date(Order.created_at) == today
    ).count()
    
    employees_count = Employee.query.filter(Employee.is_active == True).count()
    products_count = Product.query.count()
    recipes_count = Recipe.query.count()
    
    return render_template('main/dashboard_concept2.html', 
                         title="Dashboard Concept 2",
                         orders_today=orders_today,
                         employees_count=employees_count,
                         products_count=products_count,
                         recipes_count=recipes_count)

@main.route('/dashboard/concept3')
@login_required
def dashboard_concept3():
    """Dashboard Concept 3 - Template pour test"""
    
    # Calcul des statistiques pour l'affichage
    today = date.today()
    
    # KPI de base
    orders_today = Order.query.filter(
        db.func.date(Order.created_at) == today
    ).count()
    
    employees_count = Employee.query.filter(Employee.is_active == True).count()
    products_count = Product.query.count()
    recipes_count = Recipe.query.count()
    
    return render_template('main/dashboard_concept3.html', 
                         title="Dashboard Concept 3",
                         orders_today=orders_today,
                         employees_count=employees_count,
                         products_count=products_count,
                         recipes_count=recipes_count)
