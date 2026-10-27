FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir ".[api]"
COPY alembic.ini ./
COPY migrations ./migrations
COPY scripts/load_db.py ./scripts/load_db.py
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn cropews.api.main:app --host 0.0.0.0 --port 8000"]
