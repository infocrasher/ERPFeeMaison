# create_admin.py
from app import create_app, db
from models import User

app = create_app()
with app.app_context():
    if User.query.filter_by(username='admin').first():
        print("L'utilisateur 'admin' existe déjà.")
    else:
        admin_user = User(username='admin', email='admin@example.com', role='admin')
        admin_user.set_password('admin')
        db.session.add(admin_user)
        db.session.commit()
        print("✅ Utilisateur 'admin' créé avec succès. Mot de passe : 'admin'")