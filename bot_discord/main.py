import discord 
from discord import Activity, ActivityType, app_commands
from discord.ext import commands, tasks
from itertools import cycle
import os
import asyncio
import time
from cogs import Help
import io
import traceback



client = commands.Bot(command_prefix="=", intents= discord.Intents.all())

# Chemins centralisés pour les fichiers et exécutables
PATHS = {
    'token_file': "C:/Users/danie/Mon Drive/Bot Python Discord/token.txt",
    'gpt_token_file': "C:/Users/danie/Mon Drive/Bot Python Discord/tokengpt.txt",
    'ffmpeg_exe': r"C:/Users/Danie/Mon Drive/Bot Python Discord/ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe",
    'gpt_logs': "C:/Users/danie/Mon Drive/Bot Python Discord/gptlogs.txt",
    'dalle_logs': "C:/Users/danie/Mon Drive/Bot Python Discord/dallelogs.txt",
    'warns_json': "./Autres/warns.json",
    'levels_json': "./Autres/levels.json",
    'banned_words_json': "./Autres/banned_words.json",
    'hilaire2_png': "./Autres/hilaire2.png",
    'hilaire_png': "./Autres/hilaire.png",
    '8ball_png': "./Autres/8ball.png",
    'info_png': "./Autres/info.png",
    'version_jpg': "./Autres/version.jpg",
    'sounds_dir': "./Sounds",
    'cogs_dir': "./cogs"
}

# Configuration centralisée
CONFIG = {
    'webhook_url': "https://discord.com/api/webhooks/1433124903397359673/FTyJEbBq0cxVGx_kwaws1D5WRhPVq5MnQgko4ZqbZMqOa6DJoYbZOwpOVkXiV8oFYIQl",
    'target_user_id': 745923070736465940,
}

# Ajouter les chemins et la config au client pour y accéder depuis les cogs
client.paths = PATHS
client.config = CONFIG

activities = cycle([
    Activity(name='Crococlip 🐊', type=discord.ActivityType.playing),
    Activity(name='Geogebra Mode Examen 📊', type=discord.ActivityType.playing),
    Activity(name='Coding 👨‍💻', type=ActivityType.listening),
    Activity(name='MBN Modding 🔧', type=ActivityType.streaming, url='https://www.youtube.com/watch?v=nPeqfo4kkGw'),
    Activity(name='Samsung Watch 5 Pro ⌚', type=discord.ActivityType.playing),
    Activity(name='Chat GPT 🧠', type=discord.ActivityType.competing),
    Activity(name='Dall E 🎈', type=discord.ActivityType.competing),
    Activity(name='ZXZ AI 😏', type=discord.ActivityType.watching),
])


# Définir les commandes slash AVANT on_ready()
@client.tree.command(name="ping", description="Affiche le ping du bot en ms")
async def ping(interaction: discord.Interaction):
    bot_latency = round(client.latency * 1000)
    await interaction.response.send_message(f"Pong! {bot_latency} ms.")


@client.event
async def on_message(message):
    if client.user.mentioned_in(message) and not ("@everyone" in message.content or "@here" in message.content):
        async with message.channel.typing():
            await asyncio.sleep(1)  # Simulation de l'écriture du bot (1 seconde dans cet exemple)
            await message.channel.send(f"Oh salut {message.author.mention}, fais ``=helps`` pour connaître les différentes commandes.")
    else:
        await client.process_commands(message)


@client.event
async def on_ready():
    await asyncio.sleep(1)
    change_activity.start()
    
    # Synchroniser les commandes slash après que le bot soit connecté
    # ATTENTION: Les commandes peuvent prendre jusqu'à 1 heure pour apparaître
    try:
        synced = await client.tree.sync()
        print(f"\n Synchronisé {len(synced)} commande(s) slash")
        for cmd in synced:
            print(f"   - /{cmd.name}")
    except Exception as e:
        print(f"\n Erreur lors de la synchronisation des commandes slash: {e}")
        print("Vérifiez que le bot a été invité avec le scope 'applications.commands'")
        traceback.print_exc()
    
    print("")
    print("NOTE: Les commandes slash peuvent prendre jusqu'à 1 heure pour apparaître.")
    print("      Si elles n'apparaissent pas, réinvitez le bot avec le scope 'applications.commands'")
    print("")


async def load():
    # Utiliser le chemin centralisé depuis main.py
    cogs_dir = PATHS['cogs_dir']
    for filename in os.listdir(cogs_dir):
        if filename.endswith(".py"):
            try:
                await client.load_extension(f"cogs.{filename[:-3]}")
                print(f"Chargé: cogs.{filename[:-3]}")
            except Exception as e:
                print(f"Erreur lors du chargement de cogs.{filename[:-3]}: {e}")


@tasks.loop(seconds=7)
async def change_activity():
    activity = next(activities)
    await client.change_presence(activity=activity)
   
# show if commands exist
@client.event    
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(title= "Commande inconnue", description="Utilisez **=helps** pour la liste des commandes", color=discord.Color.red())
        embed.set_image(url=ctx.guild.icon)
        embed.set_footer(text=Help.version1)
        await ctx.send(embed=embed, delete_after=10) 
        
    if isinstance(ctx.channel, discord.TextChannel):
        await ctx.message.delete()      

# stop the bot
@client.command()
@commands.is_owner()
async def stop(ctx):
    await ctx.message.delete()
    bot_latency = round(client.latency * 1000)
    embed = discord.Embed(title= "Arrêt", description=f"Le Bot s'arrête Ping {bot_latency} ms.", color=discord.Color.red())
    embed.set_footer(text=Help.version1)
    with open(PATHS['hilaire2_png'], "rb") as f:
        image_data = f.read()
    embed.set_thumbnail(url="attachment://hilaire2.png")
    embed.set_image(url=ctx.guild.icon)
    await ctx.send(embed=embed, file=discord.File(io.BytesIO(image_data), "hilaire2.png"))
    print("")
    print("Arrêté par l'utilisateur")
    print("")
    await client.close()

# Run the bot
if __name__ == "__main__":
    try:
        print("Chargement des extensions...")
        print("")
        # Charger les extensions de manière synchrone avant le démarrage
        loop = asyncio.get_event_loop()
        loop.run_until_complete(load())
        print("")
        print("Démarrage du bot...")
        print("")
        with open(PATHS['token_file'], "r") as f:
            token = f.read().strip()
        client.run(token)
    except Exception as e:
        print("")
        print("Arrêté: impossible de lancer le bot")
        traceback.print_exc()
        time.sleep(10)