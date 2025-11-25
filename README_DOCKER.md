# 🐳 VEEC Scorer - Configuration Docker

> **Configuration Docker production-ready pour l'application VEEC Scorer**

## 🎯 Démarrage Ultra-Rapide

### 3 Méthodes au Choix

#### 1️⃣ Script Interactif (Recommandé)
```bash
./start-docker.sh
```
Interface interactive pour choisir le mode (production/développement/build/clean)

#### 2️⃣ Docker Compose
```bash
# Production
docker-compose up -d

# Développement
docker-compose -f docker-compose.dev.yml up
```

#### 3️⃣ Docker Direct
```bash
docker build -t veec-scorer .
docker run -d -p 8051:8051 --name veec-scorer veec-scorer:latest
```

### Accès Application
**→ http://localhost:8051**

---

## 📦 Fichiers Fournis

```
app-complet-match/
├── Dockerfile                   🐳 Image production multi-stage
├── docker-compose.yml          🚀 Configuration production
├── docker-compose.dev.yml      🛠️  Configuration développement
├── .dockerignore               ⚡ Optimisation build
├── start-docker.sh             🎬 Script interactif
│
├── DOCKER.md                   📖 Guide complet Docker (détails avancés)
├── QUICKSTART_DOCKER.md        ⚡ Guide rapide (2 minutes)
└── DOCKER_SUMMARY.md           📊 Résumé technique
```

---

## 🎨 Caractéristiques

### 🏗️ Architecture Multi-Stage
```dockerfile
Stage 1 (Builder)    → Compilation dépendances
    ↓
Stage 2 (Runtime)    → Image finale optimisée
```

**Avantages :**
- Image finale légère (~200-300 MB)
- Build rapide avec cache Docker
- Sécurité renforcée

### 🔐 Sécurité

| Aspect | Implémentation |
|--------|----------------|
| Utilisateur | Non-root (veec:1000) |
| Secrets | Externalisés (.env) |
| Image de base | python:3.11-slim (minimale) |
| Vulnérabilités | Compatible Trivy/Snyk |
| Logs | Stdout/stderr (12-factor) |

### ⚡ Performance

| Métrique | Valeur |
|----------|--------|
| Workers Gunicorn | 4 |
| Threads/worker | 2 |
| Timeout | 120s |
| Max requests | 1000 |
| Keep-alive | 5s |

### 🏥 Health Check

```yaml
Interval:     30s
Timeout:      10s
Retries:      3
Start period: 40s
```

### 📊 Ressources

```yaml
Réservées: 0.5 CPU / 256 MB RAM
Limites:   2.0 CPU / 1 GB RAM
```

---

## 📝 Commandes Utiles

### Gestion Container

```bash
# Démarrer
docker-compose up -d

# Arrêter
docker-compose down

# Redémarrer
docker-compose restart

# Rebuild
docker-compose up -d --build

# État
docker-compose ps

# Stats temps réel
docker stats veec-scorer
```

### Logs

```bash
# Temps réel
docker-compose logs -f veec-scorer

# 100 dernières lignes
docker-compose logs --tail=100 veec-scorer

# Dernière heure
docker-compose logs --since 1h veec-scorer
```

### Maintenance

```bash
# Entrer dans le container
docker exec -it veec-scorer bash

# Nettoyer images inutilisées
docker image prune -a

# Nettoyer tout
docker system prune -a --volumes
```

---

## 🌐 Déploiement Production

### Variables d'Environnement

Créer `.env` :
```env
DASH_DEBUG=False
HOST=0.0.0.0
PORT=8051
TZ=Europe/Paris
```

### Avec Nginx

`/etc/nginx/sites-available/veec-scorer` :
```nginx
server {
    listen 80;
    server_name scorer.votredomaine.com;

    location / {
        proxy_pass http://localhost:8051;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Avec SSL (Certbot)

```bash
# Installer Certbot
sudo apt install certbot python3-certbot-nginx

# Obtenir certificat
sudo certbot --nginx -d scorer.votredomaine.com

# Renouvellement auto
sudo certbot renew --dry-run
```

---

## 🧪 Tests et Validation

### Tester le Build

```bash
# Build
docker build -t veec-scorer:test .

