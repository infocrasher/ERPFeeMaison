# Référence Routes & Modèles – ERP Fée Maison

Ce document synthétise, depuis le code actuel, les blueprints, préfixes d’URL et noms d’endpoints (pour `url_for`), ainsi que la répartition des modèles. Objectif: éviter toute supposition et fiabiliser les liens.

## Conventions d’utilisation
- Utiliser `url_for('nom_blueprint.nom_endpoint', **params)` dans les vues/templates.
- Les chemins finaux = préfixe d’enregistrement + préfixe du blueprint + chemin de la route.
- Les noms d’endpoints = nom de fonction décorée par `@<blueprint>.route` (aucun `endpoint=` personnalisé détecté).

Exemples rapides:
- `url_for('auth.login')` → `/auth/login`
- `url_for('orders.view_order', order_id=123)` → `/admin/orders/123`
- `url_for('dashboard_routes.daily_dashboard')` → `/dashboards/daily`

---

## Blueprints, préfixes et routes

Chaque module indique: blueprint, préfixes et endpoints (nom → chemin relatif). Le chemin final est obtenu via `url_for`.

### main
- Blueprint: `main`
- Préfixe enregistrement: none
- Endpoints:
  - `main.hello_world`: `/`, `/home`
  - `main.dashboard`: `/dashboard`
  - `main.dashboard_concepts_index`: `/dashboard/concepts`
  - `main.dashboard_concept1|2|3`: `/dashboard/concept1|2|3`

### auth
- Blueprint: `auth`
- Préfixe enregistrement: `/auth`
- Endpoints:
  - `auth.login`: `/login`
  - `auth.logout`: `/logout`
  - `auth.account`: `/account`

### products
- Blueprint: `products`
- Préfixe enregistrement: `/admin/products`
- Endpoints:
  - `products.list_categories`: `/categories`
  - `products.new_category`: `/category/new`
  - `products.edit_category`: `/category/<int:category_id>/edit`
  - `products.delete_category`: `/category/<int:category_id>/delete`
  - `products.list_products`: `/`
  - `products.view_product`: `/<int:product_id>`
  - `products.new_product`: `/new`
  - `products.edit_product`: `/<int:product_id>/edit`
  - `products.delete_product`: `/<int:product_id>/delete`
  - `products.autocomplete_products`: `/autocomplete`

### orders (CRUD & actions)
- Blueprint: `orders`
- Préfixe enregistrement: `/admin/orders`
- Endpoints:
  - `orders.new_customer_order`: `/customer/new`
  - `orders.new_production_order`: `/production/new`
  - `orders.list_orders`: `/`
  - `orders.list_customer_orders`: `/customer`
  - `orders.list_production_orders`: `/production`
  - `orders.api_products`: `/api/products`
  - `orders.new_order`: `/new`
  - `orders.view_order`: `/<int:order_id>`
  - `orders.edit_order`: `/<int:order_id>/edit`
  - `orders.edit_order_status`: `/<int:order_id>/edit_status`
  - `orders.orders_calendar`: `/calendar`
  - `orders.pay_order`: `/<int:order_id>/pay`
  - `orders.assign_deliveryman`: `/<int:order_id>/assign-deliveryman`
  - `orders.report_order_issue`: `/<int:order_id>/report-issue`
  - `orders.resolve_order_issue`: `/<int:order_id>/resolve-issue/<int:issue_id>`

### orders – status (changement de statuts)
- Blueprint: `status`
- Préfixe enregistrement: `/orders`
- Endpoints:
  - `status.change_status_to_ready`: `/<int:order_id>/change-status-to-ready`
  - `status.change_status_to_delivered`: `/<int:order_id>/change-status-to-delivered`
  - `status.select_employees_for_status_change`: `/<int:order_id>/select-employees/<string:new_status>`
  - `status.manual_status_change`: `/<int:order_id>/manual-status-change`
  - `status.get_active_employees`: `/api/active-employees`

### dashboards (module unifié)
- Blueprint principal: `dashboards` (préfixe dans le blueprint: `/dashboards`)
- Sous-blueprints pages `dashboard_routes`:
  - `dashboard_routes.daily_dashboard`: `/daily`
  - `dashboard_routes.monthly_dashboard`: `/monthly`
