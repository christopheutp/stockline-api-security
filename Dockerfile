FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 stockline \
    && mkdir -p /data \
    && chown stockline:stockline /data

COPY app/ ./app/

ENV DATABASE_URL=sqlite:////data/stockline.db
USER stockline
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
