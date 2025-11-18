#!/usr/bin/env python3
"""
Script de mise à jour des URLs et endpoints dans la documentation ERP Fée Maison
Version simplifiée et robuste
"""

import re
import os
from pathlib import Path
from datetime import datetime

class URLDocumentationUpdater:
    def __init__(self):
        # Déterminer le chemin du projet depuis le dossier scripts/
        current_dir = Path.cwd()
        if current_dir.name == 'scripts':
            self.project_root = current_dir.parent
        else:
            self.project_root = current_dir
            
        self.app_dir = self.project_root / "app"
        self.docs_dir = self.project_root / "documentation"
        
        # Données collectées
        self.blueprints = {}
        self.routes_by_module = {}
        self.blueprint_registrations = {}
        
    def collect_blueprints(self):
        """Collecte tous les blueprints du projet"""
        print("🔍 Collecte des blueprints...")
        
        # Analyser app/__init__.py pour les enregistrements
        init_file = self.app_dir / "__init__.py"
        if init_file.exists():
            with open(init_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Chercher les imports de blueprints
            import_pattern = r'from\s+([^.]+\.[^.]+\.[^.]*)\s+import\s+(\w+)\s+as\s+(\w+)_blueprint'
            imports = re.findall(import_pattern, content)
            
            for module_path, blueprint_var, blueprint_name in imports:
                self.blueprints[blueprint_name] = {
                    'module': module_path,
                    'variable': blueprint_var,
                    'import_as': f"{blueprint_var}_blueprint"
                }
            
            # Chercher les enregistrements avec préfixes
            reg_pattern = r'app\.register_blueprint\((\w+_blueprint)(?:,\s*url_prefix=[\'"]([^\'"]+)[\'"])?\)'
            registrations = re.findall(reg_pattern, content)
            
            for blueprint_var, url_prefix in registrations:
                self.blueprint_registrations[blueprint_var] = url_prefix if url_prefix else None
        
        # Analyser les fichiers __init__.py des modules
        for init_file in self.app_dir.rglob("__init__.py"):
            try:
                with open(init_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Chercher les définitions de Blueprint
                blueprint_pattern = r'(\w+)\s*=\s*Blueprint\([\'"]([^\'"]+)[\'"][^)]*\)'
                matches = re.findall(blueprint_pattern, content)
                
                for var_name, blueprint_name in matches:
                    module_path = str(init_file.parent.relative_to(self.project_root))
                    if blueprint_name not in self.blueprints:
                        self.blueprints[blueprint_name] = {
                            'module': module_path,
                            'variable': var_name,
                            'import_as': f"{var_name}_blueprint"
                        }
                        
            except Exception as e:
                print(f"⚠️ Erreur lecture {init_file}: {e}")
    
    def collect_routes(self):
        """Collecte toutes les routes du projet"""
        print("🔍 Collecte des routes...")
        
        # Chercher tous les fichiers routes.py
        route_files = []
        route_files.extend(list(self.app_dir.rglob("*routes.py")))
        route_files.extend(list(self.app_dir.rglob("routes.py")))
        
        for route_file in route_files:
            try:
                with open(route_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                module_name = route_file.parent.name
                if module_name not in self.routes_by_module:
                    self.routes_by_module[module_name] = []
                
                # Chercher les décorateurs @route
                route_pattern = r'@(\w+)\.route\([\'"]([^\'"]+)[\'"][^)]*\)'
                matches = re.findall(route_pattern, content)
                
                for blueprint_var, route_path in matches:
                    self.routes_by_module[module_name].append({
                        'blueprint': blueprint_var,
                        'path': route_path,
                        'full_path': self.get_full_url(module_name, route_path)
                    })
                    
            except Exception as e:
                print(f"⚠️ Erreur lecture {route_file}: {e}")
    
    def get_full_url(self, module_name, route_path):
        """Construit l'URL complète avec le préfixe"""
        # Chercher le préfixe pour ce module
        prefix = ""
        for blueprint_name, info in self.blueprints.items():
            if info['module'] == module_name:
                import_as = info['import_as']
                if import_as in self.blueprint_registrations:
                    prefix = self.blueprint_registrations[import_as] or ""
                break
        
        return f"{prefix}{route_path}" if prefix else route_path
    
    def generate_urls_section(self):
        """Génère la section des URLs pour la documentation"""
        print("📝 Génération de la section URLs...")
        
        urls_section = "### **URLs Réelles par Module**\n```\n"
        
        # Organiser par module
        for module_name, routes in self.routes_by_module.items():
            if not routes:
                continue
            
            # Déterminer l'icône et le nom d'affichage
            icon_map = {
                'main': '🏠',
                'auth': '🔐',
                'products': '📦',
                'orders': '📋',
                'recipes': '🏭',
                'stock': '📦',
                'purchases': '🛒',
                'employees': '👥',
                'deliverymen': '🚚',
                'sales': '💰',
                'dashboards': '📊',
                'accounting': '🧮',
                'zkteco': '⏰'
            }
            
            icon = icon_map.get(module_name, '📁')
            display_name = module_name.replace('_', ' ').title()
            
            urls_section += f"{icon} {display_name}\n"
            
            # Afficher les routes (limitées à 8 par module)
            for route in routes[:8]:
                urls_section += f"├── {route['full_path']}\n"
            
            if len(routes) > 8:
                urls_section += f"└── ... et {len(routes) - 8} autres routes\n"
            else:
                urls_section += "\n"
        
        urls_section += "```\n\n"
        return urls_section
    
    def generate_blueprint_section(self):
        """Génère la section des blueprints pour la documentation"""
        print("📝 Génération de la section blueprints...")
        
        blueprint_section = "### **Blueprints Enregistrés (RÉEL)**\n```python\n"
        blueprint_section += "# Enregistrement dans app/__init__.py\n"
        
        for blueprint_name, info in self.blueprints.items():
            import_as = info['import_as']
            if import_as in self.blueprint_registrations:
                url_prefix = self.blueprint_registrations[import_as]
                if url_prefix:
                    blueprint_section += f"app.register_blueprint({import_as}, url_prefix='{url_prefix}')\n"
                else:
                    blueprint_section += f"app.register_blueprint({import_as})\n"
        
        blueprint_section += "```\n\n"
        return blueprint_section
    
    def update_architecture_file(self):
        """Met à jour le fichier ARCHITECTURE_TECHNIQUE.md"""
        print("📝 Mise à jour de ARCHITECTURE_TECHNIQUE.md...")
        
        arch_file = self.docs_dir / "ARCHITECTURE_TECHNIQUE.md"
        if not arch_file.exists():
            print("❌ Fichier ARCHITECTURE_TECHNIQUE.md non trouvé")
            return False
        
        try:
            # Lire le fichier actuel
            with open(arch_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Générer les nouvelles sections
            new_blueprint_section = self.generate_blueprint_section()
            new_urls_section = self.generate_urls_section()
            
            # Remplacer la section des blueprints
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
                    
                    # Remplacer les sections
                    new_content = content[:start_pos] + new_blueprint_section + new_urls_section + content[end_pos:]
                    
                    # Créer une sauvegarde
                    backup_file = arch_file.with_suffix('.md.backup')
                    with open(backup_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    # Écrire le nouveau contenu
                    with open(arch_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    print(f"✅ ARCHITECTURE_TECHNIQUE.md mis à jour (backup: {backup_file.name})")
                    return True
                else:
                    print("⚠️ Section URLs non trouvée")
            else:
                print("⚠️ Section Blueprints non trouvée")
                
        except Exception as e:
            print(f"❌ Erreur mise à jour {arch_file}: {e}")
        
        return False
    
    def update_questions_file(self):
        """Met à jour le fichier QUESTIONS_TEST_IA.md avec les vraies URLs"""
        print("📝 Mise à jour de QUESTIONS_TEST_IA.md...")
        
        questions_file = self.docs_dir / "QUESTIONS_TEST_IA.md"
        if not questions_file.exists():
            print("❌ Fichier QUESTIONS_TEST_IA.md non trouvé")
            return False
        
        try:
            with open(questions_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Mettre à jour les questions pièges avec les vraies URLs
            updates = []
            
            # Question sur les commandes
            if 'orders' in self.routes_by_module:
                order_routes = [r['path'] for r in self.routes_by_module['orders'] if 'new' in r['path']]
                if order_routes:
                    correct_url = self.get_full_url('orders', order_routes[0])
                    updates.append({
                        'old': 'Réponse attendue : `/admin/orders/new` (pas `/orders/new`)',
                        'new': f'Réponse attendue : `{correct_url}` (pas `/admin/orders/new`)'
                    })
            
            # Question sur les dashboards
            if 'dashboards' in self.blueprints:
                prefix = self.blueprint_registrations.get('dashboards_bp', '')
                updates.append({
                    'old': 'Réponse attendue : Pas de préfixe (pas `/dashboards`)',
                    'new': f'Réponse attendue : `{prefix}` (avec préfixe)'
                })
            
            # Appliquer les mises à jour
            for update in updates:
                content = content.replace(update['old'], update['new'])
            
            # Sauvegarder
            backup_file = questions_file.with_suffix('.md.backup')
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            with open(questions_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ QUESTIONS_TEST_IA.md mis à jour (backup: {backup_file.name})")
            return True
            
        except Exception as e:
            print(f"❌ Erreur mise à jour {questions_file}: {e}")
        
        return False
    
    def generate_summary_report(self):
        """Génère un rapport de synthèse"""
        print("📊 Génération du rapport de synthèse...")
        
        total_routes = sum(len(routes) for routes in self.routes_by_module.values())
        
        report = f"""# 📊 Rapport de Mise à Jour URLs - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🔍 Données Collectées

### **Blueprints ({len(self.blueprints)})**
"""
        
        for name, info in self.blueprints.items():
            report += f"- **{name}** : {info['variable']} dans {info['module']}\n"
        
        report += f"\n### **Routes ({total_routes})**\n"
        
        for module, routes in self.routes_by_module.items():
            if routes:
                report += f"- **{module}** : {len(routes)} routes\n"
        
        report += f"\n### **Préfixes URL**\n"
        
        for blueprint_var, prefix in self.blueprint_registrations.items():
            prefix_display = prefix if prefix else "Aucun"
            report += f"- **{blueprint_var}** : {prefix_display}\n"
        
        # Sauvegarder le rapport
        report_file = self.docs_dir / f"RAPPORT_URLS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✅ Rapport généré : {report_file.name}")
        return report
    
    def run(self):
        """Exécute la mise à jour complète"""
        print("🚀 Début de la mise à jour des URLs...")
        print(f"📁 Projet : {self.project_root}")
        print(f"📁 Documentation : {self.docs_dir}")
        print()
        
        # Collecter les données
        self.collect_blueprints()
        self.collect_routes()
        
        # Mettre à jour les fichiers
        arch_updated = self.update_architecture_file()
        questions_updated = self.update_questions_file()
        
        # Générer le rapport
        report = self.generate_summary_report()
        
        print()
        print("✅ Mise à jour terminée !")
        print()
        print("📋 Résumé :")
        print(f"- {len(self.blueprints)} blueprints analysés")
        print(f"- {sum(len(routes) for routes in self.routes_by_module.values())} routes trouvées")
        print(f"- Architecture : {'✅' if arch_updated else '❌'}")
        print(f"- Questions : {'✅' if questions_updated else '❌'}")
        
        return report

def main():
    """Point d'entrée principal"""
    updater = URLDocumentationUpdater()
    updater.run()

if __name__ == "__main__":
    main() 