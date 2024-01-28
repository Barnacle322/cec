FROM python:3.12.0-alpine

COPY src/ app/
WORKDIR /app

RUN pip install gunicorn==20.1.0 flask==3.0.0 flask-sqlalchemy flask-login pillow google-cloud-storage psycopg psycopg-binary sqlalchemy-cockroachdb
RUN rm -rf /root/.cache/pip/*

ENV PORT 8080

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 project:application