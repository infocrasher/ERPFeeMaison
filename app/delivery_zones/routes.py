from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required

from extensions import db
from decorators import admin_required
from app.delivery_zones import delivery_zones_bp


class DeliveryZone(db.Model):
    __tablename__ = 'delivery_zones'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': float(self.price or 0.0),
        }


@delivery_zones_bp.route('/admin/delivery-zones', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_zones():
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        price_str = request.form.get('price') or '0'
        try:
            price = float(price_str)
        except ValueError:
            price = 0.0

        if not name:
            flash("Le nom de la commune est requis.", "danger")
        else:
            existing = DeliveryZone.query.filter_by(name=name).first()
            if existing:
                existing.price = price
                existing.is_active = True
                flash("Commune mise à jour.", "success")
            else:
                zone = DeliveryZone(name=name, price=price)
                db.session.add(zone)
                flash("Commune ajoutée.", "success")
            db.session.commit()
        return redirect(url_for('delivery_zones.manage_zones'))

    zones = DeliveryZone.query.order_by(DeliveryZone.is_active.desc(), DeliveryZone.name.asc()).all()
    return render_template('delivery_zones/manage.html', zones=zones)


@delivery_zones_bp.route('/admin/delivery-zones/<int:zone_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_zone(zone_id):
    zone = DeliveryZone.query.get_or_404(zone_id)
    zone.is_active = not zone.is_active
    db.session.commit()
    flash("Commune mise à jour.", "success")
    return redirect(url_for('delivery_zones.manage_zones'))


@delivery_zones_bp.route('/admin/delivery-zones/api/search')
@login_required
@admin_required
def api_search_zones():
    query = (request.args.get('q') or '').strip()
    q = DeliveryZone.query.filter(DeliveryZone.is_active.is_(True))
    if query:
        like = f"%{query}%"
        q = q.filter(DeliveryZone.name.ilike(like))
    zones = q.order_by(DeliveryZone.name.asc()).limit(20).all()
    return jsonify([z.to_dict() for z in zones])


