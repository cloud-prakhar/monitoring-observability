FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 300 -r requirements.txt

COPY app.py .

EXPOSE 8085

CMD ["python", "app.py"]
