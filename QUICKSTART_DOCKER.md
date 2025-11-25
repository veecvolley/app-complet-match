# 🚀 Démarrage Rapide avec Docker

Guide ultra-rapide pour déployer VEEC Scorer avec Docker en 2 minutes.

## ⚡ Démarrage Express

### Option 1 : Script Automatique (Le Plus Simple)

```bash
./start-docker.sh
```

Suivez les instructions à l'écran et choisissez :
- **1** pour Production
- **2** pour Développement

### Option 2 : Commande Directe

```bash
# Production
docker-compose up -d

# Développement (avec hot-reload)
docker-compose -f docker-compose.dev.yml up
```

## 🌐 Accéder à l'Application

Une fois démarré, ouvrez votre navigateur :

**→ http://localhost:8051**

## 📋 Commandes Essentielles

```bash
# Voir les logs en temps réel
docker-compose logs -f veec-scorer

# Arrêter l'application
docker-compose down

# Redémarrer
docker-compose restart

# Reconstruire et redémarrer
docker-compose up -d --build

# Voir l'état
docker-compose ps

# Statistiques en temps réel
docker stats veec-scorer
```

## 🛠️ Configuration

### Variables d'Environnement

Créez un fichier `.env` :

```env
DASH_DEBUG=False
HOST=0.0.0.0
PORT=8051
TZ=Europe/Paris
```

### Personnaliser le Port

Modifier `docker-compose.yml` :

```yaml
ports:
  - "8080:8051"  # Accès via http://localhost:8080
```

## 🔍 Dépannage Rapide

### L'application ne démarre pas

```bash
# Vérifier les logs
docker-compose logs veec-scorer

# Redémarrer proprement
docker-compose down
docker-compose up -d
```

### Port 8051 déjà utilisé

```bash
# Changer le port dans docker-compose.yml
ports:
  - "8052:8051"  # Utiliser 8052 au lieu de 8051
```

### Rebuild complet

```bash
# Tout nettoyer et recommencer
docker-compose down -v
docker-compose up -d --build
```

## 📊 Monitoring

### Health Check

```bash
# Vérifier la santé du conteneur
docker inspect veec-scorer | grep -A 10 Health
```

### Logs de Production

```bash
# Dernières 100 lignes
docker-compose logs --tail=100 veec-scorer

# Logs de la dernière heure
docker-compose logs --since 1h veec-scorer

# Suivre les logs
docker-compose logs -f veec-scorer
```

## 🚢 Déploiement Production

### Serveur Distant

```bash
# Via SSH
ssh user@serveur.com
git clone <repo>
cd app-complet-match
docker-compose up -d
```

### Avec Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name scorer.votredomaine.com;

    location / {
        proxy_pass http://localhost:8051;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Avec HTTPS (Let's Encrypt)

```bash
# Installer Certbot
sudo apt install certbot python3-certbot-nginx

# Obtenir un certificat
sudo certbot --nginx -d scorer.votredomaine.com
```

## 📦 Fichiers Docker Fournis

| Fichier | Description |
|---------|-------------|
| `Dockerfile` | Image de production optimisée multi-stage |
| `docker-compose.yml` | Configuration production |
| `docker-compose.dev.yml` | Configuration développement |
| `.dockerignore` | Fichiers exclus du build |
| `start-docker.sh` | Script de démarrage interactif |
| `DOCKER.md` | Documentation complète Docker |

## 🎯 Cas d'Usage

### Développement Local

```bash
# Hot-reload activé
docker-compose -f docker-compose.dev.yml up
```

### Tests

```bash
# Build et test
docker build -t veec-scorer:test .
docker run -p 8051:8051 veec-scorer:test
```

### Production

```bash
# Démarrage production avec logs
docker-compose up -d && docker-compose logs -f
```

## 📚 Documentation Complète

Pour plus de détails, consultez :

- **[DOCKER.md](DOCKER.md)** - Guide Docker complet
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Guide de déploiement général
- **[README_STRUCTURE.md](README_STRUCTURE.md)** - Architecture de l'app

---

**Besoin d'aide ?** Consultez la [documentation complète Docker](DOCKER.md)
