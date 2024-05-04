import os
import discord
from discord.ext import commands, tasks
import json
from bot_commands import *
from bot_commands_external import *

# Stałe wartości
TOKEN = os.getenv('DISCORD_TOKEN')
COMMAND_PREFIX = '/'
LOG_FILE = 'log.csv'
SEARCH_TERMS = ['Nazwa pliku', 'Pełna ścieżka', 'Właściciel pliku']

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

response = requests.get(url, headers=headers)
if response.status_code == 429:
    sleep(5)  # Waiting for rate limit reset
    response = requests.get(url, headers=headers)

with open('config.json') as f:
    data = json.load(f)
    token = data['token']

class CustomHelpCommand(commands.HelpCommand):
    def get_command_signature(self, command):
        return f'{self.clean_prefix}{command.qualified_name} {command.signature}'

    async def send_bot_help(self, mapping):
        channel = self.get_destination()
        help_embed = discord.Embed(title="Dostępne komendy", description="Oto lista wszystkich dostępnych komend:", color=discord.Color.blue())
        for cog, commands in mapping.items():
            filtered = await self.filter_commands(commands, sort=True)
            command_signatures = [self.get_command_signature(c) for c in filtered]
            if command_signatures:
                cog_name = getattr(cog, "qualified_name", "Podstawowe")
                help_embed.add_field(name=cog_name, value="\n".join(command_signatures), inline=False)

        await channel.send(embed=help_embed)

    async def send_command_help(self, command):
        channel = self.get_destination()
        help_embed = discord.Embed(title=self.get_command_signature(command),
                                   description=command.help or "Brak opisu.",
                                   color=discord.Color.green())
        await channel.send(embed=help_embed)

    async def send_group_help(self, group):
        channel = self.get_destination()
        help_embed = discord.Embed(title=self.get_command_signature(group),
                                   description=group.help or "Brak opisu.",
                                   color=discord.Color.green())

        filtered = await self.filter_commands(group.commands, sort=True)
        for command in filtered:
            help_embed.add_field(name=self.get_command_signature(command), value=command.help or "Brak opisu", inline=False)

        await channel.send(embed=help_embed)

@bot.event
async def on_ready():
    print(f'Zalogowano jako {bot.user}')

bot.run(TOKEN)