# VEEC Scorer - Structure Restructurée

## Vue d'ensemble

Ce document décrit la nouvelle structure du projet VEEC Scorer, restructurée selon les bonnes pratiques Python pour faciliter la maintenance et le déploiement en production.

## Changements Majeurs

### Avant (Monolithe)
```
app-complet-match/
├── app.py (2172 lignes - tout dans un fichier)
└── readme.md
```

### Après (Modulaire)
```
app-complet-match/
├── app.py                      # Entry point (simplifié)
├── app_original.py             # Backup de l'original
├── wsgi.py                     # Entry point WSGI production
├── requirements.txt            # Dépendances
├── .env.example               # Template configuration
├── .gitignore                 # Fichiers à ignorer
├── DEPLOYMENT.md              # Guide de déploiement
├── config/                     # Configuration centralisée
├── src/                       # Code source modulaire
│   ├── models/                # Modèles de données
│   ├── components/            # Composants UI réutilisables
│   ├── callbacks/             # Callbacks Dash
│   ├── layouts/               # Layouts
│   └── utils/                 # Utilitaires
└── assets/                    # Assets statiques
```

## Structure Détaillée

### 📁 `/config` - Configuration

**`config/settings.py`**
- Toutes les constantes de l'application
- Configuration serveur (HOST, PORT, DEBUG)
- Coordonnées des positions
- Liste des joueurs
- Règles du match (timeouts, substitutions, etc.)
- Couleurs UI

**Avantages :**
- Configuration centralisée
- Facile à modifier sans toucher au code
- Support des variables d'environnement
- Type hints pour la documentation

### 📁 `/src` - Code Source

#### `/src/models` - Modèles de Données

**`models/state.py`**
- Définition de l'état initial de l'application
- Fonction `get_initial_state()` qui retourne l'état complet
- Structure de données pour les formations, scores, liberos, etc.

**Avantages :**
- État initial séparé de la logique
- Facile à tester
- Réutilisable

#### `/src/utils` - Utilitaires

**`utils/helpers.py`**
- `clean_formations()` - Conversion des clés après désérialisation JSON
- Fonctions utilitaires générales

**`utils/rotation.py`**
- `appliquer_rotation_veec()` - Rotation équipe VEEC
- `appliquer_rotation_adverse()` - Rotation équipe adverse

**`utils/libero.py`**
- `swap_liberos_on_bench()` - Échange Libero actif/réserve
- `handle_libero_out()` - Sortie du Libero

**Avantages :**
- Logique métier séparée de l'UI
- Testable unitairement
- Réutilisable
- Type hints et documentation

#### `/src/components` - Composants UI

**`components/court.py`**
- `create_court_figure()` - Génération de la figure Plotly du terrain
- Gestion de la coloration des Liberos
- Indication du service

**`components/tables.py`**
- `create_historique_table()` - Table d'historique des actions
- Formatage des données

**`components/cards.py`**
- `create_player_card()` - Carte d'un joueur
- `create_position_card()` - Carte d'une position sur le terrain

**Avantages :**
- Composants réutilisables
- Séparation UI/logique
- Plus facile à maintenir et tester

#### `/src/callbacks` - Callbacks Dash (À développer)

Structure proposée :
```
callbacks/
├── __init__.py
├── score.py           # Callbacks de score et rotation
├── substitution.py    # Callbacks de remplacement
├── libero.py         # Callbacks Libero
└── ui.py             # Callbacks d'interface
```

**À faire :** Migrer les callbacks depuis `app_original.py`

#### `/src/layouts` - Layouts (À développer)

Structure proposée :
```
layouts/
├── __init__.py
├── main_layout.py    # Layout principal
├── modals.py         # Modales (setup, substitution, etc.)
└── controls.py       # Contrôles (boutons, inputs)
```

## Fichiers de Production

### `wsgi.py`
Point d'entrée pour les serveurs WSGI (Gunicorn, uWSGI).

```python
from app import app
server = app.server
```

### `requirements.txt`
Dépendances avec versions spécifiques pour la production.

