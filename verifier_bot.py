import os
import sys
import discord
from discord.ext import commands
from discord import app_commands, ButtonStyle
import logging
import json
import requests
from io import StringIO
import pandas as pd
from typing import List, Tuple, Optional, List, Tuple
from pathlib import Path
import secrets
import asyncio
from collections import deque
import pandas as pd
from datetime import datetime, timedelta
import pickle
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logs
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ],
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Load environment variables
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
BESTINSLOT_API = "https://v2api.bestinslot.xyz/collection/snapshot"
MAGICEDEN_API = "https://api-mainnet.magiceden.dev/v2/wallets/"
RATE_LIMIT_QPM = 30
RATE_LIMIT_WINDOW = 60  # seconds
CHECK_INTERVAL = 60  # seconds
VERIFICATION_TIMEOUT = 1800  # 30 minutes
USER_DATA_FILE = 'data/user_addresses.json'

# How often to check all wallets (in minutes)
WALLET_CHECK_INTERVAL = 30  # Check every 30 minutes

# Collection configurations
COLLECTIONS = {
    'pixelpepes': 'Pixel Pepe Holder',
    'space-pepes': 'Space Pepe Holder',
    'soy-pepes': 'Soy Pepe Holder',
    'clay-pepes': 'Clay Pepe Holder',
    'pixel-mumus': 'Pixel Mumu Holder',
}

# Booster role name
BOOSTER_ROLE_NAME = "Server Booster"

# Initialize bot with minimal required intents and permissions
intents = discord.Intents.default()
intents.guilds = True  # Only need guilds intent for slash commands
intents.members = True  # Need member updates for booster tracking

# Initialize bot with minimal intents
bot = commands.Bot(
    command_prefix='!',
    intents=intents,
    description='Ordinal Verification Bot'
)

class CommandView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Add Address', style=ButtonStyle.primary, custom_id='add_address_button', row=0)
    async def add_address_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddAddressModal())

    @discord.ui.button(label='Remove Address', style=ButtonStyle.danger, custom_id='remove_address_button', row=0)
    async def remove_address_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RemoveAddressModal())

    @discord.ui.button(label='List Addresses', style=ButtonStyle.secondary, custom_id='list_addresses_button', row=1)
    async def list_addresses_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await list_addresses._callback(interaction)

    @discord.ui.button(label='Check Roles', style=ButtonStyle.secondary, custom_id='check_roles_button', row=1)
    async def check_roles_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await check_roles._callback(interaction)

    @discord.ui.button(label='Verify Now', style=ButtonStyle.success, custom_id='verify_help_button', row=2)
    async def verify_help_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await verify._callback(interaction)

class AddAddressModal(discord.ui.Modal, title='Add Wallet Address'):
    address = discord.ui.TextInput(label='Wallet Address', placeholder='Enter your wallet address here')

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        address = str(self.address)
        
        # Check bio verification first
        has_bio = await verify_me_bio(address, user_id)
        if not has_bio:
            await interaction.response.send_message(
                "❌ Please add your Discord ID to your Magic Eden bio first!\n" \
                f"Your Discord ID is: {user_id}", 
                ephemeral=True
            )
            return
            
        await add_address._callback(interaction, address)

class RemoveAddressModal(discord.ui.Modal, title='Remove Wallet Address'):
    address = discord.ui.TextInput(label='Wallet Address', placeholder='Enter the wallet address to remove')

    async def on_submit(self, interaction: discord.Interaction):
        await remove_address._callback(interaction, str(self.address))

class VerificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Verify', style=ButtonStyle.primary, custom_id='verify_button')
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await verify._callback(interaction)

    @discord.ui.button(label='Help', style=ButtonStyle.secondary, custom_id='help_button')
    async def help_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        help_text = (
            "**🐸 Pixel Pepes Verifier Bot Help**\n\n"
            "**How it Works:**\n"
            "1. Add your Discord ID to your Magic Eden bio\n"
            "2. Click Add Address & enter your wallet\n"
            "3. Click Verify to check your Ordinals\n"
            "4. Get roles based on your holdings\n"
            "5. Roles update every 30 minutes\n"
        )
        view = CommandView()
        await interaction.response.send_message(help_text, view=view, ephemeral=True)

