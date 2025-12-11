import socket
import sys

def start_listener(port=8080):
    HOST = '0.0.0.0'
    
    print(f"📡 Démarrage du DIAGNOSTIC RÉSEAU sur le port {port}")
    print(f"👉 Arrêtez l'ERP avant de lancer ce script !")
    print(f"👉 En attente de connexion de la pointeuse...")
    print("-" * 50)
    
    try:
        # Création du socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Option pour réutiliser l'adresse immédiatement (évite "Address already in use")
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            try:
                s.bind((HOST, port))
            except PermissionError:
                print(f"❌ ERREUR: Permission refusée. Essayez avec sudo.")
                return
            except OSError as e:
                print(f"❌ ERREUR: Le port {port} est déjà utilisé !")
                print("   Assurez-vous d'avoir ARRÊTÉ l'ERP/Flask.")
                print(f"   Détail: {e}")
                return

            s.listen()
            print(f"✅ Serveur en écoute sur {HOST}:{port}")
            print("⏳ En attente de la pointeuse... (Appuyez sur Ctrl+C pour quitter)")
            
            while True:
                conn, addr = s.accept()
                with conn:
                    print(f"\n🔔 CONNEXION REÇUE de: {addr[0]}")
                    
                    data = conn.recv(1024)
                    if not data:
                        break
                        
                    print(f"📦 Données reçues ({len(data)} bytes):")
                    try:
                        print(data.decode('utf-8'))
                    except:
                        print(data)
                        
                    # Réponse HTTP simple pour que la pointeuse soit contente
                    response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nOK"
                    conn.sendall(response.encode('utf-8'))
                    print("✅ Réponse OK envoyée")
                    print("-" * 50)

    except KeyboardInterrupt:
        print("\n👋 Arrêt du diagnostic.")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")

if __name__ == '__main__':
    port = 8080
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    start_listener(port)
