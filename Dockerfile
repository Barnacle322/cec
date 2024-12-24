FROM python:3.12.0-alpine

# Install necessary packages for locales and timezone configuration
RUN apk update && apk add --no-cache \
    bash \
    gcc \
    musl-dev \
    libc-dev \
    libintl \
    gettext \
    tzdata \
    && apk add --no-cache --virtual .build-deps \
    build-base \
    && cp /usr/share/zoneinfo/Asia/Bishkek /etc/localtime \
    && echo "Asia/Bishkek" > /etc/timezone \
    && apk del .build-deps

# Generate the required locales
RUN apk add --no-cache \
    alpine-conf \
    && setup-locale -i ru_RU.UTF-8 -f UTF-8 \
    && setup-locale -i en_US.UTF-8 -f UTF-8

# Set environment variables for locale
ENV LANG ru_RU.UTF-8
ENV LANGUAGE ru_RU:ru
ENV LC_ALL ru_RU.UTF-8

COPY src/ app/
COPY pyproject.toml /app
COPY poetry.lock /app

WORKDIR /app

RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --without dev --no-root --no-cache
RUN pip install granian
RUN rm -rf /root/.cache/pip/*

ENV PORT 80

RUN exec poetry run pybabel compile -d ./project/translations
CMD exec poetry run granian --interface wsgi --port $PORT --host 0.0.0.0 --workers 5 --threads 8 project:application