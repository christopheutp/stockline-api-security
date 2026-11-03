# Image de StockLine en trois étapes (exercice 5) :
#   base       : Python et les seules dépendances de production
#   tests      : base + outils de test + tests (jamais déployée)
#   production : base + le code de l'application, utilisateur sans privilèges
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 && useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin stockline \
 && mkdir /data && chown stockline /data

FROM base AS tests
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
CMD ["pytest", "-q", "-p", "no:cacheprovider"]

FROM base AS production
COPY app ./app
USER stockline
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
