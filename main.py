import discord
from discord.ext import commands, tasks
import random
import os
import json
from flask import Flask
from threading import Thread

# --- 1. PARTE QUE MANTÉM ONLINE (SERVIDOR WEB) ---
app = Flask('')
@app.route('/')
def home(): return "Fazenda Online!"

def run(): app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. PARTE QUE SALVA OS DADOS (DATABASE JSON) ---
def carregar_dados():
    try:
        if os.path.exists('dados.json'):
            with open('dados.json', 'r') as f: return json.load(f)
    except: pass
    return {}

def salvar_dados():
    with open('dados.json', 'w') as f:
        json.dump(dados_usuarios, f, indent=4)

dados_usuarios = carregar_dados()

# --- 3. CONFIGURAÇÃO DO BOT ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
cooldown = {}
CANAL_ID = 1359295941194027019

RARIDADES_INFO = {
    "Comum": {"valor": 10, "cor": discord.Color.light_gray(), "chance": 70},
    "Raro": {"valor": 25, "cor": discord.Color.blue(), "chance": 20},
    "Épico": {"valor": 50, "cor": discord.Color.purple(), "chance": 7},
    "Lendário": {"valor": 80, "cor": discord.Color.orange(), "chance": 2.5},
    "Mítico": {"valor": 200, "cor": discord.Color.from_rgb(255, 0, 100), "chance": 0.5}
}
EMOJIS = ["🔥", "⚡", "🌙", "💎", "👑", "🗡️", "🧠"]

# --- 4. A VIEW COM O CALLBACK INTEGRADO ---
class GadoButton(discord.ui.Button):
    def __init__(self, emoji, custom_id):
        super().__init__(emoji=emoji, custom_id=custom_id, style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        # Este é o CALLBACK que você queria!
        view: GadoView = self.view
        user_id = str(interaction.user.id)

        if interaction.user.id in cooldown and cooldown[interaction.user.id] > 0:
            return await interaction.response.send_message("⏳ Cooldown!", ephemeral=True)

        if self.custom_id == view.emoji_certo:
            view.foi_capturado = True
            cooldown[interaction.user.id] = 2
            
            # Salva no inventário
            if user_id not in dados_usuarios:
                dados_usuarios[user_id] = {"moedas": 0, "gados": []}
            
            dados_usuarios[user_id]["moedas"] += view.valor
            dados_usuarios[user_id]["gados"].append({"emoji": view.emoji_certo, "raridade": view.raridade})
            salvar_dados()

            embed = discord.Embed(title="🤠 CAPTURADO!", color=discord.Color.green())
            embed.description = f"{interaction.user.mention} pegou o gado **{view.raridade}**!"
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            
            await interaction.response.edit_message(content=None, embed=embed, view=None)
            view.stop()
        else:
            await interaction.response.send_message("❌ Errou o emoji!", ephemeral=True)

class GadoView(discord.ui.View):
    def __init__(self, emoji_certo, valor, raridade, tempo, message=None):
        super().__init__(timeout=tempo)
        self.emoji_certo = emoji_certo
        self.valor = valor
        self.raridade = raridade
        self.message = message
        self.foi_capturado = False

    async def on_timeout(self):
        if not self.foi_capturado and self.message:
            try: await self.message.edit(content="💨 O gado fugiu!", embed=None, view=None)
            except: pass

@tasks.loop(minutes=2)
async def evento():
    channel = bot.get_channel(CANAL_ID)
    if not channel: return

    raridade = random.choices(list(RARIDADES_INFO.keys()), weights=[i["chance"] for i in RARIDADES_INFO.values()])[0]
    info = RARIDADES_INFO[raridade]
    certo = random.choice(EMOJIS)
    
    opcoes = random.sample(EMOJIS, 4)
    if certo not in opcoes: opcoes[0] = certo
    random.shuffle(opcoes)

    view = GadoView(certo, info['valor'], raridade, 60)
    for e in opcoes:
        view.add_item(GadoButton(emoji=e, custom_id=e))

    msg = await channel.send(f"🌿 Gado **{raridade}** apareceu! Clique no: **{certo}**", view=view)
    view.message = msg

    for uid in list(cooldown.keys()):
        cooldown[uid] -= 1
        if cooldown[uid] <= 0: del cooldown[uid]

@bot.event
async def on_ready():
    print(f"✅ {bot.user} Online!")
    if not evento.is_running(): evento.start()

# --- RODAR TUDO ---
keep_alive() # Isso ajuda a manter 24h com o Cron-job
bot.run(os.getenv("DISCORD_TOKEN"))

