#!/bin/bash

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Installing Pixel Pepes Verifier Bot...${NC}\n"

# Check for required commands
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}Error: python3 is required but not installed.${NC}" >&2; exit 1; }
command -v pip3 >/dev/null 2>&1 || { echo -e "${RED}Error: pip3 is required but not installed.${NC}" >&2; exit 1; }
command -v sudo >/dev/null 2>&1 || { echo -e "${RED}Error: sudo is required but not installed.${NC}" >&2; exit 1; }

# Check if running as root
if [ "$(id -u)" -eq 0 ]; then
    echo -e "${RED}Error: This script should not be run as root${NC}" >&2
    exit 1
fi

# Prompt for bot username
read -p "Enter username for the bot service (default: verifier-bot): " BOT_USER
BOT_USER=${BOT_USER:-verifier-bot}

# Check if user already exists
if id "$BOT_USER" &>/dev/null; then
    echo -e "${YELLOW}User $BOT_USER already exists${NC}"
else
    echo -e "${GREEN}Creating user $BOT_USER...${NC}"
    sudo useradd -r -m -s /bin/bash "$BOT_USER"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create user $BOT_USER${NC}"
        exit 1
    fi
fi

# Get the current directory
CURRENT_DIR=$(pwd)
BOT_HOME="/home/$BOT_USER/pixel_pepe_verifier"

# Create bot home directory
echo -e "${GREEN}Creating bot directory at $BOT_HOME...${NC}"
sudo mkdir -p "$BOT_HOME"

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo -e "${YELLOW}Creating from .env.example...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}Please edit .env with your bot token and guild ID${NC}\n"
    else
        echo -e "${RED}Error: .env.example not found${NC}" >&2
        exit 1
    fi
fi

# Rename bot script if needed
if [ -f "ordinal_bot.py" ] && [ ! -f "verifier_bot.py" ]; then
    echo -e "${GREEN}Renaming bot script from ordinal_bot.py to verifier_bot.py...${NC}"
    cp ordinal_bot.py verifier_bot.py
fi

# Copy files to bot directory
echo -e "${GREEN}Copying files to $BOT_HOME...${NC}"
sudo cp -r ./* "$BOT_HOME/"
sudo cp .env "$BOT_HOME/" 2>/dev/null || echo -e "${YELLOW}No .env file to copy${NC}"

# Set permissions
echo -e "${GREEN}Setting permissions...${NC}"
sudo chown -R "$BOT_USER":"$BOT_USER" "$BOT_HOME"
sudo chmod -R 750 "$BOT_HOME"

# Create data directory with proper permissions
echo -e "${GREEN}Setting up data directory...${NC}"
sudo mkdir -p "$BOT_HOME/data"
sudo chmod 700 "$BOT_HOME/data"
sudo chown -R "$BOT_USER":"$BOT_USER" "$BOT_HOME/data"

# Set up Python virtual environment
echo -e "${GREEN}Setting up Python virtual environment...${NC}"
sudo -u "$BOT_USER" bash -c "cd $BOT_HOME && python3 -m venv venv"

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
sudo -u "$BOT_USER" bash -c "cd $BOT_HOME && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

# Create systemd service file
echo -e "${GREEN}Creating systemd service file...${NC}"
cat > verifier-bot.service << EOF
[Unit]
Description=Pixel Pepes Ordinal Verification Bot
After=network.target

[Service]
Type=simple
User=$BOT_USER
WorkingDirectory=$BOT_HOME
Environment=PYTHONUNBUFFERED=1
ExecStart=$BOT_HOME/venv/bin/python3 verifier_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Set up systemd service
echo -e "${GREEN}Setting up systemd service...${NC}"
sudo cp verifier-bot.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable and start the service
echo -e "${GREEN}Starting bot service...${NC}"
sudo systemctl enable verifier-bot.service
sudo systemctl start verifier-bot.service

# Verify service is running
if systemctl is-active --quiet verifier-bot.service; then
    echo -e "\n${GREEN}Installation successful! Bot service is running.${NC}\n"
else
    echo -e "\n${RED}Warning: Bot service failed to start. Check logs below:${NC}\n"
    sudo systemctl status verifier-bot.service
    exit 1
fi

# Print helpful commands
echo -e "${YELLOW}Useful commands:${NC}"
echo -e "  • View status: ${GREEN}sudo systemctl status verifier-bot${NC}"
echo -e "  • View logs: ${GREEN}journalctl -u verifier-bot -f${NC}"
echo -e "  • Restart bot: ${GREEN}sudo systemctl restart verifier-bot${NC}"
echo -e "  • Stop bot: ${GREEN}sudo systemctl stop verifier-bot${NC}"
