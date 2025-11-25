"""
WSGI Entry Point pour déploiement en production
Utilisé par Gunicorn ou d'autres serveurs WSGI
"""
from app import app

# Expose le serveur Flask sous-jacent de Dash
server = app.server

if __name__ == "__main__":
    server.run()
