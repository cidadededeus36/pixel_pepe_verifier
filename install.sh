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

# Create data directory
echo -e "${GREEN}Setting up data directory...${NC}"
mkdir -p data
chmod 700 data

# Create virtual environment
echo -e "${GREEN}Setting up Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Install/upgrade pip
echo -e "${GREEN}Upgrading pip...${NC}"
pip install --upgrade pip

# Install requirements
echo -e "${GREEN}Installing dependencies...${NC}"
pip install -r requirements.txt

# Set up systemd service
echo -e "${GREEN}Setting up systemd service...${NC}"
sudo cp ordinal-bot.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable and start the service
echo -e "${GREEN}Starting bot service...${NC}"
sudo systemctl enable ordinal-bot.service
sudo systemctl start ordinal-bot.service

# Verify service is running
if systemctl is-active --quiet ordinal-bot.service; then
    echo -e "\n${GREEN}Installation successful! Bot service is running.${NC}\n"
else
    echo -e "\n${RED}Warning: Bot service failed to start. Check logs below:${NC}\n"
    sudo systemctl status ordinal-bot.service
    exit 1
fi

# Print helpful commands
echo -e "${YELLOW}Useful commands:${NC}"
echo -e "  • View status: ${GREEN}sudo systemctl status ordinal-bot${NC}"
echo -e "  • View logs: ${GREEN}journalctl -u ordinal-bot -f${NC}"
echo -e "  • Restart bot: ${GREEN}sudo systemctl restart ordinal-bot${NC}"
echo -e "  • Stop bot: ${GREEN}sudo systemctl stop ordinal-bot${NC}"

