FROM node:22-bookworm-slim

USER root

RUN apt-get update \
  && apt-get install -y --no-install-recommends python3 python3-pip python3-venv ca-certificates make g++ \
  && npm install -g n8n@latest \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN python3 -m venv /opt/venv \
  && /opt/venv/bin/pip install --no-cache-dir -r /app/requirements.txt

COPY RPL.json /app/RPL.json
COPY scripts /app/scripts
COPY start.sh /app/start.sh

RUN chmod +x /app/start.sh \
  && chown -R node:node /app /opt/venv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    N8N_USER_FOLDER=/home/node

EXPOSE 5678

CMD ["/app/start.sh"]
