import sys
import os
from datetime import datetime

# Ajouter le chemin du projet pour l'import de l'app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.sales.models import CashMovement
from extensions import db

def lister_cashouts(date_debut_str="2025-12-20"):
    app = create_app()
    with app.app_context():
        try:
            date_debut = datetime.strptime(date_debut_str, "%Y-%m-%d")
            
            # Rechercher les mouvements de type 'sortie' (cash out)
            # On vérifie les types courants : 'sortie', 'out'
            cashouts = CashMovement.query.filter(
                CashMovement.created_at >= date_debut,
                CashMovement.type.in_(['sortie', 'out'])
            ).order_by(CashMovement.created_at.asc()).all()

            print(f"\n{'='*80}")
            print(f"💰 LISTE DES CASHOUTS (SORTIES) DEPUIS LE {date_debut_str}")
            print(f"{'='*80}")
            print(f"{'Date':<20} | {'Montant':<12} | {'Raison':<25} | {'Notes'}")
            print(f"{'-'*20}-+-{'-'*12}-+-{'-'*25}-+-{'-'*20}")

            total_amount = 0
            for move in cashouts:
                date_str = move.created_at.strftime("%d/%m/%Y %H:%M")
                amount = f"{move.amount:,.2f} DA"
                reason = (move.reason[:22] + '...') if move.reason and len(move.reason) > 25 else (move.reason or 'N/A')
                notes = move.notes or ''
                
                print(f"{date_str:<20} | {amount:<12} | {reason:<25} | {notes}")
                total_amount += move.amount

            print(f"{'-'*80}")
            print(f"{'TOTAL DES SORTIES':<20} | {total_amount:,.2f} DA")
            print(f"{'='*80}\n")

        except ValueError:
            print("❌ Format de date invalide. Utilisez AAAA-MM-JJ (ex: 2025-12-20)")
        except Exception as e:
            print(f"❌ Une erreur est survenue : {e}")

if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else "2025-12-20"
    lister_cashouts(date_arg)

