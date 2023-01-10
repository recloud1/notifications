FROM python:3.10

ENV POETRY_VERSION=1.2.0

RUN apt-get update \
    && pip install --no-cache-dir poetry==$POETRY_VERSION \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /var/project

COPY ./pyproject.toml ./poetry.lock ./

RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi

COPY ./ ./


ENV PYTHONPATH = ${PYTHONPATH}:/var/project/src
WORKDIR /var/project/src

ENTRYPOINT ["python", "-m", "gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