# Define required permissions for commands
REQUIRED_PERMISSIONS = discord.Permissions(
    manage_roles=True,
    view_channel=True,
    send_messages=True,
    use_application_commands=True
)

# Remove default help command as we'll use slash commands
bot.remove_command('help')

async def verify_all_wallets():
    """Periodically verify all registered wallets and update roles"""
    while True:
        try:
            logging.info('Starting periodic wallet verification...')
            guild_id = int(os.getenv('GUILD_ID', '0'))
            guild = bot.get_guild(guild_id)
            
            if not guild:
                logging.error(f'Could not find guild with ID {guild_id}')
                await asyncio.sleep(WALLET_CHECK_INTERVAL * 60)
                continue
                
            user_data = load_user_data()
            
            for user_id, addresses in user_data.items():
                try:
                    member = await guild.fetch_member(int(user_id))
                    if not member:
                        logging.warning(f'Could not find member with ID {user_id}')
                        continue
                        
                    logging.info(f'Checking addresses for user {member.name} ({user_id})')
                    
                    # Check each collection
                    for collection_slug, role_name in COLLECTIONS.items():
                        role = discord.utils.get(guild.roles, name=role_name)
                        if not role:
                            logging.warning(f'Could not find role {role_name}')
                            continue
                            
                        # Check if user owns any Ordinals in collection
                        has_ordinal = False
                        for address in addresses:
                            owns, count, _ = await verify_ownership(address, collection_slug)
                            if owns and count > 0:
                                has_ordinal = True
                                break
                                
                        # Update role
                        try:
                            if has_ordinal and role not in member.roles:
                                await member.add_roles(role)
                                logging.info(f'Added role {role_name} to {member.name}')
                            elif not has_ordinal and role in member.roles:
                                await member.remove_roles(role)
                                logging.info(f'Removed role {role_name} from {member.name}')
                        except discord.Forbidden:
                            logging.error(f'Missing permissions to modify roles for {member.name}')
                        except Exception as e:
                            logging.error(f'Error updating roles for {member.name}: {e}')
                            
                except Exception as e:
                    logging.error(f'Error processing user {user_id}: {e}')
                    
                # Sleep briefly between users to avoid rate limits
                await asyncio.sleep(1)
                
            logging.info('Finished periodic wallet verification')
            
        except Exception as e:
            logging.error(f'Error in verify_all_wallets: {e}')
            
        # Wait for next check interval
        await asyncio.sleep(WALLET_CHECK_INTERVAL * 60)

@bot.tree.command(name="setup_verification", description="Setup verification message with buttons (Requires Manage Channels)")
@app_commands.checks.has_permissions(manage_channels=True)
async def setup_verification(interaction: discord.Interaction):
    # Check if bot has required permissions in the channel
    permissions = interaction.channel.permissions_for(interaction.guild.me)
    if not (permissions.send_messages and permissions.view_channel and permissions.embed_links):
        missing_perms = []
        if not permissions.send_messages:
            missing_perms.append("Send Messages")
        if not permissions.view_channel:
            missing_perms.append("View Channel")
        if not permissions.embed_links:
            missing_perms.append("Embed Links")
        await interaction.response.send_message(
            f"❌ Bot is missing required permissions in this channel: {', '.join(missing_perms)}\n"
            "Please give the bot these permissions in the channel settings.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="🐸 Pixel Pepes Holder Verification",
        description=(
            "Welcome to the Pixel Pepes holder verification!\n\n"
            "Click the **Verify** button below to link your wallet and receive your holder roles.\n"
            "Click the **Help** button for detailed instructions on how to use the bot."
        ),
        color=discord.Color.blue()
    )
    
    try:
        view = VerificationView()
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Verification message set up!", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ Failed to send verification message. Please check the bot's permissions in this channel.",
            ephemeral=True
        )

