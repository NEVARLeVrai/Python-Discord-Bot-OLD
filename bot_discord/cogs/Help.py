import discord
from discord.ext import commands
import io
import requests
import traceback
from datetime import datetime
import os
import json

# Variable version1 pour compatibilité (sera remplacée par get_current_version quand possible)
version1 = "Bot V.NULL"

def get_version_info(client):
    """Lit les informations de version depuis le fichier update_logs.json"""
    try:
        update_logs_path = client.paths['update_logs_json']
        if os.path.exists(update_logs_path):
            with open(update_logs_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        else:
            # Valeurs par défaut si le fichier n'existe pas
            print(f"Fichier update_logs.json introuvable à: {update_logs_path}")
            return {
                "current_version": "Bot V.NULL",
                "history": []
            }
    except Exception as e:
        print(f"Erreur lors de la lecture de update_logs.json: {e}")
        import traceback
        traceback.print_exc()
        return {
            "current_version": "Bot V.NULL",
            "history": []
        }

def get_current_version(client):
    """Retourne la version actuelle"""
    data = get_version_info(client)
    return data.get("current_version", "Bot V.NULL")

def get_latest_logs(client):
    """Retourne les logs de la dernière version"""
    data = get_version_info(client)
    history = data.get("history", [])
    if history:
        return history[0].get("logs", "Aucun log disponible.")
    return "Aucun log de mise à jour disponible."

def get_all_history(client):
    """Retourne tout l'historique des versions"""
    data = get_version_info(client)
    return data.get("history", [])


class Help(commands.Cog):   
    def __init__(self, client):
        self.target_user_id = client.config['target_user_id']  # Replace with your Discord user ID
        self.client = client
        self.webhook_url = client.config['webhook_url'] # Remplacez WEBHOOK
    
    def get_version_footer(self):
        """Helper pour obtenir la version pour les footers"""
        return get_current_version(self.client)
 

    @commands.command(name="report")
    async def report(self, ctx, *, message: str):
        """Signaler un bug"""
        if isinstance(ctx.channel, discord.TextChannel):
            await ctx.message.delete()
            
        ticket_number = datetime.now().strftime("%d%m%Y")  # Créez un numéro de ticket basé sur la date et l'heure
        data = {
            "content": f"**Bug signalé !**\n\nTicket: **#{ticket_number}{ctx.author.name}**\nPar: **{ctx.author.name}**\nID: **{ctx.author.id}**\nMention: {ctx.author.mention}\n\nContenu: {message}\n\n**{self.get_version_footer()}**"
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(self.client.config['webhook_url'], json=data, headers=headers)
        
        if response.status_code == 204:
            # Envoyer un message à l'utilisateur avec le numéro de ticket
            user = ctx.author
            embedc2 = discord.Embed(title="Signalement", description="Votre rapport de bug a été enregistré avec succès.", color=discord.Color.green())
            embedc2.add_field(name="",value=f"Ticket : **#{ticket_number}{ctx.author.name}**", inline=False)
            embedc2.add_field(name="",value="Nous allons le corriger dès que possible!", inline=False)
            embedc2.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embedc2.set_footer(text=self.get_version_footer())
            await user.send(embed=embedc2)
            
            # Envoyer un message de confirmation dans le canal actuel
            embedc = discord.Embed(title="Signalement", description="Merci d'avoir signalé ce bug.", color=discord.Color.green())
            embedc.add_field(name="",value=f"Ticket : **#{ticket_number}{ctx.author.name}**", inline=False)
            embedc.add_field(name="",value="Nous allons le corriger dès que possible.", inline=False)
            embedc.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embedc.set_footer(text=self.get_version_footer())
            await ctx.send(embed=embedc, delete_after=5)
        else:
            embedc1 = discord.Embed(title="Erreur de signalement.", description="Erreur lors de l'envoi du message.", color=discord.Color.red())
            embedc1.add_field(name="",value="Veuillez réessayer plus tard.", inline=False)
            embedc1.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embedc1.set_footer(text=self.get_version_footer())
            await ctx.send(embed=embedc1, delete_after=5)


        
    @commands.command()
    async def helps(self, ctx):
        if isinstance(ctx.channel, discord.TextChannel):
            await ctx.message.delete()

        embed_message = discord.Embed(
            title="Helps",
            description="Toutes les commandes",
            color=discord.Color.random()
        )

        embed_message.set_author(
            name=f"Demandé par {ctx.author.name}",
            icon_url=ctx.author.avatar
        )

        embed_message.add_field(name="helps", value="Affiche ce message =helps")
        embed_message.add_field(name="ping", value="Affiche le ping du bot =ping")
        embed_message.add_field(name="version, v", value="Affiche la version du bot =version")
        embed_message.add_field(name="stop", value="Arrête le bot =stop (owner only)")
        embed_message.add_field(name="report", value="Signale un bug ou feedback =report [message]")
        embed_message.add_field(name="sync, syncslash, reloadslash", value="Re-synchronise les commandes slash =sync (owner only)")
        embed_message.add_field(name="clearslash, clearslashcommands, deleteslash", value="Supprime toutes les commandes slash =clearslash (owner only)")
        embed_message.add_field(name="slashinfo, slashdebug, cmdinfo", value="Affiche des infos de diagnostic sur les commandes slash =slashinfo (owner only)")
        embed_message.set_footer(text=self.get_version_footer())

        embed_message2 = discord.Embed(
            title="Helps Soundboard",
            description="Toutes les commandes de Soundboard",
            color=discord.Color.random()
        )

        embed_message2.set_author(
            name=f"Demandé par {ctx.author.name}",
            icon_url=ctx.author.avatar
        )
        
        embed_message2.add_field(name="slist", value="Liste tous les sons disponibles avec leur durée =slist")
        embed_message2.add_field(name="splay", value="Joue un son =splay [numéro] (ex: =splay 1) - se connecte automatiquement au vocal")
        embed_message2.add_field(name="sleave", value="Fait quitter le bot du salon vocal =sleave")
        embed_message2.add_field(name="sstop", value="Arrête le son en cours =sstop")
        embed_message2.add_field(name="srandom", value="Joue des sons aléatoires toutes les 1-5 minutes =srandom - se connecte automatiquement au vocal")
        embed_message2.add_field(name="srandomskip", value="Skip le son aléatoire en cours =srandomskip")
        embed_message2.add_field(name="srandomstop", value="Arrête la lecture aléatoire =srandomstop")
        embed_message2.add_field(name="vkick", value="Expulse un utilisateur du vocal =vkick [@user] ou sans mention pour tous (admin perms only)")
        embed_message2.add_field(name="tts", value="Fait parler le bot =tts [langue] [volume] [texte] (ex: =tts fr 3.0 Bonjour) - se connecte automatiquement au vocal")
        embed_message2.add_field(name="Formats audio", value="Formats supportés : MP3, MP4, M4A, OGG, OPUS, WAV, FLAC, AAC", inline=False)
        embed_message2.add_field(name="Gestion des conflits", value="Soundboard, YouTube et TTS partagent la connexion vocale. Si un module joue, les autres l'interrompent et jouent directement (pas de file d'attente entre modules différents).", inline=False)
        
        
        embed_message3 = discord.Embed(
        title="Helps Leveling",
        description="Toutes les commandes de Leveling",
        color=discord.Color.random()
        )

        embed_message3.set_author(
            name=f"Demandé par {ctx.author.name}",
            icon_url=ctx.author.avatar
        )
        

        embed_message3.add_field(name="level, lvl", value="Voir votre niveau =level [@user] (optionnel)")
        embed_message3.add_field(name="resetlevel, rsl", value="Reset tous les niveaux =resetlevel (messages perms only)")
        embed_message3.add_field(name="levelsettings, lvls", value="Active/désactive le système de leveling =levelsettings (admins perms only)")
        embed_message3.add_field(name="levelboard, levelleaderboard, levellb, lvlboard", value="Affiche le leaderboard des levels =levelboard")
        embed_message3.add_field(name="⚡ Système automatique", value="Le leveling fonctionne automatiquement : chaque message = +1 XP. Un niveau est atteint quand XP ≥ (niveau+1)². Un message de félicitations est envoyé automatiquement.", inline=False)
        
        embed_message4 = discord.Embed(
        title="Helps Mods",
        description="Toutes les commandes Mods",
        color=discord.Color.random()
        )

        embed_message4.set_author(
            name=f"Demandé par {ctx.author.name}",
            icon_url=ctx.author.avatar
        )
        
      
        embed_message4.add_field(name="clear, prune", value="Supprime des messages =clear [nombre] (messages perms only) max 70 messages")
        embed_message4.add_field(name="cleanraidsimple, clr", value="Supprime un salon par nom =cleanraidsimple [nom] (messages perms only)")
        embed_message4.add_field(name="cleanraidmultiple, clrs", value="Supprime des salons par date =cleanraidmultiple [date] [heure] (messages perms only) ex: =cleanraidmultiple 2024-01-01 14h30")
        embed_message4.add_field(name="warn", value="Avertir un membre =warn [@user] [raison] [nombre] (messages perms only) ex: =warn @user Spam 3")
        embed_message4.add_field(name="resetwarn, warnreset", value="Reset les warns d'un membre =resetwarn [@user] (messages perms only)")
        embed_message4.add_field(name="warnboard, warnleaderboard, warnlb", value="Affiche le leaderboard des warns =warnboard")
        embed_message4.add_field(name="kick", value="Expulse un membre =kick [@user] [raison] (kick perms only)")
        embed_message4.add_field(name="ban", value="Bannit un membre =ban [@user ou ID] [raison] (ban perms only)")
        embed_message4.add_field(name="unban", value="Débannit un membre =unban [ID] (ban perms only)")
        embed_message4.add_field(name="giverole", value="Donne un rôle =giverole [@user] [@role] (owner only)")
        embed_message4.add_field(name="removerole", value="Enlève un rôle =removerole [@user] [@role] (owner only)")
        embed_message4.add_field(name="mp", value="Envoie un message privé =mp [@user ou ID] [message]")
        embed_message4.add_field(name="spam", value="Spam des messages =spam [nombre] [#salon ou mention] [message] (admin perms only)")
        embed_message4.add_field(name="banword, addbannedword", value="Ajoute un mot à la liste des mots bannis =banword [mot] (messages perms only)")
        embed_message4.add_field(name="unbanword, removebannedword", value="Retire un mot de la liste des mots bannis =unbanword [mot] (messages perms only)")
        embed_message4.add_field(name="listbannedwords, bannedwords, bwlist", value="Affiche la liste des mots bannis =listbannedwords (messages perms only)")
        embed_message4.add_field(name="⚠️ Détection automatique", value="Les mots bannis sont automatiquement détectés et supprimés. L'utilisateur reçoit un warn automatique par MP avec la raison \"mot banni utilisé : [mot]\".", inline=False)
        embed_message4.add_field(name="Sanctions automatiques", value="5 warns → timeout 10 min\n10 warns → timeout 10 min\n15 warns → kick automatique\n20 warns → ban automatique", inline=False)
        
        embed_message5 = discord.Embed(
        title="Helps Utility",
        description="Toutes les commandes d'Utility",
        color=discord.Color.random()
        )

        embed_message5.set_author(
            name=f"Demandé par {ctx.author.name}",
            icon_url=ctx.author.avatar
        )
        
      
        embed_message5.add_field(name="gpt", value="Utilise GPT =gpt [votre question]")
        embed_message5.add_field(name="dalle", value="Génère une image avec DALL-E =dalle [votre prompt]")
        embed_message5.add_field(name="repeat, say", value="Envoie un message =repeat [#salon ou @user] [message]")
        embed_message5.add_field(name="8ball, magicball", value="Pose une question à la boule magique =8ball [votre question]")
        embed_message5.add_field(name="hilaire", value="Jeu Hilaire =hilaire")
        embed_message5.add_field(name="deldms, delmp", value="Supprime tous les DMs du bot =deldms (admin perms only)")
        embed_message5.add_field(name="🔗 Conversion automatique", value="Le bot convertit automatiquement les liens sociaux pour des embeds optimisés:\n• TikTok → tiktokez.com (résout les liens courts vm.tiktok.com)\n• Instagram → eeinstagram.com\n• Twitter/X → fxtwitter.com\n• Reddit → vxreddit.com (résout les liens courts redd.it)\n\nLes messages originaux sont supprimés et remplacés par le lien optimisé.", inline=False)
        
        embed_message6 = discord.Embed(
            title="Helps MP",
            description="Commandes disponible en MP",
            color=discord.Color.random()
        )

        embed_message6.set_author(
            name=f"Demandé par {ctx.author.name}",
            icon_url=ctx.author.avatar
        )

        embed_message6.add_field(name="helps", value="Affiche ce message =helps")
        embed_message6.add_field(name="ping", value="Affiche le ping du bot =ping")
        embed_message6.add_field(name="version, v", value="Affiche la version du bot =version")
        embed_message6.add_field(name="stop", value="Arrête le bot =stop (owner only)")
        embed_message6.add_field(name="report", value="Signale un bug ou feedback =report [message]")
        embed_message6.add_field(name="gpt", value="Utilise GPT =gpt [votre question]")
        embed_message6.add_field(name="dalle", value="Génère une image avec DALL-E =dalle [votre prompt]")
       
              
        # Utiliser le chemin centralisé depuis main.py
        with open(self.client.paths['info_png'], "rb") as f:
            image_data = f.read()
        embed_message6.set_thumbnail(url="attachment://info.png")

        embed_message7 = discord.Embed(
            title="Helps YouTube",
            description="Toutes les commandes YouTube",
            color=discord.Color.random()
        )

        embed_message7.set_author(
            name=f"Demandé par {ctx.author.name}",
            icon_url=ctx.author.avatar
        )
        
        embed_message7.add_field(name="leave", value="Déconnecte le bot du vocal =leave")
        embed_message7.add_field(name="play", value="Joue une vidéo YouTube =play [URL] - se connecte automatiquement au vocal")
        embed_message7.add_field(name="search", value="Recherche une vidéo YouTube =search [recherche] - se connecte automatiquement au vocal")
        embed_message7.add_field(name="skip", value="Skip la vidéo en cours =skip")
        embed_message7.add_field(name="stopm", value="Arrête la lecture =stopm")
        embed_message7.add_field(name="pause", value="Met en pause la vidéo =pause")
        embed_message7.add_field(name="resume", value="Reprend la vidéo =resume")
        embed_message7.add_field(name="queue", value="Affiche la file d'attente =queue")
        embed_message7.add_field(name="clearq", value="Vide la file d'attente =clearq")
        embed_message7.add_field(name="loop", value="Active/désactive la boucle =loop")
        embed_message7.add_field(name="File d'attente", value="La file d'attente fonctionne uniquement entre vidéos YouTube. Si Soundboard ou TTS joue, YouTube interrompt et joue directement.", inline=False)
        embed_message7.set_footer(text=self.get_version_footer())

        await ctx.send(embed=embed_message)
        await ctx.send(embed=embed_message4)
        await ctx.send(embed=embed_message5)
        await ctx.send(embed=embed_message7)
        await ctx.send(embed=embed_message2)
        await ctx.send(embed=embed_message3)
        await ctx.send(embed=embed_message6, file=discord.File(io.BytesIO(image_data), "info.png"))
    
    
    @commands.command(aliases=["v"])
    async def version(self, ctx, history: str = None):
        """Affiche la version du bot. Utilisez =version history pour voir l'historique complet"""
        if isinstance(ctx.channel, discord.TextChannel):
            await ctx.message.delete()
        
        version_info = get_version_info(self.client)
        current_version = get_current_version(self.client)
        latest_logs = get_latest_logs(self.client)
        
        # Si l'utilisateur demande l'historique complet
        if history and history.lower() in ["history", "historique", "h"]:
            all_history = get_all_history(self.client)
            if not all_history:
                embed = discord.Embed(
                    title="Historique des Versions",
                    description="Aucun historique disponible.",
                    color=discord.Color.orange()
                )
                embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
                await ctx.send(embed=embed, delete_after=10)
                return
            
            # Créer un embed avec l'historique complet
            embed = discord.Embed(
                title="📜 Historique des Versions",
                description=f"**Version actuelle:** {current_version}\n\n",
                color=discord.Color.blue()
            )
            embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            
            # Ajouter chaque version de l'historique (limité à 10 pour éviter les embeds trop longs)
            for idx, entry in enumerate(all_history[:10], 1):
                version = entry.get("version", "Inconnue")
                date = entry.get("date", "Date inconnue")
                logs = entry.get("logs", "Aucun log")
                # Limiter la longueur des logs pour éviter les embeds trop longs
                if len(logs) > 200:
                    logs = logs[:197] + "..."
                embed.add_field(
                    name=f"{idx}. {version} - {date}",
                    value=f"`{logs}`",
                    inline=False
                )
            
            if len(all_history) > 10:
                embed.set_footer(text=f"Affichage des 10 dernières versions sur {len(all_history)} totales")
            else:
                embed.set_footer(text=f"{len(all_history)} version(s) dans l'historique")
            
            await ctx.send(embed=embed)
            return
        
        # Affichage normal de la version actuelle
        embed = discord.Embed(title="Versions du Bot", color=discord.Color.random())
        embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed.add_field(name="", value="")
        embed.add_field(name="Version Actuelle", value=current_version)
        
        # Ajouter la date de la dernière version si disponible
        all_history = get_all_history(self.client)
        if all_history and len(all_history) > 0:
            latest_date = all_history[0].get("date", "")
            if latest_date:
                embed.add_field(name="Date de la dernière mise à jour", value=latest_date)
        
        embed.add_field(name="Derniers Logs", value=f"`{latest_logs}`", inline=False)
        embed.add_field(name="", value="")
        embed.add_field(name="📜 Historique", value="Utilisez `=version history` pour voir l'historique complet", inline=False)
        embed.add_field(name="Date format", value="`DD/MM/YYYY`")
        
        # Utiliser le chemin centralisé depuis main.py
        with open(self.client.paths['version_jpg'], "rb") as f:
            image_data = f.read()
        embed.set_thumbnail(url="attachment://version.jpg")
        await ctx.send(embed=embed, file=discord.File(io.BytesIO(image_data), "version.jpg"))
        
    @commands.command()
    async def ping(self, ctx):
        if isinstance(ctx.channel, discord.TextChannel):
            await ctx.message.delete()
            
        bot_latency = round(self.client.latency * 1000)
        
        embed = discord.Embed(title=f"Pong! {bot_latency} ms.", color=discord.Color.random())
        embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed.set_footer(text=self.get_version_footer())
        await ctx.send(embed=embed)





async def setup(client):
    await client.add_cog(Help(client))