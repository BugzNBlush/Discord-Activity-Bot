import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import sqlite3

# Bot setup
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)

# SQLite DB setup
conn = sqlite3.connect('activity.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS activity (user_id INTEGER PRIMARY KEY, messages INTEGER, voice_time INTEGER)''')
conn.commit()

# Discord token (you'll set this in the environment variables later)
TOKEN = 'YOUR_DISCORD_TOKEN'

# Check user activity every hour
@tasks.loop(hours=1)
async def check_activity():
    guild = bot.get_guild(YOUR_GUILD_ID)  # Replace with your server ID
    for member in guild.members:
        if member.bot:
            continue
        # Get message count and voice time from database
        c.execute('SELECT messages, voice_time FROM activity WHERE user_id = ?', (member.id,))
        data = c.fetchone()
        if data:
            messages, voice_time = data
            if messages >= 500 or voice_time >= 1200:  # 20 hours = 1200 minutes
                role = discord.utils.get(guild.roles, name="🗨️ Active Member")
                if role and role not in member.roles:
                    await member.add_roles(role)
            else:
                role = discord.utils.get(guild.roles, name="🗨️ Active Member")
                if role and role in member.roles:
                    await member.remove_roles(role)

# Command to check activity manually
@bot.command()
async def activity(ctx, member: discord.Member):
    c.execute('SELECT messages, voice_time FROM activity WHERE user_id = ?', (member.id,))
    data = c.fetchone()
    if data:
        await ctx.send(f"{member.name} has {data[0]} messages and {data[1]} minutes of voice time.")
    else:
        await ctx.send(f"{member.name} has no activity recorded.")

# Event listeners for message and voice activity
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    c.execute('INSERT OR REPLACE INTO activity (user_id, messages) VALUES (?, ?)', 
              (message.author.id, message.author.messages + 1))
    conn.commit()
    await bot.process_commands(message)

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    voice_time = 0
    if after.channel:
        voice_time = 1  # Increment voice time if user joins a channel
    c.execute('INSERT OR REPLACE INTO activity (user_id, voice_time) VALUES (?, ?)', 
              (member.id, voice_time))
    conn.commit()

# Run bot
bot.run(TOKEN)
