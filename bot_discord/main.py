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
import aiohttp



# Initialiser le bot avec les intents nécessaires
intents = discord.Intents.all()
client = commands.Bot(command_prefix="=", intents=intents)

# Chemins centralisés pour les fichiers et exécutables
PATHS = {
    'token_file': "C:/Users/danie/Mon Drive/Bot Python Discord/token.txt",
    'gpt_token_file': "C:/Users/danie/Mon Drive/Bot Python Discord/tokengpt.txt",
    'ffmpeg_exe': r"C:/Users/Danie/Mon Drive/Bot Python Discord/ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe",
    'gpt_logs': "C:/Users/danie/Mon Drive/Bot Python Discord/gptlogs.txt",
    'dalle_logs': "C:/Users/danie/Mon Drive/Bot Python Discord/dallelogs.txt",
    'warns_json': "./json/warns.json",
    'levels_json': "./json/levels.json",
    'banned_words_json': "./json/banned_words.json",
    'hilaire2_png': "./img/hilaire2.png",
    'hilaire_png': "./img/hilaire.png",
    '8ball_png': "./img/8ball.png",
    'info_png': "./img/info.png",
    'version_jpg': "./img/version.jpg",
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

@client.event
async def on_ready():
    print(f"Bot connecté: {client.user}")
    print(f"Nombre de serveurs: {len(client.guilds)}\n")
    
    await asyncio.sleep(1)
    change_activity.start()
    
    # Synchroniser les commandes slash
    try:
        # Synchronisation par serveur (instantanée)
        for guild in client.guilds:
            try:
                await client.tree.sync(guild=guild)
            except:
                pass
        
        # Synchronisation globale
        await client.tree.sync()
        print("Commandes slash synchronisées\n")
    except Exception as e:
        print(f"Erreur lors de la synchronisation: {e}\n")


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
   
# Gestionnaire d'erreurs pour les commandes prefix
@client.event    
async def on_command_error(ctx, error):
    # Supprimer le message de commande si c'est un channel texte
    if isinstance(ctx.channel, discord.TextChannel):
        try:
            await ctx.message.delete()
        except:
            pass
    
    # Commande inconnue
    if isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(title="Commande inconnue", description="Utilisez **=helps** pour la liste des commandes", color=discord.Color.red())
        if ctx.guild:
            embed.set_image(url=ctx.guild.icon)
        embed.set_footer(text=Help.version1)
        await ctx.send(embed=embed, delete_after=10)
        return
    
    # Permissions manquantes pour l'utilisateur
    if isinstance(error, commands.MissingPermissions):
        missing_perms = [perm.replace('_', ' ').title() for perm in error.missing_permissions]
        perms_text = ", ".join(missing_perms)
        embed = discord.Embed(
            title="Permissions insuffisantes",
            description=f"Vous n'avez pas les permissions nécessaires pour utiliser cette commande.\n\n**Permissions requises:** {perms_text}",
            color=discord.Color.red()
        )
        embed.set_footer(text=Help.version1)
        await ctx.send(embed=embed, delete_after=10)
        return
    
    # Permissions manquantes pour le bot
    if isinstance(error, commands.BotMissingPermissions):
        missing_perms = [perm.replace('_', ' ').title() for perm in error.missing_permissions]
        perms_text = ", ".join(missing_perms)
        embed = discord.Embed(
            title="Permissions du bot insuffisantes",
            description=f"Le bot n'a pas les permissions nécessaires pour exécuter cette commande.\n\n**Permissions requises:** {perms_text}",
            color=discord.Color.red()
        )
        embed.set_footer(text=Help.version1)
        await ctx.send(embed=embed, delete_after=10)
        return
    
    # Argument requis manquant
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="Argument manquant",
            description=f"La commande `{ctx.command.name}` nécessite l'argument `{error.param.name}`.\n\nUtilisez **=helps** pour voir la syntaxe correcte.",
            color=discord.Color.red()
        )
        embed.set_footer(text=Help.version1)
        await ctx.send(embed=embed, delete_after=10)
        return
    
    # Argument invalide
    if isinstance(error, commands.BadArgument):
        embed = discord.Embed(
            title="Argument invalide",
            description=f"L'argument fourni est invalide.\n\nUtilisez **=helps** pour voir la syntaxe correcte de la commande `{ctx.command.name}`.",
            color=discord.Color.red()
        )
        embed.set_footer(text=Help.version1)
        await ctx.send(embed=embed, delete_after=10)
        return
    
    # Commande en cooldown
    if isinstance(error, commands.CommandOnCooldown):
        embed = discord.Embed(
            title="Commande en cooldown",
            description=f"Vous devez attendre **{error.retry_after:.1f}** secondes avant de réutiliser cette commande.",
            color=discord.Color.orange()
        )
        embed.set_footer(text=Help.version1)
        await ctx.send(embed=embed, delete_after=error.retry_after)
        return
    
    # Commande réservée au propriétaire
    if isinstance(error, commands.NotOwner):
        embed = discord.Embed(
            title="Accès refusé",
            description="Cette commande est réservée au propriétaire du bot.",
            color=discord.Color.red()
        )
        embed.set_footer(text=Help.version1)
        await ctx.send(embed=embed, delete_after=10)
        return
    
    # Commande uniquement en guild
    if isinstance(error, commands.NoPrivateMessage):
        embed = discord.Embed(
            title="Commande non disponible",
            description="Cette commande ne peut pas être utilisée en message privé.",
            color=discord.Color.red()
        )
        embed.set_footer(text=Help.version1)
        await ctx.send(embed=embed, delete_after=10)
        return
    
    # Erreur de check (pour les checks personnalisés)
    if isinstance(error, commands.CheckFailure):
        embed = discord.Embed(
            title="Vérification échouée",
            description="Vous ne remplissez pas les conditions requises pour utiliser cette commande.",
            color=discord.Color.red()
        )
        embed.set_footer(text=Help.version1)
        await ctx.send(embed=embed, delete_after=10)
        return
    
    # Erreur d'invocation (erreurs générales dans la commande)
    if isinstance(error, commands.CommandInvokeError):
        original_error = error.original
        # Gérer les erreurs Discord spécifiques
        if isinstance(original_error, discord.Forbidden):
            embed = discord.Embed(
                title="Erreur de permissions",
                description="Le bot n'a pas les permissions nécessaires pour effectuer cette action.",
                color=discord.Color.red()
            )
            embed.set_footer(text=Help.version1)
            try:
                await ctx.send(embed=embed, delete_after=10)
            except:
                pass
            return
        elif isinstance(original_error, discord.NotFound):
            embed = discord.Embed(
                title="Ressource introuvable",
                description="La ressource demandée n'a pas été trouvée.",
                color=discord.Color.red()
            )
            embed.set_footer(text=Help.version1)
            try:
                await ctx.send(embed=embed, delete_after=10)
            except:
                pass
            return
        else:
            # Autres erreurs - afficher un message générique
            embed = discord.Embed(
                title="Erreur lors de l'exécution",
                description="Une erreur s'est produite lors de l'exécution de la commande.",
                color=discord.Color.red()
            )
            embed.set_footer(text=Help.version1)
            try:
                await ctx.send(embed=embed, delete_after=10)
            except:
                pass
            # Logger l'erreur pour le débogage
            command_name = ctx.command.name if ctx.command else 'inconnue'
            print(f"\nErreur dans la commande {command_name}:")
            traceback.print_exception(type(original_error), original_error, original_error.__traceback__)
            return
    
    # Pour toutes les autres erreurs non gérées
    print(f"\nErreur non gérée dans {ctx.command.name if ctx.command else 'commande inconnue'}:")
    traceback.print_exception(type(error), error, error.__traceback__)


