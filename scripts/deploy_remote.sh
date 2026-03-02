#!/bin/bash
# Usage: ./scripts/deploy_remote.sh [USER] [HOST] [SSH_KEY_PATH_OR_PASSWORD]

set -e

USER=$1
HOST=$2
AUTH=$3

if [ -z "$USER" ] || [ -z "$HOST" ]; then
  echo "Usage: ./scripts/deploy_remote.sh [USER] [HOST] [SSH_KEY_PATH_OR_PASSWORD]"
  exit 1
fi

SSH_CMD="ssh"
SCP_CMD="scp"
RSYNC_CMD="rsync"

# Check if AUTH is a file (key) or password
if [ -f "$AUTH" ]; then
  KEY="$AUTH"
  # Ensure key permissions are correct
  chmod 600 "$KEY"
  # Add compatibility flags for older servers or specific crypto policies
  SSH_OPTS="-o StrictHostKeyChecking=no -i $KEY -o PubkeyAcceptedKeyTypes=+ssh-rsa -o HostKeyAlgorithms=+ssh-rsa"
  SSH_WRAPPER=""
else
  # Assume it's a password
  PASSWORD="$AUTH"
  SSH_OPTS="-o StrictHostKeyChecking=no -o PubkeyAcceptedKeyTypes=+ssh-rsa -o HostKeyAlgorithms=+ssh-rsa"
  
  if ! command -v sshpass &> /dev/null; then
    echo "Error: sshpass is not installed. Cannot use password authentication."
    echo "Please install sshpass (brew install sshpass) or use SSH key."
    exit 1
  fi
  
  export SSHPASS="$PASSWORD"
  SSH_WRAPPER="sshpass -e"
fi

echo "Deploying to $USER@$HOST..."

# Test SSH connection first
echo "Testing SSH connection..."
if ! $SSH_WRAPPER $SSH_CMD $SSH_OPTS -o ConnectTimeout=5 $USER@$HOST "echo Connection success"; then
    echo "Error: Cannot establish SSH connection to $USER@$HOST"
    exit 1
fi

# 1. Sync files
echo "Syncing files..."
$SSH_WRAPPER $RSYNC_CMD -avz -e "$SSH_CMD $SSH_OPTS" \
  --exclude 'venv' \
  --exclude '__pycache__' \
  --exclude '.git' \
  --exclude 'node_modules' \
  --exclude '.next' \
  --exclude 'scripts/deploy_remote.sh' \
  ./ $USER@$HOST:~/agentmesh/

# 2. Run setup and deploy on remote
echo "Running remote deployment..."
$SSH_WRAPPER $SSH_CMD $SSH_OPTS $USER@$HOST << EOF
  set -e
  
  if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker \$USER
    echo "Docker installed. Please re-login or run 'newgrp docker' to use docker without sudo."
  fi

  # Check if docker-compose-plugin is installed (needed for 'docker compose')
  if ! docker compose version &> /dev/null; then
     echo "Installing Docker Compose Plugin..."
     sudo apt-get update && sudo apt-get install -y docker-compose-plugin || true
     # Fallback for standalone docker-compose
     if ! docker compose version &> /dev/null; then
        sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-\$(uname -s)-\$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
     fi
  fi

  cd ~/agentmesh

  # Create .env if not exists
  if [ ! -f .env ]; then
    echo "Creating .env..."
    echo "AGENTMESH_AUTH_SECRET=\$(openssl rand -hex 32)" > .env
    echo "AGENTMESH_API_KEY=\$(openssl rand -hex 32)" >> .env
    echo "POSTGRES_USER=agentmesh" >> .env
    echo "POSTGRES_PASSWORD=\$(openssl rand -hex 16)" >> .env
    echo "POSTGRES_DB=agentmesh" >> .env
    echo "NEXT_PUBLIC_API_URL=http://$HOST/api" >> .env
  fi

  echo "Building and starting services..."
  # Try 'docker compose' first, fallback to 'docker-compose'
  if docker compose version &> /dev/null; then
    sudo docker compose -f docker-compose.prod.yml up -d --build
    echo "Deployment complete! Services are running."
    sudo docker compose -f docker-compose.prod.yml ps
  else
    sudo docker-compose -f docker-compose.prod.yml up -d --build
    echo "Deployment complete! Services are running."
    sudo docker-compose -f docker-compose.prod.yml ps
  fi
EOF
