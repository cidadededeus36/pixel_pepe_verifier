#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Copy service file to systemd
sudo cp ordinal-bot.service /etc/systemd/system/

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable and start the service
sudo systemctl enable ordinal-bot.service
sudo systemctl start ordinal-bot.service

echo "Installation complete! Bot service has been installed and started."
echo "To check status: sudo systemctl status ordinal-bot"
echo "To view logs: journalctl -u ordinal-bot -f"