- Sous-blueprints API `dashboard_api`:
  - `dashboard_api.daily_production`: `/daily/production`
  - `dashboard_api.daily_stock`: `/daily/stock`
  - `dashboard_api.daily_sales`: `/daily/sales`
  - `dashboard_api.daily_employees`: `/daily/employees`
  - `dashboard_api.monthly_overview`: `/monthly/overview`
  - `dashboard_api.monthly_revenue_trend`: `/monthly/revenue-trend`
  - `dashboard_api.monthly_product_performance`: `/monthly/product-performance`
  - `dashboard_api.monthly_employee_performance`: `/monthly/employee-performance`
  - `dashboard_api.refresh_dashboard`: `/refresh`
  - `dashboard_api.export_monthly_dashboard`: `/export/monthly`

### dashboards “métier” (app.orders.dashboard_routes)
- Blueprint: `dashboard`
- Préfixe enregistrement: `/dashboard`
- Endpoints:
  - `dashboard.production_dashboard`: `/production`
  - `dashboard.shop_dashboard`: `/shop`
  - `dashboard.ingredients_alerts`: `/ingredients-alerts`
  - `dashboard.admin_dashboard`: `/admin`
  - `dashboard.sales_dashboard`: `/sales`
  - `dashboard.orders_stats_api`: `/api/orders-stats`

### recipes
- Blueprint: `recipes`
- Préfixes: blueprint `/admin/recipes` + enregistrement `/admin/recipes` (double; voir note)
- Endpoints:
  - `recipes.list_recipes`: `/`
  - `recipes.view_recipe`: `/<int:recipe_id>`
  - `recipes.new_recipe`: `/new`
  - `recipes.edit_recipe`: `/<int:recipe_id>/edit`
  - `recipes.delete_recipe`: `/<int:recipe_id>/delete`
  - `recipes.api_ingredients_search`: `/api/ingredients/search`

### stock
- Blueprint: `stock`
- Préfixe enregistrement: `/admin/stock`
- Endpoints:
  - `stock.overview`: `/overview`
  - `stock.quick_entry`: `/quick_entry`
  - `stock.adjustment`: `/adjustment`
  - `stock.dashboard_magasin|local|comptoir|consommables`: `/dashboard/magasin|local|comptoir|consommables`
  - `stock.transfers_list`: `/transfers`
  - `stock.create_transfer`: `/transfers/create`
  - `stock.approve_transfer`: `/transfers/<int:transfer_id>/approve`
  - `stock.complete_transfer`: `/transfers/<int:transfer_id>/complete`
  - `stock.api_stock_levels`: `/api/stock_levels/<int:product_id>`
  - `stock.api_movements_history`: `/api/movements_history/<int:product_id>`

### purchases
- Blueprint: `purchases`
- Préfixe enregistrement: `/admin/purchases`
- Endpoints:
  - `purchases.list_purchases`: `/`
  - `purchases.new_purchase`: `/new`
  - `purchases.view_purchase`: `/<int:id>`
  - `purchases.mark_as_paid`: `/<int:id>/mark_paid`
  - `purchases.mark_as_unpaid`: `/<int:id>/mark_unpaid`
  - `purchases.cancel_purchase`: `/<int:id>/cancel`
  - `purchases.edit_purchase`: `/<int:id>/edit`
  - `purchases.api_products_search`: `/api/products_search`
  - `purchases.api_pending_count`: `/api/pending_count`
  - `purchases.api_product_units`: `/api/products/<int:product_id>/units`
  - `purchases.test_stock_update`: `/test_stock_update`

### accounting
- Blueprint: `accounting`
- Préfixe dans le blueprint: `/admin/accounting`
- Endpoints principaux (extraits):
  - `accounting.dashboard`: `/`
  - Comptes: `list_accounts`, `new_account`, `view_account`, `edit_account`, `delete_account` → `/accounts[...]`
  - Journaux: `list_journals`, `new_journal`, `view_journal`, `edit_journal`, `delete_journal` → `/journals[...]`
  - Écritures: `list_entries`, `new_entry`, `view_entry`, `edit_entry`, `delete_entry`, `validate_entry` → `/entries[...]`
  - Exercices/Periods: `list_fiscal_years`, `new_fiscal_year`, `list_periods`, `new_period`, `edit_period`, `close_period`
  - Dépenses/Trésorerie: `list_expenses`, `new_expense`, `edit_expense`, `delete_expense`, `set_initial_balances`, `adjust_cash`, `adjust_bank`
  - Rapports: `reports`, `trial_balance`, `profit_loss`
  - API: `api_accounts`

### sales
- Blueprint: `sales`
- Préfixes: blueprint `/sales` + enregistrement `/sales` (double; voir note)
- Endpoints:
  - POS/ventes: `sales.pos_interface`: `/pos`, `sales.get_products`: `/api/products`, `sales.complete_sale`: `/api/complete-sale`, `sales.process_sale`: `/pos/checkout`
  - Historique/rapports: `sales.sales_history`: `/history`, `sales.sales_reports`: `/reports`
  - Caisse: `open_cash_register`, `close_cash_register`, `new_cash_movement`, `list_cash_sessions`, `list_cash_movements`, `cash_status`, `list_delivery_debts`, `pay_delivery_debt`, `cashout` → `/cash/...`

