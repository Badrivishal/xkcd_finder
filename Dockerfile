FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; else pip install --no-cache-dir gradio; fi
COPY . .

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && \
    apt-get upgrade -yq ca-certificates && \
    apt-get install -yq --no-install-recommends \
    prometheus-node-exporter

EXPOSE 7860
EXPOSE 8000
EXPOSE 9100
ENV GRADIO_SERVER_NAME=0.0.0.0

CMD bash -c "prometheus-node-exporter --web.listen-address=':9100' & python app.py"