FROM python:3.13.0rc1-slim

# Set environment variables to prevent Python from writing .pyc files and to ensure output is not buffered.
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

ENV PIP_DEFAULT_TIMEOUT=120

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml /app

RUN poetry install --only main --no-root

COPY . /app

EXPOSE 80

CMD ["uvicorn", "maybee_backend.main:app", "--host", "0.0.0.0", "--port", "80"]