# Gestionnaire d'erreurs pour les commandes slash
@client.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    # Fonction helper pour répondre à l'interaction
    async def send_error_embed(embed):
        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            # Si ça échoue, essayer avec followup
            try:
                await interaction.followup.send(embed=embed, ephemeral=True)
            except:
                pass
    
    # Permissions manquantes pour l'utilisateur
    if isinstance(error, app_commands.MissingPermissions):
        missing_perms = [perm.replace('_', ' ').title() for perm in error.missing_permissions]
        perms_text = ", ".join(missing_perms)
        embed = discord.Embed(
            title="Permissions insuffisantes",
            description=f"Vous n'avez pas les permissions nécessaires pour utiliser cette commande.\n\n**Permissions requises:** {perms_text}",
            color=discord.Color.red()
        )
        embed.set_footer(text=Help.version1)
        await send_error_embed(embed)
        return
    
    # Permissions manquantes pour le bot
    if isinstance(error, app_commands.BotMissingPermissions):
        missing_perms = [perm.replace('_', ' ').title() for perm in error.missing_permissions]
        perms_text = ", ".join(missing_perms)
        embed = discord.Embed(
            title="Permissions du bot insuffisantes",
            description=f"Le bot n'a pas les permissions nécessaires pour exécuter cette commande.\n\n**Permissions requises:** {perms_text}",
            color=discord.Color.red()
        )
        embed.set_footer(text=Help.version1)
        await send_error_embed(embed)
        return
    
    # Commande en cooldown
    if isinstance(error, app_commands.CommandOnCooldown):
        embed = discord.Embed(
            title="Commande en cooldown",
            description=f"Vous devez attendre **{error.retry_after:.1f}** secondes avant de réutiliser cette commande.",
            color=discord.Color.orange()
        )
        embed.set_footer(text=Help.version1)
        await send_error_embed(embed)
        return
    
    # Commande réservée au propriétaire
    if isinstance(error, app_commands.NotOwner):
        embed = discord.Embed(
            title="Accès refusé",
            description="Cette commande est réservée au propriétaire du bot.",
            color=discord.Color.red()
        )
        embed.set_footer(text=Help.version1)
        await send_error_embed(embed)
        return
    
    # Erreur de check
    if isinstance(error, app_commands.CheckFailure):
        embed = discord.Embed(
            title="Vérification échouée",
            description="Vous ne remplissez pas les conditions requises pour utiliser cette commande.",
            color=discord.Color.red()
        )
        embed.set_footer(text=Help.version1)
        await send_error_embed(embed)
        return
    
    # Erreur d'invocation
    if isinstance(error, app_commands.CommandInvokeError):
        original_error = error.original
        # Gérer les erreurs Discord spécifiques
        if isinstance(original_error, discord.Forbidden):
            embed = discord.Embed(
                title="Erreur de permissions",
                description="Le bot n'a pas les permissions nécessaires pour effectuer cette action.",
                color=discord.Color.red()
            )
            embed.set_footer(text=Help.version1)
            await send_error_embed(embed)
            return
        elif isinstance(original_error, discord.NotFound):
            embed = discord.Embed(
                title="Ressource introuvable",
                description="La ressource demandée n'a pas été trouvée.",
                color=discord.Color.red()
            )
            embed.set_footer(text=Help.version1)
            await send_error_embed(embed)
            return
        else:
            # Autres erreurs
            embed = discord.Embed(
                title="Erreur lors de l'exécution",
                description="Une erreur s'est produite lors de l'exécution de la commande.",
                color=discord.Color.red()
            )
            embed.set_footer(text=Help.version1)
            await send_error_embed(embed)
            # Logger l'erreur pour le débogage
            command_name = interaction.command.name if interaction.command else 'inconnue'
            print(f"\nErreur dans la commande slash {command_name}:")
            traceback.print_exception(type(original_error), original_error, original_error.__traceback__)
            return
    
    # Pour toutes les autres erreurs non gérées
    embed = discord.Embed(
        title="Erreur",
        description="Une erreur inattendue s'est produite.",
        color=discord.Color.red()
    )
    embed.set_footer(text=Help.version1)
    await send_error_embed(embed)
    command_name = interaction.command.name if interaction.command else 'inconnue'
    print(f"\nErreur non gérée dans la commande slash {command_name}:")
    traceback.print_exception(type(error), error, error.__traceback__)      

