import discord
from discord.ext import commands
import io
import requests
from cogs import Help
import traceback
from datetime import datetime

version1="Bot V.2910-25"
version2 ="`optimization, fixed bugs and added new commands`"


class Help(commands.Cog):   
    def __init__(self, client):
        self.target_user_id = client.config['target_user_id']  # Replace with your Discord user ID
        self.client = client
        self.webhook_url = client.config['webhook_url'] # Remplacez WEBHOOK
 

    @commands.command(name="report")
    async def report(self, ctx, *, message: str):
        """Signaler un bug"""
        if isinstance(ctx.channel, discord.TextChannel):
            await ctx.message.delete()
            
        ticket_number = datetime.now().strftime("%d%m%Y")  # Créez un numéro de ticket basé sur la date et l'heure
        data = {
            "content": f"**Bug signalé !**\n\nTicket: **#{ticket_number}{ctx.author.name}**\nPar: **{ctx.author.name}**\nID: **{ctx.author.id}**\nMention: {ctx.author.mention}\n\nContenu: {message}\n\n**{version1}**"
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
            embedc2.set_footer(text=version1)
            await user.send(embed=embedc2)
            
            # Envoyer un message de confirmation dans le canal actuel
            embedc = discord.Embed(title="Signalement", description="Merci d'avoir signalé ce bug.", color=discord.Color.green())
            embedc.add_field(name="",value=f"Ticket : **#{ticket_number}{ctx.author.name}**", inline=False)
            embedc.add_field(name="",value="Nous allons le corriger dès que possible.", inline=False)
            embedc.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embedc.set_footer(text=version1)
            await ctx.send(embed=embedc, delete_after=5)
        else:
            embedc1 = discord.Embed(title="Erreur de signalement.", description="Erreur lors de l'envoi du message.", color=discord.Color.red())
            embedc1.add_field(name="",value="Veuillez réessayer plus tard.", inline=False)
            embedc1.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
            embedc1.set_footer(text=version1)
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
        embed_message.set_footer(text=version1)

        embed_message2 = discord.Embed(
            title="Helps Soundboard",
            description="Toutes les commandes de Soundboard",
            color=discord.Color.random()
        )

        embed_message2.set_author(
            name=f"Demandé par {ctx.author.name}",
            icon_url=ctx.author.avatar
        )
        
        embed_message2.add_field(name="slist", value="Liste tous les sons disponibles =slist")
        embed_message2.add_field(name="splay", value="Joue un son =splay [numéro] (ex: =splay 1)")
        embed_message2.add_field(name="sjoin", value="Fait rejoindre le bot au salon vocal =sjoin (besoin d'être en vocal)")
        embed_message2.add_field(name="sleave", value="Fait quitter le bot du salon vocal =sleave")
        embed_message2.add_field(name="sstop", value="Arrête le son en cours =sstop")
        embed_message2.add_field(name="srandom", value="Joue des sons aléatoires toutes les 1-5 minutes =srandom")
        embed_message2.add_field(name="srandomskip", value="Skip le son aléatoire en cours =srandomskip")
        embed_message2.add_field(name="srandomstop", value="Arrête la lecture aléatoire =srandomstop")
        embed_message2.add_field(name="vkick", value="Expulse un utilisateur du vocal =vkick [@user] ou sans mention pour tous (admin perms only)")
        embed_message2.add_field(name="tts", value="Fait parler le bot =tts [langue] [volume] [texte] (ex: =tts fr 3.0 Bonjour)")
        
        
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
        embed_message7.add_field(name="play", value="Joue une vidéo YouTube =play [URL]")
        embed_message7.add_field(name="search", value="Recherche une vidéo YouTube =search [recherche]")
        embed_message7.add_field(name="skip", value="Skip la vidéo en cours =skip")
        embed_message7.add_field(name="stopm", value="Arrête la lecture =stopm")
        embed_message7.add_field(name="pause", value="Met en pause la vidéo =pause")
        embed_message7.add_field(name="resume", value="Reprend la vidéo =resume")
        embed_message7.add_field(name="queue", value="Affiche la file d'attente =queue")
        embed_message7.add_field(name="clearq", value="Vide la file d'attente =clearq")
        embed_message7.add_field(name="loop", value="Active/désactive la boucle =loop")
        embed_message7.set_footer(text=version1)

        await ctx.send(embed=embed_message)
        await ctx.send(embed=embed_message4)
        await ctx.send(embed=embed_message5)
        await ctx.send(embed=embed_message7)
        await ctx.send(embed=embed_message2)
        await ctx.send(embed=embed_message3)
        await ctx.send(embed=embed_message6, file=discord.File(io.BytesIO(image_data), "info.png"))
    
    
    @commands.command(aliases=["v"])
    async def version(self, ctx):
        if isinstance(ctx.channel, discord.TextChannel):
            await ctx.message.delete()
        embed = discord.Embed(title="Versions du Bot", color=discord.Color.random())
        embed.set_author(name=f"Demandé par {ctx.author.name}", icon_url=ctx.author.avatar)
        embed.add_field(name="", value="")
        embed.add_field(name="Last Version", value=version1)
        embed.add_field(name="Update Logs", value=version2)
        embed.add_field(name="", value="")
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
        embed.set_footer(text=version1)
        await ctx.send(embed=embed)



    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user:
            return  # Ignore les messages envoyés par le bot lui-même
        
        if isinstance(message.channel, discord.DMChannel):
            user = message.author
            content = message.content
            
            # Vérifie si le message est une commande ou une mention
            if content.startswith("=") or message.mention_everyone or self.client.user in message.mentions:
                return  # Ignore les messages de commande ou les mentions
            
            # Vérifier si c'est une réponse à un MP initié par la commande =mp
            mods_cog = self.client.get_cog('Mods')
            if mods_cog and hasattr(mods_cog, 'mp_conversations'):
                if user.id in mods_cog.mp_conversations:
                    # C'est une réponse à un MP initié par =mp
                    original_sender_id = mods_cog.mp_conversations[user.id]
                    original_sender = self.client.get_user(original_sender_id)
                    
                    if original_sender:
                        await original_sender.send(f"**Réponse de {user} ({user.mention}):**\n\n{content}")
                    return
            
            # Sinon, forwarder au target_user_id comme avant
            target_user = self.client.get_user(self.client.config['target_user_id'])
            
            if target_user:
                await target_user.send(f"Message privé de **{user}**: \n\n{content}")


async def setup(client):
    await client.add_cog(Help(client))