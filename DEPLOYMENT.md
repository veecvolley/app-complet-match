# Guide de Déploiement - VEEC Scorer

Ce guide décrit comment déployer l'application VEEC Scorer en production.

## Structure du Projet

```
app-complet-match/
├── app.py                      # Point d'entrée principal (refactorisé)
├── app_original.py             # Application originale (référence)
├── wsgi.py                     # Point d'entrée WSGI pour production
├── requirements.txt            # Dépendances Python
├── .env.example               # Template de configuration
├── config/                     # Configuration
│   ├── __init__.py
│   └── settings.py            # Constantes et configuration
├── src/                       # Code source
│   ├── __init__.py
│   ├── models/                # Modèles de données
│   │   ├── __init__.py
│   │   └── state.py          # État initial de l'application
│   ├── components/            # Composants UI
│   │   ├── __init__.py
│   │   ├── court.py          # Visualisation terrain
│   │   ├── tables.py         # Tables d'historique
│   │   └── cards.py          # Cartes joueurs/positions
│   ├── callbacks/             # Callbacks Dash (à migrer)
│   │   └── __init__.py
│   ├── layouts/               # Layouts (à développer)
│   │   └── __init__.py
│   └── utils/                 # Utilitaires
│       ├── __init__.py
│       ├── helpers.py        # Fonctions helper
│       ├── rotation.py       # Logique de rotation
│       └── libero.py         # Logique Libero
└── assets/                    # Assets statiques (CSS, images, logos)
```

## Installation

### 1. Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de packages Python)
- Virtualenv (recommandé)

### 2. Installation des dépendances

```bash
# Créer un environnement virtuel
python3 -m venv venv

# Activer l'environnement
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copier le fichier de configuration
cp .env.example .env

# Éditer le fichier .env selon vos besoins
nano .env  # ou votre éditeur préféré
```

## Développement

### Lancer l'application en mode développement

```bash
# Avec debug activé
python app.py
```

L'application sera accessible à : `http://localhost:8051`

### Lancer avec auto-reload (développement)

```bash
# Le mode debug de Dash inclut l'auto-reload
DEBUG=True python app.py
```

## Déploiement en Production

### Option 1 : Gunicorn (Recommandé)

Gunicorn est le serveur WSGI standard pour les applications Python en production.

#### Lancement basique

```bash
gunicorn wsgi:server -b 0.0.0.0:8051
```

#### Avec workers multiples (recommandé)

```bash
# 4 workers pour gérer plusieurs connexions simultanées
gunicorn wsgi:server \
    --bind 0.0.0.0:8051 \
    --workers 4 \
    --worker-class sync \
    --timeout 120 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --log-level info
```

#### Configuration Gunicorn (gunicorn_config.py)

Créez un fichier `gunicorn_config.py` :

```python
import multiprocessing
import os

# Bind
bind = f"0.0.0.0:{os.getenv('PORT', '8051')}"

# Workers
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"

# Timeout
timeout = 120
keepalive = 5

# Logging
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"

# Process naming
proc_name = "veec_scorer"

# Server mechanics
daemon = False
pidfile = None
```

Puis lancez :

```bash
mkdir -p logs
gunicorn -c gunicorn_config.py wsgi:server
```

### Option 2 : Uvicorn (Alternative ASGI)

Si vous préférez utiliser uvicorn (serveur ASGI), vous devrez adapter l'application :

```bash
pip install uvicorn asgiref

# Lancement
uvicorn wsgi:server --host 0.0.0.0 --port 8051 --workers 4
```

**Note :** Dash est conçu pour WSGI (Gunicorn), pas ASGI (Uvicorn). Gunicorn est recommandé.

### Option 3 : Docker

#### Créer un Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Exposer le port
EXPOSE 8051

# Variables d'environnement par défaut
ENV DEBUG=False
ENV HOST=0.0.0.0
ENV PORT=8051

# Lancer l'application avec Gunicorn
CMD ["gunicorn", "-c", "gunicorn_config.py", "wsgi:server"]
```

#### Construire et lancer

```bash
# Construire l'image
docker build -t veec-scorer .

# Lancer le conteneur
docker run -d \
    -p 8051:8051 \
    -e DEBUG=False \
    --name veec-scorer \
    veec-scorer