# Vérifier la taille
docker images veec-scorer:test

# Run test
docker run --rm -p 8051:8051 veec-scorer:test
```

### Health Check

```bash
# Vérifier la santé
docker inspect veec-scorer | grep -A 10 Health

# Tester manuellement
curl http://localhost:8051
```

### Load Testing

```bash
# Installer hey (Go)
go install github.com/rakyll/hey@latest

# Test de charge
hey -n 1000 -c 10 http://localhost:8051
```

---

## 🚢 Cas d'Usage

### 💻 Développement Local

```bash
# Avec hot-reload
docker-compose -f docker-compose.dev.yml up

# Modifications détectées automatiquement
# Pas besoin de rebuild
```

### 🏢 Serveur de Production

```bash
# Déploiement
ssh user@serveur.com
git clone <repo>
cd app-complet-match
docker-compose up -d

# Monitoring
docker-compose logs -f
```

### ☁️ Cloud (AWS/GCP/Azure)

```bash
# Build multi-architecture
docker buildx build --platform linux/amd64,linux/arm64 -t veec-scorer .

# Push vers registry
docker tag veec-scorer:latest registry.example.com/veec-scorer
docker push registry.example.com/veec-scorer
```

### 🎯 Docker Swarm

```bash
# Init swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml veec

# Scale
docker service scale veec_veec-scorer=3
```

---

## 🛠️ Configuration Avancée

### Personnaliser Workers

Modifier `Dockerfile` :
```dockerfile
CMD ["gunicorn", "wsgi:server", \
     "--workers", "8",  # ← Augmenter ici
     "--bind", "0.0.0.0:8051"]
```

### Changer le Port

Modifier `docker-compose.yml` :
```yaml
ports:
  - "8080:8051"  # Port externe:interne
```

### Ajouter Volumes

```yaml
volumes:
  - ./data:/app/data         # Persistance données
  - ./logs:/app/logs         # Logs
  - ./config.json:/app/config.json  # Config custom
```

---

## 🐛 Dépannage

### Problème : Container ne démarre pas

```bash
# 1. Vérifier logs
docker-compose logs veec-scorer

# 2. Vérifier port disponible
netstat -tulpn | grep 8051

# 3. Rebuild complet
docker-compose down -v
docker-compose up -d --build
```

### Problème : Performance faible

```bash
# Augmenter ressources dans docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 2G
```

### Problème : Erreur de permission

```bash
# Corriger permissions volumes
sudo chown -R 1000:1000 ./logs ./data

# Vérifier dans container
docker exec -it veec-scorer id
```

---

## 📚 Documentation

| Document | Objectif | Audience |
|----------|----------|----------|
| **QUICKSTART_DOCKER.md** | Démarrage express 2 min | Débutants |
| **DOCKER.md** | Guide complet Docker | DevOps |
| **DOCKER_SUMMARY.md** | Résumé technique | Tous |
| **DEPLOYMENT.md** | Déploiement général | Production |
| **README_STRUCTURE.md** | Architecture app | Développeurs |

---

## ✅ Checklist Production

Avant de déployer en production :

- [ ] Variables `.env` configurées
- [ ] Port 8051 ouvert dans firewall
- [ ] Reverse proxy configuré (Nginx/Traefik)
- [ ] SSL/TLS activé (Certbot/Let's Encrypt)
- [ ] Monitoring configuré (logs/metrics)
- [ ] Backup strategy définie
- [ ] Health checks fonctionnels
- [ ] Ressources dimensionnées
- [ ] Security scan effectué (Trivy)
- [ ] Tests de charge réalisés

---

## 🎯 Support

**Problème ?** Consultez dans l'ordre :

1. **QUICKSTART_DOCKER.md** - Dépannage rapide
2. **DOCKER.md** - Documentation complète
3. **Logs** - `docker-compose logs -f`
4. **Issues** - Créer une issue GitHub

---

<div align="center">

**🎉 Configuration Docker Production-Ready**

**Version:** 2.0
**Date:** 2025-11-25
**Status:** ✅ Production Ready

[Documentation](#-documentation) • [Démarrage](#-démarrage-ultra-rapide) • [Support](#-support)

</div>
