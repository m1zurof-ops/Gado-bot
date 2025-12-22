import discord
from discord.ext import commands, tasks
import random

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

cooldown = {}

EMOJIS = ["🔥", "⚡", "🌙", "💎", "👑", "🗡️", "🧠"]

@bot.event
async def on_ready():
    print(f"Bot online como {bot.user}")
    evento.start()

@tasks.loop(minutes=2)
async def evento():
    channel = bot.get_channel(1359295941194027019)

    certo = random.choice(EMOJIS)
    opcoes = random.sample(EMOJIS, 4)
    if certo not in opcoes:
        opcoes[0] = certo
        random.shuffle(opcoes)

    view = discord.ui.View(timeout=30)

    for emoji in opcoes:
        async def callback(interaction, e=emoji):
            user = interaction.user.id

            if user in cooldown:
                await interaction.response.send_message(
                    "⏳ Você está em cooldown!", ephemeral=True
                )
                return

            if e == certo:
                cooldown[user] = 2
                await interaction.response.send_message(
                    f"🎉 {interaction.user.mention} acertou o emoji {certo}!",
                    ephemeral=False
                )
            else:
                await interaction.response.send_message(
                    "❌ Emoji errado!", ephemeral=True
                )

        button = discord.ui.Button(emoji=emoji, style=discord.ButtonStyle.secondary)
        button.callback = callback
        view.add_item(button)

    await channel.send("🎲 **Evento iniciado! Clique no emoji correto:**", view=view)

    for user in list(cooldown.keys()):
        cooldown[user] -= 1
        if cooldown[user] <= 0:
            del cooldown[user]

import os
bot.run(os.getenv(MTQ1Mjc0MjgxNzkyMjQxNjc5NA.Gf8zXe.8Mo64wJDBP-LEe2RTdKpIb5iR6Gb_SsCOmt3-k))
