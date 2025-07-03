from extensions import db

class Deliveryman(db.Model):
    __tablename__ = 'deliverymen'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    # Ajoute d'autres champs si besoin (adresse, etc.)

    def __repr__(self):
        return f"<Deliveryman {self.name}>" 