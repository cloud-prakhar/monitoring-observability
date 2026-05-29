# Dockerfile for the Flask Web API
#
# python:3.12-slim is a small Debian-based image (~50MB vs ~900MB for the full image).
# "slim" removes optional packages and documentation, keeping only what Python needs.

FROM python:3.12-slim

WORKDIR /app

# Copy requirements first so Docker can cache the pip install layer.
# If only app.py changes on rebuild, pip install is skipped.
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 300 -r requirements.txt

COPY app.py .

EXPOSE 8081

CMD ["python", "app.py"]
