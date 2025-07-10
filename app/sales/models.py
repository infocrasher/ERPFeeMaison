from datetime import datetime
from extensions import db

class CashRegisterSession(db.Model):
    __tablename__ = 'cash_register_session'
    id = db.Column(db.Integer, primary_key=True)
    opened_at = db.Column(db.DateTime, default=datetime.utcnow)
    closed_at = db.Column(db.DateTime, nullable=True)
    initial_amount = db.Column(db.Float, nullable=False)
    closing_amount = db.Column(db.Float, nullable=True)
    opened_by_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    closed_by_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    is_open = db.Column(db.Boolean, default=True)
    # Relations
    opened_by = db.relationship('Employee', foreign_keys=[opened_by_id])
    closed_by = db.relationship('Employee', foreign_keys=[closed_by_id])
    movements = db.relationship('CashMovement', backref='session', lazy=True)

class CashMovement(db.Model):
    __tablename__ = 'cash_movement'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('cash_register_session.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(32))  # vente, entrée, sortie, acompte, etc.
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(128))
    notes = db.Column(db.Text, nullable=True)  # Remarques optionnelles
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    employee = db.relationship('Employee') 