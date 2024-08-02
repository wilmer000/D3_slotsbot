import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from collections import defaultdict
import time

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.messages = True
intents.guilds = True

class MyBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree = app_commands.CommandTree(self)
        self.mention_limits = defaultdict(lambda: {'count': 0, 'last_reset': time.time()})

    async def on_ready(self):
        await self.tree.sync(guild=None)  # Sync commands globally
        print(f'We have logged in as {self.user}')
    
    async def on_message(self, message):
        if message.author.bot:
            return

        if any(mention in message.content for mention in ['@everyone', '@here']):
            role = discord.utils.get(message.author.roles, name=f"{message.channel.category.name}_role")
            if role in message.author.roles:
                current_time = time.time()
                limits = self.mention_limits[message.author.id]
                
                # Reset count if 24 hours have passed
                if current_time - limits['last_reset'] >= 86400:
                    limits['count'] = 0
                    limits['last_reset'] = current_time
                
                # Check if limit is reached
                if limits['count'] < 2:  # Set your desired limit here
                    limits['count'] += 1
                else:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention}, you have reached your mention limit for today.", delete_after=10)
            else:
                await message.delete()

bot = MyBot(intents=intents)

@bot.tree.command(name="create_temp_category", description="Skapa en temporär kategori med kanaler")
@app_commands.describe(
    category_name="Namnet på kategorin",
    channel_names="Namn på kanalerna (komma-separerade)",
    duration="Varaktighet i sekunder",
    member="Tagga en medlem"
)
async def create_temp_category(interaction: discord.Interaction, category_name: str, channel_names: str, duration: int, member: discord.Member):
    guild = interaction.guild

    # Skapa roll
    role_name = f"{category_name}_role"
    role = await guild.create_role(name=role_name)
    await member.add_roles(role)

    # Skapa kategori och kanaler
    category = await guild.create_category(category_name)
    channels = channel_names.split(',')
    for channel_name in channels:
        channel = await guild.create_text_channel(channel_name.strip(), category=category)
        await channel.set_permissions(guild.default_role, read_messages=False)
        await channel.set_permissions(role, read_messages=True, send_messages=True)

    await interaction.response.send_message(f"Kategori {category_name} och kanaler skapade. Varaktighet: {duration} sekunder.", ephemeral=True)
    
    # Vänta och ta bort kategori och roll efter varaktighet
    await asyncio.sleep(duration)
    await category.delete()
    await role.delete()

bot.run('')
