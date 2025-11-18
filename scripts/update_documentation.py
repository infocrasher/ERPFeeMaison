#!/usr/bin/env python3
"""
Script de mise à jour automatique de la documentation ERP Fée Maison
Analyse le code réel et met à jour les fichiers de documentation
"""

import os
import re
import glob
from pathlib import Path
from datetime import datetime
import subprocess

class DocumentationUpdater:
    def __init__(self):
        self.project_root = Path.cwd()
        self.app_dir = self.project_root / "app"
        self.docs_dir = self.project_root / "documentation"
        
        # Données collectées
        self.blueprints = {}
        self.routes = {}
        self.models = {}
        self.tables = {}
        
    def analyze_blueprints(self):
        """Analyse tous les blueprints du projet"""
        print("🔍 Analyse des blueprints...")
        
        # Chercher tous les fichiers __init__.py dans app/
        init_files = list(self.app_dir.rglob("__init__.py"))
        
        for init_file in init_files:
            try:
                with open(init_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Chercher les définitions de Blueprint
                blueprint_matches = re.findall(r'(\w+)\s*=\s*Blueprint\([\'"]([^\'"]+)[\'"][^)]*\)', content)
                
                for var_name, blueprint_name in blueprint_matches:
                    module_path = str(init_file.parent.relative_to(self.project_root))
                    self.blueprints[blueprint_name] = {
                        'variable': var_name,
                        'file': str(init_file),
                        'module': module_path
                    }
                    
            except Exception as e:
                print(f"⚠️ Erreur lecture {init_file}: {e}")
    
    def analyze_routes(self):
        """Analyse toutes les routes du projet"""
        print("🔍 Analyse des routes...")
        
        # Chercher tous les fichiers routes.py
        route_files = list(self.app_dir.rglob("*routes.py"))
        route_files.extend(list(self.app_dir.rglob("routes.py")))
        
        for route_file in route_files:
            try:
                with open(route_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Chercher les décorateurs @route
                route_matches = re.findall(r'@(\w+)\.route\([\'"]([^\'"]+)[\'"][^)]*\)', content)
                
                module_name = route_file.parent.name
                if module_name not in self.routes:
                    self.routes[module_name] = []
                
                for blueprint_var, route_path in route_matches:
                    self.routes[module_name].append({
                        'blueprint': blueprint_var,
                        'path': route_path,
                        'file': str(route_file)
                    })
                    
            except Exception as e:
                print(f"⚠️ Erreur lecture {route_file}: {e}")
    
    def analyze_models(self):
        """Analyse tous les modèles du projet"""
        print("🔍 Analyse des modèles...")
        
        # Analyser models.py principal
        main_models = self.project_root / "models.py"
        if main_models.exists():
            try:
                with open(main_models, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Compter les lignes
                line_count = len(content.split('\n'))
                self.models['main'] = {
                    'file': 'models.py',
                    'lines': line_count,
                    'classes': self.extract_classes(content)
                }
                
            except Exception as e:
                print(f"⚠️ Erreur lecture {main_models}: {e}")
        
        # Analyser les modèles dans app/
        model_files = list(self.app_dir.rglob("models.py"))
        
        for model_file in model_files:
            try:
                with open(model_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                module_name = str(model_file.parent.relative_to(self.project_root))
                self.models[module_name] = {
                    'file': str(model_file),
                    'lines': len(content.split('\n')),
                    'classes': self.extract_classes(content)
                }
                
            except Exception as e:
                print(f"⚠️ Erreur lecture {model_file}: {e}")
    
    def extract_classes(self, content):
        """Extrait les noms des classes d'un fichier"""
        class_matches = re.findall(r'class\s+(\w+)\s*\([^)]*\):', content)
        return class_matches
    
    def analyze_tables(self):
        """Analyse les noms de tables"""
        print("🔍 Analyse des tables...")
        
        for module_name, model_info in self.models.items():
            try:
                with open(model_info['file'], 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Chercher __tablename__
                table_matches = re.findall(r'__tablename__\s*=\s*[\'"]([^\'"]+)[\'"]', content)
                
                for table_name in table_matches:
                    self.tables[table_name] = {
                        'module': module_name,
                        'file': model_info['file']
                    }
                    
            except Exception as e:
                print(f"⚠️ Erreur lecture {model_info['file']}: {e}")
    
    def get_blueprint_registrations(self):
        """Récupère les enregistrements de blueprints depuis app/__init__.py"""
        print("🔍 Analyse des enregistrements de blueprints...")
        
        init_file = self.app_dir / "__init__.py"
        if not init_file.exists():
            return {}
        
        try:
            with open(init_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            registrations = {}
            
            # Chercher les app.register_blueprint
            reg_matches = re.findall(r'app\.register_blueprint\(([^,]+)(?:,\s*url_prefix=[\'"]([^\'"]+)[\'"])?\)', content)
            
            for blueprint_var, url_prefix in reg_matches:
                blueprint_var = blueprint_var.strip()
                registrations[blueprint_var] = {
                    'url_prefix': url_prefix if url_prefix else None
                }
            
            return registrations
            
        except Exception as e:
            print(f"⚠️ Erreur lecture {init_file}: {e}")
            return {}
    
    def generate_architecture_doc(self):
        """Génère la documentation d'architecture mise à jour"""
        print("📝 Génération de la documentation d'architecture...")
        
        registrations = self.get_blueprint_registrations()
        
        # Générer la section des blueprints
        blueprint_section = "### **Blueprints Enregistrés (RÉEL)**\n```python\n"
        blueprint_section += "# Enregistrement dans app/__init__.py\n"
        
        for blueprint_name, info in self.blueprints.items():
            if blueprint_name in registrations:
                url_prefix = registrations[blueprint_name]['url_prefix']
                if url_prefix:
                    blueprint_section += f"app.register_blueprint({info['variable']}_blueprint, url_prefix='{url_prefix}')\n"
                else:
                    blueprint_section += f"app.register_blueprint({info['variable']}_blueprint)\n"
        
        blueprint_section += "```\n\n"
        
        # Générer la section des URLs
        urls_section = "### **URLs Réelles par Module**\n```\n"
        
        for module_name, routes in self.routes.items():
            if not routes:
                continue
                
            # Déterminer le préfixe
            prefix = ""
            for blueprint_name, info in self.blueprints.items():
                if info['module'] == module_name and blueprint_name in registrations:
                    prefix = registrations[blueprint_name]['url_prefix'] or ""
                    break
            
            urls_section += f"📦 {module_name.title()}\n"
            for route in routes[:5]:  # Limiter à 5 routes par module
                full_url = f"{prefix}{route['path']}" if prefix else route['path']
                urls_section += f"├── {full_url}\n"
            urls_section += "\n"
        
        urls_section += "```\n\n"
        
        return blueprint_section + urls_section
    
    def generate_questions_doc(self):
        """Génère les questions de test mises à jour"""
        print("📝 Génération des questions de test...")
        
        # Analyser les vraies routes pour créer des questions pièges
        questions = []
        
        # Question sur les commandes
        if 'orders' in self.routes:
            order_routes = [r['path'] for r in self.routes['orders'] if 'new' in r['path']]
            if order_routes:
                questions.append({
                    'question': 'Quel est l\'URL pour créer une nouvelle commande ?',
                    'correct': order_routes[0],
                    'incorrect': '/admin/orders/new'
                })
        
        # Question sur les dashboards
        if 'dashboards' in self.blueprints:
            questions.append({
                'question': 'Quel est le préfixe pour les dashboards ?',
                'correct': '/dashboards',
                'incorrect': 'Pas de préfixe'
            })
        
        return questions
    
    def update_architecture_file(self):
        """Met à jour le fichier ARCHITECTURE_TECHNIQUE.md"""
        print("📝 Mise à jour de ARCHITECTURE_TECHNIQUE.md...")
        
        arch_file = self.docs_dir / "ARCHITECTURE_TECHNIQUE.md"
        if not arch_file.exists():
            print("❌ Fichier ARCHITECTURE_TECHNIQUE.md non trouvé")
            return
        
        try:
            with open(arch_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Générer le nouveau contenu
            new_sections = self.generate_architecture_doc()
            
            # Remplacer la section existante
            # Chercher la section des blueprints
            start_marker = "### **Blueprints Enregistrés (RÉEL)**"
            end_marker = "### **URLs Réelles par Module**"
            
            start_pos = content.find(start_marker)
            if start_pos != -1:
                end_pos = content.find(end_marker, start_pos)
                if end_pos != -1:
                    # Trouver la fin de la section URLs
                    next_section = content.find("### **", end_pos + 10)
                    if next_section != -1:
                        end_pos = next_section
                    
                    # Remplacer la section
                    new_content = content[:start_pos] + new_sections + content[end_pos:]
                    
                    # Sauvegarder
                    backup_file = arch_file.with_suffix('.md.backup')
                    with open(backup_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    with open(arch_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    print(f"✅ ARCHITECTURE_TECHNIQUE.md mis à jour (backup: {backup_file.name})")
                else:
                    print("⚠️ Section URLs non trouvée")
            else:
                print("⚠️ Section Blueprints non trouvée")
                
        except Exception as e:
            print(f"❌ Erreur mise à jour {arch_file}: {e}")
    
    def generate_report(self):
        """Génère un rapport de mise à jour"""
        print("📊 Génération du rapport...")
        
        report = f"""# 📊 Rapport de Mise à Jour Documentation - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🔍 Données Collectées

### **Blueprints ({len(self.blueprints)})**
"""
        
        for name, info in self.blueprints.items():
            report += f"- **{name}** : {info['variable']} dans {info['file']}\n"
        
        report += f"\n### **Routes ({sum(len(routes) for routes in self.routes.values())})**\n"
        
        for module, routes in self.routes.items():
            if routes:
                report += f"- **{module}** : {len(routes)} routes\n"
        
        report += f"\n### **Modèles ({len(self.models)})**\n"
        
        for module, info in self.models.items():
            report += f"- **{module}** : {info['lines']} lignes, {len(info['classes'])} classes\n"
        
        report += f"\n### **Tables ({len(self.tables)})**\n"
        
        for table, info in self.tables.items():
            report += f"- **{table}** : {info['module']}\n"
        
        # Sauvegarder le rapport
        report_file = self.docs_dir / f"RAPPORT_MISE_A_JOUR_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✅ Rapport généré : {report_file.name}")
        return report
    
    def run(self):
        """Exécute la mise à jour complète"""
        print("🚀 Début de la mise à jour de la documentation...")
        print(f"📁 Projet : {self.project_root}")
        print(f"📁 Documentation : {self.docs_dir}")
        print()
        
        # Analyser le code
        self.analyze_blueprints()
        self.analyze_routes()
        self.analyze_models()
        self.analyze_tables()
        
        # Générer le rapport
        report = self.generate_report()
        
        # Mettre à jour les fichiers
        self.update_architecture_file()
        
        print()
        print("✅ Mise à jour terminée !")
        print()
        print("📋 Résumé :")
        print(f"- {len(self.blueprints)} blueprints analysés")
        print(f"- {sum(len(routes) for routes in self.routes.values())} routes trouvées")
        print(f"- {len(self.models)} fichiers modèles analysés")
        print(f"- {len(self.tables)} tables identifiées")
        
        return report

def main():
    """Point d'entrée principal"""
    updater = DocumentationUpdater()
    updater.run()

if __name__ == "__main__":
    main() 