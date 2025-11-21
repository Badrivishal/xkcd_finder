gcloud run deploy xkcd-finder \
    --set-env-vars=HF_TOKEN=$1 \
    --memory=2Gi \
    --startup-probe=timeoutSeconds=240,periodSeconds=240,tcpSocket.port=7860 \
    --image docker.io/mrpetzi/xkcd_finder:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 7860