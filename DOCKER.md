# Guide Docker - VEEC Scorer

Ce guide explique comment déployer l'application VEEC Scorer avec Docker en production et en développement.

## Prérequis

- Docker >= 20.10
- Docker Compose >= 2.0
- 1 GB RAM minimum
- 2 GB espace disque

## 🚀 Déploiement Production

### Option 1 : Docker Compose (Recommandé)

```bash
# Construire et lancer l'application
docker-compose up -d

# Vérifier les logs
docker-compose logs -f veec-scorer

# Arrêter l'application
docker-compose down
```

L'application sera accessible sur **http://localhost:8051**

### Option 2 : Docker directement

```bash
# Construire l'image
docker build -t veec-scorer:latest .

# Lancer le conteneur
docker run -d \
  --name veec-scorer \
  -p 8051:8051 \
  -e DASH_DEBUG=False \
  --restart unless-stopped \
  veec-scorer:latest

# Vérifier les logs
docker logs -f veec-scorer

# Arrêter le conteneur
docker stop veec-scorer
docker rm veec-scorer
```

## 🛠️ Développement avec Docker

### Utiliser le docker-compose de développement

```bash
# Lancer en mode développement (avec hot-reload)
docker-compose -f docker-compose.dev.yml up

# Les modifications de code seront automatiquement détectées
# L'application redémarre automatiquement
```

### Développement sans hot-reload

```bash
# Construire l'image de dev
docker build -t veec-scorer:dev .

# Lancer avec volumes montés
docker run -d \
  --name veec-scorer-dev \
  -p 8051:8051 \
  -e DASH_DEBUG=True \
  -v $(pwd)/app.py:/app/app.py \
  -v $(pwd)/src:/app/src \
  -v $(pwd)/config:/app/config \
  veec-scorer:dev
```

## 📊 Surveillance et Maintenance

### Vérifier l'état du conteneur

```bash
# État des conteneurs
docker-compose ps

# Statistiques en temps réel
docker stats veec-scorer

# Health check
docker inspect veec-scorer | grep -A 10 Health
```

### Consulter les logs

```bash
# Logs en temps réel
docker-compose logs -f veec-scorer

# Dernières 100 lignes
docker-compose logs --tail=100 veec-scorer

# Logs d'une période spécifique
docker-compose logs --since 1h veec-scorer
```

### Redémarrer l'application

```bash
# Redémarrage simple
docker-compose restart veec-scorer

# Reconstruction complète
docker-compose down
docker-compose up -d --build
```

## 🔧 Configuration Avancée

### Variables d'environnement

Créer un fichier `.env` à la racine :

```env
# Application
DASH_DEBUG=False
HOST=0.0.0.0
PORT=8051

# Timezone
TZ=Europe/Paris

# Gunicorn
GUNICORN_WORKERS=4
GUNICORN_THREADS=2
GUNICORN_TIMEOUT=120
```

Utiliser dans `docker-compose.yml` :

```yaml
services:
  veec-scorer:
    env_file:
      - .env
```

### Personnaliser le nombre de workers

Modifier dans `docker-compose.yml` :

```yaml
services:
  veec-scorer:
    environment:
      - GUNICORN_WORKERS=8  # Augmenter pour plus de performance
```

Ou créer un `Dockerfile.custom` :

```dockerfile
FROM veec-scorer:latest

# Override CMD avec plus de workers
CMD ["gunicorn", "wsgi:server", \
     "--bind", "0.0.0.0:8051", \
     "--workers", "8", \
     "--timeout", "180"]
```

### Persister les données

```yaml
services:
  veec-scorer:
    volumes:
      - ./data:/app/data        # Données applicatives
      - ./logs:/app/logs        # Logs
      - ./backups:/app/backups  # Sauvegardes
```

## 🌐 Déploiement avec Reverse Proxy

### Avec Nginx

`nginx.conf` :

```nginx
upstream veec_scorer {
    server localhost:8051;
}

server {
    listen 80;
    server_name scorer.veec.fr;

    location / {
        proxy_pass http://veec_scorer;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (si nécessaire)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Avec Traefik

`docker-compose.yml` avec Traefik :

```yaml
version: '3.8'

