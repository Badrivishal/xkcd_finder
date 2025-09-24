# !/bin/bash

# Make sure that the script is run as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root"
    exit 1
fi

# Make sure that parameter is passed and that /root/.ssh/id_ed25519 exists
if [ -z "$1" ]; then
    echo "No HF_TOKEN provided. Please provide the token as the first argument."
    exit 1
fi
if [ ! -f /root/.ssh/id_ed25519 ]; then
    echo "SSH private key /root/.ssh/id_ed25519 not found. Please ensure it exists."
    exit 1
fi

# Monitor if the application is running and append result to log file
curl -sI http://paffenroth-23.dyn.wpi.edu:8011 | grep "200 OK" >> /var/log/xkcd_finder_monitor.log
if [ $? -eq 0 ]; then
    echo "$(date): Application is running." >> /var/log/xkcd_finder_monitor.log
else
    echo "$(date): Application is NOT running." >> /var/log/xkcd_finder_monitor.log
    # Log in via SSH and rerun deploy.sh by pulling it with curl and executing directly
    ssh -i /root/.ssh/id_ed25519 -o StrictHostKeyChecking=no -p 22011 student-admin@paffenroth-23.dyn.wpi.edu \
        "curl -fsSL https://raw.githubusercontent.com/Badrivishal/xkcd_finder/refs/heads/deployment/deployment_scripts/deploy.sh | sudo bash -s -- $1"
fi