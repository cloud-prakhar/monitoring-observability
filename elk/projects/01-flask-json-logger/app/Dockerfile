# Dockerfile for the Flask JSON Logger (ELK Project 1)
#
# python:3.12-slim is a small Debian-based image. The app only needs Flask.

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 300 -r requirements.txt

COPY app.py .

EXPOSE 8091

CMD ["python", "app.py"]
