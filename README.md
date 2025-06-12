# Pixel Pepes Verifier Bot

A Discord bot that verifies Ordinal ownership for Pixel Pepes collections and assigns roles accordingly.

## Features

- Verify Ordinal ownership using BestInSlot.xyz API
- Magic Eden bio verification for wallet ownership
- Interactive button interface for all commands
- Automatic role assignment based on Ordinal holdings
- Periodic verification (every 30 minutes) to remove roles if Ordinals are sold
- Support for multiple collections
- Slash commands and buttons for easy interaction
- Ephemeral responses for privacy

## Local Setup

1. Create a `.env` file with the following variables:
   ```
   DISCORD_BOT_TOKEN=your_bot_token
   GUILD_ID=your_guild_id
   ```

2. Install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Run the bot:
   ```bash
   python ordinal_bot.py
   ```

## Deployment

### Prerequisites

1. VPS Requirements:
   - Ubuntu 20.04 or later
   - Python 3.8 or later
   - Git installed
   - Sudo access

2. Discord Bot Setup:
   - Create a bot in [Discord Developer Portal](https://discord.com/developers/applications)
   - Enable Server Members Intent
   - Get your bot token
   - Get your server (guild) ID

### VPS Deployment (Recommended)

1. Update system and install Python:
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install python3-venv python3-pip git -y
   ```

2. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pixel_pepe_verifier.git
   cd pixel_pepe_verifier
   ```

3. Configure environment:
   ```bash
   cp .env.example .env
   nano .env  # Add your bot token and guild ID
   ```

4. Run installation script:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

5. Verify deployment:
   ```bash
   # Check service status
   sudo systemctl status ordinal-bot
   
   # View logs
   journalctl -u ordinal-bot -f
   ```

### Data Storage

The bot stores data in:
- `data/user_addresses.json`: Wallet addresses
- `bot.log`: Application logs

Backup these files regularly for data safety.

### Security Considerations

1. File Permissions:
   ```bash
   # Secure .env file
   chmod 600 .env
   
   # Secure data directory
   chmod 700 data
   ```

2. Bot Token Safety:
   - Never commit .env file
   - Rotate bot token if compromised
   - Use restricted bot permissions

### Bot Invite Link

Use this link to invite the bot to your server (requires Manage Roles permission):
https://discord.com/api/oauth2/authorize?client_id=1382141792207507546&permissions=268435456&scope=bot%20applications.commands

### Maintenance

#### Regular Updates
```bash
# Update bot code
git pull

# Reinstall dependencies and restart
./install.sh
```

#### Service Management
```bash
# Start bot
sudo systemctl start ordinal-bot

# Stop bot
sudo systemctl stop ordinal-bot

# Restart bot
sudo systemctl restart ordinal-bot

# Check status
sudo systemctl status ordinal-bot
```

#### Logging
```bash
# View live logs
journalctl -u ordinal-bot -f

# View last 100 lines
journalctl -u ordinal-bot -n 100

# View logs since last hour
journalctl -u ordinal-bot --since "1 hour ago"
```

#### Backup
```bash
# Backup data directory
cp -r data data.backup

# Backup environment
cp .env .env.backup
```

## Commands & Buttons

All functionality is available through both slash commands and buttons:

- **Verify** - Check Ordinal ownership and get roles
- **Add Address** - Link your wallet address (requires ME bio verification)
- **Remove Address** - Remove a wallet address
- **List Addresses** - View your registered wallets
- **Check Roles** - View your current collection roles
- **Help** - Show available commands and instructions

Admin Commands:
- `/setup_roles` - Create necessary roles (Requires Manage Roles)
- `/setup_verification` - Set up verification channel with buttons
- `/ping` - Check bot latency

## Required Permissions

The bot uses minimal permissions for security:
- Manage Roles (to assign roles based on Ordinal ownership)
- View Channels (to see verification channel)
- Send Messages (to send verification messages)
- Use Application Commands (for slash commands)

## Security

- Magic Eden bio verification ensures wallet ownership
- Wallet addresses stored locally and privately
- All responses are ephemeral (only visible to the user)
- Minimal bot permissions for reduced attack surface
- Single instance enforcement using lock file
- Command-specific permission requirements
