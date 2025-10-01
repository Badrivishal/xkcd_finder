#!/bin/bash

# Check arguments
if [ -z "$1" ]; then
    echo "No HF_TOKEN provided. Please provide the token as the first argument."
    exit 1
fi

if [ -z "$2" ]; then
    echo "No SSH private key path provided. Please provide it as the second argument."
    exit 1
fi

HF_TOKEN="$1"
KEY_PATH="$2"

# Check if the provided key exists
if [ ! -f "$KEY_PATH" ]; then
    echo "SSH private key $KEY_PATH not found. Please ensure it exists."
    exit 1
fi

# Monitor if the application is running and append result to log file
curl -sI http://paffenroth-23.dyn.wpi.edu:8011 | grep "200 OK" >> ~/xkcd_finder_monitor.log
if [ $? -eq 0 ]; then
    echo "$(date): Application is running." >> ~/xkcd_finder_monitor.log
else
    echo "$(date): Application is NOT running." >> ~/xkcd_finder_monitor.log
    # Log in via SSH and rerun deploy.sh by pulling it with curl and executing directly
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -p 22011 student-admin@paffenroth-23.dyn.wpi.edu \
        "curl -fsSL https://github.com/Badrivishal/xkcd_finder/raw/refs/heads/main/deployment_scripts/deploy.sh | sudo bash -s -- $HF_TOKEN"
fi