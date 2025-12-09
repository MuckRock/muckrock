FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./compose/local/entrypoint /entrypoint
RUN chmod +x /entrypoint

COPY ./compose/local/start /start
RUN chmod +x /start

COPY . /app

ENTRYPOINT ["/entrypoint"]
CMD ["/start"]
