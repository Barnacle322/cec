FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    locales \
    && ln -sf /usr/share/zoneinfo/Asia/Bishkek /etc/localtime \
    && echo "Asia/Bishkek" > /etc/timezone \
    && sed -i 's/^# *\(ru_RU.UTF-8\)/\1/' /etc/locale.gen \
    && sed -i 's/^# *\(en_US.UTF-8\)/\1/' /etc/locale.gen \
    && locale-gen \
    && rm -rf /var/lib/apt/lists/*

ENV LANG=ru_RU.UTF-8
ENV LANGUAGE=ru_RU:ru
ENV LC_ALL=ru_RU.UTF-8

COPY src/ app/
COPY pyproject.toml /app
COPY uv.lock /app

WORKDIR /app

RUN pip install uv
RUN uv sync --frozen --no-install-project
RUN uv pip install granian
RUN rm -rf /root/.cache/pip/*

ENV PORT=80

RUN uv run pybabel compile -d ./project/translations
CMD ["uv", "run", "granian", "--interface", "wsgi", "--port", "80", "--host", "0.0.0.0", "--workers", "3", "project:application"]