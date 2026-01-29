FROM python:3.11-slim

WORKDIR /app

RUN pip install flask

COPY . .

EXPOSE 5003

CMD ["python", "app.py"]