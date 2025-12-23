import discord
from discord.ext import commands, tasks
import random
import json
import os
import asyncio
from flask import Flask
from threading import Thread

# --- SERVIDOR WEB PARA O RENDER ---
app = Flask('')
@app.route('/')
def home(): return "Fazenda Online!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- CONFIGURAÇÕES DO BOT ---
TOKEN = os.environ.get("DISCORD_TOKEN")
CANAL_ID = 1359295941194027019  # Seu ID configurado
PREFIXO = "!"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIXO, intents=intents)

# --- BANCO DE DADOS ---
DATA_FILE = "dados_usuarios.json"

def carregar_dados():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try: return json.load(f)
            except: return {}
    return {}

def salvar_dados():
    with open(DATA_FILE, "w") as f:
        json.dump(dados_usuarios, f, indent=4)

dados_usuarios = carregar_dados()

def init_user(user_id):
    if str(user_id) not in dados_usuarios:
        dados_usuarios[str(user_id)] = {"moedas": 0, "gados": []}

# --- LÓGICA DO JOGO ---
SETAS = {
    "ESQUERDA": "⬅️",
    "CIMA": "⬆️",
    "BAIXO": "⬇️",
    "DIREITA": "➡️"
}

RARIDADES_INFO = {
    "Comum": {"chance": 60, "valor": 10},
    "Raro": {"chance": 25, "valor": 25},
    "Épico": {"chance": 10, "valor": 50},
    "Lendário": {"chance": 4, "valor": 100},
    "Mítico": {"chance": 1, "valor": 250}
}

# --- SISTEMA DE CAPTURA ---
class SetaView(discord.ui.View):
    def __init__(self, sequencia, valor, raridade):
        super().__init__(timeout=20)
        self.sequencia_alvo = sequencia
        self.valor = valor
        self.raridade = raridade
        self.cliques_usuario = []

    async def callback_seta(self, interaction: discord.Interaction, direcao_clicada):
        indice_atual = len(self.cliques_usuario)
        
        if direcao_clicada == self.sequencia_alvo[indice_atual]:
            self.cliques_usuario.append(direcao_clicada)
            
            if len(self.cliques_usuario) == len(self.sequencia_alvo):
                uid = str(interaction.user.id)
                init_user(uid)
                dados_usuarios[uid]["moedas"] += self.valor
                dados_usuarios[uid]["gados"].append({"raridade": self.raridade})
                salvar_dados()

                embed = discord.Embed(title="🎯 CAPTURA FEITA!", color=0x2ecc71)
                embed.description = f"{interaction.user.mention} acertou a sequência e pegou o gado **{self.raridade}**!"
                await interaction.response.edit_message(content=None, embed=embed, view=None)
                self.stop()
            else:
                await interaction.response.send_message("✅ Direção certa! Continue...", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Errou! O gado fugiu.", ephemeral=True)
            self.stop()

# --- LOOP DE SPAWN (2 MINUTOS) ---
@tasks.loop(minutes=2)
async def gerar_gado():
    channel = bot.get_channel(CANAL_ID)
    if not channel: return

    raridade = random.choices(list(RARIDADES_INFO.keys()), weights=[i["chance"] for i in RARIDADES_INFO.values()])[0]
    info = RARIDADES_INFO[raridade]

    # Dificuldade: Comum/Raro (1), Épico/Lendário (2), Mítico (3)
    tamanho = 1 if raridade in ["Comum", "Raro"] else 2 if raridade in ["Épico", "Lendário"] else 3
    
    sequencia = [random.choice(list(SETAS.keys())) for _ in range(tamanho)]
    visual_setas = " ".join([SETAS[s] for s in sequencia])

    msg = await channel.send(f"⚠️ **UM GADO {raridade.upper()} APARECEU!**\nMemorize a direção em 5 segundos:\n# {visual_setas}")
    
    await asyncio.sleep(5)

    view = SetaView(sequencia, info['valor'], raridade)
    
    for nome, emoji in SETAS.items():
        btn = discord.ui.Button(emoji=emoji, style=discord.ButtonStyle.primary)
        async def make_callback(interaction, n=nome):
            await view.callback_seta(interaction, n)
        btn.callback = make_callback
        view.add_item(btn)

    await msg.edit(content="🎮 **PARA ONDE ELE FOI?** (Clique na ordem certa!)", view=view)

# --- INICIALIZAÇÃO ---
@bot.event
async def on_ready():
    print(f'✅ {bot.user} está online!')
    if not gerar_gado.is_running():
        gerar_gado.start()

@bot.command()
async def inventario(ctx):
    uid = str(ctx.author.id)
    init_user(uid)
    u = dados_usuarios[uid]
    resumo = {}
    for g in u["gados"]:
        tipo = g['raridade']
        resumo[tipo] = resumo.get(tipo, 0) + 1
    
    lista = "\n".join([f"🔹 {t}: x{q}" for t, q in resumo.items()]) if resumo else "Curral vazio."
    embed = discord.Embed(title=f"🎒 Inventário de {ctx.author.name}", color=0x764f3d)
    embed.add_field(name="💰 Moedas", value=f"`{u['moedas']}`", inline=False)
    embed.add_field(name="🐄 Rebanho", value=lista, inline=False)
    await ctx.send(embed=embed)

keep_alive()
bot.run(TOKEN)
    
