from app import create_app, db
from sqlalchemy import text
import os

app = create_app(os.getenv('FLASK_ENV') or 'default')

with app.app_context():
    try:
        print("Applying manual schema update for order_items reception tracking...")
        
        # Add is_received column
        try:
            db.session.execute(text("ALTER TABLE order_items ADD COLUMN is_received BOOLEAN DEFAULT FALSE NOT NULL"))
            print("✅ Added column is_received")
        except Exception as e:
            print(f"⚠️ Could not add is_received (might exist): {e}")

        # Add received_at column
        try:
            db.session.execute(text("ALTER TABLE order_items ADD COLUMN received_at TIMESTAMP NULL"))
            print("✅ Added column received_at")
        except Exception as e:
            print(f"⚠️ Could not add received_at (might exist): {e}")

        # Add received_by_id column
        try:
            db.session.execute(text("ALTER TABLE order_items ADD COLUMN received_by_id INTEGER NULL"))
            print("✅ Added column received_by_id")
        except Exception as e:
            print(f"⚠️ Could not add received_by_id (might exist): {e}")
            
        # Add foreign key constraint
        try:
            db.session.execute(text("ALTER TABLE order_items ADD CONSTRAINT fk_order_items_received_by FOREIGN KEY (received_by_id) REFERENCES employees(id)"))
            print("✅ Added FK constraint")
        except Exception as e:
            print(f"⚠️ Could not add FK constraint (might exist): {e}")

        db.session.commit()
        print("🎉 Database schema update completed successfully!")
        
    except Exception as e:
        print(f"❌ Error updating database: {e}")
        db.session.rollback()
