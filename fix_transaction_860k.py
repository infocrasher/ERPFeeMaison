from app import create_app, db
from app.accounting.models import JournalEntryLine, Account, AccountType, AccountNature

app = create_app()

with app.app_context():
    print("🔧 Démarrage de la correction de la transaction 860k...")
    
    # 1. Récupérer la ligne fautive
    line_id = 762
    line = JournalEntryLine.query.get(line_id)
    
    if not line:
        print(f"❌ Erreur : La ligne d'écriture {line_id} est introuvable.")
        exit(1)
        
    print(f"✅ Ligne trouvée : {line.description} | Montant : {line.debit_amount}")
    print(f"Compte actuel : {line.account.code} - {line.account.name} (Type : {line.account.account_type.value})")
    
    # 2. Vérifier/Créer le compte de destination (119 - Report à nouveau débiteur)
    # C'est un compte de "Capitaux Propres" qui stocke les ajustements passés sans impacter le résultat du mois
    target_code = '119'
    target_account = Account.query.filter_by(code=target_code).first()
    
    if not target_account:
        print(f"creation du compte {target_code}...")
        target_account = Account(
            code=target_code,
            name="Report à Nouveau (Ajustements)",
            account_type=AccountType.CLASSE_1, # Type correct pour les capitaux (Classe 1)
            account_nature=AccountNature.CREDIT, # Le report à nouveau créditeur (ou débiteur selon sens, ici on le veut Passif/Capitaux donc c'est une ressource) 
            # Note: Le 119 est débiteur s'il est négatif, mais structurellement c'est un compte de passif.
            # Pour simplifier, on le met en CREDIT comme les autres capitaux, le solde ajustera.
            is_active=True
        )
        db.session.add(target_account)
        db.session.flush()
    
    # 3. Effectuer la modification
    print(f"🔄 Reclassification vers : {target_account.code} - {target_account.name}")
    line.account_id = target_account.id
    
    try:
        db.session.commit()
        print("✅ SUCCÈS : L'écriture a été déplacée vers le Bilan (Classe 1).")
        print("📉 Elle n'apparaîtra plus dans les 'Charges' du mois.")
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERREUR : {e}")
