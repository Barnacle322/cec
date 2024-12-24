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

# Install glibc and generate the required locales
RUN apk --no-cache add ca-certificates wget && \
    wget -q -O /etc/apk/keys/sgerrand.rsa.pub https://alpine-pkgs.sgerrand.com/sgerrand.rsa.pub && \
    wget https://github.com/sgerrand/alpine-pkg-glibc/releases/download/2.35-r0/glibc-2.35-r0.apk && \
    apk add glibc-2.35-r0.apk && \
    rm glibc-2.35-r0.apk && \
    wget https://github.com/sgerrand/alpine-pkg-glibc/releases/download/2.35-r0/glibc-bin-2.35-r0.apk && \
    apk add glibc-bin-2.35-r0.apk && \
    rm glibc-bin-2.35-r0.apk && \
    /usr/glibc-compat/bin/localedef -i ru_RU -f UTF-8 ru_RU.UTF-8 && \
    /usr/glibc-compat/bin/localedef -i en_US -f UTF-8 en_US.UTF-8

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