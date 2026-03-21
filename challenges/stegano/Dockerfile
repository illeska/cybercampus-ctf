FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir flask Pillow

COPY . .

EXPOSE 5007

CMD ["python3", "app.py"]