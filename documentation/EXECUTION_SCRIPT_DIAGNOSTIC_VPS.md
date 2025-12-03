# Instructions pour exécuter le script de diagnostic sur le VPS

## Problème rencontré
```
ModuleNotFoundError: No module named 'flask'
```

## Solutions

### Solution 1 : Activer l'environnement virtuel (recommandé)

```bash
# Se connecter au VPS
ssh erp-admin@51.254.36.25

# Aller dans le répertoire du projet
cd /opt/erp/app

# Activer l'environnement virtuel
# Option A : Si l'environnement est dans le projet
source venv/bin/activate

# Option B : Si l'environnement est ailleurs
source /opt/erp/venv/bin/activate  # ou le chemin correct

# Vérifier que Flask est disponible
python3 -c "import flask; print('Flask OK')"

# Exécuter le script
python3 scripts/diagnostic_stock_rechta.py
```

### Solution 2 : Utiliser le Python du système avec le chemin complet

```bash
# Trouver où Flask est installé
python3 -c "import sys; print(sys.path)"

# Ou utiliser le Python de l'environnement virtuel directement
/opt/erp/app/venv/bin/python3 scripts/diagnostic_stock_rechta.py
```

### Solution 3 : Vérifier la structure du projet

```bash
# Vérifier la structure
ls -la /opt/erp/app/

# Chercher l'environnement virtuel
find /opt/erp -name "activate" -type f 2>/dev/null

# Chercher Flask
find /opt/erp -name "flask" -type d 2>/dev/null
```

### Solution 4 : Si l'environnement virtuel n'existe pas

```bash
# Créer un environnement virtuel
cd /opt/erp/app
python3 -m venv venv

# Activer l'environnement
source venv/bin/activate

# Installer les dépendances (si requirements.txt existe)
pip install -r requirements.txt

# Ou installer Flask manuellement
pip install flask sqlalchemy flask-login
```

## Commandes complètes recommandées

```bash
# 1. Se connecter au VPS
ssh erp-admin@51.254.36.25

# 2. Aller dans le projet
cd /opt/erp/app

# 3. Activer l'environnement virtuel (essayer ces chemins)
source venv/bin/activate
# OU
source /opt/erp/venv/bin/activate
# OU
source ~/venv/bin/activate

# 4. Vérifier Flask
python3 -c "import flask; print('Flask version:', flask.__version__)"

# 5. Exécuter le script
python3 scripts/diagnostic_stock_rechta.py
```

## Alternative : Utiliser le script SQL directement

Si le script Python ne fonctionne pas, vous pouvez utiliser directement les requêtes SQL :

```bash
# Se connecter à PostgreSQL
psql -U erp_admin -d erp_fee_maison

# Ou avec le mot de passe
PGPASSWORD=votre_mot_de_passe psql -U erp_admin -d erp_fee_maison -f /opt/erp/app/scripts/diagnostic_stock_rechta.sql
```

## Vérification de l'environnement

Pour vérifier quel Python est utilisé :

```bash
# Voir le Python actuel
which python3

# Voir les modules installés
python3 -c "import sys; print('\n'.join(sys.path))"

# Vérifier Flask
python3 -c "import flask" 2>&1
```