# Commande pour re-synchroniser les commandes slash
@client.command(name="sync", aliases=["syncslash", "reloadslash"])
@commands.is_owner()
async def sync_commands(ctx):
    """Re-synchronise les commandes slash (owner only)"""
    if isinstance(ctx.channel, discord.TextChannel):
        await ctx.message.delete()
    
    try:
        # Message intermédiaire
        embed = discord.Embed(
            title="🔄 Synchronisation en cours...",
            description="Synchronisation des commandes slash...",
            color=discord.Color.orange()
        )
        embed.set_footer(text=Help.version1)
        status_msg = await ctx.send(embed=embed)
        
        # Synchroniser sur le serveur actuel
        synced_guild = await client.tree.sync(guild=ctx.guild)
        # Synchroniser globalement
        synced_global = await client.tree.sync()
        
        success_embed = discord.Embed(
            title="✓ Synchronisation réussie",
            description=f"Commandes synchronisées sur '{ctx.guild.name}'",
            color=discord.Color.green()
        )
        
        if synced_guild or synced_global:
            count = len(synced_guild) if synced_guild else len(synced_global) if synced_global else 0
            success_embed.add_field(
                name="Commandes synchronisées",
                value=f"{count} commande(s) disponible(s)",
                inline=False
            )
        
        success_embed.set_footer(text=Help.version1)
        await status_msg.edit(embed=success_embed)
        
        # Supprimer le message après 10 secondes
        await asyncio.sleep(10)
        try:
            await status_msg.delete()
        except:
            pass
            
    except Exception as e:
        error_embed = discord.Embed(
            title="✗ Erreur de synchronisation",
            description=f"Erreur: {str(e)}",
            color=discord.Color.red()
        )
        error_embed.set_footer(text=Help.version1)
        try:
            await status_msg.edit(embed=error_embed)
            await asyncio.sleep(10)
            try:
                await status_msg.delete()
            except:
                pass
        except:
            await ctx.send(embed=error_embed, delete_after=10)

