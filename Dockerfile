# -----------------------------------------
# Dockerfile - CyberCampus CTF (Flask + Gunicorn)
# -----------------------------------------
FROM python:3.11-slim

# Répertoire de travail à l'intérieur du conteneur
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le reste du code dans le conteneur
COPY . .

# Définir la variable d'environnement Flask
ENV FLASK_ENV=production

# Exposer le port 5000
EXPOSE 5000

# Commande pour lancer Gunicorn avec Flask
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
