FROM python:3.12.5-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

COPY requirements-app.txt .
RUN pip install --no-cache-dir -r requirements-app.txt

COPY migrations migrations
COPY src src
COPY data data
COPY tests tests

RUN useradd --create-home app
USER app

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "profile_pipeline.web:create_app()"]
