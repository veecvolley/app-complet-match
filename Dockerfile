# VEEC Scorer - Production Dockerfile
# Multi-stage build pour optimiser la taille de l'image

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim as builder

WORKDIR /build

# Installer les dépendances de build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copier seulement requirements.txt pour exploiter le cache Docker
COPY requirements.txt .

# Installer les dépendances Python dans un environnement virtuel
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.11-slim

# Métadonnées
LABEL maintainer="VEEC Volleyball Team"
LABEL description="VEEC Scorer - Application de suivi de match de volleyball"
LABEL version="2.0"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    DASH_DEBUG=False \
    HOST=0.0.0.0 \
    PORT=8051

# Créer un utilisateur non-root pour la sécurité
RUN groupadd -r veec && useradd -r -g veec -u 1000 veec

# Définir le répertoire de travail
WORKDIR /app

# Copier l'environnement virtuel depuis le builder
COPY --from=builder /opt/venv /opt/venv

# Copier l'application
COPY --chown=veec:veec . .

# Créer les répertoires nécessaires
RUN mkdir -p /app/logs && chown -R veec:veec /app

# Passer à l'utilisateur non-root
USER veec

# Exposer le port
EXPOSE 8051

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8051').read()" || exit 1

# Commande de démarrage avec gunicorn
CMD ["gunicorn", \
    "wsgi:server", \
    "--bind", "0.0.0.0:8051", \
    "--workers", "4", \
    "--worker-class", "sync", \
    "--threads", "2", \
    "--timeout", "120", \
    "--keep-alive", "5", \
    "--max-requests", "1000", \
    "--max-requests-jitter", "100", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "--log-level", "info"]
