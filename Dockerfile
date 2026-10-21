FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/backend

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend /app/backend
COPY products.js /app/products.js

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && python manage.py seed_catalog --if-empty && python manage.py runserver 0.0.0.0:8000"]
