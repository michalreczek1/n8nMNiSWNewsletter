FROM n8nio/n8n:latest

USER root

RUN apk add --no-cache python3 py3-pip py3-virtualenv

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
    N8N_USER_FOLDER=/home/node/.n8n

USER node

EXPOSE 5678

CMD ["/app/start.sh"]