@bot.event
async def setup_hook():
    logging.info('Setting up bot...')
    
    # Start periodic wallet verification
    bot.loop.create_task(verify_all_wallets())
    try:
        guild_id = os.getenv('GUILD_ID', '0')
        if guild_id == '0' or not guild_id.isdigit():
            logging.warning('No valid GUILD_ID found in environment variables. Commands will be registered globally.')
            MY_GUILD = None
        else:
            MY_GUILD = discord.Object(id=int(guild_id))
            logging.info(f'Guild ID: {MY_GUILD.id}')
        
        # Register commands with minimal permissions
        # Only register commands that don't have decorators
        commands = [
            setup_verification
        ]
        
        for cmd in commands:
            cmd.default_permissions = REQUIRED_PERMISSIONS
            if MY_GUILD:
                bot.tree.add_command(cmd, guild=MY_GUILD)
            else:
                bot.tree.add_command(cmd)
        
        logging.info('Syncing commands...')
        try:
            if MY_GUILD:
                synced = await bot.tree.sync(guild=MY_GUILD)
            else:
                synced = await bot.tree.sync()
            logging.info(f'Commands synced successfully! Synced {len(synced)} commands:')
            for cmd in synced:
                logging.info(f'  - {cmd.name}')
        except discord.errors.Forbidden as e:
            logging.error(f'Failed to sync commands: {e}. Check bot permissions.')
        except Exception as e:
            logging.error(f'Failed to sync commands: {e}', exc_info=True)
    except Exception as e:
        logging.error(f'Failed in setup_hook: {e}', exc_info=True)

@bot.event
async def on_ready():
    logging.info(f'{bot.user} has connected to Discord!')
    logging.info('Connected to the following guilds:')
    for guild in bot.guilds:
        logging.info(f'- {guild.name} (id: {guild.id})')
        
        # Log bot permissions in guild
        logging.info(f'\nBot permissions in {guild.name}:')
        logging.info('Required permissions:')
        logging.info('  - manage_roles (for role assignment)')
        logging.info('  - view_channel (to see commands)')
        logging.info('  - send_messages (to respond)')
        logging.info('  - use_application_commands (for slash commands)')
        
        logging.info('\nActual permissions:')
        all_perms = [
            (perm, value) 
            for perm, value in guild.me.guild_permissions
        ]
        all_perms.sort(key=lambda x: x[0])
        
        for perm, value in all_perms:
            status = '✅' if value else '❌'
            logging.info(f'  {status} {perm}')
        
        if guild.me.guild_permissions.use_application_commands:
            logging.info('\n✅ Bot has permission to use application commands')
        else:
            logging.warning('\n❌ Bot does not have permission to use application commands')
        
        # Check if we have the minimal required permissions
        required_perms = {
            'manage_roles': guild.me.guild_permissions.manage_roles,
            'view_channel': guild.me.guild_permissions.view_channel,
            'send_messages': guild.me.guild_permissions.send_messages,
            'use_application_commands': guild.me.guild_permissions.use_application_commands
        }
        
        missing_perms = [perm for perm, has in required_perms.items() if not has]
        if missing_perms:
            logging.warning(f'\n❌ Missing required permissions: {", ".join(missing_perms)}')
        else:
            logging.info('\n✅ All required permissions are present')
        
    logging.info('------')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    print(f'Message received from {message.author}: {message.content}')
    await bot.process_commands(message)

@bot.tree.command(name="ping", description="Test if the bot is responding")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message('Pong! 🏓', ephemeral=True)