# Commande pour diagnostiquer les problèmes de commandes slash
@client.command(name="slashinfo", aliases=["slashdebug", "cmdinfo"])
@commands.is_owner()
async def slash_info(ctx):
    """Affiche des informations de diagnostic sur les commandes slash (owner only)"""
    if isinstance(ctx.channel, discord.TextChannel):
        await ctx.message.delete()
    
    embed = discord.Embed(
        title="🔍 Diagnostic des Commandes Slash",
        color=discord.Color.blue()
    )
    
    # Informations du bot
    embed.add_field(
        name="Bot Information",
        value=f"**Nom:** {client.user.name}\n**ID:** {client.user.id}",
        inline=False
    )
    
    # Commandes locales
    local_commands = []
    try:
        commands_list = client.tree.get_commands()
        for cmd in commands_list:
            local_commands.append(cmd.name)
    except:
        pass
    
    embed.add_field(
        name="Commandes Enregistrées",
        value=f"{len(local_commands)} commande(s): {', '.join([f'`/{cmd}`' for cmd in local_commands]) if local_commands else 'Aucune'}", 
        inline=False
    )
    
    # Lien d'invitation
    invite_url = f"https://discord.com/api/oauth2/authorize?client_id={client.user.id}&permissions=8&scope=bot%20applications.commands"
    embed.add_field(
        name="🔗 Lien d'Invitation",
        value=f"[Cliquez ici]({invite_url})",
        inline=False
    )
    
    embed.set_footer(text=Help.version1)
    await ctx.send(embed=embed, delete_after=30)