### employees
- Blueprint: `employees`
- Préfixe enregistrement: `/employees`
- Endpoints principaux: `list_employees`, `new_employee`, `view_employee`, `edit_employee`, `toggle_employee_status`
- Pointage: `employee_attendance`, `attendance_dashboard`, `live_attendance`, `manual_attendance`
- API pointage: `api_attendance_today`, `api_employee_attendance`
- Paie: `payroll_dashboard`, `employee_analytics`, `manage_work_hours`, `calculate_payroll`, `view_payroll`, `generate_payslips`, `payroll_period_summary`

### deliverymen
- Blueprint: `deliverymen`
- Préfixe enregistrement: `/admin`
- Endpoints: `list_deliverymen`, `new_deliveryman`, `edit_deliveryman`, `delete_deliveryman`

### admin
- Blueprint: `admin`
- Préfixe enregistrement: `/admin`
- Endpoints: `admin.dashboard`: `/dashboard`

### zkteco
- Blueprint: `zkteco`
- Préfixe enregistrement: `/zkteco`
- Endpoints: `zkteco.root`: `/`, `zkteco.ping`: `/api/ping`, `zkteco.attendance`: `/api/attendance`, `zkteco.employees`: `/api/employees`, `zkteco.test_attendance`: `/api/test-attendance`

### b2b
- Blueprint: `b2b`
- Préfixe enregistrement: `/admin/b2b`
- Clients: `list_clients`, `new_client`, `edit_client`, `view_client`
- Commandes: `list_orders`, `new_order`, `view_order`, `edit_order`, `change_order_status`
- Factures: `list_invoices`, `new_invoice`, `view_invoice`, `edit_invoice`, `change_invoice_status`, `export_invoice_pdf`, `send_invoice_email`
- API: `api_clients`, `api_products`

---

## Répartition des modèles

### Modèles centraux (racine `models.py`)
- Auth/Users: `User`
- Catalogue: `Category`, `Product`, `Unit`
- Recettes: `Recipe`, `RecipeIngredient`
- Commandes: `Order`, `OrderItem`
- Livraison: `DeliveryDebt`
- B2B: `B2BClient`, `B2BOrder`, `B2BOrderItem`, `Invoice`, `InvoiceItem` + table `invoice_orders`

Import type:
```python
from models import Product, Category, Recipe, RecipeIngredient, Order, OrderItem, Unit, User, DeliveryDebt
```

### Modèles par module
- Ventes/Caisse (`app/sales/models.py`): `CashRegisterSession`, `CashMovement`
- Employés/RH (`app/employees/models.py`): `Employee`, `AttendanceRecord`, `AttendanceSummary`, `AttendanceException`, `WorkHours`, `PayrollPeriod`, `PayrollEntry`, `PayrollCalculation`, `OrderIssue`, `AbsenceRecord` + table `order_employees`
- Comptabilité (`app/accounting/models.py`): `Account`, `Journal`, `JournalEntry`, `JournalEntryLine`, `FiscalYear`
- Livreurs (`app/deliverymen/models.py`): `Deliveryman`
- Achats (`app/purchases/models.py`): `Purchase`, `PurchaseItem` + enums `PurchaseStatus`, `PurchaseUrgency`
- Stock (`app/stock/models.py`): `StockMovement`, `StockTransfer`, `StockTransferLine` + enums `StockMovementType`, `StockLocationType`, `TransferStatus`

---

## Notes techniques
- Préfixes « doubles » repérés:
  - `recipes`: préfixe dans le blueprint ET lors de l’enregistrement.
  - `sales`: même situation avec `/sales`.
- Impact: `url_for(...)` reste la source de vérité. Toujours générer les URLs via `url_for`.

---

## Exemples `url_for`
```jinja
<a href="{{ url_for('products.list_products') }}">Produits</a>
<a href="{{ url_for('orders.view_order', order_id=order.id) }}">Voir commande</a>
<a href="{{ url_for('dashboard_routes.daily_dashboard') }}">Dashboard journalier</a>
<a href="{{ url_for('sales.cash_status') }}">Caisse</a>
<a href="{{ url_for('accounting.trial_balance') }}">Balance générale</a>
<a href="{{ url_for('employees.view_employee', employee_id=e.id) }}">Employé</a>
```

—

Dernière génération: basée sur le code chargé au moment de l’écriture.









