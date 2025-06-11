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

## Setup

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
