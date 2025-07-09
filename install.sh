#!/usr/bin/env bash
set -e

# Log helper
log() {
    echo "[INFO] $1"
}

# Ask for user input
read -rp "Enter AdGuard username: " ADGUARD_USER
read -rp "Enter AdGuard password: " ADGUARD_PASS
read -rp "Enter AdGuard URL (e.g. http://127.0.0.1): " ADGUARD_URL

log "Creating .env file..."
cat << EOF > .env
ADGUARD_USER=${ADGUARD_USER}
ADGUARD_PASS=${ADGUARD_PASS}
ADGUARD_URL=${ADGUARD_URL}
EOF

log ".env file created with the following content:"
cat .env

#log "Creating temporary directory..."
#mkdir -p tmp

#log "Changing into tmp directory..."
#cd tmp

#log "Downloading master.zip from GitHub..."
#wget \
#  --referer=https://github.com/arsscriptum/adguard-api-ctrl \
#  -O master.zip \
#  https://github.com/arsscriptum/adguard-api-ctrl/archive/refs/heads/master.zip

#log "Unzipping master.zip..."
#unzip -o master.zip

#cd adguard-api-ctrl-master

log "Creating Python virtual environment..."
python3 -m venv pyenv

log "Activating virtual environment..."
source pyenv/bin/activate

log "Installing Python requirements..."
pip install --upgrade pip
pip install -r requirements.txt

CURRENT=$(pwd)
FULLPY="${CURRENT}/pyenv/bin/python"
FULLSCRIPT="${CURRENT}/adguard_api_server.py"

log "Running the adguard_api_server.py script..."
$FULLPY $FULLSCRIPT
