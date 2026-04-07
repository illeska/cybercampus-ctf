FROM python:3.11-slim

WORKDIR /app

# Dépendances
RUN pip install pyinstaller flask

# Copier les sources
COPY licenseguard.py .
COPY serve.py .
COPY templates/ ./templates/

# Compiler le binaire PyInstaller (ce que le joueur télécharge et reverse)
RUN pyinstaller --onefile --strip --name licenseguard licenseguard.py && \
    mkdir -p /app/public && \
    cp /app/dist/licenseguard /app/public/licenseguard && \
    rm -rf build *.spec __pycache__

EXPOSE 5008

CMD ["python3", "serve.py"]