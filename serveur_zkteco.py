from flask import Flask, request
import requests
import sys

# ================= CONFIGURATION =================
VPS_API_URL = "https://erp.declaimers.com/zkteco/api/attendance"
VPS_TOKEN = "TokenSecretFeeMaison2025"
SERVER_PORT = 8090
# =================================================

app = Flask(__name__)

def send_to_vps(user_id, timestamp, state):
    punch_type = "out" if str(state) in ['1', '5'] else "in"
    
    payload = {
        "user_id": user_id,
        "timestamp": timestamp,
        "punch_type": punch_type
    }
    headers = {"Authorization": f"Bearer {VPS_TOKEN}"}
    
    try:
        # On utilise flush=True pour forcer l'ecriture dans le log immediatement
        print(f"   -> Envoi VPS : User {user_id} ({punch_type}) a {timestamp}...", end="", flush=True)
        r = requests.post(VPS_API_URL, json=payload, headers=headers, timeout=5)
        if r.status_code in [200, 201]:
            print(" [OK]")
            return True
        else:
            print(f" [ERREUR VPS: {r.status_code}]")
            return False
    except Exception as e:
        print(f" [ERREUR RESEAU: {e}]")
        return False

@app.route('/iclock/cdata', methods=['GET', 'POST'])
def receive_data():
    table = request.args.get('table', '')
    
    if table == 'ATTLOG':
        raw_data = request.get_data().decode('utf-8')
        if not raw_data: return "OK"
        print(f"\n[RECU] Paquet de logs", flush=True)
        
        lines = raw_data.strip().split('\n')
        count = 0
        
        for line in lines:
            parts = line.split('\t')
            if len(parts) >= 3:
                uid = parts[0]
                ts = parts[1]
                state = parts[2]
                send_to_vps(uid, ts, state)
                count += 1
        
        print(f"   -- {count} pointages traites.", flush=True)
        return "OK"
    if request.method == 'GET' and 'options' in request.args:
        return "GET OPTION FROM: 10000\nATTLOGStamp=None\nOPERLOGStamp=None\nATTPHOTOStamp=None\nErrorDelay=30\nDelay=10\nTransTimes=00:00;14:05\nTransInterval=1\nTransFlag=1111000000\nRealtime=1\nEncrypt=0"
    return "OK"

@app.route('/iclock/getrequest', methods=['GET', 'POST'])
def get_request():
    return "OK"

@app.route('/iclock/devicecmd', methods=['GET', 'POST'])
def device_cmd():
    return "OK"

if __name__ == '__main__':
    # Plus d'emojis ici non plus
    print(f"SERVEUR ZKTECO -> ERP EN LIGNE (Port {SERVER_PORT})", flush=True)
    print("En attente de pointages...", flush=True)
    app.run(host='0.0.0.0', port=SERVER_PORT)



