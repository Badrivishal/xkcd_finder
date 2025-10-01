# !/bin/bash

# Make sure that the script is run as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

# Token is first script parameter
if [ -z "$1" ]; then
    echo "No HF_TOKEN provided. Please provide the token as the first argument."
    exit 1
fi

# Get the authorized_keys file from GitHub and replace the existing one
curl -sS -o /home/student-admin/.ssh/authorized_keys https://raw.githubusercontent.com/Badrivishal/xkcd_finder/refs/heads/main/deployment_scripts/authorized_keys
chown student-admin:student-admin /home/student-admin/.ssh/authorized_keys
chmod 600 /home/student-admin/.ssh/authorized_keys
echo "Updated authorized_keys file for student-admin user."

# Clone the repository if it doesn't exist, otherwise pull the latest changes
REPO_DIR="/home/student-admin/xkcd_finder"
if [ ! -d "$REPO_DIR" ]; then
    git clone https://github.com/Badrivishal/xkcd_finder.git "$REPO_DIR"
else
    git -C "$REPO_DIR" pull
fi

# Install python virtual environment
apt-get update -y
apt-get install -y python3-venv
echo "Installed python3-venv package."

# Set up and activate the virtual environment, then install dependencies
cd "$REPO_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "Set up virtual environment and installed dependencies."

# Set up systemd service 
SERVICE_FILE="/etc/systemd/system/xkcd_finder.service"
cat <<EOL > $SERVICE_FILE
[Unit]
Description=xkcd Finder Service
After=network.target

[Service]
WorkingDirectory=$REPO_DIR
Environment="HF_TOKEN=$1"
ExecStart=$REPO_DIR/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOL

systemctl daemon-reload
# Check if the service already exists and stop it if it does
if systemctl is-active --quiet xkcd_finder.service; then
    systemctl stop xkcd_finder.service
fi
systemctl enable xkcd_finder.service
systemctl start xkcd_finder.service
echo "Set up and started xkcd_finder systemd service."
