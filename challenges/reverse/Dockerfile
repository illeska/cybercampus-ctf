FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y binutils && rm -rf /var/lib/apt/lists/*

RUN pip install pyinstaller flask

COPY licenseguard.py .
COPY serve.py .
COPY templates/ ./templates/

RUN pyinstaller --onefile --strip --name licenseguard licenseguard.py && \
    mkdir -p /app/public && \
    cp /app/dist/licenseguard /app/public/licenseguard && \
    rm -rf build *.spec __pycache__

EXPOSE 5008

CMD ["python3", "serve.py"]