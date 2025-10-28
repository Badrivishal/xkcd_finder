FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; else pip install --no-cache-dir gradio; fi
COPY . .

EXPOSE 7860
ENV GRADIO_SERVER_NAME=0.0.0.0

CMD ["python", "app.py"]