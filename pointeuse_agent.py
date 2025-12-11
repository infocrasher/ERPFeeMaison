#!/usr/bin/env python3
"""
Agent récepteur pour pointeuse ZKTeco
Écoute sur port 8090 et transmet au VPS
"""

import http.server
import json
import requests
import traceback
from datetime import datetime

# ================= CONFIGURATION =================
PORT = 4370
VPS_URL = "https://erp.declaimers.com/zkteco/api/attendance"
TOKEN = "TokenSecretFeeMaison2025"
# =================================================


class PointeuseHandler(http.server.BaseHTTPRequestHandler):
    """Handler pour recevoir les données de la pointeuse et les transmettre au VPS"""
    
    def log_message(self, format, *args):
        """Surcharge pour un meilleur logging"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {format % args}")
    
    def do_GET(self):
        """Répondre aux requêtes iClock de la pointeuse"""
        path = self.path
        
        # Protocole iClock : /iclock/cdata (keep-alive de la pointeuse)
        if '/iclock/cdata' in path:
            print(f"📡 iClock keep-alive reçu: {path}")
            
            # Réponse iClock standard : "OK" en texte brut
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            
            # Réponse iClock : OK ou commandes
            # Format: OK (pas de commande) ou C:commande
            response_text = "OK"
            self.wfile.write(response_text.encode())
            print(f"✅ iClock réponse: {response_text}")
        
        # Autres requêtes GET (tests manuels)
        else:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'status': 'ok',
                'message': 'Agent Pointeuse Actif',
                'port': PORT,
                'timestamp': datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())
            print("✅ GET - Test manuel")
    
    def do_POST(self):
        """Recevoir les données de pointage de la pointeuse (protocole iClock)"""
        try:
            # Lire les données brutes
            length = int(self.headers.get('Content-Length', 0))
            raw_data = self.rfile.read(length) if length > 0 else b''
            
            print(f"\n{'='*60}")
            print(f"📥 POST POINTAGE REÇU !")
            print(f"{'='*60}")
            print(f"Path: {self.path}")
            print(f"Taille: {length} octets")
            print(f"Content-Type: {self.headers.get('Content-Type', 'N/A')}")
            
            # Protocole iClock : données en texte brut, pas JSON
            text_data = raw_data.decode('utf-8', errors='ignore')
            print(f"📄 Données brutes:\n{text_data}")
            
            # Parser le format iClock
            # Format typique : ATTLOG data (transactions d'attendance)
            # Exemple: 1\t2025-12-07 00:25:30\t0\t0\t0
            # Format: user_id\ttimestamp\tpunch_type\tstatus\tverify
            
            attendance_records = self.parse_iclock_data(text_data)
            
            if attendance_records:
                print(f"✅ {len(attendance_records)} pointage(s) parsé(s)")
                
                # Transmettre chaque pointage au VPS
                success_count = 0
                for record in attendance_records:
                    if self.forward_to_vps(record):
                        success_count += 1
                
                print(f"📊 Résultat: {success_count}/{len(attendance_records)} transmis au VPS")
                
                # Réponse iClock : OK (confirme réception)
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"OK")
                print("✅ Réponse 'OK' envoyée à la pointeuse")
            else:
                print("⚠️  Aucun pointage valide trouvé dans les données")
                # Toujours répondre OK pour que la pointeuse ne réessaie pas
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"OK")
        
        except Exception as e:
            print(f"❌ ERREUR: {e}")
            traceback.print_exc()
            # Même en cas d'erreur, répondre OK à la pointeuse
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"OK")
    
    def parse_iclock_data(self, text_data):
        """Parser les données au format iClock (texte tabulé)"""
        records = []
        
        for line in text_data.strip().split('\n'):
            if not line.strip():
                continue
            
            # Format iClock ATTLOG: user_id\ttimestamp\tpunch_type\tstatus\tverify
            parts = line.split('\t')
            
            if len(parts) >= 2:
                try:
                    user_id = parts[0].strip()
                    timestamp = parts[1].strip()
                    
                    # punch_type : 0=Check-In, 1=Check-Out, etc.
                    punch_code = parts[2].strip() if len(parts) > 2 else '0'
                    
                    # Convertir punch_code en in/out
                    if punch_code == '1':
                        punch_type = 'out'
                    else:
                        punch_type = 'in'  # 0 ou autre = in par défaut
                    
                    record = {
                        'user_id': int(user_id) if user_id.isdigit() else user_id,
                        'timestamp': timestamp,
                        'punch_type': punch_type
                    }
                    
                    records.append(record)
                    print(f"  ✅ Pointage parsé: User {user_id} - {timestamp} - {punch_type}")
                
                except Exception as e:
                    print(f"  ⚠️  Erreur parsing ligne: {line} - {e}")
                    continue
        
        return records
    
    def forward_to_vps(self, data):
        """Transmettre les données au VPS avec authentification"""
        try:
            print(f"\n📤 Transmission au VPS...")
            print(f"URL: {VPS_URL}")
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {TOKEN}'
            }
            
            response = requests.post(
                VPS_URL,
                json=data,
                headers=headers,
                timeout=10
            )
            
            print(f"📊 Statut VPS: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ Pointage transmis au VPS avec succès")
                try:
                    vps_response = response.json()
                    print(f"💬 Réponse VPS: {json.dumps(vps_response, indent=2, ensure_ascii=False)}")
                except:
                    print(f"💬 Réponse VPS: {response.text}")
                return True
            else:
                print(f"❌ Erreur VPS: {response.status_code}")
                print(f"💬 Réponse: {response.text}")
                return False
        
        except requests.exceptions.Timeout:
            print(f"❌ Timeout lors de la connexion au VPS")
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Erreur de connexion au VPS: {e}")
            return False
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            traceback.print_exc()
            return False


def main():
    """Démarrer le serveur"""
    print("="*60)
    print("🚀 AGENT POINTEUSE ZKTECO")
    print("="*60)
    print(f"📍 Port d'écoute: {PORT}")
    print(f"🌐 URL VPS: {VPS_URL}")
    print(f"⏰ Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print()
    print("⏳ En attente des données de la pointeuse...")
    print()
    
    try:
        server = http.server.HTTPServer(('0.0.0.0', PORT), PointeuseHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt de l'agent demandé (Ctrl+C)")
        server.shutdown()
    except Exception as e:
        print(f"\n❌ ERREUR FATALE: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()

