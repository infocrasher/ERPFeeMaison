#!/usr/bin/env python3
"""
Script pour analyser les erreurs HTTP 400 lors de la finalisation des ventes PDV
"""
import sys
import re
from datetime import datetime, timedelta

def analyser_logs_400(fichier_log=None, heures_recentes=1):
    """
    Analyse les logs pour trouver les erreurs 400 lors de la finalisation des ventes
    
    Args:
        fichier_log: Chemin vers le fichier de log (optionnel)
        heures_recentes: Nombre d'heures à analyser en arrière
    """
    print("=" * 80)
    print("ANALYSE ERREURS 400 - FINALISATION VENTES PDV")
    print("=" * 80)
    print()
    
    # Si un fichier est fourni, l'utiliser
    if fichier_log:
        try:
            with open(fichier_log, 'r', encoding='utf-8') as f:
                lignes = f.readlines()
            print(f"📄 Fichier analysé : {fichier_log}")
            print(f"📊 Total lignes : {len(lignes)}")
        except FileNotFoundError:
            print(f"❌ Fichier non trouvé : {fichier_log}")
            return
        except PermissionError:
            print(f"❌ Permission refusée pour : {fichier_log}")
            print("💡 Essayez avec sudo")
            return
    else:
        print("⚠️  Aucun fichier spécifié. Utilisez --file pour spécifier un fichier de log.")
        print()
        print("Exemples de commandes :")
        print("  sudo journalctl -u erp --since '1 hour ago' --no-pager > /tmp/erp_logs.txt")
        print("  python3 scripts/analyser_erreurs_400_pdv.py --file /tmp/erp_logs.txt")
        print()
        print("  sudo tail -1000 /opt/erp/app/logs/fee_maison.log > /tmp/app_logs.txt")
        print("  python3 scripts/analyser_400_pdv.py --file /tmp/app_logs.txt")
        return
    
    # Filtrer les lignes récentes si nécessaire
    maintenant = datetime.now()
    seuil = maintenant - timedelta(hours=heures_recentes)
    
    erreurs_400 = []
    ventes_complete_sale = []
    autres_erreurs = []
    
    # Patterns à rechercher
    pattern_400 = re.compile(r'400|Bad Request|complete-sale.*400', re.IGNORECASE)
    pattern_complete_sale = re.compile(r'complete.?sale|finalisation.*vente', re.IGNORECASE)
    pattern_erreur = re.compile(r'ERROR|Exception|Traceback|Erreur', re.IGNORECASE)
    
    for i, ligne in enumerate(lignes, 1):
        # Chercher les erreurs 400
        if pattern_400.search(ligne) or ('complete-sale' in ligne.lower() and '400' in ligne):
            erreurs_400.append((i, ligne.strip()))
        
        # Chercher les appels à complete-sale
        if pattern_complete_sale.search(ligne):
            ventes_complete_sale.append((i, ligne.strip()))
        
        # Chercher d'autres erreurs
        if pattern_erreur.search(ligne) and 'complete-sale' in ligne.lower():
            autres_erreurs.append((i, ligne.strip()))
    
    print()
    print("=" * 80)
    print("RÉSULTATS DE L'ANALYSE")
    print("=" * 80)
    print()
    
    # Afficher les erreurs 400
    if erreurs_400:
        print(f"❌ ERREURS HTTP 400 trouvées : {len(erreurs_400)}")
        print("-" * 80)
        for num_ligne, ligne in erreurs_400[:20]:  # Limiter à 20 pour la lisibilité
            print(f"Ligne {num_ligne}: {ligne}")
        if len(erreurs_400) > 20:
            print(f"... et {len(erreurs_400) - 20} autres erreurs 400")
        print()
    else:
        print("✅ Aucune erreur HTTP 400 trouvée dans les logs")
        print()
    
    # Afficher les appels à complete-sale
    if ventes_complete_sale:
        print(f"📋 Appels à complete-sale trouvés : {len(ventes_complete_sale)}")
        print("-" * 80)
        for num_ligne, ligne in ventes_complete_sale[:10]:
            print(f"Ligne {num_ligne}: {ligne[:150]}...")
        print()
    
    # Afficher les autres erreurs
    if autres_erreurs:
        print(f"⚠️  Autres erreurs liées à complete-sale : {len(autres_erreurs)}")
        print("-" * 80)
        for num_ligne, ligne in autres_erreurs[:10]:
            print(f"Ligne {num_ligne}: {ligne[:150]}...")
        print()
    
    # Analyse contextuelle : chercher les lignes autour des erreurs 400
    if erreurs_400:
        print("=" * 80)
        print("CONTEXTE DES ERREURS 400 (lignes avant/après)")
        print("=" * 80)
        print()
        
        for num_ligne, ligne_erreur in erreurs_400[:5]:  # Analyser les 5 premières
            print(f"📍 Erreur à la ligne {num_ligne}:")
            print(f"   {ligne_erreur}")
            print()
            
            # Afficher le contexte (5 lignes avant et après)
            debut = max(0, num_ligne - 6)
            fin = min(len(lignes), num_ligne + 5)
            
            for j in range(debut, fin):
                prefix = ">>> " if j == num_ligne - 1 else "    "
                print(f"{prefix}L{j+1}: {lignes[j].strip()}")
            print("-" * 80)
            print()
    
    # Recommandations
    print("=" * 80)
    print("RECOMMANDATIONS")
    print("=" * 80)
    print()
    
    if erreurs_400:
        print("🔍 CAUSES POSSIBLES DES ERREURS 400 :")
        print()
        print("1. Panier vide (items = [])")
        print("   → Vérifier que le panier n'est pas vide avant l'envoi")
        print()
        print("2. Produit introuvable (product_id invalide)")
        print("   → Vérifier que tous les produits existent encore en base")
        print()
        print("3. Stock insuffisant")
        print("   → Vérifier le stock_comptoir avant la finalisation")
        print()
        print("4. Session de caisse fermée")
        print("   → Vérifier que la session de caisse est ouverte")
        print()
        print("5. Données invalides (format JSON incorrect)")
        print("   → Vérifier le format des données envoyées")
        print()
        print("💡 Pour voir les logs en temps réel :")
        print("   sudo journalctl -u erp -f | grep -i 'complete-sale\\|400\\|error'")
        print()
        print("💡 Pour voir les logs de l'application :")
        print("   sudo tail -f /opt/erp/app/logs/fee_maison.log | grep -i 'complete-sale\\|400\\|error'")
    else:
        print("✅ Aucune erreur 400 détectée dans les logs analysés.")
        print("💡 Si les erreurs persistent, vérifiez :")
        print("   - Les logs Nginx : sudo tail -f /var/log/nginx/erp_error.log")
        print("   - Les logs système : sudo journalctl -u erp -f")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyser les erreurs HTTP 400 lors de la finalisation des ventes PDV')
    parser.add_argument('--file', type=str, help='Fichier de log à analyser')
    parser.add_argument('--hours', type=int, default=1, help='Nombre d\'heures à analyser en arrière (défaut: 1)')
    
    args = parser.parse_args()
    
    analyser_logs_400(args.file, args.hours)