```

#### Docker Compose

Créez un fichier `docker-compose.yml` :

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8051:8051"
    environment:
      - DEBUG=False
      - HOST=0.0.0.0
      - PORT=8051
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
```

Lancez avec :

```bash
docker-compose up -d
```

## Reverse Proxy avec Nginx

Pour un déploiement professionnel, utilisez Nginx comme reverse proxy :

### Configuration Nginx

Créez `/etc/nginx/sites-available/veec-scorer` :

```nginx
server {
    listen 80;
    server_name votre-domaine.com;

    location / {
        proxy_pass http://127.0.0.1:8051;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (si nécessaire)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Assets statiques
    location /assets/ {
        alias /chemin/vers/app-complet-match/assets/;
        expires 30d;
        access_log off;
    }
}
```

Activez la configuration :

```bash
sudo ln -s /etc/nginx/sites-available/veec-scorer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Service Systemd

Pour lancer l'application au démarrage du serveur :

### Créer un service systemd

Créez `/etc/systemd/system/veec-scorer.service` :

```ini
[Unit]
Description=VEEC Scorer Application
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/chemin/vers/app-complet-match
Environment="PATH=/chemin/vers/app-complet-match/venv/bin"
ExecStart=/chemin/vers/app-complet-match/venv/bin/gunicorn -c gunicorn_config.py wsgi:server
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### Activer et démarrer le service

```bash
sudo systemctl daemon-reload
sudo systemctl enable veec-scorer
sudo systemctl start veec-scorer
sudo systemctl status veec-scorer
```

## Migration des Callbacks

L'application a été restructurée mais les callbacks de `app_original.py` doivent être migrés vers `app.py` ou extraits dans des modules séparés.

### Étapes de migration :

1. **Copier les callbacks** depuis `app_original.py` vers `app.py`
2. **Vérifier les imports** - tous les modules sont maintenant dans `src/`
3. **Tester chaque callback** individuellement
4. **(Optionnel) Extraire dans des modules** :
   - `src/callbacks/score.py` - Callbacks de score et rotation
   - `src/callbacks/substitution.py` - Callbacks de remplacement
   - `src/callbacks/libero.py` - Callbacks spécifiques Libero
   - `src/callbacks/ui.py` - Callbacks d'interface

## Maintenance

### Logs

```bash
# Voir les logs en temps réel
tail -f logs/access.log
tail -f logs/error.log

# Voir les logs systemd
sudo journalctl -u veec-scorer -f
```

### Redémarrage

```bash
# Avec systemd
sudo systemctl restart veec-scorer

# Avec Gunicorn (envoyer signal HUP pour reload)
kill -HUP $(cat gunicorn.pid)

# Avec Docker
docker restart veec-scorer
```

### Monitoring

Utilisez des outils comme :
- **Supervisor** - Gestionnaire de processus
- **Prometheus + Grafana** - Monitoring des métriques
- **Sentry** - Tracking des erreurs

## Sécurité

### Checklist de sécurité production :

- [ ] DEBUG=False dans .env
- [ ] Utiliser HTTPS (certificat SSL/TLS)
- [ ] Configurer un firewall (ufw, iptables)
- [ ] Limiter les connexions (rate limiting)
- [ ] Sauvegardes régulières des données
- [ ] Mises à jour de sécurité régulières

## Performance

### Optimisations :

1. **Caching** - Utiliser Redis pour les données fréquemment accédées
2. **CDN** - Servir les assets statiques via un CDN
3. **Compression** - Activer gzip dans Nginx
4. **Load Balancing** - Déployer plusieurs instances derrière un load balancer

## Troubleshooting

### L'application ne démarre pas

```bash
# Vérifier les logs
tail -n 50 logs/error.log

# Vérifier les dépendances
pip list

# Tester l'import
python -c "from app import app; print('OK')"
```

### Erreurs de module introuvable

```bash
# Vérifier que tous les __init__.py existent
find . -type d -name "__pycache__" -prune -o -type d -exec test -f {}/__init__.py \; -print

# Ajouter le répertoire au PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/chemin/vers/app-complet-match"
```

## Support

Pour toute question ou problème :
- Consultez le README.md
- Vérifiez les issues GitHub
- Contactez l'équipe de développement

---

**Version:** 2.0 (Restructuré)
**Date:** 2025-11-25