# Commande pour effacer toutes les commandes slash
@client.command(name="clearslash", aliases=["clearslashcommands", "deleteslash"])
@commands.is_owner()
async def clear_slash_commands(ctx):
    """Efface toutes les commandes slash de Discord (owner only)"""
    if isinstance(ctx.channel, discord.TextChannel):
        await ctx.message.delete()
    
    status_msg = None
    try:
        # Message intermédiaire
        embed = discord.Embed(
            title="🗑️ Suppression des commandes slash",
            description="Suppression en cours...",
            color=discord.Color.orange()
        )
        embed.set_footer(text=Help.version1)
        status_msg = await ctx.send(embed=embed)
        
        # Obtenir l'application ID pour compter les commandes avant suppression
        app_info = await client.application_info()
        application_id = app_info.id
        
        # Compter les commandes avant suppression
        try:
            global_commands_before = await client.http.get_global_commands(application_id)
            count_global_before = len(global_commands_before)
        except:
            count_global_before = 0
        
        guild_counts_before = {}
        for guild in client.guilds:
            try:
                guild_commands = await client.http.get_guild_commands(application_id, guild.id)
                guild_counts_before[guild.id] = len(guild_commands)
            except:
                guild_counts_before[guild.id] = 0
        
        # Méthode recommandée : clear_commands() puis sync()
        # Cette méthode synchronise un arbre vide, ce qui supprime toutes les commandes
        
        # 1. Effacer les commandes globales
        client.tree.clear_commands(guild=None)
        await client.tree.sync(guild=None)
        
        # 2. Effacer les commandes par serveur
        synced_guilds = 0
        for guild in client.guilds:
            try:
                client.tree.clear_commands(guild=guild)
                await client.tree.sync(guild=guild)
                synced_guilds += 1
            except Exception:
                continue
        
        # Vérifier que les commandes ont bien été supprimées
        try:
            global_commands_after = await client.http.get_global_commands(application_id)
            count_global_after = len(global_commands_after)
        except:
            count_global_after = 0
        
        total_deleted_global = count_global_before - count_global_after
        total_deleted_guild = sum(guild_counts_before.values())
        
        # Créer l'embed de résultat
        success_embed = discord.Embed(
            title="✅ Commandes slash supprimées",
            description="Toutes les commandes slash ont été supprimées.",
            color=discord.Color.green()
        )
        
        if count_global_before > 0:
            success_embed.add_field(
                name="Commandes globales",
                value=f"{count_global_before} → {count_global_after} (supprimées: {total_deleted_global})",
                inline=False
            )
        
        if sum(guild_counts_before.values()) > 0:
            success_embed.add_field(
                name="Commandes par serveur",
                value=f"Supprimées de {synced_guilds} serveur(s)",
                inline=False
            )
        
        success_embed.add_field(
            name="⚠️ Important",
            value="Les commandes ont été supprimées. **Redémarrez Discord** ou attendez quelques minutes pour que les changements soient visibles. Les commandes peuvent rester en cache côté client Discord.",
            inline=False
        )
        
        success_embed.set_footer(text=Help.version1)
        await status_msg.edit(embed=success_embed)
        
        # Supprimer le message après 10 secondes
        await asyncio.sleep(10)
        try:
            await status_msg.delete()
        except:
            pass
        
    except Exception as e:
        error_embed = discord.Embed(
            title="✗ Erreur de suppression",
            description=f"Erreur: {str(e)}",
            color=discord.Color.red()
        )
        error_embed.set_footer(text=Help.version1)
        try:
            if status_msg:
                await status_msg.edit(embed=error_embed)
                await asyncio.sleep(10)
                try:
                    await status_msg.delete()
                except:
                    pass
            else:
                await ctx.send(embed=error_embed, delete_after=10)
        except:
            await ctx.send(embed=error_embed, delete_after=10)

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