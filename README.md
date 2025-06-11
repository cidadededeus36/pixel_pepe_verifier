# Discord NFT Verification Bot

A Discord bot that verifies NFT ownership across multiple collections and assigns roles accordingly.

## Features

- Verify NFT ownership using BestInSlot.xyz API
- Automatic role assignment based on NFT holdings
- Support for multiple collections
- Slash command interface
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

## Commands

- `/verify` - Verify NFT ownership and get roles
- `/add_address <address>` - Add a wallet address to your profile
- `/remove_address <address>` - Remove a wallet address from your profile
- `/list_addresses` - List your registered wallet addresses
- `/setup_roles` - Create necessary roles (Admin only)
- `/check_roles` - Check role configuration
- `/ping` - Check bot latency

## Required Permissions

The bot requires the following permissions:
- Manage Roles (to assign roles based on NFT ownership)
- View Channels (to see where commands are used)
- Send Messages (to respond to commands)
- Use Application Commands (for slash commands)

## Security

- Sensitive data like wallet addresses are stored locally
- Command responses are ephemeral (only visible to the command user)
- Minimal bot permissions required
- Single instance enforcement using lock file
