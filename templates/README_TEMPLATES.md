# 🎨 Système de Templates de Factures PDF

## 📋 Vue d'ensemble

Le système de templates permet de générer des factures PDF avec différents styles et configurations. Chaque template est personnalisable en termes de couleurs, polices, mise en page et contenu.

## 🚀 Templates Disponibles

### 1. Template Standard (default)
- **Style :** Professionnel Fée Maison
- **Couleurs :** Bleu marine (#2E4057) + Or (#D4AF37)
- **Usage :** Template par défaut pour toutes les factures

### 2. Template Minimal
- **Style :** Épuré et simple
- **Couleurs :** Noir et gris
- **Usage :** Pour des factures sobres

### 3. Template Élégant
- **Style :** Luxueux avec couleurs vives
- **Couleurs :** Bleu indigo (#1A237E) + Orange (#FF6F00)
- **Usage :** Pour des clients premium

## 🔗 URLs d'Export

```
# Template par défaut
GET /admin/b2b/invoices/{invoice_id}/export/pdf

# Template spécifique
GET /admin/b2b/invoices/{invoice_id}/export/pdf/{template_name}
```

**Exemples :**
- `/admin/b2b/invoices/1/export/pdf` (défaut)
- `/admin/b2b/invoices/1/export/pdf/minimal`
- `/admin/b2b/invoices/1/export/pdf/elegant`

## 🛠️ Créer un Template Personnalisé

### Méthode 1 : Assistant Interactif

```bash
python generate_custom_template.py
```

L'assistant vous guide pour :
- ✅ Configurer les informations entreprise
- ✅ Choisir les couleurs
- ✅ Définir les tailles de police
- ✅ Personnaliser le pied de page
- ✅ Générer le code Python

### Méthode 2 : Configuration Manuelle

1. **Créer la configuration** dans `app/b2b/invoice_templates.py` :

```python
def get_mon_template_template():
    """Mon template personnalisé"""
    config = {
        'company': {
            'name': 'FÉE MAISON',
            'subtitle1': 'Restaurant • Traiteur',
            'subtitle2': 'Cuisine Authentique',
        },
        'colors': {
            'primary': '#1B5E20',      # Vert foncé
            'secondary': '#4CAF50',    # Vert
            'accent': '#FFC107',       # Jaune
            'text': '#000000',
            'background': '#F1F8E9'    # Vert très clair
        },
        'sizes': {
            'header': 19,
            'subtitle': 13,
            'invoice_title': 17,
            'normal': 10,
            'small': 9
        },
        'footer': {
            'text1': '🌿 Cuisine Bio & Naturelle • Fée Maison 🌿',
            'text2': 'Paiement sous 30 jours'
        },
        'currency': 'DA',
        'tax_rate': 0.19,
        'show_tax': True
    }
    return InvoiceTemplate(config)
```

2. **Ajouter dans routes.py** :

```python
from .invoice_templates import get_mon_template_template

templates = {
    'default': get_fee_maison_template,
    'minimal': get_minimal_template,
    'elegant': get_elegant_template,
    'mon_template': get_mon_template_template,  # Nouveau
}
```

3. **Mettre à jour le template HTML** `view.html` :

```html
<li><a class="dropdown-item" href="{{ url_for('b2b.export_invoice_pdf_template', invoice_id=invoice.id, template_name='mon_template') }}">
    <i class="bi bi-leaf me-2"></i>Template Bio
</a></li>
```

## ⚙️ Configuration Détaillée

### Structure de Configuration

```python
config = {
    'company': {
        'name': str,           # Nom de l'entreprise
        'subtitle1': str,      # Sous-titre 1
        'subtitle2': str,      # Sous-titre 2
        'address': str,        # Adresse (optionnel)
        'phone': str,          # Téléphone (optionnel)
        'email': str,          # Email (optionnel)
        'website': str         # Site web (optionnel)
    },
    'colors': {
        'primary': str,        # Couleur principale (#RRGGBB)
        'secondary': str,      # Couleur secondaire
        'accent': str,         # Couleur d'accent
        'text': str,           # Couleur du texte
        'background': str      # Couleur d'arrière-plan
    },
    'fonts': {
        'header': str,         # Police en-tête
        'subtitle': str,       # Police sous-titre
        'normal': str,         # Police normale
        'bold': str            # Police grasse
    },
    'sizes': {
        'header': int,         # Taille en-tête (pts)
        'subtitle': int,       # Taille sous-titre
        'invoice_title': int,  # Taille titre facture
        'normal': int,         # Taille normale
        'small': int           # Taille petite
    },
    'margins': {
        'top': float,          # Marge haute (inches)
        'bottom': float,       # Marge basse
        'left': float,         # Marge gauche
        'right': float         # Marge droite
    },
    'footer': {
        'text1': str,          # Texte pied de page 1
        'text2': str           # Texte pied de page 2
    },
    'currency': str,           # Devise (DA, EUR, USD...)
    'tax_rate': float,         # Taux de TVA (0.19 = 19%)
    'show_tax': bool           # Afficher la TVA
}
```

### Couleurs Recommandées

| Thème | Principale | Secondaire | Accent |
|-------|------------|------------|--------|
| **Classique** | #2E4057 | #5A6C7D | #D4AF37 |
| **Moderne** | #000000 | #666666 | #999999 |
| **Élégant** | #1A237E | #3F51B5 | #FF6F00 |
| **Nature** | #2E7D32 | #4CAF50 | #FFC107 |
| **Luxe** | #8E24AA | #BA68C8 | #FFD54F |
| **Tech** | #0D47A1 | #1976D2 | #00BCD4 |

### Polices Disponibles (ReportLab)

- `Helvetica` : Police standard
- `Helvetica-Bold` : Police grasse
- `Times-Roman` : Police serif
- `Times-Bold` : Police serif grasse
- `Courier` : Police monospace

## 🧪 Tests et Validation

### Tester un Template

1. **Créer une facture de test**
2. **Utiliser l'URL avec le template** :
   ```
   /admin/b2b/invoices/1/export/pdf/mon_template
   ```
3. **Vérifier le rendu PDF**

### Points de Contrôle

- ✅ **Lisibilité** : Texte bien visible
- ✅ **Alignement** : Éléments bien positionnés
- ✅ **Couleurs** : Contraste suffisant
- ✅ **Marges** : Espacement correct
- ✅ **Calculs** : Totaux exacts
- ✅ **Composition** : Produits composés bien affichés

## 🎯 Bonnes Pratiques

### Design

1. **Couleurs contrastées** : Assurer la lisibilité
2. **Hiérarchie visuelle** : Tailles de police cohérentes
3. **Espacement** : Marges et espacements suffisants
4. **Identité** : Refléter l'image de Fée Maison

### Performance

1. **Templates légers** : Éviter les configurations complexes
2. **Réutilisation** : Créer des templates réutilisables
3. **Cache** : Les objets template peuvent être mis en cache

### Maintenance

1. **Nommage clair** : Noms de templates explicites
2. **Documentation** : Documenter les templates personnalisés
3. **Versioning** : Garder un historique des modifications

## 🔧 Dépannage

### Erreurs Courantes

| Erreur | Cause | Solution |
|--------|-------|----------|
| `Template non trouvé` | Nom incorrect | Vérifier le nom dans `templates` dict |
| `Couleur invalide` | Format couleur incorrect | Utiliser format `#RRGGBB` |
| `Police non trouvée` | Police indisponible | Utiliser polices ReportLab standard |
| `Marge trop petite` | Valeur < 0.1 | Utiliser au minimum 0.1 inch |

### Debug

Ajouter des logs dans le template :

```python
def generate_pdf(self, invoice):
    print(f"Génération PDF pour facture {invoice.invoice_number}")
    print(f"Template: {self.config['company']['name']}")
    # ... reste du code
```

## 📚 Ressources

- [Documentation ReportLab](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- [Couleurs Hex](https://htmlcolorcodes.com/)
- [Guide Design PDF](https://www.adobe.com/creativecloud/design/discover/invoice-design.html)

---

**💡 Conseil :** Commencez par modifier un template existant avant de créer un template complètement nouveau !