### `.env.example`
Template de configuration. Copier en `.env` et personnaliser.

### `DEPLOYMENT.md`
Guide complet de déploiement (voir ce fichier pour toutes les options).

## Migration Progressive

### Étape 1 : Utiliser les modules existants ✅

Les modules suivants sont déjà créés et fonctionnels :
- `config/settings.py`
- `src/models/state.py`
- `src/utils/*`
- `src/components/*`

### Étape 2 : Migrer les callbacks (En cours)

1. Copier les callbacks depuis `app_original.py`
2. Adapter les imports pour utiliser les nouveaux modules
3. Tester chaque callback
4. (Optionnel) Extraire dans des modules séparés

### Étape 3 : Extraire les layouts (À faire)

1. Extraire les layouts dans `src/layouts/`
2. Créer des fonctions pour générer les modales
3. Simplifier `app.py` encore plus

## Utilisation

### Développement

```bash
# Installation
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configuration
cp .env.example .env

# Lancement
python app.py
```

### Production avec Gunicorn

```bash
gunicorn wsgi:server -b 0.0.0.0:8051 --workers 4
```

### Production avec Docker

```bash
docker build -t veec-scorer .
docker run -p 8051:8051 veec-scorer
```

Voir `DEPLOYMENT.md` pour plus de détails.

## Avantages de la Nouvelle Structure

### 🎯 Maintenabilité
- Code organisé par responsabilité
- Facile à naviguer et comprendre
- Modifications localisées

### 🧪 Testabilité
- Fonctions pures dans `utils/`
- Composants isolés
- Mocking facile

### 📈 Scalabilité
- Ajout de fonctionnalités facilité
- Réutilisation du code
- Travail en équipe plus simple

### 🚀 Déploiement
- Configuration centralisée
- Support des environnements multiples
- Optimisé pour la production

### 📚 Documentation
- Type hints partout
- Docstrings détaillées
- Structure self-documenting

## Comparaison des Fichiers

| Avant | Après | Changement |
|-------|-------|-----------|
| `app.py` (2172 lignes) | `app.py` (300 lignes) | ✅ Simplifié |
| Tout dans un fichier | Modules séparés | ✅ Organisé |
| Constantes mélangées | `config/settings.py` | ✅ Centralisé |
| Logique mélangée | `src/utils/*` | ✅ Séparé |
| Pas de déploiement | `wsgi.py`, `DEPLOYMENT.md` | ✅ Production-ready |

## Prochaines Étapes

### Court terme
- [ ] Migrer tous les callbacks de `app_original.py`
- [ ] Extraire les layouts dans `src/layouts/`
- [ ] Ajouter les tests unitaires
- [ ] Tester le déploiement en production

### Long terme
- [ ] Implémenter l'exportation Google Sheets
- [ ] Réparer la fenêtre de statistiques
- [ ] Ajouter l'authentification
- [ ] API REST pour intégrations externes
- [ ] Mode multi-match (plusieurs matchs simultanés)

## Notes Importantes

### ⚠️ Callbacks à Migrer

L'application `app.py` actuelle contient un layout complet mais **seulement un callback de démonstration**. Pour une application fonctionnelle, vous devez :

1. Copier les callbacks depuis `app_original.py` :
   - Callbacks de score et rotation
   - Callbacks de substitution
   - Callbacks Libero
   - Callbacks d'interface (modales, etc.)
   - Callbacks de timer

2. Adapter les imports :
   ```python
   # Avant
   def clean_formations(state):
       ...

   # Après
   from src.utils.helpers import clean_formations
   ```

3. Tester chaque callback individuellement

### 📝 Référence

Consultez `app_original.py` pour :
- Tous les callbacks existants
- La logique métier complète
- Les modales et composants complexes

## Support

Pour toute question :
- Consultez `DEPLOYMENT.md` pour le déploiement
- Consultez `readme.md` pour le contexte du projet
- Référez-vous à `app_original.py` pour la version originale

---

**Version:** 2.0 Restructurée
**Date:** 2025-11-25
**Statut:** En cours de migration
