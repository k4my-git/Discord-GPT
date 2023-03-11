# This example requires the 'message_content' privileged intents

import os
import discord
from discord import app_commands

guild = discord.Object(617002556740206623)

tree = app_commands.CommandTree(bot)

@bot.event
async def on_ready(self):
    print(f'{self.user}#{self.user.id} LOGIN!')

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.content.startswith('test'):
        await message.channel.send('ok')

bot.run(os.environ["DISCORD_TOKEN"])