services:
  veec-scorer:
    image: veec-scorer:latest
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.veec.rule=Host(`scorer.veec.fr`)"
      - "traefik.http.services.veec.loadbalancer.server.port=8051"
      - "traefik.http.routers.veec.entrypoints=websecure"
      - "traefik.http.routers.veec.tls.certresolver=letsencrypt"
    networks:
      - traefik-network

networks:
  traefik-network:
    external: true
```

## 🔐 Sécurité

### Bonnes pratiques

1. **Utilisateur non-root** : Le Dockerfile utilise déjà l'utilisateur `veec` (UID 1000)

2. **Secrets** : Ne jamais inclure de secrets dans l'image
   ```bash
   # Utiliser Docker secrets
   docker secret create db_password ./db_password.txt
   ```

3. **Scan de vulnérabilités**
   ```bash
   # Avec Trivy
   docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
     aquasec/trivy:latest image veec-scorer:latest
   ```

4. **Limiter les ressources**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2.0'
         memory: 1G
   ```

## 📦 Multi-Architecture (ARM/x86)

Construire pour plusieurs architectures :

```bash
# Créer un builder multi-plateforme
docker buildx create --name multiarch --use

# Construire pour AMD64 et ARM64
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t veec-scorer:latest \
  --push \
  .
```

## 🚢 Déploiement Cloud

### Docker Swarm

```bash
# Initialiser Swarm
docker swarm init

# Déployer le stack
docker stack deploy -c docker-compose.yml veec

# Scaler l'application
docker service scale veec_veec-scorer=3
```

### Kubernetes

Créer `k8s/deployment.yml` :

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: veec-scorer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: veec-scorer
  template:
    metadata:
      labels:
        app: veec-scorer
    spec:
      containers:
      - name: veec-scorer
        image: veec-scorer:latest
        ports:
        - containerPort: 8051
        env:
        - name: DASH_DEBUG
          value: "False"
        resources:
          requests:
            memory: "256Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "2000m"
---
apiVersion: v1
kind: Service
metadata:
  name: veec-scorer-service
spec:
  selector:
    app: veec-scorer
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8051
  type: LoadBalancer
```

Déployer :

```bash
kubectl apply -f k8s/deployment.yml
```

## 🧪 Tests

### Tester l'image localement

```bash
# Build
docker build -t veec-scorer:test .

# Run en mode interactif
docker run -it --rm -p 8051:8051 veec-scorer:test

# Tester le health check
docker inspect veec-scorer-test | jq '.[0].State.Health'
```

### Tester la performance

```bash
# Installer hey
go install github.com/rakyll/hey@latest

# Test de charge
hey -n 1000 -c 10 http://localhost:8051
```

## 📝 Commandes Utiles

```bash
# Nettoyer les images inutilisées
docker image prune -a

# Voir la taille de l'image
docker images veec-scorer

# Entrer dans le conteneur
docker exec -it veec-scorer bash

# Copier des fichiers
docker cp veec-scorer:/app/logs ./logs

# Exporter l'image
docker save veec-scorer:latest | gzip > veec-scorer.tar.gz

# Importer l'image
docker load < veec-scorer.tar.gz
```

## 🐛 Dépannage

### L'application ne démarre pas

```bash
# Vérifier les logs
docker-compose logs veec-scorer

# Vérifier la santé
docker inspect veec-scorer | grep -A 10 Health

# Vérifier les ports
docker port veec-scorer
```

### Problèmes de permissions

```bash
# Changer les permissions des volumes
sudo chown -R 1000:1000 ./logs ./data
```

### Rebuild complet

```bash
# Supprimer tout et recommencer
docker-compose down -v
docker system prune -a
docker-compose up -d --build
```

---

**Documentation :** [DEPLOYMENT.md](DEPLOYMENT.md)
**Structure :** [README_STRUCTURE.md](README_STRUCTURE.md)
**Status :** [README_STATUS.md](README_STATUS.md)
