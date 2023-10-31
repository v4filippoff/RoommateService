FROM python:3.10 AS base

RUN apt-get update && apt-get install -y gettext

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    POETRY_HOME="/opt/poetry"

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

WORKDIR /app


FROM base AS builder

RUN pip install cleo urllib3 charset-normalizer

RUN curl -sSL https://install.python-poetry.org | python -

COPY poetry.lock pyproject.toml ./

FROM builder AS dev

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction


FROM builder AS stage

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-dev

COPY . .