@bot.tree.command(name="add_address", description="Add a wallet address for verification")
async def add_address(interaction: discord.Interaction, address: str):
    user_id = str(interaction.user.id)
    
    # Initialize user's address list if not exists
    if user_id not in user_addresses:
        user_addresses[user_id] = []
    
    # Check if address already exists
    if address in user_addresses[user_id]:
        await interaction.response.send_message("❌ This address is already registered!", ephemeral=True)
        return
    
    # Add the new address
    user_addresses[user_id].append(address)
    await interaction.response.send_message(f"✅ Added address: {address}", ephemeral=True)
    await verify(interaction)

@bot.tree.command(name="remove_address", description="Remove a wallet address")
async def remove_address(interaction: discord.Interaction, address: str):
    user_id = str(interaction.user.id)
    
    if user_id not in user_addresses or address not in user_addresses[user_id]:
        await interaction.response.send_message("❌ This address is not registered!", ephemeral=True)
        return
    
    user_addresses[user_id] = [addr for addr in user_addresses[user_id] if addr != address]
    await interaction.response.send_message(f"✅ Removed address: {address}", ephemeral=True)
    await verify(interaction)

@bot.tree.command(name="list_addresses", description="List all your registered wallet addresses")
async def list_addresses(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    
    if user_id not in user_addresses or not user_addresses[user_id]:
        await interaction.response.send_message("❌ You have no registered addresses!", ephemeral=True)
        return
    
    addresses = get_user_addresses(user_id)
    formatted_addresses = "\n".join([f"{i+1}. {addr}" for i, addr in enumerate(addresses)])
    await interaction.response.send_message(f"Your linked addresses:\n```{formatted_addresses}```", ephemeral=True)

def get_user_addresses(user_id: str) -> List[str]:
    """Get list of addresses for a user"""
    return user_addresses.get(user_id, [])

@bot.tree.command(name="verify", description="Verify Ordinal ownership and assign roles")
async def verify(interaction: discord.Interaction):
    if not interaction.guild:
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ This command can only be used in a server!", ephemeral=True)
        else:
            await interaction.followup.send("❌ This command can only be used in a server!", ephemeral=True)
        return

    user_id = str(interaction.user.id)
    if user_id not in user_addresses or not user_addresses[user_id]:
        class NoAddressView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)

            @discord.ui.button(label='Add Address', style=ButtonStyle.primary)
            async def add_address_button(self, inner_interaction: discord.Interaction, button: discord.ui.Button):
                await inner_interaction.response.send_modal(AddAddressModal())

        if not interaction.response.is_done():
            await interaction.response.send_message("❌ No wallet addresses found! Click below to add one:", view=NoAddressView(), ephemeral=True)
        else:
            await interaction.followup.send("❌ No wallet addresses found! Click below to add one:", view=NoAddressView(), ephemeral=True)
        return

    if not interaction.response.is_done():
        await interaction.response.send_message("Starting verification process... Please wait.", ephemeral=True)
    else:
        await interaction.followup.send("Starting verification process... Please wait.", ephemeral=True)
    user_id = str(interaction.user.id)
    addresses = get_user_addresses(user_id)
    
    if not addresses:
        await interaction.followup.send("❌ Please add your wallet address first using /add_address", ephemeral=True)
        return
    
    verified_collections = []
    roles_added = []
    roles_error = []
    holdings = {}
    
    # Check each collection
    for slug, role_name in COLLECTIONS.items():
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if not role:
            logging.warning(f"Role not found: {role_name}")
            continue
            
        logging.info(f"Checking role {role_name} (position {role.position})")
        user_has_role = role in interaction.user.roles
        owns_ordinal = False
        max_count = 0
        collection_inscriptions = None
        
        for addr in addresses:
            is_holder, count, inscriptions = await verify_ownership(addr, slug)
            if is_holder and count is not None:  # Make sure we have valid count data
                owns_ordinal = True
                if count > max_count:
                    max_count = count
                    collection_inscriptions = inscriptions
                if not user_has_role:
                    try:
                        await interaction.user.add_roles(role)
                        roles_added.append(role_name)
                        logging.info(f"Added role {role_name} to user")
                    except discord.Forbidden as e:
                        logging.error(f"Failed to add role {role_name}: {e}")
                        roles_error.append(role_name)
                break
        
        if owns_ordinal:
            verified_collections.append(slug)
            holdings[slug] = (max_count, collection_inscriptions)
        elif user_has_role:
            try:
                await interaction.user.remove_roles(role)
                logging.info(f"Removed role {role_name} from user")
            except discord.Forbidden as e:
                logging.error(f"Failed to remove role {role_name}: {e}")
                roles_error.append(role_name)
    
    # Prepare response message
    if verified_collections:
        msg = "✅ Verification successful!\n\n"
        if roles_added:
            msg += f"Added roles: {', '.join(roles_added)}\n\n"
        
        msg += "Your holdings:\n"
        for slug in verified_collections:
            count, inscriptions = holdings[slug]
            collection_name = COLLECTIONS[slug].replace(' Holder', '')
            msg += f"• {collection_name}: {count} inscription{'s' if count != 1 else ''}\n"
    else:
        msg = "❌ No Ordinals found in the verified collections."
    
    if roles_error:
        msg += f"\n⚠️ Bot couldn't manage these roles: {', '.join(roles_error)}"
        msg += "\nPlease check the bot's permissions and role hierarchy."
    
    await interaction.followup.send(msg, ephemeral=True)

