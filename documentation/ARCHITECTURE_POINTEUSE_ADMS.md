# DOCUMENTATION TECHNIQUE : SYNCHRONISATION POINTEUSE (MODE PUSH)
**Statut** : ✅ Opérationnel  
**Méthode** : Émulation Serveur ADMS (Push HTTP)  
**Matériel** : ZKTeco WL30 (Firmware Ver 6.60)

---

## 1. PRINCIPE DE FONCTIONNEMENT

Contrairement aux méthodes classiques où le PC interroge la pointeuse ("Pull"), nous utilisons ici la méthode "**Push**" (ADMS).  
Le firmware 6.60 du WL30 étant verrouillé pour les requêtes externes, nous avons inversé la logique :

1.  Le **PC Windows** agit comme un **Serveur Web** (écoute sur le port **8090**).
2.  La **Pointeuse** agit comme un **Client**. Elle est configurée pour "téléphoner" au PC à chaque pointage.
3.  Le **Script Python** réceptionne les données, les traduit, et les envoie au VPS.

```mermaid
graph LR
    ZK[Pointeuse WL30] -- 1. HTTP POST (ADMS) --> PC[PC SmartPOS (server_adms.py)]
    PC -- 2. Parsing Données --> Script[Logique Python]
    Script -- 3. HTTPS POST (Token) --> VPS[ERP Cloud (api/attendance)]
```

---

## 2. CONFIGURATION REQUISE

### A. Sur le PC Windows (SmartPOS)
*   **Adresse IP** : DOIT être fixée à `192.168.8.101` (Configuration IPv4 statique).
*   **Pare-feu** : Le port **8090** doit être autorisé (ou Python autorisé sur réseaux privés/publics).
*   **Dépendances** : `pip install flask requests`

### B. Sur la Pointeuse (ZKTeco WL30)
Dans le menu **Configuration Serveur Cloud** (ou ADMS) :
*   **Adresse Serveur** : `192.168.8.101`
*   **Port Serveur** : `8090`
*   **Activer Proxy** : NON / OFF
*   **Nom de Domaine** : Vide / OFF

---

## 3. ANALYSE DU SCRIPT (server_adms.py)

Le script utilise le framework **Flask** pour émuler le protocole de communication ZKTeco ADMS.

### Les Routes HTTP
Le script écoute les routes standards que la machine appelle automatiquement :

*   **POST /iclock/cdata** (Cœur du système)
    *   C'est ici que la pointeuse envoie les données (Logs, Utilisateurs, etc.).
    *   **Format reçu** : Texte brut tabulé (ex: `1\t2025-11-23 14:00:00\t0...`).
    *   **Action** : Le script parse cette ligne, extrait l'ID utilisateur et l'heure, puis transmet à l'ERP.

*   **GET /iclock/cdata** & **GET /iclock/getrequest**
    *   Ce sont les "Battements de cœur" (Heartbeats).
    *   La pointeuse demande régulièrement : *"Est-ce que le serveur est là ? As-tu des commandes pour moi ?"*.
    *   **Action** : Le script répond toujours "OK" pour maintenir la connexion active et éviter que la pointeuse ne se mette en erreur réseau (Croix rouge).

### La Transmission ERP
Une fois le pointage reçu localement, il est immédiatement envoyé au VPS :

*   **URL** : `https://erp.declaimers.com/zkteco/api/attendance`
*   **Sécurité** : Header `Authorization: Bearer TokenSecretFeeMaison2025`
*   **Payload** :
    ```json
    {
      "user_id": "1",
      "timestamp": "2025-11-23 14:30:00",
      "punch_type": "in" 
    }
    ```

---

## 4. AVANTAGES DE CETTE ARCHITECTURE

1.  **Indépendance DHCP Pointeuse** : On se fiche de l'adresse IP de la pointeuse (qu'elle soit en .104 ou .200). C'est elle qui cherche le PC.
2.  **Temps Réel** : Les pointages remontent quasi-instantanément (dès que la machine les pousse).
3.  **Stabilité** : C'est le protocole natif pour lequel le WL30 (Firmware 6.60) a été conçu.

---

## 5. DÉPANNAGE RAPIDE

| Symptôme | Cause Probable | Solution |
| :--- | :--- | :--- |
| **Pointeuse : Croix Rouge sur icône DB** | Le PC a changé d'IP ou script éteint | Vérifier IP PC = `192.168.8.101` et script lancé |
| **Script : Aucune ligne "REÇU"** | Pare-feu Windows bloque | Autoriser le port 8090 dans Pare-feu Windows |
| **Logs reçus mais Erreur VPS** | Internet coupé sur le PC | Vérifier connexion internet PC |

*   **Fichier Script Actif** : `C:\Users\pos\Desktop\ERP_AGENT\server_adms.py`
*   **Lancé par** : `START_FULL_ERP.bat`
