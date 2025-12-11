
from app import create_app
from extensions import db, migrate
from flask_migrate import stamp
import os

# Force usage of SQLite config
# We manually override the config to be sure
os.environ['FLASK_ENV'] = 'sqlite_dev'

flask_app = create_app('sqlite_dev')

# Import models to register them with SQLAlchemy
with flask_app.app_context():
    import models
    import app.accounting.models
    import app.purchases.models
    import app.sales.models
    import app.inventory.models
    import app.employees.models

with flask_app.app_context():
    print("Creating database tables...")
    db.create_all()
    print("Tables created.")
    
    print("Stamping database as 'head'...")
    stamp()
    print("Database stamped. Ready to use.")