@bot.tree.command(name="setup_roles", description="Create missing roles (Requires Manage Roles permission)")
@app_commands.checks.has_permissions(manage_roles=True)
async def setup_roles(interaction: discord.Interaction):
    roles_created = []
    roles_existing = []
    
    # Check collection roles
    for role_name in COLLECTIONS.values():
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if not role:
            await interaction.guild.create_role(name=role_name)
            roles_created.append(role_name)
        else:
            roles_existing.append(role_name)
    
    # Check booster role
    booster_role = discord.utils.get(interaction.guild.roles, name=BOOSTER_ROLE_NAME)
    if not booster_role:
        await interaction.guild.create_role(
            name=BOOSTER_ROLE_NAME,
            color=discord.Color.from_rgb(244, 127, 255),  # Pink color
            reason="Role for server boosters"
        )
        roles_created.append(BOOSTER_ROLE_NAME)
    else:
        roles_existing.append(BOOSTER_ROLE_NAME)
    
    msg = ""
    
    if roles_created:
        msg += f"✅ Created roles: {', '.join(roles_created)}\n"
    if roles_existing:
        msg += f"ℹ️ Existing roles: {', '.join(roles_existing)}"
    
    await interaction.response.send_message(msg, ephemeral=True)

@bot.tree.command(name="check_roles", description="Check which collection roles you currently have")
async def check_roles(interaction: discord.Interaction):
    user_roles = [role.name for role in interaction.user.roles]
    verified_roles = [role for role in COLLECTIONS.values() if role in user_roles]
    
    msg = ""
    
    # Check collection roles
    if verified_roles:
        msg += "Your collection roles:\n"
        for role in verified_roles:
            msg += f"• {role}\n"
    else:
        msg += "You don't have any collection roles yet!\n"
    
    # Check booster status
    if BOOSTER_ROLE_NAME in user_roles:
        msg += "\n⭐ You are a server booster! Thank you for your support!"
    
    await interaction.response.send_message(msg, ephemeral=True)

# Rate limiting setup
request_times = deque()

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

def load_user_data():
    """Load user address mappings from file"""
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_user_data(data):
    """Save user address mappings to file"""
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

user_addresses = load_user_data()

def has_collection_permission():
    async def predicate(ctx):
        return (ctx.author.guild_permissions.administrator or 
                ctx.author.guild_permissions.manage_roles)
    return commands.check(predicate)

async def check_rate_limit():
    """Implement rate limiting for API calls"""
    now = datetime.now()
    while request_times and (now - request_times[0]).seconds >= RATE_LIMIT_WINDOW:
        request_times.popleft()
    if len(request_times) >= RATE_LIMIT_QPM:
        sleep_time = RATE_LIMIT_WINDOW - (now - request_times[0]).seconds
        await asyncio.sleep(sleep_time)
    request_times.append(now)

from typing import Tuple

async def verify_ownership(address: str, collection_slug: str) -> Tuple[bool, Optional[int], Optional[str]]:
    """Verify if an address owns any inscriptions in a collection using BestInSlot API
    
    Returns:
        Tuple containing:
        - bool: Whether the address owns any inscriptions
        - Optional[int]: Number of inscriptions owned (None if address not found)
        - Optional[str]: List of owned inscriptions (None if address not found)
    """
    await check_rate_limit()
    try:
        logging.info(f"\nChecking BestInSlot inscriptions for address: {address}")
        logging.info(f"Collection slug: {collection_slug}")
        
        params = {
            'slug': collection_slug,
            'type': 'csv'
        }
        url = f"{BESTINSLOT_API}?" + "&".join(f"{k}={v}" for k, v in params.items())
        logging.info(f"Making request to: {url}")
        
        response = requests.get(BESTINSLOT_API, params=params)
        logging.info(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            logging.info("Successfully received CSV data")
            # Read CSV and clean up column names by stripping whitespace
            df = pd.read_csv(StringIO(response.text))
            df.columns = df.columns.str.strip()
            logging.info(f"CSV columns after cleaning: {df.columns.tolist()}")
            
            # Clean up wallet addresses
            df['wallet'] = df['wallet'].str.strip().str.lower()
            
            # Debug: Show first few rows
            logging.info(f"First few rows after cleaning:\n{df.head()}")
            
            if 'wallet' not in df.columns:
                logging.error("'wallet' column not found in CSV data")
                return False, None, None
            
            # Check if the address exists in the snapshot
            clean_address = address.strip().lower()
            logging.info(f"Looking for cleaned address: {clean_address}")
            
            wallet_data = df[df['wallet'] == clean_address]
            if wallet_data.empty:
                logging.info(f"Address {clean_address} not found in collection snapshot - not a holder")
                logging.info(f"Available wallets: {df['wallet'].head().tolist()}")
                return False, None, None
                
            inscriptions_count = int(wallet_data['inscriptions_count'].iloc[0])
            inscriptions = wallet_data['inscriptions'].iloc[0]
            logging.info(f"Found {inscriptions_count} inscriptions for wallet {clean_address}")
            logging.info(f"Inscriptions: {inscriptions}")
            
            # TODO: Future role enhancements
            # 1. Multiple inscription holders (inscriptions_count > 1)
            # Example:
            # if inscriptions_count > 1:
            #     await ctx.author.add_roles(multiple_holder_role)
            
            # 2. Specific inscription holders
            # Example:
            # special_inscription = "123abc"
            # if special_inscription in inscriptions.split(','):
            #     await ctx.author.add_roles(special_inscription_role)
            
            return True, inscriptions_count, inscriptions
        else:
            logging.error(f"Error response from BestInSlot API: {response.text}")
            return False, None, None
    except Exception as e:
        logging.error(f"Error verifying ownership: {e}", exc_info=True)
        return False, None, None

async def verify_me_bio(address: str, user_id: str) -> bool:
    """Verify if the user has put their Discord ID in their ME bio"""
    await check_rate_limit()
    try:
        logging.info(f"\nChecking Magic Eden bio for address: {address}")
        logging.info(f"Looking for Discord ID: {user_id}")
        
        url = f"{MAGICEDEN_API}{address}"
        logging.info(f"Making request to: {url}")
        
        response = requests.get(url)
        logging.info(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logging.info(f"Raw API response: {json.dumps(data, indent=2)}")
            
            bio = data.get('bio', '')
            logging.info(f"Found bio: {bio!r}")
            
            if not bio:
                logging.info("Bio is empty")
                return False
                
            bio = bio.strip()
            result = str(user_id) in bio
            logging.info(f"Discord ID ({user_id}) found in bio: {result}")
            logging.info(f"Bio content: {bio!r}")
            return result
        else:
            logging.error(f"Error response from Magic Eden API: {response.text}")
            return False
    except Exception as e:
        logging.error(f"Error checking ME bio: {e}", exc_info=True)
        return False

def is_bot_running():
    """Check if another instance of the bot is running using a lock file"""
    lock_file = Path('bot.lock')
    
    if lock_file.exists():
        try:
            # Check if the process in the lock file is still running
            with open(lock_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Try to kill the process with signal 0 (doesn't actually kill it)
            # This will raise an exception if the process doesn't exist
            os.kill(pid, 0)
            
            # If we get here, the process exists
            logging.error(f"Another instance of the bot is already running (PID: {pid})")
            return True
        except (ProcessLookupError, ValueError):
            # Process doesn't exist or invalid PID, safe to remove the stale lock
            lock_file.unlink(missing_ok=True)
            return False
    return False

def create_lock_file():
    """Create a lock file with current process ID"""
    with open('bot.lock', 'w') as f:
        f.write(str(os.getpid()))

def remove_lock_file():
    """Remove the lock file"""
    try:
        Path('bot.lock').unlink(missing_ok=True)
    except Exception as e:
        logging.error(f"Error removing lock file: {e}")

@bot.event
async def on_member_update(before, after):
    # Check if premium_since changed (boost status)
    if before.premium_since != after.premium_since:
        guild = after.guild
        booster_role = discord.utils.get(guild.roles, name=BOOSTER_ROLE_NAME)
        
        # Create booster role if it doesn't exist
        if not booster_role:
            try:
                booster_role = await guild.create_role(
                    name=BOOSTER_ROLE_NAME,
                    color=discord.Color.from_rgb(244, 127, 255),  # Pink color
                    reason="Role for server boosters"
                )
                logging.info(f"Created {BOOSTER_ROLE_NAME} role")
            except Exception as e:
                logging.error(f"Failed to create booster role: {e}")
                return
        
        # Member started boosting
        if after.premium_since and not before.premium_since:
            try:
                await after.add_roles(booster_role, reason="User started boosting the server")
                logging.info(f"Added booster role to {after.display_name}")
                
                # Send thank you message
                try:
                    await after.send(f"Thank you for boosting the server! You've been given the {BOOSTER_ROLE_NAME} role.")
                except:
                    logging.info(f"Couldn't DM {after.display_name} about booster role")
                    
            except Exception as e:
                logging.error(f"Failed to add booster role: {e}")
        
        # Member stopped boosting
        elif before.premium_since and not after.premium_since:
            try:
                await after.remove_roles(booster_role, reason="User stopped boosting the server")
                logging.info(f"Removed booster role from {after.display_name}")
            except Exception as e:
                logging.error(f"Failed to remove booster role: {e}")

# Run the bot
if __name__ == "__main__":
    try:
        if is_bot_running():
            logging.error("Bot is already running. Exiting.")
            sys.exit(1)
            
        create_lock_file()
        logging.info(f"Starting bot with PID {os.getpid()}")
        logging.info(f"Bot token length: {len(BOT_TOKEN) if BOT_TOKEN else 0}")
        logging.info(f"Guild ID: {os.getenv('GUILD_ID')}")
        
        # Make sure we remove the lock file even if the bot crashes
        try:
            logging.info("Attempting to start bot...")
            bot.run(BOT_TOKEN)
        except Exception as e:
            logging.error(f"Error running bot: {e}", exc_info=True)
            raise
        finally:
            logging.info("Removing lock file...")
            remove_lock_file()
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        remove_lock_file()
        sys.exit(1)
